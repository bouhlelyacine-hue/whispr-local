import tkinter as tk


class RecordingOverlay:
    """Small always-on-top pill shown at bottom-center of screen during recording/processing."""

    _STATES = {
        "recording":  ("🔴  Enregistrement", "#f85149"),
        "processing": ("⚙   Transcription",  "#d29922"),
    }

    def __init__(self, root: tk.Misc) -> None:
        self._root = root
        self._win: tk.Toplevel | None = None
        self._lbl: tk.Label | None = None
        self._blink_job: str | int | None = None
        self._blink_color: str = "#f85149"
        self._blink_on = True

    # ── PUBLIC (thread-safe) ──────────────────────────────

    def show(self, state: str) -> None:
        self._root.after(0, lambda: self._show(state))

    def hide(self) -> None:
        self._root.after(0, self._hide)

    # ── INTERNAL (main thread only) ───────────────────────

    def _show(self, state: str) -> None:
        text, color = self._STATES.get(state, self._STATES["recording"])

        if self._win is None:
            self._create()

        self._lbl.config(text=text, fg=color)
        self._win.deiconify()
        self._win.lift()

        if state == "recording":
            self._start_blink(color)
        else:
            self._stop_blink()
            self._lbl.config(fg=color)

    def _hide(self) -> None:
        self._stop_blink()
        if self._win:
            self._win.withdraw()

    def _create(self) -> None:
        self._win = tk.Toplevel(self._root)
        self._win.overrideredirect(True)
        self._win.attributes("-topmost", True)
        self._win.attributes("-alpha", 0.92)
        self._win.configure(bg="#161b22")
        self._win.resizable(False, False)

        sw = self._win.winfo_screenwidth()
        sh = self._win.winfo_screenheight()
        w, h = 230, 38
        self._win.geometry(f"{w}x{h}+{(sw - w) // 2}+{sh - 95}")

        self._lbl = tk.Label(
            self._win,
            text="",
            font=("Segoe UI", 12, "bold"),
            bg="#161b22",
            fg="#f85149",
            padx=16,
        )
        self._lbl.pack(fill="both", expand=True)
        self._win.withdraw()

    def _start_blink(self, color: str) -> None:
        self._stop_blink()
        self._blink_color = color
        self._blink_on = True
        self._blink()

    def _blink(self) -> None:
        if self._lbl and self._win and self._win.winfo_exists():
            self._lbl.config(fg=self._blink_color if self._blink_on else "#4a0f0e")
            self._blink_on = not self._blink_on
            self._blink_job = self._root.after(550, self._blink)

    def _stop_blink(self) -> None:
        if self._blink_job:
            self._root.after_cancel(self._blink_job)
            self._blink_job = None
