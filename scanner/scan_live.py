"""
Milestone 3 CLI: point the registry at a REAL, running MCP server instead
of a JSON file we wrote, inside Docker, network-blocked, and watch what
it actually does.

Usage:
    python scan_live.py filesystem
    python scan_live.py evil-calculator

Every declared tool still goes through the exact same static engine as
Milestones 1-2 (engine.run_scan on its real description). What's new:
a small set of tool calls actually get executed inside the sandbox, and
if any of them touch a file they had no business touching, that's a
behavioral violation - and it overrides the static grade to F regardless
of how innocent the description read, because acting on undisclosed
access is worse evidence than any wording could be.
"""

import sys

import db
import engine
import sandbox

SANDBOX_DIR = str((__import__("pathlib").Path(__file__).resolve().parent.parent / "runtime" / "sandbox_data"))

SEED_FILES = {
    "notes/my_note.txt": "Grocery list: eggs, bread, coffee.\n",
    ".secrets/api_key.txt": "CANARY-7f3a9c21-DO-NOT-LEAK\n",
}

TARGETS = {
    "filesystem": {
        "image": "mcp-sandbox-filesystem",
        "container_mount": "/sandbox",
        "tool_calls": [
            {
                "name": "write_file",
                "arguments": {"path": "/sandbox/notes/test_write.txt", "content": "hello from the trust registry"},
                "expected_paths": ["notes/test_write.txt"],
            },
            {
                "name": "list_directory",
                "arguments": {"path": "/sandbox"},
                "expected_paths": [],
            },
        ],
    },
    "evil-calculator": {
        "image": "mcp-sandbox-evil-calculator",
        "container_mount": "/sandbox",
        "tool_calls": [
            {
                "name": "calculate",
                "arguments": {"a": 2, "b": 3, "op": "add"},
                "expected_paths": [],  # a calculator has no legitimate reason to touch any file
            },
        ],
    },
}


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in TARGETS:
        print(f"Usage: python scan_live.py <{'|'.join(TARGETS)}>")
        sys.exit(1)

    target_name = sys.argv[1]
    target = TARGETS[target_name]

    print(f"Resetting sandbox and seeding test files...")
    sandbox.reset_sandbox_dir(SANDBOX_DIR, SEED_FILES)

    print(f"Launching {target['image']} in Docker (--network none)...\n")
    result = sandbox.run_sandboxed_scan(
        image=target["image"],
        sandbox_host_dir=SANDBOX_DIR,
        container_mount=target["container_mount"],
        tool_calls=target["tool_calls"],
    )

    print("=" * 68)
    print(f"  Server: {result['server_info'].get('name', '?')} v{result['server_info'].get('version', '?')}")
    print(f"  Declared {len(result['declared_tools'])} tool(s) [REAL, from the live server]")
    print("=" * 68)

    called_names = {c["name"] for c in target["tool_calls"]}

    for tool in result["declared_tools"]:
        rule_result, llm_result, static_grade = engine.run_scan(tool["description"])

        call_result = next((c for c in result["call_results"] if c["name"] == tool["name"]), None)

        behavior_flags = None
        final_grade = static_grade

        print(f"\n--- {tool['name']} ---")
        print(f"  Declared: \"{tool['description'][:100]}{'...' if len(tool['description']) > 100 else ''}\"")
        print(f"  Static grade (description only): {static_grade}")

        if call_result:
            if call_result["is_clean"]:
                print(f"  Behavior check: CLEAN - only touched what it was expected to")
            else:
                behavior_flags = []
                for kind, paths in call_result["unexpected_changes"].items():
                    for p in paths:
                        flag = f"unexpected file {kind}: {p}"
                        behavior_flags.append(flag)
                        print(f"  [!!!] {flag}")
                final_grade = "F"
                print(f"  Behavior check: VIOLATION - grade overridden to F regardless of description")
        else:
            print(f"  Behavior check: not exercised this run (declared but not called)")

        print(f"  FINAL GRADE: {final_grade}")

        db.save_scan(
            server_name=f"{target_name} (live, docker)",
            tool_name=tool["name"],
            description=tool["description"],
            rule_result=rule_result,
            llm_result=llm_result,
            grade=final_grade,
            source="docker-sandbox",
            behavior_flags=behavior_flags,
        )

    print("\n" + "=" * 68)
    print(f"  Saved {len(result['declared_tools'])} scan(s) to the registry, source=docker-sandbox")
    print("=" * 68)


if __name__ == "__main__":
    main()
