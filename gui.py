import os
import threading
from datetime import datetime

import customtkinter as ctk
import pyperclip
import pystray
from PIL import Image, ImageDraw

from config import HOTKEY
from injector import inject_text
from overlay import RecordingOverlay
from recorder import AudioRecorder
from transcriber import Transcriber

# UI states: status label + record button configuration
_STATES: dict[str, dict] = {
    "loading":    dict(status="⏳  Chargement du modèle...", status_color="#d29922",
                       btn="🎙  Démarrer",      btn_state="disabled",
                       btn_fg=("#374151", "#374151"), btn_hover=("#374151", "#374151")),
    "ready":      dict(status="● Prêt",           status_color="#3fb950",
                       btn="🎙  Démarrer",      btn_state="normal",
                       btn_fg=("#1f6feb", "#1f6feb"), btn_hover=("#1a5fcc", "#1a5fcc")),
    "recording":  dict(status="🔴  Enregistrement...", status_color="#f85149",
                       btn="⏹  Arrêter",       btn_state="normal",
                       btn_fg=("#7f1d1d", "#7f1d1d"), btn_hover=("#991b1b", "#991b1b")),
    "processing": dict(status="⚙  Transcription...",   status_color="#d29922",
                       btn="⚙  Patientez...",  btn_state="disabled",
                       btn_fg=("#374151", "#374151"), btn_hover=("#374151", "#374151")),
    "error":      dict(status="⚠  Erreur de chargement", status_color="#f85149",
                       btn="🎙  Démarrer",      btn_state="disabled",
                       btn_fg=("#374151", "#374151"), btn_hover=("#374151", "#374151")),
}


