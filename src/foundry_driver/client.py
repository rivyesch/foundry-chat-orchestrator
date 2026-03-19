"""Foundry Client — wraps the Azure AI Foundry SDK for conversation driving."""

from __future__ import annotations

import json
import os

from azure.ai.agents import AgentsClient
from azure.ai.agents.models import ListSortOrder
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
    """Thin wrapper around azure-ai-agents SDK for driving agent conversations."""

    def __init__(
        self,
        endpoint: str | None = None,
        agent_id: str | None = None,
    ):
        self.endpoint = endpoint or os.environ["FOUNDRY_ENDPOINT"]
        self.agent_id = agent_id or os.environ["FOUNDRY_AGENT_ID"]
        self._client = AgentsClient(
            endpoint=self.endpoint,
            credential=DefaultAzureCredential(),
        )

    def create_thread(self) -> ThreadResponse:
        """Create a new conversation thread."""
        thread = self._client.threads.create()
        return ThreadResponse(thread_id=thread.id)

    def send_message(self, thread_id: str, content: str) -> MessageResponse:
        """Send a user message to a thread."""
        msg = self._client.messages.create(
            thread_id=thread_id,
            role="user",
            content=content,
        )
        return MessageResponse(message_id=msg.id)

    def run_and_poll(self, thread_id: str) -> RunResponse:
        """Create a run and poll until completion."""
        run = self._client.runs.create_and_process(
            thread_id=thread_id,
            agent_id=self.agent_id,
        )
        error = None
        if run.status == "failed":
            error = str(run.last_error) if run.last_error else "Unknown error"
        return RunResponse(run_id=run.id, status=run.status, error=error)

    def get_messages(self, thread_id: str) -> list[ConversationMessage]:
        """Get all messages in a thread, ordered ascending."""
        raw_messages = self._client.messages.list(
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
        runs = self._client.runs.list(thread_id=thread_id)
        run_evidences = []
        for run in runs:
            tool_calls = []
            steps = self._client.run_steps.list(
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
            self._client.get_agent(self.agent_id)
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
