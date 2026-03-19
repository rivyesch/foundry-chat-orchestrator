"""Tests for the Click CLI."""

import json
from unittest.mock import patch

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


def _runner():
    return CliRunner()


def _mock_client():
    return patch("foundry_driver.cli.FoundryClient")


def test_create_thread():
    with _mock_client() as MockClient:
        MockClient.return_value.create_thread.return_value = ThreadResponse(thread_id="thread_abc")
        result = _runner().invoke(cli, ["create-thread"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["thread_id"] == "thread_abc"


def test_send_message():
    with _mock_client() as MockClient:
        MockClient.return_value.send_message.return_value = MessageResponse(message_id="msg_xyz")
        result = _runner().invoke(cli, ["send", "--thread", "thread_abc", "--message", "Hello"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["message_id"] == "msg_xyz"


def test_run():
    with _mock_client() as MockClient:
        MockClient.return_value.run_and_poll.return_value = RunResponse(run_id="run_1", status="completed")
        result = _runner().invoke(cli, ["run", "--thread", "thread_abc"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "completed"


def test_messages():
    with _mock_client() as MockClient:
        MockClient.return_value.get_messages.return_value = [
            ConversationMessage(role="user", content="Hello"),
            ConversationMessage(role="assistant", content="Hi", foundry_run_id="run_1"),
        ]
        result = _runner().invoke(cli, ["messages", "--thread", "thread_abc"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2
    assert data[1]["foundry_run_id"] == "run_1"


def test_evidence():
    with _mock_client() as MockClient:
        MockClient.return_value.get_evidence.return_value = EvidenceResponse(
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
        result = _runner().invoke(cli, ["evidence", "--thread", "thread_abc"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["thread_id"] == "thread_abc"
    assert data["runs"][0]["tool_calls"][0]["tool"] == "search-kb"


def test_preflight_success():
    with _mock_client() as MockClient:
        MockClient.return_value.preflight.return_value = PreflightResult(
            success=True, endpoint="https://test.com", agent_id="asst_123"
        )
        result = _runner().invoke(cli, ["preflight"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True


def test_preflight_failure():
    with _mock_client() as MockClient:
        MockClient.return_value.preflight.return_value = PreflightResult(
            success=False, endpoint="https://test.com", agent_id="asst_123", error="Auth failed"
        )
        result = _runner().invoke(cli, ["preflight"])
    assert result.exit_code == 1
