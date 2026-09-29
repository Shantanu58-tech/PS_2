from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mode: str = "replay"
    db_path: str = "data/satya.db"
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
    reddit_user_agent: str = "satyanet/0.1"

    yt_api_key: str = ""
    hf_token: str = ""

    emotion_model: str = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    embed_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    enable_ots: bool = False
    replay_speed: int = 60


settings = Settings()
