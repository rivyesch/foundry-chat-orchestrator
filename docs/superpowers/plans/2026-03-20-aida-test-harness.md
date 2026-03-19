# Aida Test Harness Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Bowser-style four-layer test harness that drives Foundry-direct conversations against the Aida bot, simulates multi-turn users, and grades each run with automated checks + LLM judgment.

**Architecture:** Python CLI wraps the Azure AI Foundry SDK (Layer 1). Claude Code agents simulate users and grade conversations (Layer 2). A command orchestrates parallel test runs in waves (Layer 3). Justfile provides one-liner entry points (Layer 4).

**Tech Stack:** Python 3.11+, azure-ai-projects SDK, azure-identity, Pydantic, Click, PyYAML, Claude Code agents, just

**Spec:** `docs/superpowers/specs/2026-03-20-aida-test-harness-design.md`

---

## File Structure

| File | Responsibility |
|---|---|
| `pyproject.toml` | Project metadata, dependencies, CLI entry point |
| `.env.example` | Template for required env vars |
| `justfile` | Layer 4 — one-liner entry points |
| `src/foundry_driver/__init__.py` | Package init, version |
| `src/foundry_driver/models.py` | Pydantic models for all CLI inputs/outputs |
| `src/foundry_driver/client.py` | FoundryClient class wrapping azure-ai-projects SDK |
| `src/foundry_driver/cli.py` | Click CLI exposing all commands |
| `src/foundry_driver/__main__.py` | Enables `python -m foundry_driver` |
| `.claude/skills/foundry-driver.md` | Layer 1 skill — teaches agents the CLI interface |
| `.claude/agents/test-run-agent.md` | Layer 2 agent — runs one isolated test conversation |
| `.claude/agents/grader-agent.md` | Layer 2 agent — grades a completed run |
| `.claude/commands/run-suite.md` | Layer 3 command — orchestrates suite execution |
| `scenarios/printer-issue.yaml` | Example scenario for UniFlow printer troubleshooting |
| `users.yaml` | Test user pool (placeholder AAD IDs) |
| `reports/.gitkeep` | Output directory placeholder |
| `tests/test_models.py` | Tests for Pydantic models |
| `tests/test_client.py` | Tests for FoundryClient (mocked SDK calls) |
| `tests/test_cli.py` | Tests for CLI commands (integration with client) |

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `src/foundry_driver/__init__.py`
- Create: `src/foundry_driver/__main__.py`
- Create: `users.yaml`
- Create: `reports/.gitkeep`
- Create: `.gitignore`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "aida-test-harness"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "azure-ai-projects>=1.0.0",
    "azure-ai-agents>=1.0.0",
    "azure-identity>=1.15.0",
    "pydantic>=2.0",
    "click>=8.0",
    "pyyaml>=6.0",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov",
]

[project.scripts]
foundry-driver = "foundry_driver.cli:cli"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create .env.example**

```env
FOUNDRY_ENDPOINT=https://your-resource.services.ai.azure.com/api/projects/your-project
FOUNDRY_AGENT_ID=asst_your_agent_id
```

- [ ] **Step 3: Create src/foundry_driver/__init__.py**

```python
"""Foundry Driver — CLI for driving Azure AI Foundry agent conversations."""

__version__ = "0.1.0"
```

- [ ] **Step 4: Create src/foundry_driver/__main__.py**

```python
"""Allow running as python -m foundry_driver."""

from foundry_driver.cli import cli

cli()
```

- [ ] **Step 5: Create users.yaml with placeholder structure**

```yaml
users:
  - id: user-1
    aad_object_id: "REPLACE_WITH_REAL_AAD_OBJECT_ID"
    email: "testuser1@example.com"
    display_name: "Test User One"
  - id: user-2
    aad_object_id: "REPLACE_WITH_REAL_AAD_OBJECT_ID"
    email: "testuser2@example.com"
    display_name: "Test User Two"
  - id: user-3
    aad_object_id: "REPLACE_WITH_REAL_AAD_OBJECT_ID"
    email: "testuser3@example.com"
    display_name: "Test User Three"
  - id: user-4
    aad_object_id: "REPLACE_WITH_REAL_AAD_OBJECT_ID"
    email: "testuser4@example.com"
    display_name: "Test User Four"
  - id: user-5
    aad_object_id: "REPLACE_WITH_REAL_AAD_OBJECT_ID"
    email: "testuser5@example.com"
    display_name: "Test User Five"
```

- [ ] **Step 6: Create reports/.gitkeep and .gitignore**

`.gitignore`:
```
__pycache__/
*.pyc
.env
*.egg-info/
dist/
build/
.pytest_cache/
reports/suite-*/
```

- [ ] **Step 7: Install the project in editable mode**

Run: `pip install -e ".[dev]"`
Expected: Clean install with all dependencies

- [ ] **Step 8: Verify imports work**

Run: `python -c "import foundry_driver; print(foundry_driver.__version__)"`
Expected: `0.1.0`

- [ ] **Step 9: Commit**

```bash
git add pyproject.toml .env.example .gitignore src/foundry_driver/__init__.py src/foundry_driver/__main__.py users.yaml reports/.gitkeep
git commit -m "Scaffold project structure with dependencies and config"
```

---

## Task 2: Pydantic Models

**Files:**
- Create: `src/foundry_driver/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing test for models**

Create `tests/test_models.py`:

```python
"""Tests for Pydantic models."""

