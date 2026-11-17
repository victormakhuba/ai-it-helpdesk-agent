"""Minimal ticket store (JSON file) standing in for a service desk tool.

Swap `create_ticket` for a Jira Service Management API call to integrate
with a real helpdesk.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_PATH = Path(__file__).parent / "tickets.json"


def _load(path):
    path = Path(path)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def create_ticket(summary, details, steps_tried, priority="Medium", path=DEFAULT_PATH):
    tickets = _load(path)
    ticket = {
        "id": f"HD-{len(tickets) + 1:04d}",
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "Open",
        "priority": priority,
        "summary": summary,
        "details": details,
        "steps_tried": steps_tried,
    }
    tickets.append(ticket)
    Path(path).write_text(json.dumps(tickets, indent=2), encoding="utf-8")
    return ticket


def list_tickets(path=DEFAULT_PATH):
    return _load(path)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        for t in list_tickets():
            print(f"{t['id']}  [{t['priority']}]  {t['status']}  {t['summary']}")
    else:
        print("Usage: python tickets.py list")
