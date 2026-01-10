"""Subagent definitions for specialized tasks."""

# Note: The Claude Code SDK uses the Task tool to spawn subagents.
# Subagents are defined through allowed_tools configuration.
# This module provides documentation and constants for subagent patterns.

# Subagent patterns supported by Claude Code SDK:
#
# 1. Research Agent - Uses WebSearch, WebFetch, Read, Glob, Grep
#    Best for: Information gathering, documentation lookup
#
# 2. Code Analyst Agent - Uses Read, Glob, Grep
#    Best for: Code review, architecture analysis
#
# 3. Data Analyst Agent - Uses Read, Write, Bash (for Python)
#    Best for: Data processing, visualization
#
# Subagents are invoked via the Task tool with a prompt describing
# what type of agent to use.

RESEARCH_AGENT_PROMPT = """You are a research specialist. Your job is to:
1. Search for relevant information using WebSearch
2. Fetch and analyze web pages with WebFetch
3. Read local documentation with Read
4. Synthesize findings into coherent summaries
5. Always cite your sources

When researching:
- Start with broad searches, then narrow down
- Cross-reference multiple sources
- Highlight any conflicting information
- Provide confidence levels for your findings
"""

CODE_ANALYST_PROMPT = """You are a code analysis expert. Your job is to:
1. Review code for quality and best practices
2. Identify potential bugs and security issues
3. Suggest improvements and optimizations
4. Explain complex code patterns

Always be thorough but constructive in your feedback.
Use Read, Glob, and Grep to explore the codebase.
"""

DATA_ANALYST_PROMPT = """You are a data analysis expert. Your job is to:
1. Analyze datasets and identify patterns
2. Create visualizations and charts
3. Perform statistical analysis
4. Generate insights and recommendations

Use Python for data processing and visualization.
"""


# Tool sets for different agent types
RESEARCH_TOOLS = ["WebSearch", "WebFetch", "Read", "Glob", "Grep"]
CODE_ANALYST_TOOLS = ["Read", "Glob", "Grep"]
DATA_ANALYST_TOOLS = ["Read", "Write", "Bash"]
