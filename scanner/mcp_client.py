"""
A minimal MCP client, hand-written against the protocol spec rather than
the official SDK -- the point of Milestone 3 is understanding what a
"trust registry" actually has to speak to a server, not hiding that
behind a library.

MCP's stdio transport is simple: newline-delimited JSON-RPC 2.0 messages
over stdin/stdout of a subprocess. No Content-Length framing (unlike LSP).
A server may also emit notifications with no "id" field at any time; a
correct client has to skip those while waiting for the response it asked
for, not just blindly read the next line.
"""

import json
import subprocess


class MCPStdioClient:
    def __init__(self, command: list[str]):
        self.proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._next_id = 0

    def _write(self, message: dict):
        self.proc.stdin.write(json.dumps(message) + "\n")
        self.proc.stdin.flush()

    def _read_response(self, expected_id: int, timeout_lines: int = 200) -> dict:
        """Reads lines until it finds the response matching expected_id,
        skipping any server-initiated notifications along the way."""
        for _ in range(timeout_lines):
            line = self.proc.stdout.readline()
            if not line:
                stderr = self.proc.stderr.read()
                raise RuntimeError(f"Server closed stdout unexpectedly. stderr:\n{stderr}")
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if msg.get("id") == expected_id:
                return msg
            # else: a notification (e.g. logging) from the server - ignore it
        raise TimeoutError(f"No response with id={expected_id} after {timeout_lines} lines")

    def _request(self, method: str, params: dict | None = None) -> dict:
        self._next_id += 1
        msg = {"jsonrpc": "2.0", "id": self._next_id, "method": method}
        if params is not None:
            msg["params"] = params
        self._write(msg)
        response = self._read_response(self._next_id)
        if "error" in response:
            raise RuntimeError(f"MCP server returned error for {method}: {response['error']}")
        return response.get("result", {})

    def _notify(self, method: str, params: dict | None = None):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        self._write(msg)

    def initialize(self) -> dict:
        result = self._request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "mcp-trust-registry", "version": "0.3"},
        })
        self._notify("notifications/initialized")
        return result

    def list_tools(self) -> list[dict]:
        return self._request("tools/list").get("tools", [])

    def call_tool(self, name: str, arguments: dict) -> dict:
        return self._request("tools/call", {"name": name, "arguments": arguments})

    def close(self):
        try:
            self.proc.stdin.close()
        except Exception:
            pass
        self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
