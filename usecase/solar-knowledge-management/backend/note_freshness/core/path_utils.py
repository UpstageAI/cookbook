"""Path utilities - re-export from note_split."""

from backend.note_split.core.path_utils import (
    resolve_path,
    format_path_for_display,
    normalize_path_for_wsl,
)

__all__ = ["resolve_path", "format_path_for_display", "normalize_path_for_wsl"]
