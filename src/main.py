"""PC State Snapshot & Diff - command line interface."""

from pathlib import Path
from datetime import datetime
import argparse
import json
import logging
import platform
import shutil
import sys
import os

from .config import load_config
from .storage import (
    snapshot_id,
    save_snapshot,
    load_snapshot,
    list_snapshots,
    backup_snapshots,
    restore_archive,
    cleanup_snapshots,
)
from .diff import compare
from .collectors import system, network, processes, services, ports


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config" / "config.json"
SNAPSHOT_DIR = BASE_DIR / "snapshots"
REPORT_DIR = BASE_DIR / "reports"
LOG_DIR = BASE_DIR / "logs"
BACKUP_DIR = BASE_DIR / "backups"


# ANSI terminal colors. Windows PowerShell/Windows Terminal support ANSI colors.
RESET = "\033[0m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"


def use_colors(disabled=False):
    """Return whether colored output should be used."""
    if disabled or os.environ.get("NO_COLOR") is not None:
        return False
    return sys.stdout.isatty()


def color(text, code, enabled):
    return f"{code}{text}{RESET}" if enabled else text


def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=LOG_DIR / "sysnapshot.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def collect_snapshot(config):
    sid = snapshot_id()
    snapshot = {
        "schema_version": 1,
        "id": sid,
        "timestamp": datetime.now().astimezone().isoformat(),
        "collector": {
            "hostname": platform.node(),
            "application": "PC State Snapshot & Diff",
        },
    }

    if config["collect_system"]:
        snapshot["system"] = system.collect()
    else:
        snapshot["system"] = {}

    if config["collect_network"]:
        snapshot["network"] = network.collect()
    else:
        snapshot["network"] = {}

    if config["collect_processes"]:
        ignored = {x.lower() for x in config["process_ignore"]}
        items = processes.collect()
        snapshot["processes"] = [
            x for x in items
            if (x.get("name") or "").lower() not in ignored
        ]
    else:
        snapshot["processes"] = []

    snapshot["services"] = services.collect(config["services"])

    snapshot["ports"] = ports.collect() if config["collect_ports"] else []

    return snapshot


def format_value(value):
    if value is None:
        return "N/A"
    if isinstance(value, bool):
        return "YES" if value else "NO"
    return str(value)


def print_snapshot(snapshot):
    print(f"Snapshot: {snapshot['id']}")
    print(f"Created:  {snapshot['timestamp']}")
    print()

    system_data = snapshot.get("system", {})
    print("SYSTEM")
    print(f"  Hostname:    {system_data.get('hostname', 'N/A')}")
    print(f"  OS:          {system_data.get('os', 'N/A')} {system_data.get('os_release', '')}")
    print(f"  CPU:         {system_data.get('processor') or 'N/A'}")
    print(f"  CPU cores:   {system_data.get('cpu_count_logical', 'N/A')}")
    print(f"  CPU usage:   {system_data.get('cpu_percent', 'N/A')}%")
    print(f"  RAM usage:   {system_data.get('memory', {}).get('percent', 'N/A')}%")
    print(f"  Disk usage:  {system_data.get('primary_disk', {}).get('percent', 'N/A')}%")
    print()

    net = snapshot.get("network", {})
    print("NETWORK")
    for adapter in net.get("adapters", []):
        ips = [
            a["address"] for a in adapter.get("addresses", [])
            if a.get("family") == "IPv4"
        ]
        print(f"  {adapter['name']}: {'UP' if adapter.get('is_up') else 'DOWN'} "
              f"{', '.join(ips) if ips else 'no IPv4'}")
    print(f"  Gateway: {net.get('default_gateway') or 'N/A'}")
    print(f"  DNS:     {', '.join(net.get('dns_servers', [])) or 'N/A'}")
    print()

    print(f"SERVICES ({len(snapshot.get('services', []))})")
    for item in snapshot.get("services", []):
        print(f"  {item.get('name', '?'):<20} {item.get('status', '?')}")
    print()

    print(f"PROCESSES ({len(snapshot.get('processes', []))})")
    print("  Stored process entries:", len(snapshot.get("processes", [])))
    print()

    print(f"LISTENING PORTS ({len(snapshot.get('ports', []))})")
    for item in snapshot.get("ports", []):
        if "error" in item:
            print(f"  ERROR: {item['error']}")
        else:
            print(f"  {item.get('address')}:{item.get('port')} "
                  f"PID={item.get('pid')} {item.get('process') or ''}")


