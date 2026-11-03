#!/usr/bin/env python3
"""Dev Vault catalog helper — inspect catalog/index.json without opening it by hand.

Standard library only (Python 3.9+).

Usage:
    python3 scripts/catalog.py list [--type TYPE] [--status STATUS]
    python3 scripts/catalog.py get <id>
    python3 scripts/catalog.py stats
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG = REPO_ROOT / "catalog" / "index.json"


def load_resources():
    try:
        with CATALOG.open(encoding="utf-8") as fh:
            return json.load(fh).get("resources", [])
    except FileNotFoundError:
        sys.exit(f"error: catalog not found at {CATALOG}")
    except json.JSONDecodeError as exc:
        sys.exit(f"error: catalog is not valid JSON: {exc}\n"
                 f"run scripts/validate.py for details")


def cmd_list(args):
    resources = load_resources()
    if args.type:
        resources = [r for r in resources if r.get("type") == args.type]
    if args.status:
        resources = [r for r in resources if r.get("status") == args.status]
    if not resources:
        print("no resources match (the vault may be empty)")
        return
    for r in resources:
        print(f"{r['id']:<32} {r['type']:<15} {r['status']:<13} {r['path']}")


def cmd_get(args):
    for r in load_resources():
        if r["id"] == args.id:
            print(json.dumps(r, indent=2))
            return
    sys.exit(f"error: no resource with id '{args.id}' — use 'catalog.py list' to see all")


def cmd_stats(_args):
    resources = load_resources()
    print(f"total resources: {len(resources)}")
    by_type: dict = {}
    for r in resources:
        by_type.setdefault(r["type"], []).append(r["status"])
    for rtype, statuses in sorted(by_type.items()):
        counts = {}
        for s in statuses:
            counts[s] = counts.get(s, 0) + 1
        summary = ", ".join(f"{s}: {n}" for s, n in sorted(counts.items()))
        print(f"  {rtype:<15} {len(statuses):>3}  ({summary})")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="list resources (optionally filtered)")
    p_list.add_argument("--type", choices=[
        "skills", "snippets", "configurations", "templates",
        "prompts", "workflows", "references"])
    p_list.add_argument("--status", choices=[
        "experimental", "stable", "deprecated", "archived"])

    p_get = sub.add_parser("get", help="show one resource's full catalog entry")
    p_get.add_argument("id")

    sub.add_parser("stats", help="counts by type and status")

    args = parser.parse_args()
    {"list": cmd_list, "get": cmd_get, "stats": cmd_stats}[args.command](args)


if __name__ == "__main__":
    main()
