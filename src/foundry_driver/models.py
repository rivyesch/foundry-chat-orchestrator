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
