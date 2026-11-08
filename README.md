# Artthy: Memórias que Sentem

Memorial digital para preservar as lembranças de uma pessoa especial. Em vez de só guardar
fotos, vídeos, áudios e textos, o Artthy sugere lembranças a partir do sentimento de quem
está usando e, se quiser, de algumas palavras escritas por essa pessoa.

Tudo roda no computador, de graça, e nada sai dele.

## Como funciona

1. A pessoa escolhe um sentimento (saudade, alegria, gratidão...) e, se quiser, escreve mais detalhes.
2. O sistema compara o que foi escrito com as descrições das lembranças.
3. Uma foto, um áudio e um vídeo aparecem em polaroids; outras lembranças ficam ao lado.
4. A pessoa avalia (gostei, não gostei, sem relação) e o sistema aprende com isso.

O Artthy não inventa fatos: tudo o que ele mostra vem do que foi cadastrado no acervo.

## Machine Learning

- **TF-IDF + similaridade de cosseno:** comparação por palavras entre o texto da busca e as descrições.
- **Embeddings (sentence-transformers, `paraphrase-multilingual-MiniLM-L12-v2`):** comparação por significado, em português. A nota final mistura 70% embeddings e 30% TF-IDF.
- **Aprendizado com feedback:** as avaliações ajustam a nota de cada lembrança e de cada tipo de conteúdo, e ficam guardadas em SQLite. Uma rejeição tem efeito imediato.
- **Honestidade:** o sistema avisa que ainda tem poucas avaliações até chegar a 10.
- **Transcrição de áudio e vídeo (faster-whisper):** é só uma sugestão; a pessoa sempre revisa o texto antes de salvar.

## Telas

- **Sentir:** carta de abertura, escolha do sentimento e as lembranças em polaroids (clique para ampliar).
- **Adicionar:** envio de foto, vídeo, áudio ou texto, com transcrição opcional.
- **Acervo:** disco giratório por tipo e visor com todas as lembranças.
- **Histórico:** o que já foi avaliado e a opção de zerar.

## Privacidade

As lembranças pessoais ficam na pasta `dados/` do computador e **não fazem parte deste repositório**
(veja o `.gitignore`). Aqui está apenas o código.

## Como rodar (Windows)

1. Instale o Python 3.10 ou superior.
2. Baixe este repositório e abra a pasta no terminal.
3. Crie o ambiente virtual e instale as bibliotecas:

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

4. Baixe o modelo de transcrição uma única vez: `python baixar_whisper.py`
5. Inicie o site: `python servidor.py`
6. Abra http://127.0.0.1:5000 no navegador.

Para testar com lembranças fictícias, rode `python dados_demo.py` antes de iniciar o site.

## Estrutura

| Arquivo | Para que serve |
|---|---|
| `servidor.py` | Site (Flask): páginas e rotas |
| `templates/index.html` | Interface do site |
| `banco.py` | Banco SQLite: lembranças e avaliações |
| `recomendador.py` | Machine Learning: TF-IDF, embeddings e aprendizado |
| `transcritor.py`, `baixar_whisper.py` | Transcrição com Whisper |
| `dados_demo.py` | Lembranças fictícias para teste |
| `app.py` | Interface antiga em Streamlit (opcional) |
