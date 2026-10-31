"""Run the loopback API and restricted-port workbench as one container service."""
from __future__ import annotations
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import threading
import time
from urllib.request import ProxyHandler, build_opener

ROOT = Path(__file__).resolve().parents[1]


def credential_key(runtime: Path) -> str:
    from cryptography.fernet import Fernet
    configured = os.getenv("COMAGENT_CREDENTIAL_KEY")
    if configured:
        Fernet(configured.encode("ascii"))
        return configured
    runtime.mkdir(parents=True, exist_ok=True)
    path = runtime / "credential.key"
    if path.is_symlink():
        raise RuntimeError("Credential key must be a private regular file")
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        descriptor = None
    if descriptor is not None:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(Fernet.generate_key())
    if os.name != "nt" and (stat.S_IMODE(path.stat().st_mode) & 0o077):
        raise RuntimeError("Credential key permissions must be 0600")
    key = path.read_text(encoding="ascii").strip()
    Fernet(key.encode("ascii"))
    return key


def main() -> int:
    os.chdir(ROOT)
    env = dict(os.environ)
    env["COMAGENT_CREDENTIAL_KEY"] = credential_key(ROOT / ".runtime")
    stop = threading.Event()
    for signum in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, lambda *_: stop.set())
    children = []
    try:
        api = subprocess.Popen([sys.executable, "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8000"], env=env)
        children.append(api)
        opener = build_opener(ProxyHandler({}))
        deadline = time.monotonic() + 45
        while not stop.is_set():
            if api.poll() is not None:
                return api.returncode or 1
            try:
                with opener.open("http://127.0.0.1:8000/openapi.json", timeout=2) as response:
                    if response.status == 200:
                        break
            except OSError:
                pass
            if time.monotonic() >= deadline:
                raise RuntimeError("API startup timed out")
            stop.wait(.25)
        if stop.is_set():
            return 0
        public_port = int(env.get("COMAGENT_UI_PORT", "8501"))
        if not 1 <= public_port <= 65535:
            raise RuntimeError("COMAGENT_UI_PORT must be between 1 and 65535")
        ui = subprocess.Popen([sys.executable, "frontend-workbench/run_ui.py", "--host", "0.0.0.0", "--port", "8501", "--public-port", str(public_port), "--api-url", "http://127.0.0.1:8000"], env=env)
        children.append(ui)
        while not stop.wait(.5):
            for process in children:
                if process.poll() is not None:
                    return process.returncode or 1
        return 0
    finally:
        for process in children:
            if process.poll() is None:
                process.terminate()
        for process in children:
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    raise SystemExit(main())
