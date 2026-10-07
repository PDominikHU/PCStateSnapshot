"""Snapshot comparison logic."""

from collections import defaultdict


def _index_by(items, key):
    result = {}
    for item in items:
        if key in item:
            result[str(item[key])] = item
    return result


def _diff_dict(old, new, prefix=""):
    changes = []
    old_keys = set(old)
    new_keys = set(new)

    for key in sorted(new_keys - old_keys):
        changes.append({
            "type": "ADDED",
            "path": f"{prefix}{key}",
            "old": None,
            "new": new[key],
        })

    for key in sorted(old_keys - new_keys):
        changes.append({
            "type": "REMOVED",
            "path": f"{prefix}{key}",
            "old": old[key],
            "new": None,
        })

    for key in sorted(old_keys & new_keys):
        a, b = old[key], new[key]
        path = f"{prefix}{key}"
        if isinstance(a, dict) and isinstance(b, dict):
            changes.extend(_diff_dict(a, b, path + "."))
        elif a != b:
            changes.append({
                "type": "CHANGED",
                "path": path,
                "old": a,
                "new": b,
            })

    return changes


def _diff_named_list(old, new, name, key):
    old_i = _index_by(old, key)
    new_i = _index_by(new, key)
    changes = []

    for item_key in sorted(new_i.keys() - old_i.keys()):
        changes.append({
            "category": name,
            "type": "ADDED",
            "item": item_key,
            "old": None,
            "new": new_i[item_key],
        })

    for item_key in sorted(old_i.keys() - new_i.keys()):
        changes.append({
            "category": name,
            "type": "REMOVED",
            "item": item_key,
            "old": old_i[item_key],
            "new": None,
        })

    for item_key in sorted(old_i.keys() & new_i.keys()):
        nested = _diff_dict(
            old_i[item_key],
            new_i[item_key],
            prefix=f"{name}[{item_key}].",
        )
        for change in nested:
            change["category"] = name
            changes.append(change)

    return changes


def _port_key(item):
    return f"{item.get('address')}:{item.get('port')}/{item.get('process')}"


def compare(old, new):
    changes = []

    for section in ("system", "network"):
        a = old.get(section, {})
        b = new.get(section, {})
        changes.extend(_diff_dict(a, b, prefix=f"{section}."))

    changes.extend(_diff_named_list(
        old.get("services", []),
        new.get("services", []),
        "services",
        "name",
    ))

    changes.extend(_diff_named_list(
        old.get("processes", []),
        new.get("processes", []),
        "processes",
        "pid",
    ))

    old_ports = {_port_key(x): x for x in old.get("ports", [])}
    new_ports = {_port_key(x): x for x in new.get("ports", [])}

    for key in sorted(new_ports.keys() - old_ports.keys()):
        changes.append({
            "category": "ports",
            "type": "ADDED",
            "item": key,
            "old": None,
            "new": new_ports[key],
        })

    for key in sorted(old_ports.keys() - new_ports.keys()):
        changes.append({
            "category": "ports",
            "type": "REMOVED",
            "item": key,
            "old": old_ports[key],
            "new": None,
        })

    return changes
