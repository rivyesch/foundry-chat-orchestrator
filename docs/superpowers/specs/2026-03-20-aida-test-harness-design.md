# Aida Test Harness — Design Spec

**Date:** 2026-03-20
**Status:** Draft

## Problem

Testing the Aida IT Helpdesk bot is manual — someone opens Teams, chats with the bot, and eyeballs the result. Tests are not repeated, so intermittent LLM failures go undetected. There is no statistical basis for judging quality (e.g., "4 out of 5 runs passed this scenario").

## Solution

A Bowser-style four-layer harness that drives Foundry-direct conversations against the Aida agent, simulates multi-turn users with hybrid scripted/LLM-generated responses, and grades each run with automated checks + LLM judgment. Claude Code agents handle orchestration and intelligence; Python handles only the Foundry SDK plumbing.

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Testing approach | Foundry-direct (not Teams e2e) | Each thread is isolated, no fresh-user-per-run constraint, still exercises full tool-calling path via system context injection |
| Identity mechanism | System context string in first message | `[System Context: channel='Teams_Text', userAadObjectId=..., ...]` — the only identity mechanism the agent uses for tool calls |
| User pool | Max 5 users, freely reusable | ServiceNow side effects are ignorable for grading; Foundry threads are isolated |
| Turn plan | Hybrid — scripted seed + facts, LLM-driven replies | Measures bot variance, not tester variance |
| Grading | Automated checks + LLM-as-judge | Hard checks for tool calls/parameters, soft judgment for tone/protocol |
| Orchestration | Claude Code agents (Bowser pattern) | No Claude API key management; runs through `claude` CLI |
| Test-run agent model | Haiku | User simulation is straightforward; cost-efficient |
| Grader agent model | Sonnet | Needs reasoning for nuanced rubric evaluation |
| Excluded from v1 | Teams routing layer (welcome card, "call me") | Only testable via Graph API e2e; not the priority |

## Architecture

### Layer 1 — Skill: Foundry Driver

Python CLI wrapping the `azure-ai-projects` SDK. Agents call it via Bash and receive structured JSON.

**Module:** `src/foundry_driver/`

**Files:**
- `client.py` — `FoundryClient` class with methods: `create_thread()`, `send_message(thread_id, content)`, `run_and_poll(thread_id)`, `get_messages(thread_id)`, `get_evidence(thread_id)`
- `cli.py` — Click CLI exposing: `create-thread`, `send`, `run`, `messages`, `evidence`, `preflight`
- `models.py` — Pydantic models for all inputs/outputs

**CLI interface:**
```
python -m foundry_driver create-thread → {"thread_id": "..."}
python -m foundry_driver send --thread <id> --message "..." → {"message_id": "..."}
python -m foundry_driver run --thread <id> → {"run_id": "...", "status": "completed"}
python -m foundry_driver messages --thread <id> → [{"role": "user", "content": "..."}, ...]
python -m foundry_driver evidence --thread <id> → {"runs": [{"run_id": "...", "tool_calls": [...]}]}
python -m foundry_driver preflight → validates auth + connectivity
```

**Skill definition:** `.claude/skills/foundry-driver.md` — teaches agents the CLI interface, system context format, and JSON output structure.

**Auth:** `DefaultAzureCredential` — works with `az login` locally. No API keys in code.

**Config:** Environment variables `FOUNDRY_ENDPOINT` and `FOUNDRY_AGENT_ID` loaded from `.env`.

### Layer 2a — Agent: Test Run

**File:** `.claude/agents/test-run-agent.md`
**Model:** Haiku

**Inputs:** Scenario YAML content, assigned user (AAD ID, email, name), run_id, suite output directory.

**Workflow:**
1. Create Foundry thread
2. Send first message: system context + `[[TEST_RUN:<run_id>]]` + scenario's `seed_message`
3. Run agent, read response
4. For each subsequent turn: read agent's response, generate next user reply from persona + facts, send, run, read
5. Stop when: `max_turns` reached, or a `stop_condition` is met, or agent stops asking questions
6. Collect evidence: full transcript + run steps/tool calls for every run in the thread
7. Write run report JSON

**Run report schema:**
```json
{
  "run_id": "uuid",
  "scenario_id": "string",
  "user": {"aad_id": "...", "email": "...", "name": "..."},
  "thread_id": "string",
  "turns": [
    {"role": "user|assistant", "content": "...", "foundry_run_id": "string|null"}
  ],
  "tool_calls": [
    {"foundry_run_id": "...", "tool": "...", "input": {}, "output": {}}
  ],
  "status": "completed|timeout|error",
  "error": "string|null",
  "duration_seconds": 0
}
```

### Layer 2b — Agent: Grader

**File:** `.claude/agents/grader-agent.md`
**Model:** Sonnet

**Inputs:** Path to run report JSON, scenario YAML content.

