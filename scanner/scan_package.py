"""
Scan ANY real MCP server by npm package name - not just the two targets
scan_live.py knows about ahead of time. This is what "Sam" would actually
use after finding a real tool listed somewhere (the official MCP registry,
npm, a GitHub README) and wanting to check it before connecting it to
anything real.

Local/CLI only, on purpose. Building this server's image means running
`npm install <package>` on this machine, which needs real network access -
that step can never be sandboxed the way running the finished tool
afterward can be, because you can't download something with no network.
That's true of installing any software from anywhere; it's not a
shortcut this project takes. Because of that, this stays a command you
run yourself rather than a public form a stranger could submit arbitrary
package names to.

Usage:
    python scan_package.py <npm-package-name> [mount-arg]

Example:
    python scan_package.py @modelcontextprotocol/server-memory

Unlike scan_live.py's two built-in targets, this never auto-calls any
tool - we have no pre-written, known-safe arguments for a package we've
never seen. It only reads the server's REAL declared tools and runs them
through the same static engine as everything else. That's a real,
honest limitation: no behavioral verification here, only description-
level checks. See README for how to add a tool-call plan for a specific
package once you've looked at what it actually expects.
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


def lookup_bin_name(package_name: str) -> str:
    """Asks npm's registry what command this package actually installs -
    the real entrypoint, not a guess. Needs network; doesn't need Docker."""
    if not NPM:
        raise RuntimeError("npm isn't on PATH - can't look up package info.")
    result = subprocess.run(
        [NPM, "view", package_name, "bin", "--json"],
        capture_output=True, text=True,
    )
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"npm gave an unreadable response for '{package_name}'. stderr:\n{result.stderr[-500:]}")

    if isinstance(data, dict) and "error" in data:
        raise RuntimeError(f"npm couldn't find '{package_name}': {data['error']['summary']}")
    if not data:
        raise RuntimeError(
            f"'{package_name}' doesn't declare a runnable command (no \"bin\" field in its "
            f"package.json) - it may be a library, not something you can run directly as a server."
        )
    return next(iter(data))


def build_sandbox_image(package_name: str, bin_name: str) -> str:
    safe_tag = re.sub(r"[^a-z0-9]+", "-", package_name.lower()).strip("-")
    image_tag = f"mcp-sandbox-pkg-{safe_tag}"

    dockerfile = f'FROM node:20-slim\nRUN npm install -g {package_name}\nENTRYPOINT ["{bin_name}"]\n'

    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "Dockerfile").write_text(dockerfile)
        print(f"Building sandbox image for '{package_name}' (this step needs network - installing from npm)...")
        result = subprocess.run([DOCKER, "build", "-t", image_tag, tmp], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Docker build failed:\n{result.stderr[-1500:]}")
    return image_tag


def main():
    if len(sys.argv) < 2:
        print("Usage: python scan_package.py <npm-package-name> [mount-arg]")
        print("Example: python scan_package.py @modelcontextprotocol/server-memory")
        sys.exit(1)

    package_name = sys.argv[1]
    mount_arg = sys.argv[2] if len(sys.argv) > 2 else "/sandbox"

    if not NPM_NAME_RE.match(package_name):
        print(f"[X] '{package_name}' doesn't look like a real npm package name - refusing to run it.")
        print(f"    Expected something like 'my-package' or '@scope/my-package'.")
        sys.exit(1)

    print(f"Looking up '{package_name}' on npm...")
    try:
        bin_name = lookup_bin_name(package_name)
    except RuntimeError as e:
        print(f"\n[X] {e}")
        sys.exit(1)
    print(f"Found real entrypoint: {bin_name}\n")

    try:
        image_tag = build_sandbox_image(package_name, bin_name)
    except RuntimeError as e:
        print(f"\n[X] {e}")
        sys.exit(1)
    print(f"Built {image_tag}. Everything from here runs with --network none.\n")

    sandbox.reset_sandbox_dir(SANDBOX_DIR, SEED_FILES)

    try:
        result = sandbox.run_sandboxed_scan(
            image=image_tag,
            sandbox_host_dir=SANDBOX_DIR,
            container_mount=mount_arg,
            tool_calls=[],  # unknown package: no known-safe arguments to call
                            # its tools with, so we only read what it declares.
        )
    except Exception as e:
        print(f"[X] Could not complete the MCP handshake with this server: {e}")
        print(f"    Some servers need specific startup arguments or environment")
        print(f"    variables this generic scanner doesn't know to provide.")
        print(f"    Try: python scan_package.py {package_name} <a-different-mount-arg>")
        sys.exit(1)

    print("=" * 68)
    print(f"  Server: {result['server_info'].get('name', '?')} v{result['server_info'].get('version', '?')}")
    print(f"  Declared {len(result['declared_tools'])} tool(s) [REAL, live from npm: {package_name}]")
    print("=" * 68)

    for tool in result["declared_tools"]:
        rule_result, llm_result, static_grade = engine.run_scan(tool["description"])

        print(f"\n--- {tool['name']} ---")
        print(f"  Declared: \"{tool['description'][:100]}{'...' if len(tool['description']) > 100 else ''}\"")
        print(f"  Static grade (description only): {static_grade}")
        print(f"  Behavior check: not exercised (unknown package - no auto tool-calling)")

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

    print(f"\n{'=' * 68}")
    print(f"  Saved {len(result['declared_tools'])} scan(s) to the registry as '{package_name}'.")
    print(f"  Static checks only - no tool was actually called, so this can't")
    print(f"  catch the kind of behavioral violation Milestone 3's evil-calculator")
    print(f"  demo did. It CAN still catch a poisoned description, same as any")
    print(f"  other scan in this registry.")
    print("=" * 68)


if __name__ == "__main__":
    main()
