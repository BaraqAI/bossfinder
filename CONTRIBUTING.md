# Contributing to BossFinder

Thank you for your interest in contributing!

## Quick start

```bash
git clone https://github.com/baraqai/bossfinder.git
cd bossfinder
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # add at least one LLM key + one search key
```

## Adding a new data source

1. Create a tool in `src/bossfinder/tools/<source>_tool.py` — extend `crewai.tools.BaseTool`.
2. Create an agent in `src/bossfinder/agents/<source>_agent.py` — follow the existing pattern.
3. Add a task factory in `src/bossfinder/tasks/search_tasks.py`.
4. Register the agent and task in `src/bossfinder/crew.py` and add it to `merger_task.context`.
5. Add the required env var to `.env.example` with a comment linking to where to get the key.
6. Document the new key in the README table.

## Code style

- Python 3.10+, type hints everywhere.
- No comments unless the *why* is non-obvious.
- Each tool must return `"SKIP: <VAR> not configured"` when its API key is absent.
- Tools must never raise uncaught exceptions — catch and return the error string.

## Pull requests

- Target the `main` branch.
- Keep PRs focused: one new source per PR.
- Include a sample of the raw output your agent produces in the PR description.

## Reporting issues

Please open a GitHub issue with:
- The company name you searched for
- Which API keys you have configured (not the values)
- The full error output
