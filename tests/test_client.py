"""Tests for FoundryClient with mocked SDK calls."""

from unittest.mock import MagicMock, patch

import pytest

from foundry_driver.client import FoundryClient


@pytest.fixture
def mock_agents_client():
    """Create a mock AgentsClient."""
    with patch("foundry_driver.client.AgentsClient") as MockClient, \
         patch("foundry_driver.client.DefaultAzureCredential"):
        mock = MockClient.return_value
        yield mock


@pytest.fixture
def client(mock_agents_client):
    """Create a FoundryClient with mocked SDK."""
    return FoundryClient(
        endpoint="https://test.services.ai.azure.com/api/projects/test",
        agent_id="asst_test123",
    )


def test_create_thread(client, mock_agents_client):
    mock_thread = MagicMock()
    mock_thread.id = "thread_abc"
    mock_agents_client.threads.create.return_value = mock_thread

    result = client.create_thread()
    assert result.thread_id == "thread_abc"
    mock_agents_client.threads.create.assert_called_once()


def test_send_message(client, mock_agents_client):
    mock_msg = MagicMock()
    mock_msg.id = "msg_xyz"
    mock_agents_client.messages.create.return_value = mock_msg

    result = client.send_message("thread_abc", "Hello")
    assert result.message_id == "msg_xyz"
    mock_agents_client.messages.create.assert_called_once_with(
        thread_id="thread_abc",
        role="user",
        content="Hello",
    )


def test_run_and_poll(client, mock_agents_client):
    mock_run = MagicMock()
    mock_run.id = "run_456"
    mock_run.status = "completed"
    mock_run.last_error = None
    mock_agents_client.runs.create_and_process.return_value = mock_run

    result = client.run_and_poll("thread_abc")
    assert result.run_id == "run_456"
    assert result.status == "completed"


def test_run_and_poll_failed(client, mock_agents_client):
    mock_run = MagicMock()
    mock_run.id = "run_456"
    mock_run.status = "failed"
    mock_run.last_error = "Agent timeout"
    mock_agents_client.runs.create_and_process.return_value = mock_run

    result = client.run_and_poll("thread_abc")
    assert result.status == "failed"
    assert result.error == "Agent timeout"


def test_get_messages(client, mock_agents_client):
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

    mock_agents_client.messages.list.return_value = [mock_msg1, mock_msg2]

    result = client.get_messages("thread_abc")
    assert len(result) == 2
    assert result[0].role == "user"
    assert result[0].content == "Hello"
    assert result[1].role == "assistant"
    assert result[1].foundry_run_id == "run_1"


def test_get_messages_skips_empty(client, mock_agents_client):
    mock_msg = MagicMock()
    mock_msg.role = "assistant"
    mock_msg.text_messages = []

    mock_agents_client.messages.list.return_value = [mock_msg]

    result = client.get_messages("thread_abc")
    assert len(result) == 0


def test_get_evidence(client, mock_agents_client):
    mock_run = MagicMock()
    mock_run.id = "run_1"
    mock_agents_client.runs.list.return_value = [mock_run]

    mock_step = MagicMock()
    mock_step.type = "tool_calls"
    mock_tool_call = MagicMock()
    mock_tool_call.as_dict.return_value = {
        "type": "openapi",
        "function": {
            "name": "search-kb",
            "arguments": '{"query": "printer"}',
            "output": '{"results": []}',
        },
    }
    mock_step.step_details.tool_calls = [mock_tool_call]
    mock_agents_client.run_steps.list.return_value = [mock_step]

    result = client.get_evidence("thread_abc")
    assert result.thread_id == "thread_abc"
    assert len(result.runs) == 1
    assert result.runs[0].run_id == "run_1"
    assert result.runs[0].tool_calls[0].tool == "search-kb"


def test_preflight_success(client, mock_agents_client):
    mock_agent = MagicMock()
    mock_agent.id = "asst_test123"
    mock_agents_client.get_agent.return_value = mock_agent

    result = client.preflight()
    assert result.success is True


def test_preflight_failure(client, mock_agents_client):
    mock_agents_client.get_agent.side_effect = Exception("Auth failed")

    result = client.preflight()
    assert result.success is False
    assert "Auth failed" in result.error
