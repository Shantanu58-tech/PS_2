from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
# Repo root locally; "/" inside the container (data/, models/, replay/ are
# mounted at /data, /models, /replay by docker-compose).
ROOT = BACKEND_DIR.parent

_PATH_FIELDS = ("db_path", "data_dir", "media_dir", "models_dir", "scenario_path", "keys_dir",
                "eval_dir")


class Settings(BaseSettings):
    # Later files win: repo-root .env, then backend/.env.
    model_config = SettingsConfigDict(env_file=(ROOT / ".env", BACKEND_DIR / ".env"), extra="ignore")

    mode: str = "replay"
    db_path: str = "data/deepastambha.db"
    hmac_secret: str = "change-me-32-chars-minimum-secret"
    jwt_secret: str = "change-me-jwt-secret"
    k_anon: int = 10
    proxy_url: str = ""

    x_account_user: str = ""
    x_auth_token: str = ""
    x_ct0: str = ""

    tg_api_id: str = ""
    tg_api_hash: str = ""
    tg_session: str = "tg.session"

    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "deepastambha/0.1"

    yt_api_key: str = ""
    hf_token: str = ""

    emotion_model: str = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    embed_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    enable_ots: bool = False
    ots_calendars: str = (
        "https://a.pool.opentimestamps.org,https://b.pool.opentimestamps.org,"
        "https://a.pool.eternitywall.com"
    )
    replay_speed: int = 60
    scenario_path: str = "replay/scenario_v1.jsonl"
    data_dir: str = "data"
    media_dir: str = "data/media"
    models_dir: str = "models"
    keys_dir: str = "data/keys"
    eval_dir: str = "eval/reports"
    # Laplace-mechanism privacy budget for released demographic counts.
    dp_epsilon: float = 1.0
    # Run the analytics pipeline automatically when a replay finishes.
    auto_analytics: bool = True

    graph_store: str = "networkx"  # networkx | neo4j
    neo4j_uri: str = ""
    neo4j_user: str = ""
    neo4j_password: str = ""

    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"  # alias survives model retirements

    frontend_dist: str = ""  # defaults to <repo>/frontend/dist
    # Public hosted demo: block endpoints that ingest, re-run analytics or change
    # configuration (PRD 12: public read-only demo mode).
    demo_readonly: bool = False
    tg_session_string: str = ""  # Telethon StringSession (hosted live mode)
    # public channels shown in the live Telegram feed (fixed allowlist; visitors cannot change it)
    live_tg_channels: str = "IndianExpress,hindustantimes,livemint,moneycontrolcom"
    # live feeds: fixed allowlists of public sources (visitors cannot choose)
    live_x_accounts: str = "PIB_India,PIBFactCheck,ndmaindia,ANI"
    live_yt_channels: str = ("UCZFMm1mMw0F81Z37aaEzTUA,UCYPvAwZP8pZhSMW8qs7cVCw,"  # NDTV, India Today
                             "UCGn6a5SI8SNlj7WylmPD6GQ,UCI_7rpgXm-AQY62ZaE87dIw")   # PIB India, The Hindu
    live_reddit_subs: str = "india,IndiaSpeaks,indianews"

    @model_validator(mode="after")
    def _absolute_paths(self) -> "Settings":
        for name in _PATH_FIELDS:
            value = getattr(self, name)
            if value and not Path(value).is_absolute():
                setattr(self, name, str(ROOT / value))
        return self


settings = Settings()
