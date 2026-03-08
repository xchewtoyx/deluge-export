import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


@lru_cache()
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

    for c_path in config_paths:
        if c_path.exists() and c_path.is_file():
            try:
                with open(c_path, "rb") as f:
                    full_config = tomllib.load(f)

                    # Extract the [deluge] section specifically
                    deluge_section = full_config.get("deluge")
                    if isinstance(deluge_section, dict):
                        return deluge_section
                    else:
                        print(
                            f"Warning: '[deluge]' section missing or invalid in {c_path}",
                            file=sys.stderr,
                        )
            except tomllib.TOMLDecodeError as e:
                print(
                    f"Warning: Failed to parse TOML file at {c_path}: {e}",
                    file=sys.stderr,
                )
            except Exception:
                # Silently ignore other read errors
                pass

    return {}
