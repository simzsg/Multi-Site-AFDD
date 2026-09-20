import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    database_url: str = field(default="sqlite:///./afdd.db", repr=False)
    redis_url: str = field(default="redis://localhost:6379/0", repr=False)
    telemetry_stream: str = "telemetry"
    source_replay_start: str | None = None
    model_configured: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(override=False)
        return cls(
            database_url=os.getenv("DATABASE_URL", "sqlite:///./afdd.db"),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            telemetry_stream=os.getenv("TELEMETRY_STREAM", "telemetry"),
            source_replay_start=os.getenv("SOURCE_REPLAY_START"),
            model_configured=bool(os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_MODEL")),
        )
