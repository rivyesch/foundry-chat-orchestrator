# Aida Test Harness — one-liner entry points

# ─── Layer 4: Entry Points ───────────────────────────────────

# Run a full test suite
run-suite *ARGS:
    claude "/run-suite {{ARGS}}"

# Run a single scenario with one user (for debugging)
# Agent generates its own run_id (UUID) and defaults output to reports/
test-single SCENARIO USER:
    claude "Use @test-run-agent for scenario file: scenarios/{{SCENARIO}}.yaml, look up user id {{USER}} from users.yaml for their full details. Generate your own run_id UUID and use reports/ as the output directory."

# Grade a single run report (for re-grading)
grade REPORT:
    claude "Use @grader-agent to grade: {{REPORT}}"

# ─── Setup & Validation ─────────────────────────────────────

# Install dependencies
setup:
    uv pip install -e ".[dev]"

# Verify auth and Foundry connectivity
preflight:
    python -m foundry_driver preflight

# Run Python unit tests
test:
    python -m pytest -v
