"""CLI interface for testing the AI Chat Platform agent.

Usage:
    python -m src.cli "Your prompt here"
"""

import asyncio
import sys

from src.agent.client import AgentRunner


async def run_agent(prompt: str) -> None:
    """Run the agent with a prompt and print output."""
    runner = AgentRunner()

    async for event in runner.run(prompt):
        if event.type == "text" and event.text:
            print(event.text, end="", flush=True)
        elif event.type == "tool_start":
            print(f"\n[Tool: {event.tool_name}]", flush=True)
        elif event.type == "done":
            print()
            if event.cost is not None:
                print(f"\n[Done - Cost: ${event.cost:.4f}]")
            else:
                print("\n[Done]")


def main() -> None:
    """Run the CLI agent with the provided prompt."""
    if len(sys.argv) < 2:
        print("Usage: python -m src.cli 'Your prompt here'")
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])
    asyncio.run(run_agent(prompt))


if __name__ == "__main__":
    main()
