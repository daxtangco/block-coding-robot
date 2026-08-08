# launcher/launcher.py
"""Block Robot launcher window (layout B: buttons left, live diagnostics right).

Thin view: all logic lives in doctor.py and launcher_actions.py. Long-running
actions run on a worker thread and stream into the diagnostics panel via a
thread-safe queue polled on the Tk main loop.
"""
import queue
import shutil
import sys
import threading
import webbrowser
from pathlib import Path

import tkinter as tk
from tkinter import scrolledtext, ttk

from launcher import doctor, launcher_actions as actions


# App source dirs/files bundled into the frozen binary (see packaging/launcher.spec).
# On first run they're copied out of PyInstaller's read-only _MEIPASS into a
# writable project root so the launcher can build .venv, install deps, and run
# the server there.
_BUNDLED = ["backend", "frontend", "config.py", "sorting_logic.py",
            "requirements-vision.txt", "models"]


def project_root() -> Path:
    # When frozen, the binary is self-contained: the app source is bundled and
    # extracted to a writable per-user dir (the executable's own folder may be
    # read-only, e.g. /Applications or a DMG). When running from source, use the
    # repo root (../).
    if getattr(sys, "frozen", False):
        return Path.home() / "BlockRobot"
    return Path(__file__).resolve().parents[1]


