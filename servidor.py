import os

# O modelo de embeddings já está no seu computador: não precisa consultar a internet.
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import uuid

from flask import Flask, jsonify, render_template, request, send_from_directory

import banco
import recomendador

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 1024  # até 1 GB por envio
PASTA_DADOS = Path(__file__).parent / "dados"

banco.criar_tabelas()


def formatar(r):
    """Transforma um resultado do recomendador em um dicionário simples para o site."""
    m = r["memoria"]
    url = ""
    if m["caminho_arquivo"]:
        url = "/midia/" + m["caminho_arquivo"]
    return {
        "id": m["id"],
        "titulo": m["titulo"],
        "tipo": m["tipo"],
        "descricao": m["descricao"] or m["transcricao"] or "",
        "url": url,
        "nota": round(r["nota"], 3),
    }


# Ajuda o modelo a entender cada sentimento (só palavras sobre o sentimento, nada sobre a sua família).
# Pode editar à vontade. Para desligar, deixe a lista vazia: FRASES_SENTIMENTO = {}
FRASES_SENTIMENTO = {
    "saudade": "saudade, sentir falta de alguém, lembrar com carinho",
    "alegria": "alegria, risadas, momento feliz, felicidade, festa",
    "tristeza": "tristeza, dor, luto, choro, perda",
    "raiva": "raiva, irritação, frustração, injustiça",
    "nostalgia": "nostalgia, tempos antigos, infância, o passado",
    "gratidão": "gratidão, agradecer, ensinamentos, cuidado recebido",
    "medo": "medo, insegurança, proteção, coragem",
    "esperança": "esperança, futuro, superação, seguir em frente",
    "solidão": "solidão, silêncio, estar sozinho, companhia",
    "amor": "amor, carinho, abraço, família, afeto",
    "ansiedade": "ansiedade, preocupação, acalmar, tranquilidade",
}


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/midia/<path:caminho>")
def midia(caminho):
    """Entrega fotos, vídeos e áudios da pasta 'dados' (só dali)."""
    return send_from_directory(PASTA_DADOS, caminho)


@app.get("/api/recomendar")
def api_recomendar():
    sentimento = request.args.get("sentimento", "").strip()
    contexto = request.args.get("contexto", "").strip()
    if not sentimento:
        return jsonify(erro="Escolha um sentimento."), 400

    # O recomendador faz o trabalho de sempre (TF-IDF + embeddings + aprendizado).
    frase = FRASES_SENTIMENTO.get(sentimento.lower(), "")
    contexto_busca = (frase + ". " + contexto).strip(". ") if frase else contexto
    ranking = recomendador.recomendar(sentimento, contexto_busca, quantidade=1000)

    # Em destaque: a melhor foto, o melhor áudio e o melhor vídeo (nessa ordem).
    por_tipo = {}
    for r in ranking:
        tipo = r["memoria"]["tipo"]
        if tipo in ("foto", "audio", "video"):
            por_tipo.setdefault(tipo, []).append(r)
    destaque = [por_tipo[t][0] for t in ("foto", "audio", "video") if t in por_tipo]
    ids = {r["memoria"]["id"] for r in destaque}
    outras = [r for r in ranking if r["memoria"]["id"] not in ids][:12]

    # Aparece no terminal para você conferir o que o sistema pensou.
    print(f"\n[busca] {sentimento!r} + {contexto!r}")
    for r in ranking[:5]:
        print(f"   {r['nota']:+.3f}  {r['memoria']['tipo']:6}  {r['memoria']['titulo']}")

    return jsonify(
        destaque=[formatar(r) for r in destaque],
        candidatos={t: [formatar(r) for r in lista[:6]] for t, lista in por_tipo.items()},
        outras=[formatar(r) for r in outras],
        aprendizado=recomendador.situacao_do_aprendizado()[1],
    )


@app.get("/api/acervo")
def api_acervo():
    """Todas as lembranças guardadas, separadas por tipo (mais recentes primeiro)."""
    grupos = {"foto": [], "video": [], "audio": [], "texto": []}
    for m in banco.listar_memorias():
        tipo = m["tipo"] if m["tipo"] in grupos else "texto"
        grupos[tipo].append({
            "id": m["id"],
            "titulo": m["titulo"],
            "tipo": tipo,
            "descricao": m["descricao"] or m["transcricao"] or "",
            "url": ("/midia/" + m["caminho_arquivo"]) if m["caminho_arquivo"] else "",
        })
    for lista in grupos.values():
        lista.sort(key=lambda x: x["id"], reverse=True)
    return jsonify(grupos)


@app.post("/api/avaliar")
def api_avaliar():
    dados = request.get_json(silent=True) or {}
    try:
        banco.registrar_avaliacao(
            int(dados["memoria_id"]),
            dados["avaliacao"],
            dados.get("sentimento", ""),
            dados.get("contexto", ""),
        )
    except (KeyError, TypeError, ValueError, sqlite3.IntegrityError):
        return jsonify(erro="Avaliação inválida."), 400
    return jsonify(ok=True)


# ---------- adicionar lembranças ----------
PASTAS = {"foto": "fotos", "video": "videos", "audio": "audios"}
EXTENSOES = {
    "foto": {".jpg", ".jpeg", ".png", ".webp", ".gif"},
    "video": {".mp4", ".mov", ".webm", ".m4v"},
    "audio": {".mp3", ".m4a", ".wav", ".ogg", ".opus", ".aac", ".webm"},
}


