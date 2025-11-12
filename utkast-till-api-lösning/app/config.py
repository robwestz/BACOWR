
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Security
    API_KEY: Optional[str] = Field(default=None, description="If set, requests must send X-API-Key header matching this value.")
    # SERP provider selection: mock | serpapi | google_cse | selenium
    SERP_PROVIDER: str = Field(default="mock")
    SERPAPI_KEY: Optional[str] = None
    GOOGLE_CSE_KEY: Optional[str] = None
    GOOGLE_CSE_CX: Optional[str] = None

    # Networking
    USER_AGENT: str = Field(default="serp-brief-api/0.1 (+https://example.com)")
    MAX_CONCURRENCY: int = Field(default=10)
    REQUEST_TIMEOUT: float = Field(default=15.0)

    # Webhook signing
    WEBHOOK_SECRET: Optional[str] = None  # if set, sign payloads with HMAC-SHA256

    class Config:
        env_file = ".env"

settings = Settings()
