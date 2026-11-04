# 💙 Artthy: Memórias que Sentem

Memorial digital inteligente para preservar lembranças de uma pessoa especial.
Em vez de apenas guardar fotos, vídeos, áudios e textos, o Artthy recomenda
lembranças de acordo com o sentimento e o contexto de quem está usando.

## Como funciona

1. A pessoa escolhe um sentimento (saudade, alegria, raiva...) e, se quiser, escreve mais detalhes.
2. O sistema compara o que foi escrito com as descrições das lembranças.
3. Uma lembrança principal é apresentada, junto com outras sugestões relacionadas.
4. A pessoa avalia com 👍, 👎 ou 🤷, e o sistema aprende com essas avaliações.

## Machine Learning

- **TF-IDF:** transforma as descrições das lembranças em representações numéricas.
- **Similaridade de cosseno:** mede o quanto o contexto informado se parece com cada lembrança.
- **Aprendizado com feedback:** as avaliações ajustam as notas por lembrança, por tipo de conteúdo e por sentimento. Uma rejeição (👎) tem efeito imediato na lembrança avaliada.
- **Honestidade sobre o aprendizado:** o sistema avisa quando ainda tem poucas avaliações para afirmar padrões confiáveis.

O sistema não inventa fatos: tudo o que ele mostra vem do que foi cadastrado no acervo.

## Funcionalidades

- [x] Acervo de fotos, vídeos, áudios e textos
- [x] Sentimentos e texto livre
- [x] Recomendação com TF-IDF e similaridade de cosseno
- [x] Aprendizado com feedback, guardado em SQLite
- [x] Histórico de avaliações

## Tecnologias

Python, Streamlit, Pandas, Scikit-learn, SQLite e Pillow. Tudo gratuito e rodando localmente.

## Privacidade

Todos os dados ficam no computador, dentro da pasta `dados`. As lembranças pessoais
**não fazem parte deste repositório**: aqui está apenas o código.

## Como rodar (Windows)

1. Instale o Python 3.10 ou superior.
2. Baixe este repositório e abra a pasta no terminal.
3. Crie o ambiente virtual e instale as bibliotecas:

```
python -m venv venv
venv\Scripts\activate
pip install streamlit pandas scikit-learn pillow
```

4. Crie as pastas onde as lembranças serão guardadas:

```
mkdir dados\fotos, dados\videos, dados\audios, dados\textos
```

5. Inicie o site:

```
streamlit run app.py
```

Para testar com lembranças fictícias, rode `python dados_demo.py` antes de iniciar o site.

## Estrutura do projeto

| Arquivo | Para que serve |
|---|---|
| `app.py` | Interface do site (Streamlit) |
| `banco.py` | Banco de dados SQLite: lembranças e avaliações |
| `recomendador.py` | Machine Learning: TF-IDF, similaridade e aprendizado |
| `dados_demo.py` | Lembranças fictícias para teste |