def print_changes(changes, colors=True):
    if not changes:
        print("No changes detected.")
        return

    print(f"Changes detected: {len(changes)}")
    print()

    for change in changes:
        category = change.get("category", "system").upper()
        change_type = change["type"]
        item = change.get("item") or change.get("path")

        if change_type == "ADDED":
            type_text = color(change_type, GREEN, colors)
        elif change_type == "REMOVED":
            type_text = color(change_type, RED, colors)
        elif change_type == "CHANGED":
            type_text = color(change_type, YELLOW, colors)
        else:
            type_text = change_type
        category_text = color(f"[{category}]", CYAN, colors)
        print(f"{category_text} {type_text}: {item}")

        if change_type == "CHANGED":
            print(f"  OLD: {format_value(change.get('old'))}")
            print(f"  NEW: {format_value(change.get('new'))}")
        elif change_type == "ADDED":
            print(f"  NEW: {format_value(change.get('new'))}")
        elif change_type == "REMOVED":
            print(f"  OLD: {format_value(change.get('old'))}")
        print()


def cmd_snapshot(args, config):
    logging.info("Snapshot started")
    snapshot = collect_snapshot(config)
    path = save_snapshot(snapshot, SNAPSHOT_DIR)
    logging.info("Snapshot saved: %s", path)
    print(f"Snapshot created successfully.")
    print(f"ID:   {snapshot['id']}")
    print(f"File: {path}")


def cmd_list(args):
    files = list_snapshots(SNAPSHOT_DIR)
    if not files:
        print("No snapshots available.")
        return

    print("AVAILABLE SNAPSHOTS")
    print("-" * 72)
    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            print(f"{data.get('id', path.stem):<28} {data.get('timestamp', 'unknown')}")
        except Exception:
            print(f"{path.stem:<28} INVALID JSON")


def cmd_show(args):
    snapshot = load_snapshot(args.id, SNAPSHOT_DIR)
    print_snapshot(snapshot)


def cmd_diff(args):
    if args.latest:
        files = list_snapshots(SNAPSHOT_DIR)
        if len(files) < 2:
            print("ERROR: At least two snapshots are required for --latest.", file=sys.stderr)
            return 3
        old_id = files[-2].stem
        new_id = files[-1].stem
    else:
        old_id = args.old
        new_id = args.new

    old = load_snapshot(old_id, SNAPSHOT_DIR)
    new = load_snapshot(new_id, SNAPSHOT_DIR)
    changes = compare(old, new)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "old_snapshot": old["id"],
        "new_snapshot": new["id"],
        "change_count": len(changes),
        "changes": changes,
    }
    report_path = REPORT_DIR / f"diff_{old['id']}_to_{new['id']}.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Comparing: {old['id']} -> {new['id']}")
    print()
    print_changes(changes, colors=use_colors(args.no_color))
    print(f"JSON report: {report_path}")
    return 1 if changes else 0

def cmd_backup(args):
    archive = backup_snapshots(SNAPSHOT_DIR, BACKUP_DIR)
    logging.info("Snapshot backup created: %s", archive)
    print(f"Backup created: {archive}")


def cmd_restore(args):
    files = restore_archive(args.archive, SNAPSHOT_DIR, dry_run=args.dry_run)
    if args.dry_run:
        print("DRY RUN - no files were modified.")
        for name in files:
            print(f"  WOULD RESTORE: {name}")
    else:
        logging.info("Snapshot archive restored: %s", args.archive)
        print(f"Restored archive: {args.archive}")


def cmd_cleanup(args):
    targets = cleanup_snapshots(SNAPSHOT_DIR, args.keep, dry_run=args.dry_run)
    if args.dry_run:
        print("DRY RUN - no files were modified.")
        for path in targets:
            print(f"  WOULD REMOVE: {path.name}")
    else:
        logging.info("Snapshot cleanup completed. Removed: %s", len(targets))
        print(f"Removed {len(targets)} snapshot(s).")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="sysnapshot",
        description="PC State Snapshot & Diff - Windows system state auditing tool.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  sysnapshot snapshot
  sysnapshot list
  sysnapshot show 20261006-225409-274095
  sysnapshot diff 20261006-225409-274095 20261006-225534-684683
  sysnapshot diff --latest
  sysnapshot backup
  sysnapshot restore backups\\snapshots-20261006-225728.zip --dry-run
  sysnapshot cleanup --keep 10 --dry-run

