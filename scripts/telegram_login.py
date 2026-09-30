"""One-time Telegram login: creates a Telethon StringSession and stores it in
backend/.env as TG_SESSION_STRING (the hosted server then needs no phone login).

Two non-interactive steps (work from any terminal, including Claude Code's `!`):

    backend\\.venv\\Scripts\\python scripts\\telegram_login.py --phone +919876543210
        -> Telegram sends a login code to your Telegram app
    backend\\.venv\\Scripts\\python scripts\\telegram_login.py --code 12345 [--password YOUR_2FA_PASSWORD]
        -> saves TG_SESSION_STRING to backend/.env

Run without arguments for the classic interactive prompt instead.
Treat TG_SESSION_STRING like a password: it grants access to the account.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
PENDING = ROOT / "backend" / ".tg_login_pending.json"  # gitignored; deleted after step 2


def save_env(key: str, value: str) -> None:
    env = ROOT / "backend" / ".env"
    lines = env.read_text(encoding="utf-8").splitlines() if env.exists() else []
    lines = [ln for ln in lines if not ln.startswith(f"{key}=")] + [f"{key}={value}"]
    env.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _client(session: str = ""):
    from telethon.sessions import StringSession
    from telethon.sync import TelegramClient

    from app.config import settings

    if not (settings.tg_api_id and settings.tg_api_hash):
        sys.exit("TG_API_ID / TG_API_HASH missing in backend/.env")
    return TelegramClient(StringSession(session), int(settings.tg_api_id), settings.tg_api_hash)


def send_code(phone: str) -> None:
    client = _client()
    client.connect()
    sent = client.send_code_request(phone)
    PENDING.write_text(json.dumps({"phone": phone, "hash": sent.phone_code_hash,
                                   "session": client.session.save()}), encoding="utf-8")
    client.disconnect()
    print("Code sent. Check your Telegram app, then run:\n"
          "  backend\\.venv\\Scripts\\python scripts\\telegram_login.py --code <the code>")


def finish(code: str, password: str | None) -> None:
    from telethon.errors import SessionPasswordNeededError

    if not PENDING.exists():
        sys.exit("No pending login. Run with --phone first.")
    p = json.loads(PENDING.read_text(encoding="utf-8"))
    client = _client(p["session"])
    client.connect()
    try:
        client.sign_in(p["phone"], code, phone_code_hash=p["hash"])
    except SessionPasswordNeededError:
        if not password:
            client.disconnect()
            sys.exit("This account has two-step verification. Re-run with --code <code> --password <password>.")
        client.sign_in(password=password)
    me = client.get_me()
    save_env("TG_SESSION_STRING", client.session.save())
    client.disconnect()
    PENDING.unlink(missing_ok=True)
    print(f"Logged in as {getattr(me, 'username', None) or getattr(me, 'first_name', 'account')}; "
          "TG_SESSION_STRING saved to backend/.env")


def interactive() -> None:
    with _client() as client:
        me = client.get_me()
        session = client.session.save()
    save_env("TG_SESSION_STRING", session)
    print(f"Logged in as {getattr(me, 'username', None) or getattr(me, 'first_name', 'account')}; "
          "TG_SESSION_STRING saved to backend/.env")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phone", help="phone number with country code, e.g. +919876543210")
    ap.add_argument("--code", help="the login code Telegram sent you")
    ap.add_argument("--password", help="two-step verification password, if enabled")
    a = ap.parse_args()
    if a.phone:
        send_code(a.phone)
    elif a.code:
        finish(a.code, a.password)
    else:
        interactive()
