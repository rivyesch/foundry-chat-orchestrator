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
