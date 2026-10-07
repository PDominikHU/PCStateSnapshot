"""Running process collector."""

import psutil


def collect():
    processes = []
    for proc in psutil.process_iter(["pid", "name", "status", "username", "exe"]):
        try:
            info = proc.info
            processes.append({
                "pid": info.get("pid"),
                "name": info.get("name"),
                "status": info.get("status"),
                "username": info.get("username"),
                "exe": info.get("exe"),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    return sorted(
        processes,
        key=lambda item: ((item.get("name") or "").lower(), item.get("pid") or 0),
    )
