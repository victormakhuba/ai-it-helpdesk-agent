"""AI IT Helpdesk Agent: a first-line technician that diagnoses network problems.

The model decides which diagnostic tools to call, reads the results,
then submits a structured diagnosis. If it cannot be resolved by the user
(or confidence is low), a ticket is created automatically.
"""
import argparse
import json
import os
import sys

from scenarios import SCENARIOS
from tickets import create_ticket
from tools import TOOL_SCHEMAS, run_tool

MODEL = os.environ.get("HELPDESK_MODEL", "claude-sonnet-4-6")
MAX_TURNS = 8
CONFIDENCE_THRESHOLD = 60

SYSTEM_PROMPT = """You are a first-line IT helpdesk technician. A user reports a network problem.
Work like a good support technician:
1. Start with the basics and work outward: adapter -> IP config -> gateway -> internet by IP -> DNS.
2. Call diagnostic tools, read the output carefully, and only claim what the evidence shows.
3. When you have enough evidence, call submit_diagnosis exactly once.
In submit_diagnosis, write recommended_action as short numbered steps a non-technical user can follow.
Set user_can_resolve to false if the fix needs IT staff, an ISP, hardware, or admin rights.
Prefer the simplest safe fix first (reconnect, restart the router, toggle the adapter). Do not tell users to
change IP or DNS settings manually unless nothing simpler fits; if the fault is a router, DHCP or server
setting, set user_can_resolve to false so IT can fix it properly.
Use priority High only for outages affecting the whole connection; Low for quick self-fixes.
Be honest about uncertainty: confidence is 0-100 and should be lower when evidence is mixed."""

SUBMIT_TOOL = {
    "name": "submit_diagnosis",
    "description": "Submit the final diagnosis once enough evidence has been gathered.",
    "input_schema": {
        "type": "object",
        "properties": {
            "diagnosis": {"type": "string", "description": "Most likely root cause, one or two sentences."},
            "confidence": {"type": "integer", "description": "Confidence 0-100."},
            "recommended_action": {"type": "string", "description": "Numbered steps the user can follow."},
            "user_can_resolve": {"type": "boolean", "description": "True if the user can fix this themselves."},
            "priority": {"type": "string", "enum": ["Low", "Medium", "High"]},
        },
        "required": ["diagnosis", "confidence", "recommended_action", "user_can_resolve", "priority"],
    },
}


def run_agent(problem, client, scenario=None, tickets_path=None, verbose=True):
    """Diagnose `problem`. Returns dict with the diagnosis, steps tried and ticket (if any)."""
    messages = [{"role": "user", "content": problem}]
    steps = []
    result = None

    for _ in range(MAX_TURNS):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS + [SUBMIT_TOOL],
            messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})
        tool_results = []
        for block in resp.content:
            if block.type != "tool_use":
                continue
            if block.name == "submit_diagnosis":
                result = block.input
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": "Diagnosis recorded."})
            else:
                output = run_tool(block.name, block.input, scenario)
                steps.append({"tool": block.name, "args": block.input, "output": output})
                if verbose:
                    print(f"  [tool] {block.name}({json.dumps(block.input) if block.input else ''})")
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
        if result or not tool_results:
            break
        messages.append({"role": "user", "content": tool_results})

    if result is None:
        result = {
            "diagnosis": "Agent could not reach a diagnosis.",
            "confidence": 0,
            "recommended_action": "Escalate to a technician.",
            "user_can_resolve": False,
            "priority": "Medium",
        }

    ticket = None
    needs_ticket = (
        not result["user_can_resolve"]
        or result["confidence"] < CONFIDENCE_THRESHOLD
        or result["priority"] == "High"
    )
    if needs_ticket:
        kwargs = {"path": tickets_path} if tickets_path else {}
        ticket = create_ticket(
            summary=f"Network issue: {problem[:80]}",
            details=f"Diagnosis: {result['diagnosis']} (confidence {result['confidence']}%)\n"
                    f"Recommended action: {result['recommended_action']}",
            steps_tried=[f"{s['tool']}: {s['output'].strip().splitlines()[0] if s['output'].strip() else ''}" for s in steps],
            priority=result["priority"],
            **kwargs,
        )
    return {"result": result, "steps": steps, "ticket": ticket}


def main():
    parser = argparse.ArgumentParser(description="AI IT Helpdesk Agent")
    parser.add_argument("problem", nargs="?", help="Describe the problem in plain English")
    parser.add_argument("--demo", choices=sorted(SCENARIOS), help="Use a simulated network fault")
    parser.add_argument("--list-scenarios", action="store_true")
    args = parser.parse_args()

    if args.list_scenarios:
        for name, s in SCENARIOS.items():
            print(f"{name:20} {s['description']}")
        return
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first (see README).")

    import anthropic
    problem = args.problem or input("What's the problem? ")
    print(f"\nUser report: {problem}\nRunning diagnostics...")
    out = run_agent(problem, anthropic.Anthropic(), scenario=args.demo)
    r = out["result"]
    print(f"\nDiagnosis:   {r['diagnosis']}")
    print(f"Confidence:  {r['confidence']}%")
    print(f"Priority:    {r['priority']}")
    print(f"\nRecommended action:\n{r['recommended_action']}")
    if out["ticket"]:
        print(f"\nTicket {out['ticket']['id']} created and escalated to IT support.")
    else:
        print("\nNo ticket needed.")


if __name__ == "__main__":
    main()
