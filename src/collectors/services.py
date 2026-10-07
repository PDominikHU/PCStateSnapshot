"""Windows service collector."""

import subprocess


def _run_powershell(command):
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True,
        text=True,
        timeout=15,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "PowerShell command failed")
    return completed.stdout


def collect(service_names):
    if not service_names:
        return []

    quoted = ",".join("'" + name.replace("'", "''") + "'" for name in service_names)
    command = (
        f"Get-Service -Name {quoted} -ErrorAction SilentlyContinue | "
        "Select-Object Name,DisplayName,Status,StartType | ConvertTo-Json -Compress"
    )

    try:
        import json
        raw = _run_powershell(command).strip()
        if not raw:
            return []
        data = json.loads(raw)
        if isinstance(data, dict):
            data = [data]
        return [
            {
                "name": item.get("Name"),
                "display_name": item.get("DisplayName"),
                "status": item.get("Status"),
                "start_type": item.get("StartType"),
            }
            for item in data
        ]
    except Exception as exc:
        return [{
            "name": name,
            "status": "ERROR",
            "error": str(exc),
        } for name in service_names]


def restart_service(service_name):
    command = f"Restart-Service -Name '{service_name.replace(chr(39), chr(39)*2)}' -Force"
    _run_powershell(command)
