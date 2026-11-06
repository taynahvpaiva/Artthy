import uuid
from pathlib import Path

import streamlit as st

import banco
import recomendador
import pandas as pd

st.set_page_config(page_title="Artthy", page_icon="💙", layout="wide")

PASTA_DADOS = Path(__file__).parent / "dados"

# Para cada tipo: pasta onde salvar e extensões aceitas
TIPOS = {
    "foto": {"pasta": "fotos", "extensoes": ["jpg", "jpeg", "png"]},
    "video": {"pasta": "videos", "extensoes": ["mp4"]},
    "audio": {"pasta": "audios", "extensoes": ["mp3", "wav", "ogg", "opus"]},
    "texto": {"pasta": "textos", "extensoes": ["txt"]},
}

SENTIMENTOS = ["Saudade", "Alegria", "Tristeza", "Raiva", "Nostalgia", "Gratidão",
               "Medo", "Esperança", "Solidão", "Amor", "Ansiedade"]

# Garante que as tabelas existem sempre que o site abre
banco.criar_tabelas()


def salvar_arquivo(arquivo, tipo):
    """Guarda o arquivo enviado na pasta certa e devolve o caminho relativo."""
    pasta = TIPOS[tipo]["pasta"]
    extensao = Path(arquivo.name).suffix.lower()
    # nome único, para dois arquivos com o mesmo nome não se sobrescreverem
    nome_final = f"{uuid.uuid4().hex}{extensao}"
    destino = PASTA_DADOS / pasta / nome_final
    destino.write_bytes(arquivo.getbuffer())
    return f"{pasta}/{nome_final}"


def mostrar_midia(memoria):
    """Exibe a foto, vídeo, áudio ou texto de uma lembrança."""
    caminho = PASTA_DADOS / memoria["caminho_arquivo"] if memoria["caminho_arquivo"] else None
    if caminho is None or not caminho.exists():
        return
    if memoria["tipo"] == "foto":
        st.image(str(caminho), width="stretch")
    elif memoria["tipo"] == "video":
        st.video(str(caminho))
    elif memoria["tipo"] == "audio":
        st.audio(str(caminho))
    elif memoria["tipo"] == "texto":
        st.text(caminho.read_text(encoding="utf-8", errors="ignore"))


def avaliar(memoria_id, valor, sentimento, contexto):
    """Guarda a avaliação no banco. Roda quando um botão é clicado."""
    banco.registrar_avaliacao(memoria_id, valor, sentimento, contexto)
    st.toast("Avaliação registrada. Obrigada! 💙")


def botoes_avaliacao(memoria_id, chave, sentimento, contexto):
    """Mostra os três botões de avaliação de uma lembrança."""
    b1, b2, b3 = st.columns(3)
    b1.button("👍 Gostei", key=f"g_{chave}", on_click=avaliar,
              args=(memoria_id, "gostei", sentimento, contexto))
    b2.button("👎 Não gostei", key=f"n_{chave}", on_click=avaliar,
              args=(memoria_id, "nao_gostei", sentimento, contexto))
    b3.button("🤷 Sem relação", key=f"i_{chave}", on_click=avaliar,
              args=(memoria_id, "irrelevante", sentimento, contexto))


# ---------- TELA ----------

st.title("💙 Artthy")
st.caption("Memórias que sentem")

aba_sentir, aba_adicionar, aba_acervo, aba_historico = st.tabs(
    ["💙 Como estou me sentindo", "➕ Adicionar lembrança", "📚 Acervo", "🧠 Histórico"]
)

# ----- ABA 1: SENTIMENTOS E RECOMENDAÇÃO -----
with aba_sentir:
    st.subheader("Como você está se sentindo agora?")

    sentimento = st.radio("Escolha um sentimento", SENTIMENTOS, horizontal=True)
    contexto = st.text_area(
        "Quer contar mais? (opcional)",
        placeholder="Ex.: hoje foi um dia difícil e eu queria ouvir a voz dele...",
    )

    if st.button("Encontrar uma lembrança", type="primary"):
        # guarda o que foi pedido; a lista é recalculada abaixo, a cada atualização
        st.session_state["buscou"] = True
        st.session_state["sentimento"] = sentimento
        st.session_state["contexto"] = contexto

    _, mensagem_aprendizado = recomendador.situacao_do_aprendizado()
    st.caption(f"🧠 {mensagem_aprendizado}")

    if st.session_state.get("buscou"):
        sent = st.session_state["sentimento"]
        ctx = st.session_state["contexto"]

        # Recalcula SEMPRE, usando as avaliações mais recentes do banco
        resultado = recomendador.recomendar(sent, ctx)

        if not resultado:
            st.info("Ainda não há lembranças no acervo. Adicione na outra aba.")
        else:
            st.markdown(f"Buscando para: **{sent}**" + (f" · _{ctx}_" if ctx else ""))

            principal_r = resultado[0]
            principal = principal_r["memoria"]

            st.markdown("### 💙 Uma lembrança para este momento")
            st.markdown(f"**{principal['titulo']}**")
            mostrar_midia(principal)
            if principal["descricao"]:
                st.write(principal["descricao"])
            st.caption(
                f"Nota {principal_r['nota']:.3f} "
                f"(texto {principal_r['nota_texto']:.3f}, "
                f"ajuste do aprendizado {principal_r['ajuste']:+.2f})"
            )
            botoes_avaliacao(principal["id"], "principal", sent, ctx)

            outras = resultado[1:]
            if outras:
                st.markdown("### Outras lembranças relacionadas")
                for i, r in enumerate(outras, start=1):
                    m = r["memoria"]
                    with st.expander(m["titulo"]):
                        mostrar_midia(m)
                        if m["descricao"]:
                            st.write(m["descricao"])
                        st.caption(
                            f"Nota {r['nota']:.3f} "
                            f"(texto {r['nota_texto']:.3f}, "
                            f"ajuste {r['ajuste']:+.2f})"
                        )
                        botoes_avaliacao(m["id"], f"outra{i}", sent, ctx)