Run 'sysnapshot <command> --help' for detailed help.""",
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    sub.add_parser(
        "snapshot",
        help="Create a new PC state snapshot.",
        description="Collect the configured PC state and save it as a JSON snapshot.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  sysnapshot snapshot",
    )
    sub.add_parser(
        "list",
        help="List available snapshots.",
        description="List saved snapshots in chronological order.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  sysnapshot list",
    )

    p_show = sub.add_parser(
        "show",
        help="Show one snapshot by ID.",
        description="Display a previously saved snapshot.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  sysnapshot show 20261006-225409-274095",
    )
    p_show.add_argument("id", metavar="ID", help="Snapshot ID shown by 'sysnapshot list'.")

    p_diff = sub.add_parser(
        "diff",
        help="Compare two snapshots.",
        description="Compare two snapshots, or use --latest to compare the newest two.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  sysnapshot diff OLD_ID NEW_ID
  sysnapshot diff --latest
  sysnapshot diff OLD_ID NEW_ID --no-color""",
    )
    p_diff.add_argument("old", nargs="?", metavar="OLD_ID", help="ID of the older snapshot.")
    p_diff.add_argument("new", nargs="?", metavar="NEW_ID", help="ID of the newer snapshot.")
    p_diff.add_argument(
        "--latest",
        action="store_true",
        help="Compare the two newest snapshots automatically.",
    )
    p_diff.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored diff output.",
    )

    sub.add_parser(
        "backup",
        help="Create a ZIP backup of snapshots.",
        description="Create a ZIP archive containing the saved snapshots.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  sysnapshot backup",
    )

    p_restore = sub.add_parser(
        "restore",
        help="Restore snapshots from a ZIP backup.",
        description="Restore snapshot JSON files from a ZIP archive. Use --dry-run to preview without changing files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  sysnapshot restore backups\\snapshots-20261006-225728.zip\n  sysnapshot restore backups\\snapshots-20261006-225728.zip --dry-run",
    )
    p_restore.add_argument("archive", metavar="ARCHIVE", help="Path to the snapshot ZIP archive.")
    p_restore.add_argument("--dry-run", action="store_true", help="Preview the restore without modifying files.")

    p_cleanup = sub.add_parser(
        "cleanup",
        help="Remove old snapshots.",
        description="Keep the newest N snapshots and remove older ones. Use --dry-run to preview.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  sysnapshot cleanup --keep 10\n  sysnapshot cleanup --keep 10 --dry-run",
    )
    p_cleanup.add_argument("--keep", type=int, default=10, metavar="N", help="Number of newest snapshots to keep (default: 10).")
    p_cleanup.add_argument("--dry-run", action="store_true", help="Preview what would be removed without deleting files.")

    return parser

def main():
    setup_logging()

    if platform.system() != "Windows":
        print("ERROR: This project is designed for Windows 11.", file=sys.stderr)
        return 3

    parser = build_parser()
    args = parser.parse_args()

    if args.command == "diff":
        if args.latest and (args.old is not None or args.new is not None):
            parser.error("diff: use either --latest or OLD_ID NEW_ID, not both")
        if not args.latest and (args.old is None or args.new is None):
            parser.error("diff: provide OLD_ID NEW_ID or use --latest")

    if args.command == "cleanup" and args.keep < 0:
        parser.error("cleanup: --keep must be 0 or greater")

    try:
        config = load_config(CONFIG_FILE)

        if args.command == "snapshot":
            cmd_snapshot(args, config)
            return 0
        if args.command == "list":
            cmd_list(args)
            return 0
        if args.command == "show":
            cmd_show(args)
            return 0
        if args.command == "diff":
            return cmd_diff(args)
        if args.command == "backup":
            cmd_backup(args)
            return 0
        if args.command == "restore":
            cmd_restore(args)
            return 0
        if args.command == "cleanup":
            cmd_cleanup(args)
            return 0

        parser.error("Unknown command")
        return 3

    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        logging.exception("Configuration or input error")
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 130
    except Exception as exc:
        logging.exception("Unhandled error")
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