def bundle_dir() -> Path:
    """Where PyInstaller extracted bundled data (_MEIPASS), else the repo root."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return Path(__file__).resolve().parents[1]


def ensure_app_source(root: Path, log) -> None:
    """First-run bootstrap: copy bundled app source into the writable root.

    Idempotent — only copies items that aren't already present, so a user's
    existing .venv/settings/programs under root are never clobbered. No-op when
    not frozen (the repo already has everything).
    """
    if not getattr(sys, "frozen", False):
        return
    src = bundle_dir()
    root.mkdir(parents=True, exist_ok=True)
    for name in _BUNDLED:
        dest = root / name
        if dest.exists():
            continue
        origin = src / name
        if not origin.exists():
            continue
        log(f"Installing {name} → {dest}")
        if origin.is_dir():
            shutil.copytree(origin, dest)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origin, dest)


class LauncherApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.proj = project_root()
        self.q: "queue.Queue[str]" = queue.Queue()
        self.backend_proc = None

        root.title("Block Robot IDE")
        root.geometry("720x400")

        header = tk.Label(root, text="🤖 Block Robot IDE",
                          font=("Segoe UI", 16, "bold"))
        header.pack(pady=6)

        body = tk.Frame(root)
        body.pack(fill="both", expand=True, padx=10, pady=6)

        btns = tk.Frame(body)
        btns.pack(side="left", fill="y", padx=(0, 10))
        self._buttons = [
            self._btn(btns, "▶ Start IDE", self.on_start),
            self._btn(btns, "⚙️ Set up / update", self.on_setup),
            self._btn(btns, "🔧 Install robot tools", self.on_install_tools),
            self._btn(btns, "🩺 Check my system", self.on_check),
            self._btn(btns, "🔨 Flash the robot", self.on_flash),
        ]

        self.log = scrolledtext.ScrolledText(body, width=52, height=16,
                                             bg="#020617", fg="#e2e8f0",
                                             font=("Consolas", 9))
        self.log.pack(side="right", fill="both", expand=True)
        self.log.tag_config("link", foreground="#60a5fa", underline=True)

        # Indeterminate progress bar: shows the app is alive during the long
        # (possibly throttled) esp32 core download, which prints little output.
        self.progress = ttk.Progressbar(root, mode="indeterminate")
        self.progress.pack(fill="x", padx=10, pady=(0, 8))

        self.root.after(100, self._drain)
        self.on_check()

    def _btn(self, parent, text, cmd):
        b = tk.Button(parent, text=text, command=cmd, width=18, height=2)
        b.pack(pady=4)
        return b

    # ---- logging plumbing ----
    def _log(self, msg: str):
        self.q.put(msg)

    def _log_link(self, text: str, url: str):
        """Enqueue a clickable link line; rendered on the main thread by _drain."""
        self.q.put(("link", text, url))

    def _insert_link(self, text: str, url: str):
        tag = f"link-{self.log.index('end')}"
        self.log.insert("end", text + "\n", ("link", tag))
        self.log.tag_bind(tag, "<Button-1>", lambda e: webbrowser.open(url))
        self.log.tag_bind(tag, "<Enter>",
                          lambda e: self.log.config(cursor="hand2"))
        self.log.tag_bind(tag, "<Leave>", lambda e: self.log.config(cursor=""))

    def _drain(self):
        try:
            while True:
                item = self.q.get_nowait()
                if isinstance(item, tuple) and item and item[0] == "link":
                    self._insert_link(item[1], item[2])
                else:
                    self.log.insert("end", item + "\n")
                self.log.see("end")
        except queue.Empty:
            pass
        try:
            self.root.after(100, self._drain)
        except tk.TclError:
            pass  # window closed mid-action

    def _set_busy(self, busy: bool):
        """Toggle the progress bar + button state (call on the main thread)."""
        self._busy = busy
        for b in self._buttons:
            b.config(state="disabled" if busy else "normal")
        if busy:
            self.progress.start(12)
        else:
            self.progress.stop()

    def _run_bg(self, fn):
        """Run fn on a worker thread, showing 'busy' UI for its duration.

        Must be called from the main (Tk) thread. No-ops if an action is
        already running, so chained/stray clicks can't interleave subprocesses.
        """
        if getattr(self, "_busy", False):
            self._log("⏳ Busy — please wait for the current step to finish.")
            return
        def wrapped():
            try:
                fn()
            finally:
                self.root.after(0, lambda: self._set_busy(False))
        self._set_busy(True)
        threading.Thread(target=wrapped, daemon=True).start()

    # ---- button handlers ----
    def on_check(self):
        def work():
            self._log("── Checking system ──")
            self._report_checks(include_flash=False)
        self._run_bg(work)

    def on_setup(self):
        def work():
            ensure_app_source(self.proj, self._log)  # frozen: materialize bundled source
            actions.run_setup(self.proj, self._log)
            self.root.after(0, self.on_check)  # dispatch back to main thread
        self._run_bg(work)

    def on_start(self):
        def work():
            ensure_app_source(self.proj, self._log)  # frozen: ensure source exists
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
        self._run_bg(work)

    def _report_checks(self, include_flash: bool):
        """Run doctor checks and stream the results (call from a worker)."""
        for r in doctor.run_checks(self.proj, include_flash=include_flash):
            icon = "✅" if r.status == "ok" else "❌"
            self._log(f"{icon} {r.label}: {r.message}")
            if r.status == "fail" and r.fix_hint:
                self._log(f"   → {r.fix_hint}")

    def on_install_tools(self):
        def work():
            self._log("── Installing robot tools ──")
            actions.install_robot_tools(self.proj, self._log)
            # Re-check inline (same worker) so we don't re-enter _run_bg while
            # this action still holds the busy lock.
            self._log("── Checking system (incl. robot tools) ──")
            self._report_checks(include_flash=True)
        self._run_bg(work)

    def on_flash(self):
        def work():
            results = doctor.run_checks(self.proj, include_flash=True)
            # Robot tools (index 5) are required; arm (index 6) is optional.
            arduino = results[5]
            if arduino.status != "ok":
                self._log(f"⚙️ {arduino.label}: {arduino.message} — "
                          f"installing automatically …")
                if not actions.install_robot_tools(self.proj, self._log):
                    self._log("❌ Could not finish installing robot tools. "
                              "See the log above.")
                    return

            if str(self.proj) not in sys.path:
                sys.path.insert(0, str(self.proj))
            from backend.services.builder import list_serial_ports, get_template_path

            ports = [p for p in list_serial_ports() if p.get("port")]
            if not ports:
                self._log(doctor.NO_SERIAL_HINT)
                self._log_link("   → Download the USB driver (CP210x / CH340)",
                               doctor.USB_DRIVER_URL)
                return
            port = ports[0]["port"]
            sketch = (self.proj / get_template_path()).resolve()
            self._log(f"Flashing {sketch.name} to {port} …")
            actions.flash_firmware(self.proj, port, sketch, self._log)
        self._run_bg(work)


def run_headless(do_start: bool) -> int:
    """Run the bootstrap + setup path with no GUI (for CI / clean-room tests).

    Mirrors what the Setup (and optionally Start) buttons do, streaming to
    stdout. Returns a process exit code: 0 on success, non-zero on failure.
    """
    root = project_root()
    ensure_app_source(root, print)
    ok = actions.run_setup(root, print)
    if not ok:
        return 1
    if do_start:
        proc = actions.start_backend(root, print)
        if proc.poll() is not None:
            return 1
        print(f"IDE server started (pid {proc.pid}). Stopping (headless smoke test).")
        proc.terminate()
    return 0


def main():
    argv = sys.argv[1:]
    if "--setup" in argv or "--check" in argv:
        sys.exit(run_headless(do_start="--start" in argv))
    root = tk.Tk()
    LauncherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
