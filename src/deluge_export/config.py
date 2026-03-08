from pathlib import Path
from typing import Dict, Any

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def load_config() -> Dict[str, Any]:
    """
    Locates and parses the deluge-export config file if present.
    Locations checked (in order):
    1. ~/.config/deluge-export/config.toml
    2. ~/.deluge-export.toml
    """
    home = Path.home()
    config_paths = [
        home / ".config" / "deluge-export" / "config.toml",
        home / ".deluge-export.toml",
    ]

    config_dict = {}

    for c_path in config_paths:
        if c_path.exists() and c_path.is_file():
            try:
                with open(c_path, "rb") as f:
                    full_config = tomllib.load(f)

                    # Extract the [deluge] section specifically
                    if "deluge" in full_config:
                        config_dict = full_config["deluge"]
                    break  # Stop looking after we find one valid config
            except tomllib.TOMLDecodeError as e:
                import sys

                sys.stderr.write(
                    f"Warning: Failed to parse TOML file at {c_path}: {e}\n"
                )
            except Exception:
                # Silently ignore other read errors
                pass

    return config_dict


# Load default config upon import
DEFAULT_CONFIG = load_config()
