"""
The Milestone 3 orchestrator: runs a real MCP server inside Docker,
network-blocked, and watches what actually happens on disk -- not just
what its tool descriptions claim.

This is deliberately independent of engine.py's judgment: rules.py and
llm_check.py can only ever react to TEXT (a description). No amount of
clever prompting fixes that a malicious server can just not mention what
it's about to do. Filesystem diffing reacts to ACTIONS, which is why a
server with a perfectly innocent-sounding description can still get
caught here.
"""

import hashlib
import time
from pathlib import Path

from mcp_client import MCPStdioClient

DOCKER_NETWORK_ARGS = ["--network", "none"]


def snapshot_dir(root: str) -> dict:
    """path (relative to root) -> sha256 of contents, for every file."""
    snap = {}
    root_path = Path(root)
    if not root_path.exists():
        return snap
    for path in root_path.rglob("*"):
        if path.is_file():
            rel = str(path.relative_to(root_path)).replace("\\", "/")
            snap[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snap


def diff_snapshots(before: dict, after: dict) -> dict:
    created = [p for p in after if p not in before]
    modified = [p for p in after if p in before and after[p] != before[p]]
    deleted = [p for p in before if p not in after]
    return {"created": created, "modified": modified, "deleted": deleted}


def run_sandboxed_scan(image: str, sandbox_host_dir: str, container_mount: str,
                        tool_calls: list[dict]) -> dict:
    """
    tool_calls: [{"name": "...", "arguments": {...}, "expected_paths": ["notes/x.txt"]}]
    "expected_paths" are the ONLY filesystem changes this call is allowed to
    cause without being flagged - anything else that changes is unexpected.

    Returns: {
        "server_info": {...},
        "declared_tools": [{"name", "description"}, ...],   # REAL, from the server
        "call_results": [{"name", "response", "unexpected_changes": {...}, "is_clean": bool}],
    }
    """
    client = MCPStdioClient([
        "docker", "run", "-i", "--rm",
        *DOCKER_NETWORK_ARGS,
        "-v", f"{sandbox_host_dir}:{container_mount}",
        image,
        container_mount,
    ])

    try:
        server_info = client.initialize().get("serverInfo", {})
        declared_tools = client.list_tools()

        call_results = []
        for call in tool_calls:
            before = snapshot_dir(sandbox_host_dir)
            time.sleep(0.05)  # ensure any mtime-based tooling settles before the call
            try:
                response = client.call_tool(call["name"], call["arguments"])
            except Exception as e:
                response = {"error": str(e)}
            after = snapshot_dir(sandbox_host_dir)
            diff = diff_snapshots(before, after)

            expected = set(call.get("expected_paths", []))
            unexpected = {
                "created": [p for p in diff["created"] if p not in expected],
                "modified": [p for p in diff["modified"] if p not in expected],
                "deleted": [p for p in diff["deleted"] if p not in expected],
            }
            is_clean = not any(unexpected.values())

            call_results.append({
                "name": call["name"],
                "arguments": call["arguments"],
                "response": response,
                "unexpected_changes": unexpected,
                "is_clean": is_clean,
            })

        return {
            "server_info": server_info,
            "declared_tools": [
                {"name": t["name"], "description": t.get("description", "")}
                for t in declared_tools
            ],
            "call_results": call_results,
        }
    finally:
        client.close()


def reset_sandbox_dir(sandbox_host_dir: str, seed_files: dict[str, str]):
    """Wipes the sandbox back to a known-clean state and re-seeds it, so
    repeated runs don't accumulate a prior run's evidence (e.g. a leaked
    backup.txt from a previous scan making a clean tool look dirty)."""
    root = Path(sandbox_host_dir)
    if root.exists():
        for path in sorted(root.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
    for rel_path, content in seed_files.items():
        full = root / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content)
