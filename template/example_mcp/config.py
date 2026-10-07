import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo


def integer(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
        if minimum <= value <= maximum:
            return value
    except ValueError:
        pass
    raise ValueError(f"{name} の設定範囲は {minimum}〜{maximum} です。")


@dataclass(frozen=True)
class Settings:
    model: str
    output_tokens: int
    usage_db: Path
    window_seconds: int
    calls_per_window: int
    calls_per_day: int
    timezone: ZoneInfo

    @classmethod
    def from_env(cls):
        return cls(
            os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
            integer("EXAMPLE_MAX_OUTPUT_TOKENS", 800, 128, 4000),
            Path(os.environ.get("EXAMPLE_USAGE_DB", "/data/usage.sqlite3")),
            integer("EXAMPLE_WINDOW_SECONDS", 600, 1, 86400),
            integer("EXAMPLE_MAX_CALLS_PER_WINDOW", 3, 1, 1000),
            integer("EXAMPLE_MAX_CALLS_PER_DAY", 20, 1, 10000),
            ZoneInfo(os.environ.get("EXAMPLE_BUDGET_TIMEZONE", "Asia/Tokyo")),
        )
