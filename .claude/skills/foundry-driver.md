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

For a multi-turn conversation, repeat the send -> run -> messages cycle:

```bash
# 1. Create thread
python -m foundry_driver create-thread
# -> {"thread_id": "thread_abc"}

# 2. Send first message with system context
python -m foundry_driver send --thread thread_abc --message "[System Context: ...] Hi IT Helpdesk"

# 3. Run agent
python -m foundry_driver run --thread thread_abc
# -> {"run_id": "run_1", "status": "completed"}

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
