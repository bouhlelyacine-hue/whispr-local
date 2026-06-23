import time

import keyboard
import pyperclip


def inject_text(text: str) -> None:
    if not text:
        return

    try:
        original = pyperclip.paste()
    except Exception:
        original = ""

    try:
        pyperclip.copy(text)
        time.sleep(0.08)
        keyboard.send("ctrl+v")
        time.sleep(0.12)
    finally:
        pyperclip.copy(original)
