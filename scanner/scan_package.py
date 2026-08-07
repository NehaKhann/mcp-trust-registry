"""
Scan ANY real MCP server by npm package name - not just the two targets
scan_live.py knows about ahead of time. This is what "Sam" would actually
use after finding a real tool listed somewhere (the official MCP registry,
npm, a GitHub README) and wanting to check it before connecting it to
anything real.

The core function here (scan_package) is called from two places:
- this file's own CLI (`python scan_package.py <package>`)
- api/main.py's /api/scan-package endpoint, so the website can trigger
  the exact same sandboxed scan - see that file for why it's disabled
  by default anywhere this gets deployed.

Building the image means running `npm install <package>` wherever this
runs, which needs real network access - that step can never be sandboxed
the way running the finished tool afterward can be, because you can't
download something with no network. That's true of installing any
software from anywhere; it's not a shortcut this project takes.

Usage:
    python scan_package.py <npm-package-name> [mount-arg]

Example:
    python scan_package.py @modelcontextprotocol/server-memory

Unlike scan_live.py's two built-in targets, this never auto-calls any
tool - we have no pre-written, known-safe arguments for a package we've
never seen. It only reads the server's REAL declared tools and runs them
through the same static engine as everything else. That's a real,
honest limitation: no behavioral verification here, only description-
level checks.
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import db
import engine
import sandbox

SANDBOX_DIR = str((Path(__file__).resolve().parent.parent / "runtime" / "sandbox_data"))

SEED_FILES = {
    "notes/my_note.txt": "Grocery list: eggs, bread, coffee.\n",
    ".secrets/api_key.txt": "CANARY-7f3a9c21-DO-NOT-LEAK\n",
}

# Real npm package name rules (lowercase, optional @scope/, limited charset).
# Validated up front so this string is provably safe before it's ever used
# to build a shell command or a Dockerfile - not just "probably fine".
NPM_NAME_RE = re.compile(r"^(@[a-z0-9][a-z0-9._-]*/)?[a-z0-9][a-z0-9._-]*$")

# npm ships as npm.CMD on Windows, which subprocess can't invoke by bare
# name the way it can a real .exe - resolve the actual path once, for
# whichever OS this happens to run on.
NPM = shutil.which("npm")
DOCKER = shutil.which("docker")


class PackageScanError(Exception):
    """A user-facing failure (bad package name, npm 404, Docker build
    failure, MCP handshake failure) - safe to show the message directly,
    as opposed to an unexpected internal error."""


def lookup_bin_name(package_name: str) -> str:
    """Asks npm's registry what command this package actually installs -
    the real entrypoint, not a guess. Needs network; doesn't need Docker."""
    if not NPM:
        raise PackageScanError("npm isn't on PATH - can't look up package info.")
    result = subprocess.run(
        [NPM, "view", package_name, "bin", "--json"],
        capture_output=True, text=True,
    )
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise PackageScanError(f"npm gave an unreadable response for '{package_name}'. stderr:\n{result.stderr[-500:]}")

    if isinstance(data, dict) and "error" in data:
        raise PackageScanError(f"npm couldn't find '{package_name}': {data['error']['summary']}")
    if not data:
        raise PackageScanError(
            f"'{package_name}' doesn't declare a runnable command (no \"bin\" field in its "
            f"package.json) - it may be a library, not something you can run directly as a server."
        )
    return next(iter(data))


def build_sandbox_image(package_name: str, bin_name: str) -> str:
    if not DOCKER:
        raise PackageScanError("docker isn't on PATH - can't build a sandbox image.")
    safe_tag = re.sub(r"[^a-z0-9]+", "-", package_name.lower()).strip("-")
    image_tag = f"mcp-sandbox-pkg-{safe_tag}"

    dockerfile = f'FROM node:20-slim\nRUN npm install -g {package_name}\nENTRYPOINT ["{bin_name}"]\n'

    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "Dockerfile").write_text(dockerfile)
        result = subprocess.run([DOCKER, "build", "-t", image_tag, tmp], capture_output=True, text=True)
        if result.returncode != 0:
            raise PackageScanError(f"Docker build failed:\n{result.stderr[-1500:]}")
    return image_tag


