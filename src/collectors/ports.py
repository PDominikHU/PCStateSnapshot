"""Listening TCP port collector."""

import psutil


def collect():
    result = []
    seen = set()

    try:
        connections = psutil.net_connections(kind="tcp")
    except (psutil.AccessDenied, PermissionError):
        return [{"error": "Access denied while reading TCP connections"}]

    for conn in connections:
        if conn.status != psutil.CONN_LISTEN:
            continue

        ip = conn.laddr.ip if conn.laddr else None
        port = conn.laddr.port if conn.laddr else None
        pid = conn.pid

        key = (ip, port, pid)
        if key in seen:
            continue
        seen.add(key)

        process_name = None
        if pid:
            try:
                process_name = psutil.Process(pid).name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        result.append({
            "address": ip,
            "port": port,
            "pid": pid,
            "process": process_name,
        })

    return sorted(result, key=lambda x: (x.get("port") or 0, x.get("address") or ""))
