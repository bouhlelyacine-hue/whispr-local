from faster_whisper import WhisperModel

from config import LANGUAGE, MODEL_SIZE


class Transcriber:
    def __init__(self):
        print(f"[Whispr] Chargement du modèle '{MODEL_SIZE}' (première fois : téléchargement ~500 Mo)...")
        self.model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
        print("[Whispr] Modèle prêt.")

    def transcribe(self, audio_path: str) -> str:
        try:
            segments, _ = self.model.transcribe(audio_path, language=LANGUAGE)
            return " ".join(seg.text.strip() for seg in segments).strip()
        except Exception as e:
            print(f"[Whispr] ⚠  Erreur lors de la transcription : {e}")
            return ""
