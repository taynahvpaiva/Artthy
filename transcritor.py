import sys
import time

try:
    from faster_whisper import WhisperModel
    DISPONIVEL = True
except ImportError:
    DISPONIVEL = False

# "small" costuma ir bem em português. Se ficar lento, troque por "base".
NOME_MODELO = "small"

_modelo = None


def carregar_modelo():
    """Carrega o modelo uma única vez (roda no seu computador, só com processador)."""
    global _modelo
    if _modelo is None:
        _modelo = WhisperModel(NOME_MODELO, device="cpu", compute_type="int8")
    return _modelo


def transcrever(origem):
    """Recebe o caminho de um áudio (ou um arquivo aberto) e devolve o texto falado."""
    modelo = carregar_modelo()
    segmentos, _ = modelo.transcribe(origem, language="pt", vad_filter=True)
    return " ".join(s.text.strip() for s in segmentos).strip()


# Teste pelo terminal: python transcritor.py caminho\do\audio.opus
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Use: python transcritor.py caminho_do_audio")
    else:
        inicio = time.time()
        print(transcrever(sys.argv[1]))
        print(f"\n(levou {time.time() - inicio:.0f} segundos)")