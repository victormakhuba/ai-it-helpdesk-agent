"""Diagnostic tools the agent can call.

Real mode runs read-only Windows/Linux/macOS commands. Demo mode returns
canned output from scenarios.py. No tool changes any system setting.
"""
import platform
import re
import socket
import subprocess

from scenarios import SCENARIOS

IS_WINDOWS = platform.system() == "Windows"
HOST_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9.\-]{0,251}[A-Za-z0-9])?$")

TOOL_SCHEMAS = [
    {
        "name": "get_ipconfig",
        "description": "Show the machine's IP configuration: IP address, subnet mask, default gateway and DNS servers. A 169.254.x.x address means DHCP failed.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "ping_gateway",
        "description": "Ping the default gateway (the router). Tests the local network link.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "ping_dns",
        "description": "Ping a public IP address (default 8.8.8.8) to test internet reachability without relying on DNS.",
        "input_schema": {
            "type": "object",
            "properties": {"target": {"type": "string", "description": "IP address to ping, e.g. 8.8.8.8"}},
        },
    },
    {
        "name": "dns_lookup",
        "description": "Resolve a hostname (default www.microsoft.com) to test DNS name resolution.",
        "input_schema": {
            "type": "object",
            "properties": {"hostname": {"type": "string", "description": "Hostname to resolve"}},
        },
    },
    {
        "name": "check_network_adapter",
        "description": "Show whether the network adapter is enabled and connected, and Wi-Fi signal strength where available.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


def _run(cmd, timeout=20):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (out.stdout or "") + (out.stderr or "")
    except FileNotFoundError:
        return f"FAILED: command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return f"FAILED: {' '.join(cmd)} timed out"


def _ping(host):
    if not HOST_RE.match(host):
        return "FAILED: invalid target"
    flag = "-n" if IS_WINDOWS else "-c"
    return _run(["ping", flag, "4", host], timeout=30)


def get_ipconfig():
    return _run(["ipconfig", "/all"]) if IS_WINDOWS else _run(["ip", "addr"]) 


def _default_gateway():
    text = _run(["ipconfig"]) if IS_WINDOWS else _run(["ip", "route"])
    if IS_WINDOWS:
        m = re.search(r"Default Gateway[ .]*:\s*(\d+\.\d+\.\d+\.\d+)", text)
    else:
        m = re.search(r"default via (\d+\.\d+\.\d+\.\d+)", text)
    return m.group(1) if m else None


def ping_gateway():
    gw = _default_gateway()
    if not gw:
        return "FAILED: no default gateway configured"
    return f"Pinging gateway {gw}\n" + _ping(gw)


def ping_dns(target="8.8.8.8"):
    return _ping(target)


def dns_lookup(hostname="www.microsoft.com"):
    if not HOST_RE.match(hostname):
        return "FAILED: invalid hostname"
    try:
        ip = socket.gethostbyname(hostname)
        return f"OK: {hostname} -> {ip}"
    except OSError as e:
        return f"FAILED: could not resolve '{hostname}' ({e})"


def check_network_adapter():
    if IS_WINDOWS:
        return _run(["netsh", "interface", "show", "interface"]) + "\n" + _run(["netsh", "wlan", "show", "interfaces"])
    return _run(["ip", "-brief", "link"])


FUNCTIONS = {
    "get_ipconfig": get_ipconfig,
    "ping_gateway": ping_gateway,
    "ping_dns": ping_dns,
    "dns_lookup": dns_lookup,
    "check_network_adapter": check_network_adapter,
}


def run_tool(name, args=None, scenario=None):
    """Run a tool by name. If `scenario` is given, return simulated output."""
    args = args or {}
    if name not in FUNCTIONS:
        return f"FAILED: unknown tool '{name}'"
    if scenario:
        return SCENARIOS[scenario][name]
    allowed = {"ping_dns": {"target"}, "dns_lookup": {"hostname"}}.get(name, set())
    clean = {k: v for k, v in args.items() if k in allowed and isinstance(v, str)}
    return FUNCTIONS[name](**clean)
