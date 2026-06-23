import threading

import keyboard

from config import HOTKEY
from gui import WhisprApp
from recorder import AudioRecorder
from transcriber import Transcriber

recorder = AudioRecorder()
app: WhisprApp | None = None


def _on_hotkey() -> None:
    if app:
        app.toggle()


def _load_model() -> None:
    try:
        t = Transcriber()
        if app:
            app.set_transcriber(t)
        keyboard.add_hotkey(HOTKEY, _on_hotkey, suppress=True)
    except Exception as e:
        if app:
            app.show_load_error(f"Chargement du modèle échoué : {e}")


def main() -> None:
    global app
    app = WhisprApp(recorder)
    threading.Thread(target=_load_model, daemon=True).start()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n[Whispr] Arrêt.")


if __name__ == "__main__":
    main()
