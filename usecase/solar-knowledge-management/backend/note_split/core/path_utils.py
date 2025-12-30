"""Path utilities for cross-platform path handling, including WSL support."""
import os
import platform
import re
from pathlib import Path
from typing import Union

# Pattern to match Windows paths like C:\Users\... or C:/Users/...
_WINDOWS_PATH_PATTERN = re.compile(r'^([A-Za-z]):[/\\](.*)$')


def _is_wsl_environment() -> bool:
    """Detect if running in WSL environment.
    
    Returns:
        True if running in WSL, False otherwise
    """
    if platform.system() != "Linux":
        return False
    
    # Check /proc/version for WSL indicators
    if os.path.exists("/proc/version"):
        try:
            with open("/proc/version", "r", encoding="utf-8") as f:
                version_info = f.read().lower()
                if "microsoft" in version_info or "wsl" in version_info:
                    return True
        except (OSError, IOError):
            pass
    
    # Check for /mnt/c mount point
    if os.path.exists("/mnt/c"):
        return True
    
    return False


def normalize_path_for_wsl(path: Union[str, Path]) -> Path:
    """Normalize Windows paths to WSL paths when running in WSL environment.
    
    Args:
        path: Path string or Path object (can be Windows or WSL format)
        
    Returns:
        Normalized Path object suitable for the current environment
    """
    path_str = str(path).strip()
    
    # Strip surrounding quotes (both single and double)
    if (path_str.startswith('"') and path_str.endswith('"')) or \
       (path_str.startswith("'") and path_str.endswith("'")):
        path_str = path_str[1:-1].strip()
    
    if not _is_wsl_environment():
        return Path(path_str)
    
    # Match Windows path pattern (C:\Users\... or C:/Users/...)
    match = _WINDOWS_PATH_PATTERN.match(path_str)
    if match:
        drive_letter = match.group(1).lower()
        rest_of_path = match.group(2).replace("\\", "/")
        wsl_path = Path(f"/mnt/{drive_letter}/{rest_of_path}")
        return wsl_path
    
    return Path(path_str)


def resolve_path(path: Union[str, Path]) -> Path:
    """Resolve and normalize a path for the current environment.
    
    This function:
    - Converts Windows paths to WSL paths if in WSL
    - Expands user home directory (~)
    - Resolves to absolute path
    
    Args:
        path: Path string or Path object
        
    Returns:
        Resolved and normalized Path object
    """
    normalized = normalize_path_for_wsl(path)
    return normalized.expanduser().resolve()


def format_path_for_display(path: Union[str, Path], *, prefer_windows_format: bool = False) -> str:
    r"""Format a path for display, optionally converting WSL paths to Windows format.
    
    Args:
        path: Path string or Path object
        prefer_windows_format: If True and in WSL, convert /mnt/... to C:\... format
        
    Returns:
        Formatted path string
    """
    path_obj = Path(path)
    
    if prefer_windows_format and _is_wsl_environment():
        path_str = str(path_obj)
        if path_str.startswith("/mnt/"):
            parts = path_str.split("/", 3)
            if len(parts) >= 4:
                drive_letter = parts[2].upper()
                rest_path = parts[3].replace("/", "\\")
                return f"{drive_letter}:\\{rest_path}"
    
    return str(path_obj)



