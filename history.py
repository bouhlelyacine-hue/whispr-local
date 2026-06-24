import hashlib
import json
import os
from base64 import urlsafe_b64encode
from datetime import datetime
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

_DIR = Path(__file__).parent
HISTORY_FILE = _DIR / "history.enc"
SETTINGS_FILE = _DIR / "settings.json"


def _derive_key() -> bytes:
    """Dérive une clé AES depuis l'identité machine+utilisateur via PBKDF2.
    Aucune clé stockée sur le disque — la même clé est recalculée à chaque lancement.
    """
    seed = (
        f"{os.environ.get('COMPUTERNAME', 'machine')}"
        f"-{os.environ.get('USERNAME', 'user')}"
        f"-whispr-local-v1"
    ).encode()
    key_bytes = hashlib.pbkdf2_hmac("sha256", seed, b"whispr-history-salt", 200_000)
    return urlsafe_b64encode(key_bytes)


_fernet_cache: Fernet | None = None


def _fernet() -> Fernet:
    global _fernet_cache
    if _fernet_cache is None:
        _fernet_cache = Fernet(_derive_key())
    return _fernet_cache


# ── SETTINGS ─────────────────────────────────────────────

def load_settings() -> dict:
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"save_history": False}


def save_settings(settings: dict) -> None:
    SETTINGS_FILE.write_text(
        json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ── HISTORY ───────────────────────────────────────────────

def load_entries() -> list[dict]:
    try:
        encrypted = HISTORY_FILE.read_bytes()
        decrypted = _fernet().decrypt(encrypted).decode("utf-8")
        data = json.loads(decrypted)
        return data if isinstance(data, list) else []
    except FileNotFoundError:
        return []
    except (InvalidToken, json.JSONDecodeError):
        # Fichier corrompu ou chiffré avec une clé différente
        print("[Whispr] ⚠ Historique illisible — fichier réinitialisé.")
        clear_file()
        return []


def append_entry(ts: str, text: str) -> None:
    entries = load_entries()
    entries.append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "ts": ts,
        "text": text,
    })
    _write_entries(entries)


def clear_file() -> None:
    _write_entries([])


def _write_entries(entries: list[dict]) -> None:
    plaintext = json.dumps(entries, ensure_ascii=False, indent=2).encode("utf-8")
    HISTORY_FILE.write_bytes(_fernet().encrypt(plaintext))