def scan_package(package_name: str, mount_arg: str = "/sandbox") -> dict:
    """Does the full scan: validate -> look up real entrypoint -> build a
    sandbox image -> run it (--network none) -> static-grade every REAL
    declared tool -> save each to the registry. Returns a structured
    result; raises PackageScanError with a message safe to show a user
    for anything that goes wrong along the way.
    """
    if not NPM_NAME_RE.match(package_name):
        raise PackageScanError(
            f"'{package_name}' doesn't look like a real npm package name - refusing to run it. "
            f"Expected something like 'my-package' or '@scope/my-package'."
        )

    bin_name = lookup_bin_name(package_name)
    image_tag = build_sandbox_image(package_name, bin_name)

    sandbox.reset_sandbox_dir(SANDBOX_DIR, SEED_FILES)

    try:
        raw = sandbox.run_sandboxed_scan(
            image=image_tag,
            sandbox_host_dir=SANDBOX_DIR,
            container_mount=mount_arg,
            tool_calls=[],  # unknown package: no known-safe arguments to call
                            # its tools with, so we only read what it declares.
        )
    except Exception as e:
        raise PackageScanError(
            f"Could not complete the MCP handshake with this server: {e}. Some servers need "
            f"specific startup arguments or environment variables this generic scanner doesn't "
            f"know to provide - try a different mount-arg."
        )

    tools = []
    for tool in raw["declared_tools"]:
        rule_result, llm_result, static_grade = engine.run_scan(tool["description"])

        db.save_scan(
            server_name=package_name,
            tool_name=tool["name"],
            description=tool["description"],
            rule_result=rule_result,
            llm_result=llm_result,
            grade=static_grade,
            source="docker-sandbox",
            behavior_flags=None,
        )

        tools.append({
            "name": tool["name"],
            "description": tool["description"],
            "grade": static_grade,
            "rule_result": rule_result,
            "llm_result": llm_result,
        })

    return {
        "package_name": package_name,
        "bin_name": bin_name,
        "server_info": raw["server_info"],
        "tools": tools,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python scan_package.py <npm-package-name> [mount-arg]")
        print("Example: python scan_package.py @modelcontextprotocol/server-memory")
        sys.exit(1)

    package_name = sys.argv[1]
    mount_arg = sys.argv[2] if len(sys.argv) > 2 else "/sandbox"

    print(f"Looking up '{package_name}' on npm...")
    try:
        result = scan_package(package_name, mount_arg)
    except PackageScanError as e:
        print(f"\n[X] {e}")
        sys.exit(1)

    print(f"Found real entrypoint: {result['bin_name']}")
    print("Built and ran sandbox image. Everything ran with --network none.\n")

    print("=" * 68)
    print(f"  Server: {result['server_info'].get('name', '?')} v{result['server_info'].get('version', '?')}")
    print(f"  Declared {len(result['tools'])} tool(s) [REAL, live from npm: {package_name}]")
    print("=" * 68)

    for tool in result["tools"]:
        print(f"\n--- {tool['name']} ---")
        print(f"  Declared: \"{tool['description'][:100]}{'...' if len(tool['description']) > 100 else ''}\"")
        print(f"  Static grade (description only): {tool['grade']}")
        print("  Behavior check: not exercised (unknown package - no auto tool-calling)")

    print(f"\n{'=' * 68}")
    print(f"  Saved {len(result['tools'])} scan(s) to the registry as '{package_name}'.")
    print("  Static checks only - no tool was actually called, so this can't")
    print("  catch the kind of behavioral violation Milestone 3's evil-calculator")
    print("  demo did. It CAN still catch a poisoned description, same as any")
    print("  other scan in this registry.")
    print("=" * 68)


if __name__ == "__main__":
    main()