**Workflow:**
1. Read run report and scenario
2. Automated checks:
   - `required_outcomes` — verify tool calls exist / transcript patterns present
   - `forbidden_outcomes` — verify absence
   - `expected_tools` — verify specific tools called with correct parameters
3. LLM judgment — evaluate each `grader_rubric` item as pass/fail with reasoning
4. Map to analytics schema (from `ConversationAnalytics.cs`): `request_type`, `resolution_status`, `resolution_method`, `form_provided`, `correct_form_provided`, `escalated_to_human`, `bot_failure_type`, `conversation_quality`
5. Write graded report JSON

**Graded report schema:**
```json
{
  "run_id": "uuid",
  "scenario_id": "string",
  "verdict": "pass|fail",
  "automated_checks": {
    "required_outcomes": [{"check": "...", "passed": true}],
    "forbidden_outcomes": [{"check": "...", "passed": true}],
    "expected_tools": [{"tool": "...", "passed": true}]
  },
  "rubric_scores": [
    {"criterion": "...", "passed": true, "reasoning": "..."}
  ],
  "analytics": {
    "request_type": "...",
    "resolution_status": "...",
    "resolution_method": "...",
    "form_provided": false,
    "correct_form_provided": false,
    "escalated_to_human": false,
    "bot_failure_type": "...|null",
    "conversation_quality": 0
  },
  "failure_reasons": ["..."],
  "summary": "..."
}
```

### Layer 3 — Command: Run Suite

**File:** `.claude/commands/run-suite.md`

**Parameters:** `--scenario <id|all>`, `--repeats <n>` (default 5), `--parallel <n>` (default 3, max = user pool size)

**Workflow:**
1. Parse arguments
2. Load scenario(s) from `scenarios/*.yaml`
3. Load user pool from `users.yaml`
4. Expand run matrix: scenarios × repeats
5. Assign users round-robin
6. Create suite output directory: `reports/suite-<YYYY-MM-DD-HHMMSS>/`
7. Execute test runs in waves (wave size = parallel), dispatching `@test-run-agent` instances
8. Execute grading in parallel over completed run reports, dispatching `@grader-agent` instances
9. Aggregate results into summary table (per scenario: passed/total + failure list)

**Wave execution:** With parallel=3 and 5 runs: wave 1 runs 3 agents, wave 2 runs 2 agents. Grading runs all 5 in parallel since it's just reading files + reasoning.

**Error handling:** If a test-run-agent errors/times out, mark that run as `error` status, continue with remaining runs.

### Layer 4 — Justfile

```just
run-suite *ARGS:
    claude "/run-suite {{ARGS}}"

test-single SCENARIO USER:
    claude "Use @test-run-agent for scenario file: scenarios/{{SCENARIO}}.yaml, look up user id {{USER}} from users.yaml for their full details. Generate your own run_id UUID and use reports/ as the output directory."

grade REPORT:
    claude "Use @grader-agent to grade: {{REPORT}}"

setup:
    pip install -e .

preflight:
    python -m foundry_driver preflight
```

## Scenario YAML Schema

```yaml
id: string                    # Unique identifier, matches filename
goal: string                  # Human-readable test description
seed_message: string          # First user message to the agent
persona: string               # Character brief for simulated user
facts:                        # Key-value pairs revealed when agent asks
  key: value
max_turns: int                # Hard cap on conversation length
stop_conditions:              # Natural end conditions
  - string
required_outcomes:            # Must be present — automated pass/fail
  - tool: string
    description: string
forbidden_outcomes:           # Must NOT happen — automated pass/fail
  - string
expected_tools:               # Specific tool + parameter checks (optional)
  - name: string
    params_contain: {}
grader_rubric:                # Natural language criteria for LLM judgment
  - string
```

## User Pool

`users.yaml` — up to 5 test users with AAD object ID, email, display name. Users are reused freely across scenarios; Foundry thread isolation ensures clean state.

## Configuration

| Variable | Source | Description |
|---|---|---|
| `FOUNDRY_ENDPOINT` | `.env` | Azure AI Foundry project endpoint |
| `FOUNDRY_AGENT_ID` | `.env` | Agent ID to test against |
| Auth | `DefaultAzureCredential` | `az login` locally |

## What Is NOT In Scope (v1)

- Teams end-to-end testing via Graph API (welcome card, "call me" routing)
- CI/CD integration (v1 is operator-triggered local workflow)
- Direct database access for evidence (Foundry API only)
- Voice channel testing
- Additional skills for evaluation approaches (will be added later as needed)

## Dependencies

- `azure-ai-projects` — Foundry Agents SDK
- `azure-identity` — DefaultAzureCredential
- `pydantic` — structured models
- `click` — CLI framework
- `pyyaml` — scenario parsing
- Claude Code — agent orchestration runtime
- `just` — command runner
