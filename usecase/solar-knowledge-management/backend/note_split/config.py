"""Configuration management for the application."""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def _get_project_root() -> Path:
    """Get the project root directory.
    
    This function finds the project root by looking for pyproject.toml
    starting from the current file's directory and going up.
    
    Returns:
        Path to the project root directory
    """
    current = Path(__file__).resolve()
    # Start from backend/note_split/config.py, go up to project root
    # Try going up 3 levels first (most common case)
    for level in range(4):
        candidate = current.parents[level]
        if (candidate / 'pyproject.toml').exists():
            return candidate
    # Fallback: assume project root is 3 levels up from config.py
    return current.parent.parent.parent.parent


PROJECT_ROOT = _get_project_root()


class Config:
    """Application configuration manager."""

    # Upstage API settings
    UPSTAGE_API_KEY: str = os.getenv('UPSTAGE_API_KEY', '')
    UPSTAGE_API_BASE: str = os.getenv('UPSTAGE_API_BASE', 'https://api.upstage.ai/v1/solar')
    MODEL_NAME: str = os.getenv('MODEL_NAME', 'solar-pro')

    # Application settings
    DEFAULT_WORKSPACE: Path = Path(os.getenv('DEFAULT_WORKSPACE', './workspace'))
    PROMPTS_DIR: Path = Path(os.getenv('PROMPTS_DIR', str(PROJECT_ROOT / 'prompts')))

    # LLM settings
    DEFAULT_TEMPERATURE: float = float(os.getenv('DEFAULT_TEMPERATURE', '0.7'))
    DEFAULT_MAX_TOKENS: int = int(os.getenv('DEFAULT_MAX_TOKENS', '4096'))

    # HTTP client timeout settings (in seconds)
    HTTP_TIMEOUT_ASYNC: float = float(os.getenv('HTTP_TIMEOUT_ASYNC', '60.0'))
    HTTP_TIMEOUT_SYNC: float = float(os.getenv('HTTP_TIMEOUT_SYNC', '120.0'))

    # File settings
    ATOMIC_NOTES_SUFFIX: str = os.getenv('ATOMIC_NOTES_SUFFIX', '-atoms')

    # Atomic note generation settings
    DEFAULT_ATOM_DIRECTION: str = os.getenv('DEFAULT_ATOM_DIRECTION', '')

    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present.

        Returns:
            True if configuration is valid, False otherwise
        """
        if not cls.UPSTAGE_API_KEY:
            return False
        return True

    @classmethod
    def get_atomic_notes_folder(cls, raw_note_path: Path) -> Path:
        """Generate the folder path for atomic notes based on raw note path.

        Args:
            raw_note_path: Path to the raw note file

        Returns:
            Path to the atomic notes folder
        """
        parent = raw_note_path.parent
        stem = raw_note_path.stem
        return parent / f"{stem}{cls.ATOMIC_NOTES_SUFFIX}"

    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist."""
        cls.DEFAULT_WORKSPACE.mkdir(parents=True, exist_ok=True)
        cls.PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

