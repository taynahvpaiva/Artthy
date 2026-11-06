import os
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import recomendador

# (sentimento, frase, lembranças que VOCÊ aceita como boa resposta)
CASOS = [
    ("Saudade", "queria ouvir a voz dele",
     ["Esqueci do ferrolho na porta", "Dentista juntos"]),
    ("Raiva", "levei uma bronca e estou irritada",
     ["Esqueci do ferrolho na porta"]),
    ("Tristeza", "tudo parece ter perdido a graça",
     ["Café da tarde no Mangai"]),
    ("Alegria", "quero lembrar de um dia leve e feliz",
     ["Primeiro banho de piscina", "Dia em Cabedelo"]),
    ("Nostalgia", "quero lembrar dos nossos passeios",
     ["Dia em Cabedelo"]),
    ("Amor", "sinto falta do carinho dele",
     ["Lanche no centro"]),
]

for modo in ("tfidf", "embeddings", "hibrido"):
    recomendador.MODO = modo
    acertos_1 = acertos_3 = 0
    print(f"\n=== Modo: {modo} ===")
    for sentimento, frase, aceitas in CASOS:
        top3 = [r["memoria"]["titulo"] for r in
                recomendador.recomendar(sentimento, frase, quantidade=3)]
        no_1 = top3[0] in aceitas
        no_3 = any(t in aceitas for t in top3)
        acertos_1 += no_1
        acertos_3 += no_3
        marca = "OK  " if no_1 else ("top3" if no_3 else "erro")
        print(f"  [{marca}] {sentimento}: {frase[:32]} -> {top3[0]}")
    print(f"  1º lugar: {acertos_1}/{len(CASOS)} | top 3: {acertos_3}/{len(CASOS)}")