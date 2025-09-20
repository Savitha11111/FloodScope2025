import os
from pathlib import Path
from typing import Dict, List, Optional


class MissingSentinelHubCredentialsError(RuntimeError):
    """Raised when Sentinel Hub credentials are not available."""


_CONFIG_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CONFIG_DIR.parent

_explicit_env_file = os.getenv("FLOODSCOPE_ENV_FILE")
_ENV_FILE_CANDIDATES: List[Path] = []
if _explicit_env_file:
    _ENV_FILE_CANDIDATES.append(Path(_explicit_env_file).expanduser())
_ENV_FILE_CANDIDATES.extend([
    _PROJECT_ROOT / ".env",
    _CONFIG_DIR / ".env",
    _PROJECT_ROOT / "config" / ".env",
])

_ENV_FILES_CHECKED: List[Path] = []


def _parse_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        values[key] = value
    return values


def _load_env_file_values() -> Dict[str, str]:
    values: Dict[str, str] = {}
    seen: List[Path] = []
    for candidate in _ENV_FILE_CANDIDATES:
        try:
            path = candidate.resolve()
        except FileNotFoundError:
            path = candidate
        if path in seen:
            continue
        seen.append(path)
        _ENV_FILES_CHECKED.append(path)
        if path.is_file():
            try:
                file_values = _parse_env_file(path)
            except OSError:
                continue
            values.update({k: v for k, v in file_values.items() if v})
    return values


_ENV_FILE_VALUES = _load_env_file_values()

_LEGACY_ENV_KEYS = {
    "SENTINEL_HUB_CLIENT_ID": ("SENTINELHUB_CLIENT_ID", "SH_CLIENT_ID"),
    "SENTINEL_HUB_CLIENT_SECRET": ("SENTINELHUB_CLIENT_SECRET", "SH_CLIENT_SECRET"),
}


def _get_setting(key: str) -> Optional[str]:
    search_keys = (key,) + _LEGACY_ENV_KEYS.get(key, tuple())
    for candidate in search_keys:
        value = os.getenv(candidate)
        if value:
            return value
    for candidate in search_keys:
        value = _ENV_FILE_VALUES.get(candidate)
        if value:
            return value
    return None


# Sentinel Hub credentials
SENTINEL_HUB_CLIENT_ID = _get_setting("SENTINEL_HUB_CLIENT_ID")
SENTINEL_HUB_CLIENT_SECRET = _get_setting("SENTINEL_HUB_CLIENT_SECRET")

# Model Configuration (Paths)
PRITHVI_MODEL_PATH = "models/prithvi_transformers/Prithvi-EO-1.0-100M/Prithvi_EO_V1_100M.pt"
PRITHVI_CONFIG_PATH = "models/prithvi_transformers/Prithvi-EO-1.0-100M/config.yaml"

# Data Directories
RAW_IMAGE_DIR = "data/raw/"
PROCESSED_IMAGE_DIR = "data/processed/"
RESULTS_DIR = "data/results/"

# Ensure directories exist
os.makedirs(RAW_IMAGE_DIR, exist_ok=True)
os.makedirs(PROCESSED_IMAGE_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)


def require_sentinel_hub_credentials() -> None:
    """Ensure Sentinel Hub credentials are configured before making API calls."""

    missing = []
    if not SENTINEL_HUB_CLIENT_ID:
        missing.append("SENTINEL_HUB_CLIENT_ID")
    if not SENTINEL_HUB_CLIENT_SECRET:
        missing.append("SENTINEL_HUB_CLIENT_SECRET")

    if not missing:
        return

    checked_files = ", ".join(str(path) for path in _ENV_FILES_CHECKED)
    hint = (
        "Set the environment variables or provide them in a .env file."
        " You can point to a custom file with FLOODSCOPE_ENV_FILE."
    )
    if checked_files:
        hint += f" Checked locations: {checked_files}."

    raise MissingSentinelHubCredentialsError(
        "Missing Sentinel Hub credentials ("
        + ", ".join(missing)
        + "). "
        + hint
    )