class WhisprApp:
    def __init__(self, recorder: AudioRecorder) -> None:
        self.recorder = recorder
        self.transcriber: Transcriber | None = None
        self._is_recording = False
        self._is_processing = False
        self._lock = threading.Lock()
        self._history_widgets: list[ctk.CTkFrame] = []

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("Whispr Local")
        self.root.geometry("420x620")
        self.root.resizable(False, True)
        self.root.configure(fg_color="#0d1117")
        self.root.protocol("WM_DELETE_WINDOW", self._hide)

        self._build_ui()
        self._build_tray()
        self.overlay = RecordingOverlay(self.root)

    # ── UI BUILD ──────────────────────────────────────────

    def _build_ui(self) -> None:
        header = ctk.CTkFrame(self.root, fg_color="#161b22", corner_radius=0, height=52)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="🎙  Whispr Local",
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#e6edf3",
        ).pack(side="left", padx=20, pady=14)

        self.status_lbl = ctk.CTkLabel(
            self.root, text=_STATES["loading"]["status"],
            font=ctk.CTkFont(size=13), text_color=_STATES["loading"]["status_color"],
        )
        self.status_lbl.pack(pady=(18, 8))

        self.record_btn = ctk.CTkButton(
            self.root,
            text=_STATES["loading"]["btn"],
            font=ctk.CTkFont(size=14, weight="bold"),
            width=200, height=46,
            state="disabled",
            command=self.toggle,
        )
        self.record_btn.pack(pady=(0, 16))

        bar = ctk.CTkFrame(self.root, fg_color="transparent")
        bar.pack(fill="x", padx=16, pady=(0, 4))
        ctk.CTkLabel(bar, text="Historique",
                     font=ctk.CTkFont(size=12), text_color="#484f58").pack(side="left")
        ctk.CTkButton(
            bar, text="Effacer", width=62, height=22,
            font=ctk.CTkFont(size=11),
            fg_color="transparent", border_width=1, border_color="#30363d",
            text_color="#484f58", hover_color="#21262d",
            command=self._clear_history,
        ).pack(side="right")

        self.hist_frame = ctk.CTkScrollableFrame(
            self.root, fg_color="#0d1117", corner_radius=0,
            scrollbar_button_color="#30363d",
            scrollbar_button_hover_color="#484f58",
        )
        self.hist_frame.pack(fill="both", expand=True, padx=12, pady=4)

        ctk.CTkLabel(
            self.root, text=f"Raccourci : {HOTKEY}",
            font=ctk.CTkFont(size=11), text_color="#30363d",
        ).pack(pady=(2, 8))

    def _build_tray(self) -> None:
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([0, 0, 63, 63], fill="#1f6feb")
        d.rounded_rectangle([23, 10, 41, 36], radius=9, fill="white")
        d.arc([16, 28, 48, 50], start=180, end=0, fill="white", width=3)
        d.line([32, 50, 32, 56], fill="white", width=3)
        d.line([24, 56, 40, 56], fill="white", width=3)

        self.tray = pystray.Icon(
            "whispr_local", img, "Whispr Local",
            menu=pystray.Menu(
                pystray.MenuItem("Ouvrir", self._show, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quitter", self._quit),
            ),
        )

    # ── UI STATE ──────────────────────────────────────────

    def _set_state(self, state: str) -> None:
        cfg = _STATES.get(state, _STATES["ready"])
        self.status_lbl.configure(text=cfg["status"], text_color=cfg["status_color"])
        self.record_btn.configure(
            text=cfg["btn"], state=cfg["btn_state"],
            fg_color=cfg["btn_fg"], hover_color=cfg["btn_hover"],
        )
        if state in ("recording", "processing"):
            self.overlay.show(state)
        else:
            self.overlay.hide()

    # ── WINDOW ────────────────────────────────────────────

    def _hide(self) -> None:
        self.root.withdraw()

    def _show(self, icon=None, item=None) -> None:
        self.root.after(0, self.root.deiconify)

    def _quit(self, icon=None, item=None) -> None:
        self.tray.stop()
        self.root.after(0, self.root.destroy)

    # ── MODEL ─────────────────────────────────────────────

    def set_transcriber(self, t: Transcriber) -> None:
        self.transcriber = t
        self.root.after(0, lambda: self._set_state("ready"))

    def show_load_error(self, msg: str) -> None:
        print(f"[Whispr] ⚠ {msg}")
        self.root.after(0, lambda: self._set_state("error"))

    # ── RECORDING ─────────────────────────────────────────

    def toggle(self) -> None:
        with self._lock:
            if self.transcriber is None or self._is_processing:
                return

            if not self._is_recording:
                try:
                    self._is_recording = True
                    self.recorder.start()
                    self.root.after(0, lambda: self._set_state("recording"))
                except Exception as e:
                    self._is_recording = False
                    print(f"[Whispr] ⚠ Micro inaccessible : {e}")
                    self.root.after(0, lambda: self._set_state("ready"))
            else:
                self._is_recording = False
                self._is_processing = True
                path = self.recorder.stop()
                self.root.after(0, lambda: self._set_state("processing"))
                threading.Thread(target=self._process, args=(path,), daemon=True).start()

    def _process(self, audio_path: str | None) -> None:
        try:
            if not audio_path:
                return
            text = self.transcriber.transcribe(audio_path)
            if text:
                inject_text(text)
                self.root.after(0, lambda t=text: self._add_entry(t))
        except Exception as e:
            print(f"[Whispr] ⚠ Erreur traitement : {e}")
        finally:
            if audio_path:
                try:
                    os.unlink(audio_path)
                except OSError:
                    pass
            with self._lock:
                self._is_processing = False
            self.root.after(0, lambda: self._set_state("ready"))

    # ── HISTORY ───────────────────────────────────────────

    def _scroll_bottom(self) -> None:
        try:
            self.hist_frame._parent_canvas.yview_moveto(1.0)
        except AttributeError:
            pass

    def _add_entry(self, text: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        tb_height = min(max(44, (len(text) // 48 + 1) * 22), 110)

        card = ctk.CTkFrame(self.hist_frame, fg_color="#161b22", corner_radius=8)
        card.pack(fill="x", padx=2, pady=5)

        ctk.CTkLabel(card, text=ts,
                     font=ctk.CTkFont(size=10), text_color="#484f58").pack(
            anchor="w", padx=10, pady=(6, 0))

        tb = ctk.CTkTextbox(
            card, height=tb_height,
            font=ctk.CTkFont(size=13), wrap="word",
            border_width=0, fg_color="#1c2128", text_color="#e6edf3",
        )
        tb.pack(fill="x", padx=8, pady=4)
        tb.insert("1.0", text)

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(anchor="e", padx=8, pady=(0, 8))

        def _make_btn(label: str, cmd) -> None:
            ctk.CTkButton(
                btn_row, text=label, width=72, height=24,
                font=ctk.CTkFont(size=11),
                fg_color="transparent", border_width=1, border_color="#30363d",
                text_color="#8b949e", hover_color="#21262d",
                command=cmd,
            ).pack(side="left", padx=3)

        _make_btn("Copier",   lambda: pyperclip.copy(tb.get("1.0", "end-1c")))
        _make_btn("Injecter", lambda: inject_text(tb.get("1.0", "end-1c")))

        self._history_widgets.append(card)
        self.root.after(60, self._scroll_bottom)

    def _clear_history(self) -> None:
        for w in self._history_widgets:
            w.destroy()
        self._history_widgets.clear()

    # ── RUN ───────────────────────────────────────────────

    def run(self) -> None:
        self.tray.run_detached()
        self.root.mainloop()