@app.post("/api/adicionar")
def api_adicionar():
    tipo = request.form.get("tipo", "")
    titulo = request.form.get("titulo", "").strip()
    descricao = request.form.get("descricao", "").strip()
    transcricao = request.form.get("transcricao", "").strip()
    if tipo not in ("foto", "video", "audio", "texto") or not titulo:
        return jsonify(erro="Faltou o tipo ou o título."), 400

    caminho = ""
    if tipo != "texto":
        arquivo = request.files.get("arquivo")
        if not arquivo or not arquivo.filename:
            return jsonify(erro="Escolha o arquivo."), 400
        ext = Path(arquivo.filename).suffix.lower()
        if ext not in EXTENSOES[tipo]:
            aceitos = ", ".join(sorted(EXTENSOES[tipo]))
            return jsonify(erro=f"Formato não aceito para {tipo}. Use: {aceitos}"), 400
        pasta = PASTAS[tipo]
        (PASTA_DADOS / pasta).mkdir(parents=True, exist_ok=True)
        caminho = f"{pasta}/{uuid.uuid4().hex}{ext}"
        arquivo.save(PASTA_DADOS / caminho)

    try:
        banco.adicionar_memoria(tipo, titulo, descricao, transcricao, caminho)
    except Exception as erro:  # mostra o motivo no site em vez de quebrar
        return jsonify(erro=f"Não consegui salvar no banco: {erro}"), 500
    return jsonify(ok=True)


@app.post("/api/transcrever")
def api_transcrever():
    """Transcreve um áudio ou vídeo com o Whisper. O resultado é só uma sugestão: a pessoa revisa."""
    try:
        import transcritor
    except Exception as erro:
        return jsonify(erro=f"Transcrição indisponível: {erro}"), 503
    if not getattr(transcritor, "DISPONIVEL", True):
        return jsonify(erro="O faster-whisper não está instalado."), 503
    arquivo = request.files.get("arquivo")
    if not arquivo:
        return jsonify(erro="Envie o arquivo."), 400
    sufixo = Path(arquivo.filename or "").suffix.lower() or ".tmp"
    with tempfile.NamedTemporaryFile(delete=False, suffix=sufixo) as tmp:
        arquivo.save(tmp)
        caminho_tmp = tmp.name
    try:
        texto = transcritor.transcrever(caminho_tmp)
        if isinstance(texto, (tuple, list)):
            texto = next((t for t in texto if isinstance(t, str)), "")
        elif isinstance(texto, dict):
            texto = texto.get("texto", "")
        return jsonify(texto=(texto or "").strip())
    except Exception as erro:
        return jsonify(erro=f"Não consegui transcrever: {erro}"), 500
    finally:
        Path(caminho_tmp).unlink(missing_ok=True)


# ---------- histórico ----------
def _tabela_avaliacoes(con):
    """Descobre sozinho qual tabela guarda as avaliações."""
    for linha in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
        nome = linha[0]
        colunas = [c[1] for c in con.execute(f'PRAGMA table_info("{nome}")')]
        if "avaliacao" in colunas and "memoria_id" in colunas:
            return nome, colunas
    return None, []


@app.get("/api/historico")
def api_historico():
    titulos = {m["id"]: (m["titulo"], m["tipo"]) for m in banco.listar_memorias()}
    resumo, recentes = {}, []
    with closing(banco.conectar()) as con:
        con.row_factory = sqlite3.Row
        tabela, colunas = _tabela_avaliacoes(con)
        linhas = []
        if tabela:
            filtro, args = "", ()
            if "perfil" in colunas:
                filtro, args = " WHERE perfil = ?", (banco.PERFIL_PADRAO,)
            linhas = con.execute(f'SELECT rowid AS _rid, * FROM "{tabela}"{filtro} ORDER BY rowid DESC', args).fetchall()
    col_data = next((c for c in ("data", "criado_em", "data_hora", "datahora", "momento", "quando") if c in colunas), None)
    for ln in linhas:
        d = dict(ln)
        titulo, tipo = titulos.get(d["memoria_id"], ("(lembrança removida)", "texto"))
        item = resumo.setdefault(d["memoria_id"], {"id": d["memoria_id"], "titulo": titulo, "tipo": tipo,
                                                   "gostei": 0, "nao_gostei": 0, "irrelevante": 0})
        if d["avaliacao"] in item:
            item[d["avaliacao"]] += 1
        if len(recentes) < 15:
            recentes.append({"titulo": titulo, "avaliacao": d["avaliacao"],
                             "sentimento": d.get("sentimento") or "", "contexto": d.get("contexto") or "",
                             "quando": str(d[col_data])[:16] if col_data and d.get(col_data) else ""})
    ordenado = sorted(resumo.values(), key=lambda x: -(x["gostei"] + x["nao_gostei"] + x["irrelevante"]))
    return jsonify(resumo=ordenado, recentes=recentes, total=len(linhas),
                   mensagem=recomendador.situacao_do_aprendizado()[1])


@app.post("/api/zerar")
def api_zerar():
    with closing(banco.conectar()) as con:
        tabela, colunas = _tabela_avaliacoes(con)
        if tabela:
            if "perfil" in colunas:
                con.execute(f'DELETE FROM "{tabela}" WHERE perfil = ?', (banco.PERFIL_PADRAO,))
            else:
                con.execute(f'DELETE FROM "{tabela}"')
            con.commit()
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(debug=True)