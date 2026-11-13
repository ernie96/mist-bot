"""`UncleFarmer.exe --mcp`: a Model Context Protocol server on standard input and output, for AI
assistants and other programs. It holds no game state of its own: each tool is passed over the named
pipe to the open Uncle Farmer (control.py, gui/remote.py), which does it as if the player had. If
Uncle Farmer isn't open, this starts it. Uncle Farmer must allow it in Settings, Control.

Messages are JSON-RPC 2.0, one per line. Its texts are for the program calling it: English only.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from multiprocessing import AuthenticationError
from multiprocessing.connection import Client
from typing import IO, Any

from . import __version__, control, jsonio, paths

VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")     # newest first
START_WAIT = 90.0               # seconds to wait for a started Uncle Farmer to open its pipe
INSTRUCTIONS = ("Uncle Farmer is a farming bot for Mist World. Call status first. What you do is real, as if "
                "the player had done it: ask the player before spending arnebia, selling or throwing items "
                "away, sending messages, closing games or deleting anything. Tools marked destructive need "
                "confirm=true. Read script_reference before writing scripts.")


class Bridge:
    """The connection to the open Uncle Farmer, made (and Uncle Farmer started) when first needed."""

    def __init__(self) -> None:
        self.conn: Any = None
        self.started = False

    @staticmethod
    def _connect() -> Any:
        secret = control.read_secret()
        if secret is None:
            return None
        try:
            return Client(control.pipe_name(), family="AF_PIPE", authkey=secret)
        except (OSError, AuthenticationError, EOFError):
            return None

    def _start_app(self) -> None:
        if self.started:
            return
        self.started = True
        cmd = [paths.exe_path()] if paths.frozen() else [sys.executable, "-m", "unclefarmer"]
        flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        subprocess.Popen(cmd, cwd=paths.APP if paths.frozen() else paths.BUNDLE, stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True, creationflags=flags)

    def connection(self) -> Any:
        if self.conn is not None:
            return self.conn
        conn = self._connect()
        if conn is None and not os.environ.get("UNCLEFARMER_CONTROL_NO_START"):
            self._start_app()
            end = time.monotonic() + START_WAIT
            while conn is None and time.monotonic() < end:
                time.sleep(1.0)
                conn = self._connect()
        if conn is None:
            raise LookupError("Uncle Farmer isn't answering. Is it open? (This server %s it.)" % (
                "started" if self.started else "didn't start"))
        self.conn = conn
        return conn

    def call(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        for attempt in (1, 2):              # once more on a fresh connection if the old one broke
            try:
                conn = self.connection()
            except LookupError as e:
                return {"ok": False, "text": str(e)}
            try:
                control.send(conn, {"tool": tool, "args": args})
                answer = control.receive(conn)
            except (OSError, EOFError, ValueError) as e:
                self.close()
                if attempt == 2:
                    return {"ok": False, "text": "Lost the connection to Uncle Farmer: %s" % e}
                continue
            return answer if jsonio.is_object(answer) else {"ok": False, "text": "A wrong answer came back."}
        return {"ok": False, "text": "No answer."}

    def close(self) -> None:
        if self.conn is not None:
            try:
                self.conn.close()
            except OSError:
                pass
            self.conn = None


def tools_list() -> list[dict[str, Any]]:
    return [{"name": t.name, "description": t.description, "inputSchema": t.schema(),
             "annotations": t.annotations()} for t in control.TOOLS]


def call_result(answer: dict[str, Any]) -> dict[str, Any]:
    text = str(answer.get("text") or "")
    data = answer.get("data")
    content = [{"type": "text", "text": text or ("Done." if answer.get("ok") else "Failed.")}]
    if data is not None:
        content.append({"type": "text", "text": json.dumps(data, ensure_ascii=False, default=str)})
    return {"content": content, "isError": not answer.get("ok")}


def handle(msg: Any, bridge: Bridge) -> dict[str, Any] | None:
    """One JSON-RPC message -> the response, or None for a notification."""
    if not jsonio.is_object(msg):
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid request"}}
    method: Any = msg.get("method")
    mid: Any = msg.get("id")
    raw_params: Any = msg.get("params")
    params: dict[str, Any] = raw_params if jsonio.is_object(raw_params) else {}
    if mid is None:                       # a notification (initialized, cancelled): nothing to answer
        return None

    def ok(result: dict[str, Any]) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": mid, "result": result}

    if method == "initialize":
        asked: Any = params.get("protocolVersion")
        return ok({"protocolVersion": asked if asked in VERSIONS else VERSIONS[0],
                   "capabilities": {"tools": {"listChanged": False}},
                   "serverInfo": {"name": "uncle-farmer", "title": "Uncle Farmer (Mist Bot)", "version": __version__},
                   "instructions": INSTRUCTIONS})
    if method == "ping":
        return ok({})
    if method == "tools/list":
        return ok({"tools": tools_list()})
    if method == "tools/call":
        name: Any = params.get("name")
        raw_args: Any = params.get("arguments")
        args: dict[str, Any] = raw_args if jsonio.is_object(raw_args) else {}
        if name not in control.BY_NAME:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": "Unknown tool: %s" % name}}
        return ok(call_result(bridge.call(str(name), args)))
    if method in ("resources/list", "prompts/list"):
        return ok({str(method).split("/")[0]: []})
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "Method not found: %s" % method}}


def write(out: IO[bytes], obj: object) -> None:
    out.write(json.dumps(obj, ensure_ascii=False).encode("utf-8") + b"\n")
    out.flush()


def serve(inp: IO[bytes], out: IO[bytes], bridge: Bridge | None = None) -> None:
    bridge = bridge or Bridge()
    try:
        for raw in inp:
            line = raw.strip()
            if not line:
                continue
            try:
                msg: Any = json.loads(line.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                write(out, {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}})
                continue
            if jsonio.is_array(msg):            # a batch (2025-03-26)
                batch: list[Any] = msg
                replies = [r for r in (handle(m, bridge) for m in batch) if r is not None]
                if replies:
                    write(out, replies)
                continue
            reply = handle(msg, bridge)
            if reply is not None:
                write(out, reply)
    finally:
        bridge.close()


def main() -> int:
    if sys.stdin is None or sys.stdout is None:     # started with no standard input and output to talk on
        return 2
    serve(sys.stdin.buffer, sys.stdout.buffer)
    return 0
