"""
CLI: view what's in the registry.

Usage:
    python history.py                          # leaderboard: latest grade per server/tool
    python history.py notes-sync read_note      # full timeline for one server/tool
"""

import sys

import db


def print_leaderboard():
    rows = db.get_leaderboard()
    if not rows:
        print("Registry is empty -- run scan.py on something first.")
        return

    print("=" * 72)
    print(f"  {'SERVER / TOOL':<38}{'GRADE':<8}{'SCANS':<8}{'LAST SCANNED'}")
    print("=" * 72)
    for r in rows:
        label = f"{r['server_name']} / {r['tool_name']}"
        print(f"  {label:<38}{r['grade']:<8}{r['scan_count']:<8}{r['scanned_at'][:19]}")
    print("=" * 72)


def print_timeline(server_name: str, tool_name: str):
    rows = db.get_history(server_name, tool_name)
    if not rows:
        print(f"No scans found for {server_name} / {tool_name}")
        return

    print("=" * 72)
    print(f"  Timeline: {server_name} / {tool_name}  ({len(rows)} scan(s))")
    print("=" * 72)
    prev_grade = None
    for r in rows:
        marker = ""
        if prev_grade is not None and prev_grade != r["grade"]:
            marker = "   <-- CHANGED"
        print(f"  {r['scanned_at'][:19]}   grade {r['grade']}{marker}")
        prev_grade = r["grade"]
    print("=" * 72)


def main():
    if len(sys.argv) == 1:
        print_leaderboard()
    elif len(sys.argv) == 3:
        print_timeline(sys.argv[1], sys.argv[2])
    else:
        print("Usage:")
        print("  python history.py                       # leaderboard")
        print("  python history.py <server_name> <tool_name>   # timeline")
        sys.exit(1)


if __name__ == "__main__":
    main()
