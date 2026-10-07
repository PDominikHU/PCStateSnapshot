"""Snapshot storage helpers."""

from pathlib import Path
from datetime import datetime
import json
import shutil
import zipfile


def snapshot_id():
    return datetime.now().strftime("%Y%m%d-%H%M%S-%f")


def save_snapshot(snapshot, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    sid = snapshot["id"]
    path = directory / f"{sid}.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(snapshot, handle, indent=2, ensure_ascii=False)
    return path


def load_snapshot(identifier, directory):
    directory = Path(directory)
    path = directory / identifier
    if path.suffix.lower() != ".json":
        path = directory / f"{identifier}.json"

    if not path.exists():
        raise FileNotFoundError(f"Snapshot not found: {identifier}")

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def list_snapshots(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return sorted(directory.glob("*.json"))


def backup_snapshots(source_dir, backup_dir):
    source_dir = Path(source_dir)
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive = backup_dir / f"snapshots-{timestamp}.zip"

    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in source_dir.glob("*.json"):
            zf.write(file, arcname=file.name)

    return archive


def restore_archive(archive, snapshot_dir, dry_run=False):
    archive = Path(archive)
    snapshot_dir = Path(snapshot_dir)
    if not archive.exists():
        raise FileNotFoundError(f"Backup archive not found: {archive}")

    if dry_run:
        with zipfile.ZipFile(archive) as zf:
            return zf.namelist()

    snapshot_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(snapshot_dir)

    return zf.namelist() if False else []


def cleanup_snapshots(directory, keep, dry_run=False):
    files = list_snapshots(directory)
    if keep < 0:
        raise ValueError("keep must be >= 0")

    to_remove = files[:-keep] if keep else files

    if not dry_run:
        for file in to_remove:
            file.unlink()

    return to_remove
