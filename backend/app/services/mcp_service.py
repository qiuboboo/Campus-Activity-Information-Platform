"""MCP Client — lightweight client for the Model Context Protocol.

Provides a unified interface for connecting to MCP servers (xiaohongshu, search, etc.)
and calling their tools.  Manages MCP server processes as subprocesses.

Usage::

    from .mcp_service import call_tool

    result = call_tool("xiaohongshu", "search_notes", {"query": "校园活动"})
"""

from __future__ import annotations

import json
import logging
import os
import shlex
import subprocess
import threading
from contextlib import suppress
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MCP Server process management
# ---------------------------------------------------------------------------

_server_processes: dict[str, subprocess.Popen] = {}
_server_lock = threading.Lock()
_MCP_START_TIMEOUT = 15


def _get_mcp_config() -> dict[str, dict]:
    """Read MCP server configuration from environment.

    Format (MCP_SERVERS env var)::

        MCP_SERVERS=xiaohongshu,search
        MCP_XIAOHONGSHU_COMMAND=npx
        MCP_XIAOHONGSHU_ARGS=-y xiaohongshu-mcp
        MCP_SEARCH_COMMAND=npx
        MCP_SEARCH_ARGS=-y @anthropic/search-mcp
    """
    servers_str = os.environ.get("MCP_SERVERS", "")
    if not servers_str:
        return {}

    config: dict[str, dict] = {}
    for name in servers_str.split(","):
        name = name.strip()
        if not name:
            continue
        prefix = f"MCP_{name.upper()}"
        cmd = os.environ.get(f"{prefix}_COMMAND", "")
        args = os.environ.get(f"{prefix}_ARGS", "")
        if cmd:
            config[name] = {"command": cmd, "args": shlex.split(args) if args else []}
    return config


def _start_server(name: str, config: dict) -> None:
    """Start an MCP server subprocess."""
    with _server_lock:
        if name in _server_processes:
            proc = _server_processes[name]
            if proc.poll() is None:
                return  # already running

        logger.info("Starting MCP server: %s (%s %s)", name, config["command"], config["args"])
        try:
            proc = subprocess.Popen(
                [config["command"]] + config["args"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            _server_processes[name] = proc
        except FileNotFoundError as e:
            logger.error("Failed to start MCP server '%s': %s", name, e)


def _stop_server(name: str) -> None:
    """Stop an MCP server subprocess."""
    with _server_lock:
        proc = _server_processes.pop(name, None)
        if proc and proc.poll() is None:
            proc.terminate()
            with suppress(Exception):
                proc.wait(timeout=5)


def stop_all() -> None:
    """Stop all MCP server processes."""
    for name in list(_server_processes.keys()):
        _stop_server(name)


# ---------------------------------------------------------------------------
# MCP JSON-RPC message helpers
# ---------------------------------------------------------------------------

_MCP_REQUEST_ID = 0


def _next_id() -> int:
    global _MCP_REQUEST_ID
    _MCP_REQUEST_ID += 1
    return _MCP_REQUEST_ID


def _build_request(method: str, params: dict | None = None) -> str:
    return json.dumps(
        {"jsonrpc": "2.0", "id": _next_id(), "method": method, "params": params or {}}
    )


def _send_recv(proc: subprocess.Popen, request: str, timeout: int = 30) -> dict | None:
    """Send a JSON-RPC request to an MCP process and read the response."""
    if proc.stdin is None or proc.stdout is None:
        logger.error("MCP process has no stdin/stdout")
        return None

    try:
        proc.stdin.write(request + "\n")
        proc.stdin.flush()

        line = proc.stdout.readline()
        if not line:
            logger.error("MCP process returned empty response")
            return None

        response = json.loads(line)
        if "error" in response:
            logger.error("MCP error: %s", response["error"])
            return None
        return response.get("result")
    except (BrokenPipeError, TimeoutError, json.JSONDecodeError) as e:
        logger.error("MCP communication error: %s", e)
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def list_servers() -> dict[str, dict]:
    """Return the configured MCP servers and their running status."""
    config = _get_mcp_config()
    result = {}
    for name, cfg in config.items():
        proc = _server_processes.get(name)
        running = proc is not None and proc.poll() is None
        result[name] = {"command": cfg["command"], "running": running}
    return result


def call_tool(server_name: str, tool: str, params: dict | None = None) -> dict | None:
    """Call a tool on an MCP server.

    Args:
        server_name: Name of the MCP server (e.g. ``"xiaohongshu"``).
        tool: The tool/method name (e.g. ``"search_notes"``).
        params: Tool parameters as a dict.

    Returns:
        The result dict, or ``None`` on failure.
    """
    config = _get_mcp_config()
    if server_name not in config:
        logger.warning("MCP server '%s' not configured in MCP_SERVERS", server_name)
        return None

    _start_server(server_name, config[server_name])
    proc = _server_processes.get(server_name)
    if proc is None or proc.poll() is not None:
        logger.error("MCP server '%s' failed to start", server_name)
        return None

    # Per MCP protocol: call tools/list first to discover available tools
    # then call tools/call with the selected tool
    request = _build_request("tools/call", {"name": tool, "arguments": params or {}})
    return _send_recv(proc, request)


def list_tools(server_name: str) -> list[dict] | None:
    """List available tools on an MCP server."""
    config = _get_mcp_config()
    if server_name not in config:
        logger.warning("MCP server '%s' not configured", server_name)
        return None

    _start_server(server_name, config[server_name])
    proc = _server_processes.get(server_name)
    if proc is None or proc.poll() is not None:
        return None

    request = _build_request("tools/list")
    result = _send_recv(proc, request)
    return result.get("tools", []) if result else None


# ---------------------------------------------------------------------------
# Convenience: XHS (xiaohongshu) search
# ---------------------------------------------------------------------------


def search_xiaohongshu(query: str, **kwargs) -> list[dict]:
    """Search for notes on Xiaohongshu via MCP.

    Args:
        query: Search keywords.
        **kwargs: Additional parameters (limit, sort, etc.) passed to the MCP tool.

    Returns:
        A list of note dicts, or an empty list on failure.
    """
    params = {"query": query, **kwargs}
    result = call_tool("xiaohongshu", "search_notes", params)
    if result is None:
        return []
    # The MCP response may wrap results in different structures
    if isinstance(result, list):
        return result
    if "notes" in result:
        return result["notes"]
    if "results" in result:
        return result["results"]
    return [result]
