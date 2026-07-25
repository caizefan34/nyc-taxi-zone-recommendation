"""Configuration management with YAML support."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_CONFIG_CACHE: dict[str, Any] | None = None
_CONFIG_PATH: Path | None = None


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load configuration from YAML file.
    
    Args:
        config_path: Path to config file. If None, uses default configs/config.yaml.
    
    Returns:
        Configuration dictionary.
    
    Raises:
        FileNotFoundError: If config file doesn't exist.
        yaml.YAMLError: If config file is invalid YAML.
    """
    global _CONFIG_CACHE, _CONFIG_PATH

    if config_path is not None:
        config_path = Path(config_path)
    elif _CONFIG_PATH is not None:
        config_path = _CONFIG_PATH
    else:
        # Find config file relative to project root
        project_root = Path(__file__).resolve().parents[2]
        config_path = project_root / "configs" / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    _CONFIG_CACHE = config
    _CONFIG_PATH = config_path
    return config


def get_config(key: str, default: Any = None) -> Any:
    """Get a configuration value by dot-notation key.
    
    Args:
        key: Dot-notation key (e.g., "planning.gamma").
        default: Default value if key not found.
    
    Returns:
        Configuration value or default.
    
    Examples:
        >>> get_config("planning.gamma")
        0.5
        >>> get_config("data.zone_count", 263)
        263
    """
    global _CONFIG_CACHE

    if _CONFIG_CACHE is None:
        load_config()

    keys = key.split(".")
    value = _CONFIG_CACHE

    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default

    return value


def reload_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Force reload configuration from file.
    
    Args:
        config_path: Path to config file. If None, uses current path.
    
    Returns:
        Fresh configuration dictionary.
    """
    global _CONFIG_CACHE, _CONFIG_PATH
    _CONFIG_CACHE = None

    if config_path is not None:
        _CONFIG_PATH = Path(config_path)

    return load_config()
