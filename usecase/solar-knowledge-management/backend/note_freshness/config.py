"""Configuration management for note freshness module."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _get_project_root() -> Path:
    """Get the project root directory."""
    current = Path(__file__).resolve()
    for level in range(4):
        candidate = current.parents[level]
        if (candidate / "pyproject.toml").exists():
            return candidate
    return current.parent.parent.parent.parent


PROJECT_ROOT = _get_project_root()


class Config:
    """Application configuration manager for note freshness."""

    # Upstage API settings
    UPSTAGE_API_KEY: str = os.getenv("UPSTAGE_API_KEY", "")
    UPSTAGE_API_BASE: str = os.getenv(
        "UPSTAGE_API_BASE", "https://api.upstage.ai/v1/solar"
    )
    MODEL_NAME: str = os.getenv("MODEL_NAME", "solar-pro2")

    # Information Extraction API
    UPSTAGE_IE_API_BASE: str = "https://api.upstage.ai/v1/information-extraction"

    # Tavily API
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

    # Application settings
    PROMPTS_DIR: Path = Path(os.getenv("PROMPTS_DIR", str(PROJECT_ROOT / "prompts")))
    DATA_DIR: Path = PROJECT_ROOT / "data"

    # LLM settings
    DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
    DEFAULT_MAX_TOKENS: int = int(os.getenv("DEFAULT_MAX_TOKENS", "8192"))

    # HTTP client timeout settings
    HTTP_TIMEOUT_ASYNC: float = float(os.getenv("HTTP_TIMEOUT_ASYNC", "120.0"))
    HTTP_TIMEOUT_SYNC: float = float(os.getenv("HTTP_TIMEOUT_SYNC", "120.0"))

    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present."""
        if not cls.UPSTAGE_API_KEY:
            return False
        return True

    @classmethod
    def validate_tavily(cls) -> bool:
        """Validate Tavily API key."""
        return bool(cls.TAVILY_API_KEY)

    @classmethod
    def get_freshness_folder(cls, raw_note_path: Path) -> Path:
        """Generate the folder path for freshness data.

        Args:
            raw_note_path: Path to the raw note file

        Returns:
            Path to the freshness data folder
        """
        parent = raw_note_path.parent
        stem = raw_note_path.stem
        return parent / stem

    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist."""
        cls.PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
