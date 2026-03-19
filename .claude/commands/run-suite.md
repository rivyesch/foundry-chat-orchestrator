# Run Test Suite

Run a test suite against the Aida bot with configurable scenarios, repeat count, and parallelism.

## Usage

```
/run-suite --scenario <id|all> --repeats <n> --parallel <n>
```

**Defaults:** repeats=5, parallel=3

**Examples:**
- `/run-suite --scenario printer-issue --repeats 5 --parallel 3`
- `/run-suite --scenario all --repeats 3 --parallel 5`
- `/run-suite --scenario printer-issue --repeats 1 --parallel 1` (single debug run)

## Execution Steps

### 1. Parse Arguments

Extract from `{PROMPT}`:
- `scenario`: scenario ID or "all" (required)
- `repeats`: number of times to repeat each scenario (default: 5)
- `parallel`: max concurrent test-run agents (default: 3)

### 2. Load Scenarios

If scenario is "all", read every `.yaml` file in `scenarios/`.
Otherwise, read `scenarios/<scenario>.yaml`.

Verify each file exists and is valid YAML with at least: `id`, `goal`, `seed_message`, `persona`, `facts`.

### 3. Load User Pool

Read `users.yaml`. Extract the list of users. Verify each has `id`, `aad_object_id`, `email`, `display_name`.

If `parallel` > number of users, cap `parallel` at the user count and warn:
> "Parallel capped at {n} — only {n} test users available."

### 4. Expand Run Matrix

For each scenario x repeat, create a run entry:
- `run_id`: generate a UUID
- `scenario_id`: from the scenario
- `user`: assign round-robin from the user pool

Example with 2 scenarios x 3 repeats = 6 runs:
- Run 1: scenario-A, user-1
- Run 2: scenario-A, user-2
- Run 3: scenario-A, user-3
- Run 4: scenario-B, user-4
- Run 5: scenario-B, user-5
- Run 6: scenario-B, user-1

### 5. Create Output Directory

```bash
mkdir -p reports/suite-<YYYY-MM-DD-HHMMSS>
```

### 6. Execute Test Runs in Waves

Split runs into waves of size `parallel`.

For each wave, dispatch `@test-run-agent` instances **in parallel** using the Agent tool. Each agent receives:
- The scenario YAML content (read from the file)
- The assigned user's full details (from users.yaml)
- The run_id
- The output directory path

**Example dispatch for a wave of 3:**

Use the Agent tool three times in parallel, each with:

```
Use @test-run-agent to execute this test run:

**Run ID:** <run_id>

**Output Directory:** reports/suite-<timestamp>/

**User:**
- AAD Object ID: <aad_object_id>
- Email: <email>
- Display Name: <display_name>

**Scenario:**
<paste full scenario YAML content here>
```

Wait for the wave to complete. Report progress:
> "Wave 1/2 complete: 3 runs finished (2 completed, 1 error)"

### 7. Grade All Runs

After ALL test runs are complete, dispatch `@grader-agent` instances **in parallel** — one per completed run. All graders can run simultaneously since they only read files.

Each grader receives:
```
Use @grader-agent to grade this test run:

**Run Report:** <path to run report JSON>

**Scenario:**
<paste full scenario YAML content here>
```

### 8. Aggregate and Report

Read all `*_graded.json` files from the output directory. Build the summary:

```
┌─────────────────┬────────┬──────────────────────────────────┐
│ Scenario        │ Result │ Failures                         │
├─────────────────┼────────┼──────────────────────────────────┤
│ printer-issue   │ 4/5    │ Run 3: one-question-per-turn     │
│ escalation      │ 5/5    │ —                                │
└─────────────────┴────────┴──────────────────────────────────┘

Overall: 9/10 passed (90%)
Reports: reports/suite-2026-03-20-143022/
```

For each failure, show the run_id and the primary failure reason from the graded report.

If any runs had status "error" (test-run-agent failed), list those separately:

```
Errors (test harness failures, not bot failures):
- Run <id>: <error message>
```