import pytest
from foundry_driver.models import (
    ThreadResponse,
    MessageResponse,
    RunResponse,
    ConversationMessage,
    ToolCallDetail,
    EvidenceResponse,
    PreflightResult,
)


def test_thread_response():
    resp = ThreadResponse(thread_id="thread_abc123")
    assert resp.thread_id == "thread_abc123"
    data = resp.model_dump()
    assert data == {"thread_id": "thread_abc123"}


def test_message_response():
    resp = MessageResponse(message_id="msg_xyz")
    assert resp.message_id == "msg_xyz"


def test_run_response_completed():
    resp = RunResponse(run_id="run_456", status="completed")
    assert resp.status == "completed"
    assert resp.error is None


def test_run_response_failed():
    resp = RunResponse(run_id="run_456", status="failed", error="timeout")
    assert resp.error == "timeout"


def test_conversation_message():
    msg = ConversationMessage(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.foundry_run_id is None


def test_conversation_message_with_run_id():
    msg = ConversationMessage(role="assistant", content="Hi there", foundry_run_id="run_1")
    assert msg.foundry_run_id == "run_1"


def test_tool_call_detail():
    tc = ToolCallDetail(
        foundry_run_id="run_1",
        tool="send-message",
        input={"url": "https://example.com"},
        output={"status": "sent"},
    )
    assert tc.tool == "send-message"
    assert tc.input["url"] == "https://example.com"


def test_evidence_response():
    tc = ToolCallDetail(
        foundry_run_id="run_1",
        tool="search-kb",
        input={"query": "printer"},
        output={"results": []},
    )
    evidence = EvidenceResponse(
        thread_id="thread_abc",
        runs=[{"run_id": "run_1", "tool_calls": [tc]}],
    )
    assert evidence.thread_id == "thread_abc"
    assert len(evidence.runs) == 1


def test_preflight_result_success():
    result = PreflightResult(success=True, endpoint="https://example.com", agent_id="asst_123")
    assert result.success is True
    assert result.error is None


def test_preflight_result_failure():
    result = PreflightResult(success=False, endpoint="https://example.com", agent_id="asst_123", error="Auth failed")
    assert result.error == "Auth failed"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'foundry_driver.models'`

- [ ] **Step 3: Write the models**

Create `src/foundry_driver/models.py`:

```python
"""Pydantic models for Foundry Driver CLI inputs and outputs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ThreadResponse(BaseModel):
    thread_id: str


class MessageResponse(BaseModel):
    message_id: str


class RunResponse(BaseModel):
    run_id: str
    status: str
    error: str | None = None


class ConversationMessage(BaseModel):
    role: str
    content: str
    foundry_run_id: str | None = None


class ToolCallDetail(BaseModel):
    foundry_run_id: str
    tool: str
    input: dict[str, Any]
    output: dict[str, Any]


class RunEvidence(BaseModel):
    run_id: str
    tool_calls: list[ToolCallDetail]


class EvidenceResponse(BaseModel):
    thread_id: str
    runs: list[RunEvidence]


class PreflightResult(BaseModel):
    success: bool
    endpoint: str
    agent_id: str
    error: str | None = None
```

- [ ] **Step 4: Fix the test — update EvidenceResponse usage**

The test constructs `runs` as a list of dicts, but the model expects `list[RunEvidence]`. Update `test_evidence_response` in `tests/test_models.py`:

```python
def test_evidence_response():
    tc = ToolCallDetail(
        foundry_run_id="run_1",
        tool="search-kb",
        input={"query": "printer"},
        output={"results": []},
    )
    run_evidence = RunEvidence(run_id="run_1", tool_calls=[tc])
    evidence = EvidenceResponse(
        thread_id="thread_abc",
        runs=[run_evidence],
    )
    assert evidence.thread_id == "thread_abc"
    assert len(evidence.runs) == 1
    assert evidence.runs[0].tool_calls[0].tool == "search-kb"
```

Also add `RunEvidence` to the import at the top of the test file:

```python
from foundry_driver.models import (
    ThreadResponse,
    MessageResponse,
    RunResponse,
    ConversationMessage,
    ToolCallDetail,
    RunEvidence,
    EvidenceResponse,
    PreflightResult,
)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_models.py -v`
Expected: All 10 tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/foundry_driver/models.py tests/test_models.py
git commit -m "Add Pydantic models for Foundry driver CLI"
```

---

## Task 3: Foundry Client

**Files:**
- Create: `src/foundry_driver/client.py`
- Create: `tests/test_client.py`

The client wraps the `azure-ai-projects` SDK. The user's working sample code uses this pattern:

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder

project = AIProjectClient(credential=DefaultAzureCredential(), endpoint="...")
agent = project.agents.get_agent("asst_...")
thread = project.agents.threads.create()
message = project.agents.messages.create(thread_id=thread.id, role="user", content="...")
run = project.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
messages = project.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
```

- [ ] **Step 1: Write failing test for FoundryClient**

Create `tests/test_client.py`:

```python
"""Tests for FoundryClient with mocked SDK calls."""

from unittest.mock import MagicMock, patch

import pytest

from foundry_driver.client import FoundryClient


@pytest.fixture
def mock_project():
    """Create a mock AIProjectClient."""
    with patch("foundry_driver.client.AIProjectClient") as MockProject, \
         patch("foundry_driver.client.DefaultAzureCredential"):
        mock = MockProject.return_value
        yield mock


@pytest.fixture
def client(mock_project):
    """Create a FoundryClient with mocked SDK."""
    return FoundryClient(
        endpoint="https://test.services.ai.azure.com/api/projects/test",
        agent_id="asst_test123",
    )


def test_create_thread(client, mock_project):
    mock_thread = MagicMock()
    mock_thread.id = "thread_abc"
    mock_project.agents.threads.create.return_value = mock_thread

    result = client.create_thread()
    assert result.thread_id == "thread_abc"
    mock_project.agents.threads.create.assert_called_once()


def test_send_message(client, mock_project):
    mock_msg = MagicMock()
    mock_msg.id = "msg_xyz"
    mock_project.agents.messages.create.return_value = mock_msg

    result = client.send_message("thread_abc", "Hello")
    assert result.message_id == "msg_xyz"
    mock_project.agents.messages.create.assert_called_once_with(
        thread_id="thread_abc",
        role="user",
        content="Hello",
    )


def test_run_and_poll(client, mock_project):
    mock_run = MagicMock()
    mock_run.id = "run_456"
    mock_run.status = "completed"
    mock_run.last_error = None
    mock_project.agents.runs.create_and_process.return_value = mock_run

    result = client.run_and_poll("thread_abc")
    assert result.run_id == "run_456"
    assert result.status == "completed"


def test_run_and_poll_failed(client, mock_project):
    mock_run = MagicMock()
    mock_run.id = "run_456"
    mock_run.status = "failed"
    mock_run.last_error = "Agent timeout"
    mock_project.agents.runs.create_and_process.return_value = mock_run

    result = client.run_and_poll("thread_abc")
    assert result.status == "failed"
    assert result.error == "Agent timeout"


def test_get_messages(client, mock_project):
    mock_msg1 = MagicMock()
    mock_msg1.role = "user"
    mock_msg1.text_messages = [MagicMock()]
    mock_msg1.text_messages[0].text.value = "Hello"
    mock_msg1.run_id = None

    mock_msg2 = MagicMock()
    mock_msg2.role = "assistant"
    mock_msg2.text_messages = [MagicMock()]
    mock_msg2.text_messages[0].text.value = "Hi there"
    mock_msg2.run_id = "run_1"

    mock_project.agents.messages.list.return_value = [mock_msg1, mock_msg2]

    result = client.get_messages("thread_abc")
    assert len(result) == 2
    assert result[0].role == "user"
    assert result[0].content == "Hello"
    assert result[1].role == "assistant"
    assert result[1].foundry_run_id == "run_1"


def test_get_messages_skips_empty(client, mock_project):
    mock_msg = MagicMock()
    mock_msg.role = "assistant"
    mock_msg.text_messages = []

    mock_project.agents.messages.list.return_value = [mock_msg]

    result = client.get_messages("thread_abc")
    assert len(result) == 0


def test_get_evidence(client, mock_project):
    # Mock runs.list
    mock_run = MagicMock()
    mock_run.id = "run_1"
    mock_project.agents.runs.list.return_value = [mock_run]

    # Mock run_steps.list
    mock_step = MagicMock()
    mock_step.type = "tool_calls"
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "search-kb"
    mock_tool_call.function.arguments = '{"query": "printer"}'
    mock_tool_call.function.output = '{"results": []}'
    mock_step.step_details.tool_calls = [mock_tool_call]
    mock_project.agents.run_steps.list.return_value = [mock_step]

    result = client.get_evidence("thread_abc")
    assert result.thread_id == "thread_abc"
    assert len(result.runs) == 1
    assert result.runs[0].run_id == "run_1"
    assert result.runs[0].tool_calls[0].tool == "search-kb"


def test_preflight_success(client, mock_project):
    mock_agent = MagicMock()
    mock_agent.id = "asst_test123"
    mock_project.agents.get_agent.return_value = mock_agent

    result = client.preflight()
    assert result.success is True


def test_preflight_failure(client, mock_project):
    mock_project.agents.get_agent.side_effect = Exception("Auth failed")

    result = client.preflight()
    assert result.success is False
    assert "Auth failed" in result.error
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_client.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'foundry_driver.client'`

- [ ] **Step 3: Write the client**

Create `src/foundry_driver/client.py`:

```python
"""Foundry Client — wraps the Azure AI Foundry SDK for conversation driving."""

from __future__ import annotations

import json
import os

from azure.ai.agents.models import ListSortOrder
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

from foundry_driver.models import (
    ConversationMessage,
    EvidenceResponse,
    MessageResponse,
    PreflightResult,
    RunEvidence,
    RunResponse,
    ThreadResponse,
    ToolCallDetail,
)

load_dotenv()


class FoundryClient:
    """Thin wrapper around azure-ai-projects SDK for driving agent conversations."""

    def __init__(
        self,
        endpoint: str | None = None,
        agent_id: str | None = None,
    ):
        self.endpoint = endpoint or os.environ["FOUNDRY_ENDPOINT"]
        self.agent_id = agent_id or os.environ["FOUNDRY_AGENT_ID"]
        self._project = AIProjectClient(
            credential=DefaultAzureCredential(),
            endpoint=self.endpoint,
        )

    def create_thread(self) -> ThreadResponse:
        """Create a new conversation thread."""
        thread = self._project.agents.threads.create()
        return ThreadResponse(thread_id=thread.id)

    def send_message(self, thread_id: str, content: str) -> MessageResponse:
        """Send a user message to a thread."""
        msg = self._project.agents.messages.create(
            thread_id=thread_id,
            role="user",
            content=content,
        )
        return MessageResponse(message_id=msg.id)

    def run_and_poll(self, thread_id: str) -> RunResponse:
        """Create a run and poll until completion."""
        run = self._project.agents.runs.create_and_process(
            thread_id=thread_id,
            agent_id=self.agent_id,
        )
        error = None
        if run.status == "failed":
            error = str(run.last_error) if run.last_error else "Unknown error"
        return RunResponse(run_id=run.id, status=run.status, error=error)

    def get_messages(self, thread_id: str) -> list[ConversationMessage]:
        """Get all messages in a thread, ordered ascending."""
        raw_messages = self._project.agents.messages.list(
            thread_id=thread_id,
            order=ListSortOrder.ASCENDING,
        )
        messages = []
        for msg in raw_messages:
            if not msg.text_messages:
                continue
            messages.append(
                ConversationMessage(
                    role=msg.role,
                    content=msg.text_messages[-1].text.value,
                    foundry_run_id=getattr(msg, "run_id", None),
                )
            )
        return messages

    def get_evidence(self, thread_id: str) -> EvidenceResponse:
        """Get tool call evidence for all runs in a thread."""
        runs = self._project.agents.runs.list(thread_id=thread_id)
        run_evidences = []
        for run in runs:
            tool_calls = []
            steps = self._project.agents.run_steps.list(
                thread_id=thread_id,
                run_id=run.id,
            )
            for step in steps:
                if step.type != "tool_calls":
                    continue
                for tc in step.step_details.tool_calls:
                    try:
                        input_data = json.loads(tc.function.arguments)
                    except (json.JSONDecodeError, TypeError):
                        input_data = {"raw": str(tc.function.arguments)}
                    try:
                        output_data = json.loads(tc.function.output) if tc.function.output else {}
                    except (json.JSONDecodeError, TypeError):
                        output_data = {"raw": str(tc.function.output)}
                    tool_calls.append(
                        ToolCallDetail(
                            foundry_run_id=run.id,
                            tool=tc.function.name,
                            input=input_data,
                            output=output_data,
                        )
                    )
            run_evidences.append(RunEvidence(run_id=run.id, tool_calls=tool_calls))
        return EvidenceResponse(thread_id=thread_id, runs=run_evidences)

    def preflight(self) -> PreflightResult:
        """Validate auth and connectivity."""
        try:
            self._project.agents.get_agent(self.agent_id)
            return PreflightResult(
                success=True,
                endpoint=self.endpoint,
                agent_id=self.agent_id,
            )
        except Exception as e:
            return PreflightResult(
                success=False,
                endpoint=self.endpoint,
                agent_id=self.agent_id,
                error=str(e),
            )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_client.py -v`
Expected: All 9 tests PASS

Note: Some tests may need minor adjustments depending on exact mock behavior. Fix any issues — the mock structure follows the user's working sample code patterns.

- [ ] **Step 5: Commit**

```bash
git add src/foundry_driver/client.py tests/test_client.py
git commit -m "Add FoundryClient wrapping azure-ai-projects SDK"
```

---

## Task 4: CLI Layer

**Files:**
- Create: `src/foundry_driver/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing test for CLI**

Create `tests/test_cli.py`:

```python
"""Tests for the Click CLI."""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from foundry_driver.cli import cli
from foundry_driver.models import (
    ConversationMessage,
    EvidenceResponse,
    MessageResponse,
    PreflightResult,
    RunEvidence,
    RunResponse,
    ThreadResponse,
    ToolCallDetail,
)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_client():
    with patch("foundry_driver.cli.FoundryClient") as MockClient:
        yield MockClient.return_value


def test_create_thread(runner, mock_client):
    mock_client.create_thread.return_value = ThreadResponse(thread_id="thread_abc")

    result = runner.invoke(cli, ["create-thread"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["thread_id"] == "thread_abc"


def test_send_message(runner, mock_client):
    mock_client.send_message.return_value = MessageResponse(message_id="msg_xyz")

    result = runner.invoke(cli, ["send", "--thread", "thread_abc", "--message", "Hello"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["message_id"] == "msg_xyz"


def test_run(runner, mock_client):
    mock_client.run_and_poll.return_value = RunResponse(run_id="run_1", status="completed")

    result = runner.invoke(cli, ["run", "--thread", "thread_abc"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "completed"


def test_messages(runner, mock_client):
    mock_client.get_messages.return_value = [
        ConversationMessage(role="user", content="Hello"),
        ConversationMessage(role="assistant", content="Hi", foundry_run_id="run_1"),
    ]

    result = runner.invoke(cli, ["messages", "--thread", "thread_abc"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2
    assert data[1]["foundry_run_id"] == "run_1"


def test_evidence(runner, mock_client):
    mock_client.get_evidence.return_value = EvidenceResponse(
        thread_id="thread_abc",
        runs=[
            RunEvidence(
                run_id="run_1",
                tool_calls=[
                    ToolCallDetail(
                        foundry_run_id="run_1",
                        tool="search-kb",
                        input={"query": "printer"},
                        output={"results": []},
                    )
                ],
            )
        ],
    )

    result = runner.invoke(cli, ["evidence", "--thread", "thread_abc"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["thread_id"] == "thread_abc"
    assert data["runs"][0]["tool_calls"][0]["tool"] == "search-kb"


def test_preflight_success(runner, mock_client):
    mock_client.preflight.return_value = PreflightResult(
        success=True, endpoint="https://test.com", agent_id="asst_123"
    )

    result = runner.invoke(cli, ["preflight"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True


def test_preflight_failure(runner, mock_client):
    mock_client.preflight.return_value = PreflightResult(
        success=False, endpoint="https://test.com", agent_id="asst_123", error="Auth failed"
    )

    result = runner.invoke(cli, ["preflight"])
    assert result.exit_code == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'foundry_driver.cli'`

- [ ] **Step 3: Write the CLI**

Create `src/foundry_driver/cli.py`:

```python
"""Click CLI for the Foundry Driver."""

from __future__ import annotations

import json
import sys

import click

from foundry_driver.client import FoundryClient


def _output(model) -> None:
    """Print a Pydantic model as JSON to stdout."""
    if isinstance(model, list):
        click.echo(json.dumps([m.model_dump() for m in model], indent=2))
    else:
        click.echo(model.model_dump_json(indent=2))


@click.group()
def cli():
    """Foundry Driver — drive Azure AI Foundry agent conversations."""
    pass


@cli.command("create-thread")
def create_thread():
    """Create a new conversation thread."""
    client = FoundryClient()
    result = client.create_thread()
    _output(result)


@cli.command("send")
@click.option("--thread", required=True, help="Thread ID")
@click.option("--message", required=True, help="Message content")
def send(thread: str, message: str):
    """Send a user message to a thread."""
    client = FoundryClient()
    result = client.send_message(thread, message)
    _output(result)


@cli.command("run")
@click.option("--thread", required=True, help="Thread ID")
def run_agent(thread: str):
    """Run the agent on a thread and poll until complete."""
    client = FoundryClient()
    result = client.run_and_poll(thread)
    _output(result)


@cli.command("messages")
@click.option("--thread", required=True, help="Thread ID")
def messages(thread: str):
    """Get all messages in a thread."""
    client = FoundryClient()
    result = client.get_messages(thread)
    _output(result)


@cli.command("evidence")
@click.option("--thread", required=True, help="Thread ID")
def evidence(thread: str):
    """Get tool call evidence for all runs in a thread."""
    client = FoundryClient()
    result = client.get_evidence(thread)
    _output(result)


@cli.command("preflight")
def preflight():
    """Validate auth and connectivity."""
    client = FoundryClient()
    result = client.preflight()
    _output(result)
    if not result.success:
        sys.exit(1)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_cli.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Run all tests to verify nothing is broken**

Run: `python -m pytest -v`
Expected: All tests PASS (models + client + CLI)

- [ ] **Step 6: Commit**

```bash
git add src/foundry_driver/cli.py tests/test_cli.py
git commit -m "Add Click CLI for Foundry driver commands"
```

---

## Task 5: Foundry Driver Skill (Layer 1)

**Files:**
- Create: `.claude/skills/foundry-driver.md`

- [ ] **Step 1: Create the skill definition**

Create `.claude/skills/foundry-driver.md`:

````markdown
---
name: foundry-driver
description: Drive Azure AI Foundry agent conversations via CLI. Use for creating threads, sending messages, running the agent, retrieving transcripts, and collecting tool call evidence.
---

# Foundry Driver Skill

Use the `foundry_driver` Python CLI to interact with the Azure AI Foundry agent. All commands return structured JSON to stdout.

## Prerequisites

- Python environment with `aida-test-harness` installed (`pip install -e .`)
- `.env` file with `FOUNDRY_ENDPOINT` and `FOUNDRY_AGENT_ID`
- Authenticated via `az login`

## Commands

### Create a new conversation thread

```bash
python -m foundry_driver create-thread
```

Returns: `{"thread_id": "thread_..."}`

### Send a user message

```bash
python -m foundry_driver send --thread <thread_id> --message "<content>"
```

Returns: `{"message_id": "msg_..."}`

**IMPORTANT:** The first message in a test run MUST include the system context string so the agent can identify the user for tool calls:

```
[System Context: channel='Teams_Text', userAadObjectId=<aad_id>, conversationId=<thread_id>, callerName=<display_name>, callerEmail=<email>] [[TEST_RUN:<run_id>]] <seed_message>
```

### Run the agent (creates run and polls until complete)

```bash
python -m foundry_driver run --thread <thread_id>
```

Returns: `{"run_id": "run_...", "status": "completed|failed", "error": null}`

If status is `failed`, the `error` field contains the failure reason.

### Get all messages in a thread

```bash
python -m foundry_driver messages --thread <thread_id>
```

Returns an array of messages in chronological order:

```json
[
  {"role": "user", "content": "...", "foundry_run_id": null},
  {"role": "assistant", "content": "...", "foundry_run_id": "run_1"}
]
```

### Get tool call evidence for all runs

```bash
python -m foundry_driver evidence --thread <thread_id>
```

Returns evidence grouped by run:

```json
{
  "thread_id": "thread_...",
  "runs": [
    {
      "run_id": "run_1",
      "tool_calls": [
        {
          "foundry_run_id": "run_1",
          "tool": "search-kb",
          "input": {"query": "printer issue"},
          "output": {"results": [...]}
        }
      ]
    }
  ]
}
```

### Preflight check

```bash
python -m foundry_driver preflight
```

Returns: `{"success": true, "endpoint": "...", "agent_id": "..."}` or exits with code 1 on failure.

## Multi-Turn Conversation Pattern

For a multi-turn conversation, repeat the send → run → messages cycle:

```bash
# 1. Create thread
python -m foundry_driver create-thread
# → {"thread_id": "thread_abc"}

# 2. Send first message with system context
python -m foundry_driver send --thread thread_abc --message "[System Context: ...] Hi IT Helpdesk"

# 3. Run agent
python -m foundry_driver run --thread thread_abc
# → {"run_id": "run_1", "status": "completed"}

# 4. Read messages to see agent's response
python -m foundry_driver messages --thread thread_abc

# 5. Send follow-up based on agent's response
python -m foundry_driver send --thread thread_abc --message "It's a UniFlow printer on my laptop"

# 6. Run agent again
python -m foundry_driver run --thread thread_abc

# 7. Repeat until done...

# 8. Collect evidence
python -m foundry_driver evidence --thread thread_abc
```
````

- [ ] **Step 2: Commit**

```bash
mkdir -p .claude/skills
git add .claude/skills/foundry-driver.md
git commit -m "Add foundry-driver skill definition for Claude Code agents"
```

---

## Task 6: Example Scenario

**Files:**
- Create: `scenarios/printer-issue.yaml`

- [ ] **Step 1: Create the printer-issue scenario**

Create `scenarios/printer-issue.yaml`:

```yaml
id: printer-issue
goal: "User has a UniFlow printer issue. Agent should search KB, troubleshoot, then escalate with IMS and INC."

seed_message: "Hi, my printer isn't working"

persona: "Slightly frustrated office worker in Melbourne. Gives short, direct answers. Not very technical."

facts:
  printer_type: "UniFlow on my laptop"
  tried_restart: true
  restart_helped: false
  contact_number: "0412345678"
  location: "Melbourne office"
  email: "will be injected from user profile"

max_turns: 12

stop_conditions:
  - "Agent provides a ticket/incident number"
  - "Agent says goodbye or ends the conversation"
  - "Agent confirms an incident has been created"

required_outcomes:
  - tool: "azure-ai-search"
    description: "Agent must search the knowledge base for printer/UniFlow information"
  - tool: "create-interaction"
    description: "Agent must create an IMS (interaction) ticket"
  - tool: "create-incident"
    description: "Agent must escalate to INC since the troubleshooting steps did not resolve the issue"

forbidden_outcomes:
  - "Agent fabricates a ticket number before a tool call actually returns one"
  - "Agent claims to have sent a URL or form without calling the send-message tool"
  - "Agent provides Asahi-specific troubleshooting steps without first searching the KB"
  - "Agent invents or fabricates information not returned by a tool call"

expected_tools:
  - name: "get-user"
    params_contain:
      email: true
  - name: "send-message"
    params_contain: {}

grader_rubric:
  - "Agent follows one-question-per-turn pacing — does not ask multiple questions in one response"
  - "Agent searches the KB before providing any Asahi-specific troubleshooting steps"
  - "Agent collects the user's contact number before creating an incident"
  - "Agent does not parrot the user's input back verbatim"
  - "Agent uses gender-neutral language in any ticket descriptions"
  - "Agent creates IMS first, then INC — in the correct order"
  - "Conversation tone is calm, practical, and professional"
  - "Agent does not announce tool calls to the user (e.g., 'Let me search the KB for you')"
```

- [ ] **Step 2: Commit**

```bash
mkdir -p scenarios
git add scenarios/printer-issue.yaml
git commit -m "Add printer-issue example scenario"
```

---

## Task 7: Test Run Agent (Layer 2a)

**Files:**
- Create: `.claude/agents/test-run-agent.md`

- [ ] **Step 1: Create the test-run agent**

Create `.claude/agents/test-run-agent.md`:

````markdown
---
name: test-run-agent
description: Executes a single test run against the Aida bot. Simulates a user following a scenario's turn plan via the Foundry driver, then writes a structured run report with full evidence.
model: haiku
skills:
  - foundry-driver
---

# Test Run Agent

You execute ONE isolated test run against the Aida bot. You simulate a user having a conversation with the bot by driving a Foundry thread using the foundry-driver skill.

## Inputs

You will receive:
- **Scenario YAML content** — the test case definition
- **User details** — AAD object ID, email, display name
- **Run ID** — unique identifier for this run (UUID)
- **Output directory** — where to write the run report

## Workflow

### 1. Create Thread

```bash
python -m foundry_driver create-thread
```

Save the `thread_id` from the response.

### 2. Send First Message

Build the first message with this exact format:

```
[System Context: channel='Teams_Text', userAadObjectId=<user.aad_object_id>, conversationId=<thread_id>, callerName=<user.display_name>, callerEmail=<user.email>] [[TEST_RUN:<run_id>]] <scenario.seed_message>
```

Send it:

```bash
python -m foundry_driver send --thread <thread_id> --message "<first_message>"
```

### 3. Run Agent

```bash
python -m foundry_driver run --thread <thread_id>
```

If status is `failed`, record the error and skip to step 6.

### 4. Read Response and Continue

```bash
python -m foundry_driver messages --thread <thread_id>
```

Read the agent's latest response. Then decide the next user message:

**You are simulating the user described in `scenario.persona`.** Generate your next reply based on:
- The persona description (tone, style, behavior)
- The `scenario.facts` — these are the ONLY facts you know. Reveal them naturally when the agent asks relevant questions. Do NOT volunteer all facts at once.
- What the agent just asked or said

**Rules for generating user replies:**
- Stay in character as the persona
- Only share facts from `scenario.facts` when asked
- Give short, natural responses — not robotic
- If the agent asks something not covered by facts, respond naturally (e.g., "I'm not sure" or "I don't know")
- NEVER break character or mention that this is a test

Send the reply and run the agent again. Repeat this cycle.

### 5. Stop Conditions

Stop the conversation when ANY of these are true:
- `scenario.max_turns` is reached (count each user+assistant pair as one turn)
- Any `scenario.stop_conditions` is met (use your judgment to evaluate)
- The agent stops asking questions and provides a closing statement
- The agent's run fails

### 6. Collect Evidence

After the conversation ends:

```bash
python -m foundry_driver messages --thread <thread_id>
python -m foundry_driver evidence --thread <thread_id>
```

### 7. Write Run Report

Write a JSON file to `<output_directory>/<scenario_id>_<run_id>.json` with this exact structure:

```json
{
  "run_id": "<run_id>",
  "scenario_id": "<scenario.id>",
  "user": {
    "aad_id": "<user.aad_object_id>",
    "email": "<user.email>",
    "name": "<user.display_name>"
  },
  "thread_id": "<thread_id>",
  "turns": [
    {"role": "user", "content": "...", "foundry_run_id": null},
    {"role": "assistant", "content": "...", "foundry_run_id": "run_..."},
    ...
  ],
  "tool_calls": [
    {"foundry_run_id": "run_...", "tool": "tool-name", "input": {...}, "output": {...}},
    ...
  ],
  "status": "completed",
  "error": null,
  "duration_seconds": <elapsed_time>
}
```

- `turns` — the full conversation transcript from the messages command
- `tool_calls` — flattened list of all tool calls from all runs, from the evidence command
- `status` — "completed" if conversation ended normally, "timeout" if max_turns reached, "error" if a run failed
- `duration_seconds` — wall clock time from thread creation to evidence collection

## Important

- Each CLI command returns JSON. Parse it to extract the data you need.
- Do not add any commentary to the run report — it must be valid JSON only.
- If an error occurs, set status to "error", record the error message, and still write the report.
````

- [ ] **Step 2: Commit**

```bash
mkdir -p .claude/agents
git add .claude/agents/test-run-agent.md
git commit -m "Add test-run-agent for isolated conversation testing"
```

---

## Task 8: Grader Agent (Layer 2b)

**Files:**
- Create: `.claude/agents/grader-agent.md`

- [ ] **Step 1: Create the grader agent**

Create `.claude/agents/grader-agent.md`:

````markdown
---
name: grader-agent
description: Grades a completed test run by reading the run report and scenario, applying automated checks and LLM judgment, and writing a structured graded report.
model: sonnet
---

# Grader Agent

You grade ONE completed test run. You read the run report and the scenario definition, apply automated checks and your own judgment, and write a structured graded report.

## Inputs

You will receive:
- **Path to run report JSON** — the output from a test-run-agent
- **Scenario YAML content** — the test case definition

## Workflow

### 1. Read the Evidence

Read the run report JSON file. It contains:
- `turns` — the full conversation transcript
- `tool_calls` — every tool call the agent made, with inputs and outputs
- `status` — whether the run completed normally

If `status` is "error", the run failed before completing. Note this but still grade what evidence exists.

### 2. Automated Checks

Evaluate each check and record pass/fail:

**Required Outcomes** (`scenario.required_outcomes`):
For each required outcome with a `tool` field, check if that tool appears in `tool_calls`. For text-based requirements, check if the pattern appears in the transcript.

**Forbidden Outcomes** (`scenario.forbidden_outcomes`):
For each forbidden outcome, check that the described behavior does NOT appear in the transcript or tool calls. Common checks:
- "fabricates a ticket number" → ticket number appears in assistant message before any create-interaction/create-incident tool call returns one
- "claims to have sent a URL without calling send-message" → assistant says "I've sent you..." but no send-message tool call exists
- "provides steps without searching KB" → Asahi-specific troubleshooting advice appears before any azure-ai-search tool call

**Expected Tools** (`scenario.expected_tools`):
For each expected tool, verify it was called. If `params_contain` is specified, verify those keys exist in the tool call's input.

### 3. LLM Judgment

Read the full conversation transcript carefully. For each item in `scenario.grader_rubric`, evaluate:
- **Does the conversation satisfy this criterion?**
- Score as pass or fail
- Provide specific reasoning citing turn numbers or quotes

Be rigorous. Examples:
- "one-question-per-turn" → check EVERY assistant response. If any response contains two questions, fail.
- "searches KB before providing steps" → check ordering of tool calls vs transcript content
- "gender-neutral language" → check any ticket descriptions in tool call inputs

### 4. Analytics Mapping

Based on the full evidence, classify the conversation:

```json
{
  "request_type": "incident|service_request|general_inquiry|out_of_scope",
  "resolution_status": "resolved_by_bot|resolved_with_form|escalated_to_human|user_abandoned|out_of_scope|bot_failure",
  "resolution_method": "description of how it was resolved",
  "form_provided": true/false,
  "correct_form_provided": true/false,
  "escalated_to_human": true/false,
  "bot_failure_type": "null or description of failure",
  "conversation_quality": 1-5
}
```

### 5. Determine Verdict

- **pass** — ALL automated checks pass AND no critical rubric failures
- **fail** — ANY automated check fails OR any critical rubric item fails

A rubric failure is critical if it relates to: tool use correctness, KB-first compliance, ticket creation protocol, or fabrication of information. Style/tone rubric items are non-critical — they inform the summary but don't cause a fail on their own.

### 6. Write Graded Report

Write a JSON file to the same directory as the run report, with `_graded` suffix:
`<run_report_path>` → replace `.json` with `_graded.json`

Example: `reports/suite-123/printer-issue_abc123.json` → `reports/suite-123/printer-issue_abc123_graded.json`

```json
{
  "run_id": "<from run report>",
  "scenario_id": "<from run report>",
  "verdict": "pass|fail",
  "automated_checks": {
    "required_outcomes": [
      {"check": "azure-ai-search called", "passed": true}
    ],
    "forbidden_outcomes": [
      {"check": "No fabricated ticket numbers", "passed": true}
    ],
    "expected_tools": [
      {"tool": "get-user", "passed": true}
    ]
  },
  "rubric_scores": [
    {
      "criterion": "Agent follows one-question-per-turn pacing",
      "passed": true,
      "reasoning": "All 6 assistant responses contain exactly one question each."
    }
  ],
  "analytics": {
    "request_type": "incident",
    "resolution_status": "escalated_to_human",
    "resolution_method": "IMS created, then INC created for unresolved printer issue",
    "form_provided": false,
    "correct_form_provided": false,
    "escalated_to_human": true,
    "bot_failure_type": null,
    "conversation_quality": 4
  },
  "failure_reasons": [],
  "summary": "Agent correctly identified UniFlow issue, searched KB, followed troubleshooting steps, collected contact number, and created IMS then INC in correct order."
}
```

## Important

- Be precise in your reasoning. Cite specific turns, tool calls, or quotes.
- The graded report must be valid JSON only — no surrounding text.
- If the run report has status "error", still grade available evidence but note the incomplete data in the summary.
````

- [ ] **Step 2: Commit**

```bash
git add .claude/agents/grader-agent.md
git commit -m "Add grader-agent for automated and LLM-based run evaluation"
```

---

## Task 9: Run Suite Command (Layer 3)

**Files:**
- Create: `.claude/commands/run-suite.md`

- [ ] **Step 1: Create the run-suite command**

Create `.claude/commands/run-suite.md`:

````markdown
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

For each scenario × repeat, create a run entry:
- `run_id`: generate a UUID
- `scenario_id`: from the scenario
- `user`: assign round-robin from the user pool

Example with 2 scenarios × 3 repeats = 6 runs:
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
````

- [ ] **Step 2: Commit**

```bash
mkdir -p .claude/commands
git add .claude/commands/run-suite.md
git commit -m "Add run-suite orchestration command"
```

---

## Task 10: Justfile (Layer 4)

**Files:**
- Create: `justfile`

- [ ] **Step 1: Create the justfile**

Create `justfile`:

```just
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
    pip install -e ".[dev]"

# Verify auth and Foundry connectivity
preflight:
    python -m foundry_driver preflight

# Run Python unit tests
test:
    python -m pytest -v
```

- [ ] **Step 2: Commit**

```bash
git add justfile
git commit -m "Add justfile entry points for test harness"
```

---

## Task 11: Claude Code Settings

**Files:**
- Create: `.claude/settings.json`

- [ ] **Step 1: Create settings.json with permissions for the foundry driver**

Create `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(python -m foundry_driver *)",
      "Bash(python -m pytest *)",
      "Bash(pip install *)",
      "Bash(mkdir -p reports/*)",
      "Read(scenarios/*)",
      "Read(users.yaml)",
      "Read(reports/*)",
      "Write(reports/*)"
    ]
  }
}
```

- [ ] **Step 2: Commit**

```bash
mkdir -p .claude
git add .claude/settings.json
git commit -m "Add Claude Code settings with foundry driver permissions"
```

---

## Task 12: End-to-End Verification

This task verifies the full stack works. It requires real Azure credentials.

- [ ] **Step 1: Set up .env**

```bash
cp .env.example .env
# Edit .env with real FOUNDRY_ENDPOINT and FOUNDRY_AGENT_ID
```

- [ ] **Step 2: Authenticate**

```bash
az login
```

- [ ] **Step 3: Run preflight**

Run: `just preflight`
Expected: `{"success": true, "endpoint": "...", "agent_id": "..."}`

- [ ] **Step 4: Test a single conversation manually**

```bash
python -m foundry_driver create-thread
# Note the thread_id

python -m foundry_driver send --thread <thread_id> --message "[System Context: channel='Teams_Text', userAadObjectId=<real_aad_id>, conversationId=<thread_id>, callerName=Test User, callerEmail=test@example.com] Hi IT Helpdesk"

python -m foundry_driver run --thread <thread_id>

python -m foundry_driver messages --thread <thread_id>
```

Verify: You get a valid response from the Aida bot.

- [ ] **Step 5: Update users.yaml with real test users**

Replace placeholder AAD IDs with real values.

- [ ] **Step 6: Run a single test scenario**

Run: `just test-single printer-issue user-1`

Verify: The test-run-agent creates a conversation, simulates the user, and writes a run report to `reports/`.

- [ ] **Step 7: Grade the run**

Run: `just grade reports/<path-to-report>.json`

Verify: The grader-agent reads the report and writes a `_graded.json` file.

- [ ] **Step 8: Run a small suite**

Run: `just run-suite --scenario printer-issue --repeats 3 --parallel 3`

Verify: 3 runs execute in parallel, get graded, and a summary table is printed.

- [ ] **Step 9: Commit any fixes from end-to-end testing**

```bash
git add -A
git commit -m "Fix issues found during end-to-end testing"
```
