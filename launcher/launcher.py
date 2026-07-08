# launcher/launcher.py
"""Block Robot launcher window (layout B: buttons left, live diagnostics right).

Thin view: all logic lives in doctor.py and launcher_actions.py. Long-running
actions run on a worker thread and stream into the diagnostics panel via a
thread-safe queue polled on the Tk main loop.
"""
import queue
import sys
import threading
import webbrowser
from pathlib import Path

import tkinter as tk
from tkinter import scrolledtext

from launcher import doctor, launcher_actions as actions


def project_root() -> Path:
    # When frozen, resources sit beside the executable; else repo root (../).
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


class LauncherApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.proj = project_root()
        self.q: "queue.Queue[str]" = queue.Queue()
        self.backend_proc = None

        root.title("Block Robot IDE")
        root.geometry("720x360")

        header = tk.Label(root, text="🤖 Block Robot IDE",
                          font=("Segoe UI", 16, "bold"))
        header.pack(pady=6)

        body = tk.Frame(root)
        body.pack(fill="both", expand=True, padx=10, pady=6)

        btns = tk.Frame(body)
        btns.pack(side="left", fill="y", padx=(0, 10))
        self._btn(btns, "▶ Start IDE", self.on_start)
        self._btn(btns, "⚙️ Set up / update", self.on_setup)
        self._btn(btns, "🩺 Check my system", self.on_check)

        self.log = scrolledtext.ScrolledText(body, width=52, height=16,
                                             bg="#020617", fg="#e2e8f0",
                                             font=("Consolas", 9))
        self.log.pack(side="right", fill="both", expand=True)

        self.root.after(100, self._drain)
        self.on_check()

    def _btn(self, parent, text, cmd):
        b = tk.Button(parent, text=text, command=cmd, width=18, height=2)
        b.pack(pady=4)
        return b

    # ---- logging plumbing ----
    def _log(self, msg: str):
        self.q.put(msg)

    def _drain(self):
        try:
            while True:
                line = self.q.get_nowait()
                self.log.insert("end", line + "\n")
                self.log.see("end")
        except queue.Empty:
            pass
        try:
            self.root.after(100, self._drain)
        except tk.TclError:
            pass  # window closed mid-action

    def _run_bg(self, fn):
        threading.Thread(target=fn, daemon=True).start()

    # ---- button handlers ----
    def on_check(self):
        def work():
            self._log("── Checking system ──")
            for r in doctor.run_checks(self.proj, include_flash=False):
                icon = "✅" if r.status == "ok" else "❌"
                self._log(f"{icon} {r.label}: {r.message}")
                if r.status == "fail" and r.fix_hint:
                    self._log(f"   → {r.fix_hint}")
        self._run_bg(work)

    def on_setup(self):
        def work():
            actions.run_setup(self.proj, self._log)
            self.root.after(0, self.on_check)  # dispatch back to main thread
        self._run_bg(work)

    def on_start(self):
        results = doctor.run_checks(self.proj, include_flash=False)
        if not doctor.all_ok(results):
            fail = doctor.first_failure(results)
            self._log(f"❌ Can't start yet: {fail.label} — {fail.fix_hint}")
            return
        if self.backend_proc and self.backend_proc.poll() is None:
            self._log("IDE already running — reopening browser tab.")
        else:
            self.backend_proc = actions.start_backend(self.proj, self._log)
        webbrowser.open("http://localhost:8000")


def main():
    root = tk.Tk()
    LauncherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
