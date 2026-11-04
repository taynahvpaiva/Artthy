import unicodedata
from collections import defaultdict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import banco

# Palavras comuns que não ajudam a diferenciar uma lembrança da outra
PALAVRAS_IGNORADAS = [
    "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "do", "da", "dos", "das",
    "em", "no", "na", "nos", "nas", "por", "para", "com", "sem", "e", "ou", "mas",
    "que", "se", "me", "te", "ele", "ela", "eu", "foi", "era", "ser",
    "ter", "tinha", "muito", "muita", "hoje", "ao", "aos", "pelo", "pela", "num", "numa",
]

# Quanto cada avaliação vale (positivo sobe, negativo desce).
# O 👎 pesa mais que o 👍, para uma rejeição ter efeito imediato.
VALOR_AVALIACAO = {"gostei": 0.5, "nao_gostei": -1.0, "irrelevante": -1.5}

# Quantas avaliações o sistema precisa ter para dizer que já aprendeu padrões gerais
MINIMO_PARA_CONFIAR = 10

# Força do ajuste (a similaridade de texto continua sendo a base)
FORCA_AJUSTE = 0.5


def limpar_texto(texto):
    """Deixa tudo minúsculo e sem acentos."""
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def texto_da_memoria(memoria):
    """Junta título, descrição e transcrição: é o que o sistema 'lê' da lembrança."""
    partes = [memoria["titulo"], memoria["descricao"], memoria["transcricao"]]
    return " ".join(p for p in partes if p)


def pontuar_por_similaridade(sentimento, contexto, memorias):
    """TF-IDF + similaridade de cosseno: quanto o texto se parece com cada lembrança."""
    consulta = f"{sentimento} {contexto}".strip()
    textos = [texto_da_memoria(m) for m in memorias]

    ignoradas = [limpar_texto(p) for p in PALAVRAS_IGNORADAS]
    vetorizador = TfidfVectorizer(preprocessor=limpar_texto, stop_words=ignoradas)
    matriz_memorias = vetorizador.fit_transform(textos)
    vetor_consulta = vetorizador.transform([consulta])

    return list(cosine_similarity(vetor_consulta, matriz_memorias)[0])


def calcular_ajustes(memorias, sentimento, avaliacoes):
    """
    Aprende com o histórico. Devolve um ajuste (entre -1 e 1) para cada lembrança,
    combinando três sinais:
      1. a própria lembrança foi bem ou mal avaliada;
      2. o TIPO de lembrança (foto, áudio...) costuma agradar nesse sentimento;
      3. avaliações no MESMO sentimento pesam mais.
    """
    tipo_por_id = {m["id"]: m["tipo"] for m in memorias}

    soma_memoria = defaultdict(float)   # por lembrança
    soma_tipo = defaultdict(float)      # por tipo (só no mesmo sentimento)
    peso_tipo = defaultdict(float)

    for a in avaliacoes:
        valor = VALOR_AVALIACAO.get(a["avaliacao"], 0.0)
        mesmo_sentimento = a["sentimento"] == sentimento
        peso = 1.0 if mesmo_sentimento else 0.4

        soma_memoria[a["memoria_id"]] += valor * peso

        tipo = tipo_por_id.get(a["memoria_id"])
        if tipo and mesmo_sentimento:
            soma_tipo[tipo] += valor
            peso_tipo[tipo] += 1.0

    ajustes = []
    for m in memorias:
        # Sem diluição: uma única avaliação já tem efeito forte (limitado entre -1 e 1)
        ajuste_memoria = max(-1.0, min(1.0, soma_memoria[m["id"]]))
        # O sinal por tipo cresce mais devagar, pois depende de vários exemplos
        ajuste_tipo = soma_tipo[m["tipo"]] / (peso_tipo[m["tipo"]] + 4)
        ajuste = 0.7 * ajuste_memoria + 0.3 * ajuste_tipo
        ajustes.append(max(-1.0, min(1.0, ajuste)))
    return ajustes


def recomendar(sentimento, contexto, quantidade=4, perfil=banco.PERFIL_PADRAO):
    """Combina similaridade de texto com o que foi aprendido nas avaliações."""
    memorias = banco.listar_memorias()
    if not memorias:
        return []

    avaliacoes = banco.listar_avaliacoes(perfil)
    notas_texto = pontuar_por_similaridade(sentimento, contexto, memorias)
    ajustes = calcular_ajustes(memorias, sentimento, avaliacoes)

    resultado = []
    for m, nota, ajuste in zip(memorias, notas_texto, ajustes):
        nota_final = nota + FORCA_AJUSTE * ajuste
        resultado.append({"memoria": m, "nota": nota_final,
                          "nota_texto": nota, "ajuste": ajuste})
    resultado.sort(key=lambda r: r["nota"], reverse=True)
    return resultado[:quantidade]


def situacao_do_aprendizado(perfil=banco.PERFIL_PADRAO):
    """Diz com honestidade o quanto o sistema já tem de base para aprender."""
    total = len(banco.listar_avaliacoes(perfil))
    if total == 0:
        return total, "Ainda não há avaliações. As recomendações usam só o texto."
    if total < MINIMO_PARA_CONFIAR:
        return total, (f"{total} avaliação(ões) registrada(s). Ainda é pouco para "
                       f"afirmar padrões gerais: rejeições e elogios já afetam as "
                       f"mesmas lembranças, mas faltam {MINIMO_PARA_CONFIAR - total} "
                       f"para o aprendizado ficar mais confiável.")
    return total, f"{total} avaliações registradas. O aprendizado já tem uma base razoável."


# Roda só quando você executa "python recomendador.py" diretamente
if __name__ == "__main__":
    pedido = recomendar("Saudade", "hoje é o aniversário dele")
    for r in pedido:
        print(f"final {r['nota']:.3f} | texto {r['nota_texto']:.3f} | "
              f"ajuste {r['ajuste']:+.2f} | {r['memoria']['titulo']}")
    print(situacao_do_aprendizado()[1])