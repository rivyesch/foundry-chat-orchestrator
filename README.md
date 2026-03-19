# Aida Test Harness

Automated regression testing for the Aida IT Helpdesk bot using Azure AI Foundry direct conversations, Claude Code agent orchestration, and the Bowser layered architecture pattern.

## What It Does

Runs repeated test scenarios against the Aida bot via the Foundry Agents API, simulates realistic multi-turn user conversations, and grades each run using both automated checks and LLM judgment. Produces pass/fail statistics with full evidence trails.

## Architecture

Four-layer Bowser-style stack ([reference](https://github.com/disler/bowser)):

| Layer | Component | Purpose |
|---|---|---|
| **Layer 1 — Skill** | `foundry-driver` (Python CLI) | Drives Foundry conversations: create thread, send message, run agent, collect evidence |
| **Layer 2 — Agent** | `test-run-agent` (haiku) | Owns one test run: simulates a user following a scenario's turn plan |
| **Layer 2 — Agent** | `grader-agent` (sonnet) | Grades a completed run: automated checks + LLM judgment against rubric |
| **Layer 3 — Command** | `run-suite` | Orchestrates: expand scenarios x repeats, dispatch agents in waves, aggregate results |
| **Layer 4 — Justfile** | `justfile` | One-liner entry points for running suites, single tests, grading |

## Testing Approach

- **Foundry-direct**: Bypasses Teams, talks to the Foundry agent API directly. Each run creates a fresh thread — no user isolation issues.
- **System context injection**: First message includes `[System Context: channel='Teams_Text', userAadObjectId=..., ...]` so tool calls (send Teams message, user lookup, ticket creation) execute against real identities.
- **Hybrid turn plan**: Scenarios define a seed message + persona + key facts. The simulated user (haiku) generates natural replies constrained by the facts — measures bot variance, not tester variance.
- **Dual grading**: Automated checks for hard requirements (tool was called, correct parameters) + LLM-as-judge (sonnet) for soft requirements (tone, protocol adherence, conversation quality).
- **Statistical confidence**: Each scenario runs N times (default 5) to surface intermittent LLM failures instead of relying on single-shot testing.

## Repo Structure

```
foundry-chat-orchestrator/
├── justfile                          # Layer 4 — one-liner entry points
├── pyproject.toml                    # Python dependencies
├── .env.example                      # Required env vars
├── .claude/
│   ├── settings.json
│   ├── skills/
│   │   └── foundry-driver.md         # Layer 1 — skill definition
│   ├── agents/
│   │   ├── test-run-agent.md         # Layer 2 — test runner
│   │   └── grader-agent.md           # Layer 2 — evaluator
│   └── commands/
│       └── run-suite.md              # Layer 3 — orchestration
├── src/
│   └── foundry_driver/
│       ├── __init__.py
│       ├── client.py                 # Foundry SDK wrapper
│       ├── cli.py                    # CLI for agents to call
│       └── models.py                 # Pydantic models
├── scenarios/                        # Test scenario YAMLs
│   ├── printer-issue.yaml
│   └── ...
├── users.yaml                        # Test user pool (AAD IDs, emails)
└── reports/                          # Output: run + graded reports
```

## Scenario YAML Schema

```yaml
id: printer-issue
goal: "User has a UniFlow printer issue that needs KB lookup and escalation"
seed_message: "Hi, my printer isn't working"
persona: "Slightly frustrated office worker, gives short answers"
facts:
  printer_type: "UniFlow on laptop"
  tried_restart: true
  restart_helped: false
  contact_number: "0412345678"
max_turns: 12
stop_conditions:
  - "agent provides a ticket number"
  - "agent says goodbye or ends conversation"
required_outcomes:
  - tool: "azure-ai-search"
    description: "Agent must search KB"
  - tool: "create-interaction"
    description: "Agent must create IMS"
  - tool: "create-incident"
    description: "Agent must escalate to INC"
forbidden_outcomes:
  - "Agent fabricates a ticket number before tool call completes"
  - "Agent provides troubleshooting steps without searching KB first"
expected_tools:
  - name: "get-user"
    params_contain: {email: true}
grader_rubric:
  - "Agent follows one-question-per-turn pacing"
  - "Agent searches KB before providing Asahi-specific steps"
  - "Agent uses gender-neutral language in ticket descriptions"
```

## End-to-End Data Flow

```
just run-suite --scenario printer-issue --repeats 5 --parallel 3
│
├─ claude "/run-suite --scenario printer-issue --repeats 5 --parallel 3"
│
├─ Layer 3: run-suite.md command activates
│  ├─ Reads scenarios/printer-issue.yaml
│  ├─ Reads users.yaml (5 users available)
│  ├─ Expands: 1 scenario × 5 repeats = 5 runs
│  ├─ Assigns: run1→user1, run2→user2, ..., run5→user5
│  │
│  ├─ Wave 1 (parallel=3):
│  │  ├─ @test-run-agent (run1, printer-issue, user1)
│  │  ├─ @test-run-agent (run2, printer-issue, user2)
│  │  └─ @test-run-agent (run3, printer-issue, user3)
│  │     │
│  │     │  Each agent independently:
│  │     ├─ foundry_driver create-thread
│  │     ├─ foundry_driver send --message "[System Context: ...] Hi, my printer isn't working"
│  │     ├─ foundry_driver run → reads response
│  │     ├─ (generates next user reply from persona + facts)
│  │     ├─ foundry_driver send → foundry_driver run → ...
│  │     ├─ (repeats until stop_condition or max_turns)
│  │     ├─ foundry_driver evidence → collects tool calls
│  │     └─ Writes reports/suite-<id>/printer-issue_run1.json
│  │
│  ├─ Wave 2 (remaining 2 runs)
│  │
│  ├─ Grading (all 5 in parallel):
│  │  ├─ @grader-agent reads each run report + scenario YAML
│  │  ├─ Automated checks (required/forbidden outcomes, expected tools)
│  │  ├─ LLM judgment against rubric
│  │  └─ Writes graded report JSON
│  │
│  └─ Aggregation:
│     ┌─────────────────┬────────┬──────────────────────────────────┐
│     │ Scenario        │ Result │ Failures                         │
│     ├─────────────────┼────────┼──────────────────────────────────┤
│     │ printer-issue   │ 4/5    │ Run 3: one-question-per-turn     │
│     └─────────────────┴────────┴──────────────────────────────────┘
│     Overall: 4/5 passed (80%)
│     Reports: reports/suite-2026-03-20-143022/
```

## Setup

```bash
# Install dependencies
just setup

# Configure environment
cp .env.example .env
# Edit .env with your Foundry endpoint and agent ID

# Authenticate
az login

# Verify connectivity
just preflight

# Run a suite
just run-suite --scenario printer-issue --repeats 5 --parallel 3
```

## Configuration

### Environment Variables

| Variable | Description |
|---|---|
| `FOUNDRY_ENDPOINT` | Azure AI Foundry project endpoint |
| `FOUNDRY_AGENT_ID` | Agent ID to test against |

### User Pool

Edit `users.yaml` with up to 5 test users. Each user needs an AAD object ID, email, and display name. Users are reused freely across scenarios — each Foundry thread is isolated.
