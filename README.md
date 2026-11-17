# AI IT Helpdesk Agent

A first-line IT support agent built in Python with Claude's tool calling. A user describes a problem in plain English, the agent decides which diagnostics to run, reads the results, and returns a diagnosis, a confidence score and step-by-step advice. If the user can't fix it themselves (or confidence is low), it **creates a support ticket automatically**, like a real service desk escalation.

> Example report: *"My laptop is connected to Wi-Fi but I can't access the internet."*

## How it works

1. The user's report goes to Claude along with five read-only diagnostic tools.
2. Claude works outward like a technician: adapter -> IP config -> gateway -> internet by IP -> DNS.
3. Claude calls `submit_diagnosis` with a diagnosis, confidence (0-100), recommended action and priority.
4. If `user_can_resolve` is false or confidence is under 60%, a ticket is saved to `tickets.json` with the steps already tried.

| Tool | What it checks |
|---|---|
| `get_ipconfig` | IP, subnet, gateway, DNS servers (169.254.x.x = DHCP failure) |
| `ping_gateway` | Local link to the router |
| `ping_dns` | Internet reachability by IP (8.8.8.8) |
| `dns_lookup` | Name resolution |
| `check_network_adapter` | Adapter enabled/connected, Wi-Fi signal |

All tools are **read-only**; the agent never changes a setting. Tool inputs are validated before any command runs, and no shell is used.

## Setup (Windows)

```powershell
git clone <your-repo-url>
cd ai-it-helpdesk-agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
setx ANTHROPIC_API_KEY "your-key-here"   # then open a new terminal
```

## Usage

```powershell
# Real diagnostics on your own machine
python agent.py "My laptop is connected to Wi-Fi but I can't access the internet"

# Demo mode: simulated faults, safe to run anywhere
python agent.py --list-scenarios
python agent.py "Wi-Fi connected but no internet" --demo dns_failure

# View escalated tickets
python tickets.py list
```

Demo scenarios: `dns_failure`, `gateway_unreachable`, `no_ip_address`, `adapter_disabled`, `isp_outage`, `healthy`.

Set `HELPDESK_MODEL` to change the Claude model (default `claude-sonnet-4-6`).

## Tests

```powershell
python -m pytest
```

Tests run offline with a scripted fake model: tool validation, scenario coverage, ticket numbering, and the escalation rules.

## Example output

*(Replace this with a screenshot or paste from your own first run.)*

```
User report: Wi-Fi connected but no internet
Running diagnostics...
  [tool] check_network_adapter()
  [tool] get_ipconfig()
  [tool] ping_gateway()
  [tool] ping_dns()
  [tool] dns_lookup()

Diagnosis:   Internet is reachable by IP but DNS is failing; the configured DNS server is not responding.
Confidence:  ...%
```

## Ideas for next steps

- Send tickets to Jira Service Management via its REST API (replace `create_ticket` in `tickets.py`)
- Add tools for printer status and Windows Update checks
- Add a simple web or Teams chat front end
# ai-it-helpdesk-agent
