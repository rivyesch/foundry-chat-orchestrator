"""Tests for Pydantic models."""

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
    run_evidence = RunEvidence(run_id="run_1", tool_calls=[tc])
    evidence = EvidenceResponse(
        thread_id="thread_abc",
        runs=[run_evidence],
    )
    assert evidence.thread_id == "thread_abc"
    assert len(evidence.runs) == 1
    assert evidence.runs[0].tool_calls[0].tool == "search-kb"


def test_preflight_result_success():
    result = PreflightResult(success=True, endpoint="https://example.com", agent_id="asst_123")
    assert result.success is True
    assert result.error is None


def test_preflight_result_failure():
    result = PreflightResult(
        success=False, endpoint="https://example.com", agent_id="asst_123", error="Auth failed"
    )
    assert result.error == "Auth failed"