# ----- ABA 2: ADICIONAR -----
with aba_adicionar:
    st.subheader("Nova lembrança")

    tipo = st.selectbox(
        "Tipo de lembrança",
        options=list(TIPOS.keys()),
        format_func=lambda t: {"foto": "📷 Foto", "video": "🎬 Vídeo",
                               "audio": "🎙️ Áudio", "texto": "📝 Texto"}[t],
    )

    arquivo = st.file_uploader(
        "Arquivo (opcional para texto digitado)",
        type=TIPOS[tipo]["extensoes"],
    )
    titulo = st.text_input("Título")
    descricao = st.text_area(
        "Descrição",
        help="Conte o que está acontecendo nessa lembrança. "
             "Quanto mais detalhes, melhor o Artthy vai entender.",
    )
    transcricao = ""
    if tipo == "audio":
        transcricao = st.text_area(
            "O que é dito no áudio (transcrição manual)",
            help="Escreva o que a pessoa fala. Isso ajuda muito nas recomendações.",
        )

    if st.button("Salvar lembrança", type="primary"):
        if not titulo.strip():
            st.error("Dê um título para a lembrança.")
        elif arquivo is None and not descricao.strip():
            st.error("Envie um arquivo ou escreva uma descrição.")
        else:
            caminho = salvar_arquivo(arquivo, tipo) if arquivo else ""
            banco.adicionar_memoria(tipo, titulo.strip(), descricao.strip(),
                                    transcricao.strip(), caminho)
            st.success("Lembrança salva! 💙")

# ----- ABA 3: ACERVO -----
with aba_acervo:
    memorias = banco.listar_memorias()
    st.subheader(f"{len(memorias)} lembrança(s) no acervo")

    if not memorias:
        st.info("Ainda não há lembranças. Adicione a primeira na outra aba.")

    for m in memorias:
        with st.expander(f"{m['titulo']}  ·  {m['tipo']}"):
            mostrar_midia(m)

            novo_titulo = st.text_input("Título", m["titulo"], key=f"t{m['id']}")
            nova_desc = st.text_area("Descrição", m["descricao"], key=f"d{m['id']}")
            nova_trans = m["transcricao"]
            if m["tipo"] == "audio":
                nova_trans = st.text_area("Transcrição", m["transcricao"], key=f"tr{m['id']}")

            col1, col2 = st.columns(2)
            if col1.button("Salvar alterações", key=f"s{m['id']}"):
                banco.atualizar_memoria(m["id"], novo_titulo, nova_desc, nova_trans)
                st.success("Alterações salvas.")
                st.rerun()
            if col2.button("🗑️ Excluir", key=f"e{m['id']}"):
                banco.excluir_memoria(m["id"])
                st.rerun()

# ----- ABA 4: HISTÓRICO DE APRENDIZADO -----
with aba_historico:
    st.subheader("O que o Artthy aprendeu")

    avaliacoes = banco.listar_avaliacoes()
    _, msg = recomendador.situacao_do_aprendizado()
    st.caption(f"🧠 {msg}")

    if not avaliacoes:
        st.info("Ainda não há avaliações. Elas aparecem aqui quando você usar os botões.")
    else:
        titulos = {m["id"]: m["titulo"] for m in banco.listar_memorias()}
        nomes = {"gostei": "👍 Gostei", "nao_gostei": "👎 Não gostei",
                 "irrelevante": "🤷 Sem relação"}

        tabela = pd.DataFrame([
            {
                "Quando": a["criado_em"],
                "Lembrança": titulos.get(a["memoria_id"], "(excluída)"),
                "Sentimento": a["sentimento"],
                "Avaliação": nomes.get(a["avaliacao"], a["avaliacao"]),
            }
            for a in avaliacoes
        ])

        st.markdown("#### Resumo por lembrança")
        resumo = (tabela.groupby(["Lembrança", "Avaliação"]).size()
                  .unstack(fill_value=0))
        st.dataframe(resumo, use_container_width=True)

        st.markdown("#### Histórico completo")
        st.dataframe(tabela.iloc[::-1], use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("#### Zerar o aprendizado")
    st.caption("Apaga só as avaliações. As lembranças continuam no acervo.")
    confirmar = st.checkbox("Tenho certeza que quero apagar todas as avaliações")
    if st.button("Zerar avaliações", disabled=not confirmar):
        conexao = banco.conectar()
        conexao.execute("DELETE FROM avaliacoes")
        conexao.commit()
        conexao.close()
        st.rerun()