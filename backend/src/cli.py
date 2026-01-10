"""CLI interface for testing the AI Chat Platform agent.

Usage:
    python -m src.cli "Your prompt here"
"""

import sys


def main() -> None:
    """Run the CLI agent with the provided prompt."""
    if len(sys.argv) < 2:
        print("Usage: python -m src.cli 'Your prompt here'")
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])
    print(f"[Placeholder] Would run agent with prompt: {prompt}")
    # TODO: Implement agent runner in Phase 5


if __name__ == "__main__":
    main()
