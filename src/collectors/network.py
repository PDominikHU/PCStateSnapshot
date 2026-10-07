"""Network information collector."""

import socket
import psutil


def _default_gateway():
    try:
        import subprocess
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-NetIPConfiguration | Where-Object {$_.IPv4DefaultGateway -ne $null} | Select-Object -First 1 -ExpandProperty IPv4DefaultGateway).NextHop"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        gateway = completed.stdout.strip()
        return gateway or None
    except Exception:
        return None


def _dns_servers():
    try:
        import subprocess
        command = "(Get-DnsClientServerAddress -AddressFamily IPv4 | Where-Object {$_.ServerAddresses.Count -gt 0} | ForEach-Object {$_.ServerAddresses})"
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return sorted({line.strip() for line in completed.stdout.splitlines() if line.strip()})
    except Exception:
        return []


def collect():
    result = []
    addresses = psutil.net_if_addrs()
    stats = psutil.net_if_stats()

    for name, entries in addresses.items():
        adapter = {
            "name": name,
            "is_up": bool(stats.get(name).isup) if name in stats else None,
            "speed_mbps": stats.get(name).speed if name in stats else None,
            "addresses": [],
        }

        for entry in entries:
            family = str(entry.family)
            if entry.family == socket.AF_INET:
                family = "IPv4"
            elif entry.family == socket.AF_INET6:
                family = "IPv6"
            elif getattr(psutil, "AF_LINK", None) == entry.family:
                family = "MAC"

            adapter["addresses"].append({
                "family": family,
                "address": entry.address,
                "netmask": entry.netmask,
                "broadcast": entry.broadcast,
            })

        result.append(adapter)

    return {
        "adapters": result,
        "default_gateway": _default_gateway(),
        "dns_servers": _dns_servers(),
    }
