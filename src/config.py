"""Configuration loading and validation."""

from pathlib import Path
import json


DEFAULT_CONFIG = {
    "services": ["Spooler", "BITS", "wuauserv"],
    "collect_processes": True,
    "collect_ports": True,
    "collect_network": True,
    "collect_system": True,
    "process_ignore": [],
}


def load_config(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)

    if not isinstance(config, dict):
        raise ValueError("Configuration root must be a JSON object.")

    merged = DEFAULT_CONFIG.copy()
    merged.update(config)

    if not isinstance(merged["services"], list) or not all(
        isinstance(x, str) and x.strip() for x in merged["services"]
    ):
        raise ValueError("'services' must be a list of non-empty strings.")

    for key in (
        "collect_processes",
        "collect_ports",
        "collect_network",
        "collect_system",
    ):
        if not isinstance(merged[key], bool):
            raise ValueError(f"'{key}' must be true or false.")

    if not isinstance(merged["process_ignore"], list) or not all(
        isinstance(x, str) for x in merged["process_ignore"]
    ):
        raise ValueError("'process_ignore' must be a list of strings.")

    return merged
