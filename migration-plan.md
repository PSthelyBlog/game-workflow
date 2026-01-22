# Migration Plan: Anthropic Python SDK → Claude Agent SDK

## Objective

Replace `anthropic` Python SDK with `claude-agent-sdk` to enable automatic authentication inheritance from Claude Code CLI (supports both subscription and API key auth).

## Key Benefit

Users can authenticate via:
- **Subscription** (Pro/Max): Run `claude` once to login → SDK uses it automatically
- **API Key**: Set `ANTHROPIC_API_KEY` → works as before

No explicit configuration needed - the SDK handles auth priority automatically.

---

## Files to Modify

### Core Changes

| File | Change |
|------|--------|
| `pyproject.toml` | Replace `anthropic>=0.40.0` with `claude-agent-sdk>=0.1.0` |
| `src/game_workflow/utils/agent_sdk.py` | **NEW** - SDK wrapper utilities |
| `src/game_workflow/agents/design.py` | Replace Anthropic client with Agent SDK |
| `src/game_workflow/agents/publish.py` | Replace Anthropic client with Agent SDK |
| `src/game_workflow/agents/build.py` | Replace ClaudeCodeRunner with native SDK |
| `src/game_workflow/agents/base.py` | Make API key optional, add deprecation warning |
| `src/game_workflow/config.py` | Add Agent SDK config options |

### Test Updates

| File | Change |
|------|--------|
| `tests/conftest.py` | Add Agent SDK mock fixtures |
| `tests/unit/test_design_agent.py` | Update mocking patterns |
| `tests/unit/test_publish_agent.py` | Update mocking patterns |
| `tests/unit/test_build_agent.py` | Update mocking patterns |
| `tests/unit/test_agents.py` | Update API key validation tests |

### Documentation

| File | Change |
|------|--------|
| `README.md` | Update auth instructions |
| `docs/setup.md` | Document subscription vs API key auth |
| `CLAUDE.md` | Update SDK references |

---

## Implementation Steps

### Step 1: Add Agent SDK Utility Module

Create `src/game_workflow/utils/agent_sdk.py`:

```python
"""Claude Agent SDK utilities for structured JSON generation."""

from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage

async def generate_structured_response(
    prompt: str,
    system_prompt: str,
    model: str = "claude-sonnet-4-5-20250929",
) -> str:
    """Generate a text response using the Agent SDK.

    Returns the concatenated text from all assistant messages.
    """
    text_parts = []
    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            model=model,
            system_prompt=system_prompt,
            allowed_tools=[],  # No tools for pure generation
            permission_mode="bypassPermissions",
        )
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "text"):
                    text_parts.append(block.text)
        elif isinstance(message, ResultMessage) and message.is_error:
            raise RuntimeError(f"Agent SDK error: {message}")

    return "".join(text_parts)
```

### Step 2: Update Dependencies

In `pyproject.toml`:

```toml
dependencies = [
    "claude-agent-sdk>=0.1.0",  # Replaces anthropic
    "mcp>=1.0.0",
    # ... rest unchanged
]
```

### Step 3: Migrate DesignAgent

In `src/game_workflow/agents/design.py`:

**Remove:**
- Lines 15-16: `from anthropic import Anthropic` and `from anthropic.types import Message, TextBlock`
- Line 133: `self._client: Anthropic | None = None`
- Lines 141-157: `client` property
- Lines 463-477: `_extract_text()` method

**Add:**
```python
from game_workflow.utils.agent_sdk import generate_structured_response
```

**Update `_generate_concepts()`** (and similar methods):

```python
# Before:
response = self.client.messages.create(
    model=self.model,
    max_tokens=8192,
    messages=[{"role": "user", "content": user_prompt}],
    system=system_prompt,
)
text = self._extract_text(response)

# After:
text = await generate_structured_response(
    prompt=user_prompt,
    system_prompt=system_prompt,
    model=self.model,
)
```

### Step 4: Migrate PublishAgent

Same pattern as DesignAgent - replace Anthropic client calls with `generate_structured_response()`.

### Step 5: Migrate BuildAgent

In `src/game_workflow/agents/build.py`, replace ClaudeCodeRunner with native SDK:

```python
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage

async def _invoke_claude_code(self, project_dir: Path, prompt: str, ...) -> str:
    """Invoke Claude Code using the Agent SDK."""
    options = ClaudeAgentOptions(
        cwd=str(project_dir),
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        permission_mode="acceptEdits",
        setting_sources=["project"],  # Load skills from project
    )

    output_parts = []
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "text"):
                    output_parts.append(block.text)
        elif isinstance(message, ResultMessage):
            if message.is_error:
                raise BuildFailedError(f"Claude Code failed: {message}")

    return "\n".join(output_parts)
```

### Step 6: Update BaseAgent

In `src/game_workflow/agents/base.py`:

```python
def _validate_config(self) -> None:
    """Validate configuration (API key no longer required)."""
    # API key is optional with Agent SDK - it inherits from Claude Code CLI
    if self.api_key:
        import warnings
        warnings.warn(
            "ANTHROPIC_API_KEY is set but not required. "
            "Claude Agent SDK inherits authentication from Claude Code CLI.",
            DeprecationWarning,
            stacklevel=3
        )
```

### Step 7: Update Tests

In `tests/conftest.py`, add mock fixtures:

```python
@pytest.fixture
def mock_agent_sdk_query(monkeypatch):
    """Mock the Agent SDK query function."""
    async def _mock_query(response_text: str):
        from unittest.mock import AsyncMock
        from claude_agent_sdk import AssistantMessage, ResultMessage

        async def mock_response():
            # Yield assistant message with text
            msg = AsyncMock()
            msg.content = [AsyncMock(text=response_text)]
            yield msg
            # Yield result
            result = AsyncMock()
            result.is_error = False
            yield result

        return mock_response()

    return _mock_query
```

Update test files to use new mock patterns.

### Step 8: Update Documentation

**README.md** - Add authentication section:
```markdown
## Authentication

The workflow supports two authentication methods:

1. **Claude Subscription** (Pro/Max): Run `claude` in your terminal to login
2. **API Key**: Set `ANTHROPIC_API_KEY` environment variable

The Claude Agent SDK automatically uses whichever authentication is available.
```

---

## Verification

1. **Unit Tests**: `pytest tests/unit -v`
2. **Type Check**: `mypy src/game_workflow`
3. **Lint**: `ruff check . && ruff format --check .`
4. **Integration Test**: `python -m game_workflow run "Create a simple puzzle game" --dry-run`
5. **Manual Test**: Full workflow with real Claude Code authentication

---

## Rollback Plan

If issues arise:
1. Keep `anthropic` as fallback dependency
2. Add `USE_LEGACY_SDK=1` env var to toggle old behavior
3. Gradual migration: DesignAgent first, then PublishAgent, then BuildAgent

---

## Notes

- The Agent SDK bundles Claude Code CLI - no separate installation needed
- Existing ClaudeCodeRunner in subprocess.py can be deprecated but kept for compatibility
- All JSON parsing logic remains unchanged - only the API call layer changes
