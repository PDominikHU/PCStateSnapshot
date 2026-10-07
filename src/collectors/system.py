"""System information collector."""

import platform
import socket

import psutil


def collect():
    partitions = psutil.disk_partitions()
    root = partitions[0].mountpoint if partitions else "C:\\"
    disk = psutil.disk_usage(root)
    vm = psutil.virtual_memory()

    return {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "cpu_percent": psutil.cpu_percent(interval=0.2),
        "memory": {
            "total_bytes": vm.total,
            "available_bytes": vm.available,
            "used_bytes": vm.used,
            "percent": vm.percent,
        },
        "primary_disk": {
            "mountpoint": root,
            "total_bytes": disk.total,
            "used_bytes": disk.used,
            "free_bytes": disk.free,
            "percent": disk.percent,
        },
        "boot_time": psutil.boot_time(),
    }
