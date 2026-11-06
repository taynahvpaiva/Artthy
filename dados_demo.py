import banco

banco.criar_tabelas()

EXEMPLOS = [
    ("texto", "Domingo de churrasco",
     "Almoço de domingo em família, todo mundo rindo e conversando no quintal. "
     "Ele fazia churrasco e contava piadas, e a casa ficava cheia de alegria."),
    ("texto", "Conselho sobre dar a volta por cima",
     "Num dia difícil ele me disse para respirar fundo, ter calma e não desistir. "
     "Falou que tudo passa e que a raiva esfria com o tempo."),
    ("texto", "Viagem de carro até a praia",
     "Estrada longa, música tocando no rádio, a gente cantando junto. "
     "Lembrança de liberdade, férias e felicidade."),
    ("texto", "Aniversário com bolo",
     "Festa de aniversário com bolo, parabéns cantado e muita gente reunida. "
     "Ele abraçou forte e disse que tinha orgulho de mim."),
    ("texto", "Dia de pescaria",
     "Acordamos cedo para pescar. Silêncio, paz e conversa tranquila na beira do rio. "
     "Ele ensinou a ter paciência."),
    ("texto", "Discussão boba que virou risada",
     "Brigamos por causa de uma besteira, ficamos com raiva, "
     "mas minutos depois ele fez uma piada e rimos até chorar."),
    ("texto", "Mensagem de carinho",
     "Ele escreveu dizendo que sentia saudade e que me amava muito. "
     "Gratidão por todo o cuidado e pelo apoio nos estudos."),
    ("texto", "Primeiro dia de aula",
     "Ele me levou na escola, deu a mão e disse para não ter medo. "
     "Fiquei ansiosa, mas me senti segura ao lado dele."),
]

titulos_existentes = {m["titulo"] for m in banco.listar_memorias()}
novas = 0
for tipo, titulo, descricao in EXEMPLOS:
    if titulo not in titulos_existentes:
        banco.adicionar_memoria(tipo, titulo, descricao)
        novas += 1

print(f"{novas} lembrança(s) de exemplo adicionada(s).")