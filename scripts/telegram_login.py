"""One-time Telegram login: creates a Telethon StringSession and stores it in
backend/.env as TG_SESSION_STRING (the hosted server then needs no phone login).

Run it in your own terminal (it asks for your phone number and the login code
Telegram sends you, and your 2FA password if you use one):

    cd backend
    .venv\\Scripts\\python ..\\scripts\\telegram_login.py

Treat TG_SESSION_STRING like a password: it grants access to the account.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def save_env(key: str, value: str) -> None:
    env = ROOT / "backend" / ".env"
    lines = env.read_text(encoding="utf-8").splitlines() if env.exists() else []
    lines = [ln for ln in lines if not ln.startswith(f"{key}=")] + [f"{key}={value}"]
    env.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    from telethon.sessions import StringSession
    from telethon.sync import TelegramClient

    from app.config import settings

    if not (settings.tg_api_id and settings.tg_api_hash):
        sys.exit("TG_API_ID / TG_API_HASH missing in backend/.env")
    with TelegramClient(StringSession(), int(settings.tg_api_id), settings.tg_api_hash) as client:
        me = client.get_me()
        session = client.session.save()
    save_env("TG_SESSION_STRING", session)
    print(f"Logged in as {getattr(me, 'username', None) or getattr(me, 'first_name', 'account')}; "
          "TG_SESSION_STRING saved to backend/.env")


if __name__ == "__main__":
    main()
