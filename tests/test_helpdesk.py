import sys
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import agent
import tickets
from scenarios import SCENARIOS
from tools import FUNCTIONS, run_tool, _parse_gateway


def tool_use(name, inp, id_="t1"):
    return NS(type="tool_use", name=name, input=inp, id=id_)


class FakeClient:
    """Plays back scripted model responses so the agent loop can be tested offline."""
    def __init__(self, script):
        self.script = list(script)
        self.messages = NS(create=self._create)

    def _create(self, **kwargs):
        return NS(content=self.script.pop(0))


def test_every_scenario_covers_every_tool():
    for name, s in SCENARIOS.items():
        for tool in FUNCTIONS:
            assert tool in s, f"{name} missing {tool}"


def test_demo_mode_returns_scenario_output():
    assert "FAILED" in run_tool("dns_lookup", {}, scenario="dns_failure")


def test_invalid_targets_are_rejected():
    assert "invalid" in run_tool("ping_dns", {"target": "8.8.8.8; rm -rf /"}).lower()
    assert "invalid" in run_tool("dns_lookup", {"hostname": "a b"}).lower()


def test_unknown_tool():
    assert "unknown tool" in run_tool("format_disk")


def test_ticket_ids_increment(tmp_path):
    p = tmp_path / "t.json"
    a = tickets.create_ticket("a", "d", [], path=p)
    b = tickets.create_ticket("b", "d", [], path=p)
    assert (a["id"], b["id"]) == ("HD-0001", "HD-0002")


def test_unresolvable_issue_creates_ticket(tmp_path):
    client = FakeClient([
        [tool_use("ping_gateway", {})],
        [tool_use("submit_diagnosis", {
            "diagnosis": "Router unreachable", "confidence": 90,
            "recommended_action": "1. Restart router", "user_can_resolve": False, "priority": "High"})],
    ])
    out = agent.run_agent("no internet", client, scenario="gateway_unreachable",
                          tickets_path=tmp_path / "t.json", verbose=False)
    assert out["ticket"]["id"] == "HD-0001"
    assert out["steps"][0]["tool"] == "ping_gateway"


def test_resolvable_issue_creates_no_ticket(tmp_path):
    client = FakeClient([
        [tool_use("check_network_adapter", {})],
        [tool_use("submit_diagnosis", {
            "diagnosis": "Wi-Fi adapter disabled", "confidence": 95,
            "recommended_action": "1. Turn Wi-Fi on", "user_can_resolve": True, "priority": "Low"})],
    ])
    out = agent.run_agent("no wifi", client, scenario="adapter_disabled",
                          tickets_path=tmp_path / "t.json", verbose=False)
    assert out["ticket"] is None


def test_low_confidence_escalates(tmp_path):
    client = FakeClient([[tool_use("submit_diagnosis", {
        "diagnosis": "Unclear", "confidence": 40,
        "recommended_action": "1. Retry", "user_can_resolve": True, "priority": "Medium"})]])
    out = agent.run_agent("weird", client, tickets_path=tmp_path / "t.json", verbose=False)
    assert out["ticket"] is not None


def test_gateway_parsing_all_platforms():
    assert _parse_gateway("   Default Gateway . . . . . . . . . : 192.168.1.1") == "192.168.1.1"
    assert _parse_gateway("   route to: default\ndestination: default\n    gateway: 10.0.0.1\n  interface: en0") == "10.0.0.1"
    assert _parse_gateway("default via 172.16.0.1 dev eth0") == "172.16.0.1"
    assert _parse_gateway("nothing here") is None


def test_high_priority_always_escalates(tmp_path):
    client = FakeClient([[tool_use("submit_diagnosis", {
        "diagnosis": "DNS server down", "confidence": 95,
        "recommended_action": "1. Restart router", "user_can_resolve": True, "priority": "High"})]])
    out = agent.run_agent("no internet", client, tickets_path=tmp_path / "t.json", verbose=False)
    assert out["ticket"] is not None
