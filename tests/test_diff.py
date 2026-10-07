"""Small dependency-free tests for the diff engine."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.diff import compare


def test_no_change():
    snapshot = {
        "system": {"hostname": "PC"},
        "network": {},
        "services": [{"name": "Spooler", "status": "Running"}],
        "processes": [{"pid": 1, "name": "System"}],
        "ports": [],
    }
    assert compare(snapshot, snapshot) == []


def test_service_change():
    old = {
        "system": {},
        "network": {},
        "services": [{"name": "BITS", "status": "Running"}],
        "processes": [],
        "ports": [],
    }
    new = {
        "system": {},
        "network": {},
        "services": [{"name": "BITS", "status": "Stopped"}],
        "processes": [],
        "ports": [],
    }
    changes = compare(old, new)
    assert any(
        c["category"] == "services" and c["type"] == "CHANGED"
        for c in changes
    )


def test_port_added():
    old = {"system": {}, "network": {}, "services": [], "processes": [], "ports": []}
    new = {
        "system": {},
        "network": {},
        "services": [],
        "processes": [],
        "ports": [{"address": "0.0.0.0", "port": 8080, "pid": 1, "process": "python.exe"}],
    }
    changes = compare(old, new)
    assert any(c["category"] == "ports" and c["type"] == "ADDED" for c in changes)


if __name__ == "__main__":
    test_no_change()
    test_service_change()
    test_port_added()
    print("All tests passed.")
