from faster_whisper import WhisperModel

print("Baixando o modelo... pode demorar alguns minutos.")
WhisperModel("small", device="cpu", compute_type="int8")
print("Modelo pronto!")