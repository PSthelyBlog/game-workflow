# TODO

## Known Issues

### 1. Publish Phase Template Error

**Status**: Open
**Severity**: Medium
**Location**: `src/game_workflow/agents/publish.py:603` → `templates/itchio-page.md:134`

**Error**:
```
jinja2.exceptions.UndefinedError: 'dict object' has no attribute 'label'
```

**Description**:
The publish phase fails when rendering the itch.io store page template. The template expects link objects with `.label` and `.url` attributes, but receives plain dictionaries instead.

**Root Cause**:
In `templates/itchio-page.md` line 134:
```jinja2
- [{{ link.label }}]({{ link.url }})
```

The template uses dot notation (`link.label`) but the data passed is a dictionary that should be accessed with bracket notation (`link['label']`) or the data should be Pydantic models with proper attributes.

**Fix Options**:
1. Update the template to use bracket notation: `{{ link['label'] }}`
2. Ensure the `store_page` data uses Pydantic models instead of raw dicts
3. Add a Jinja2 filter or update the template context to handle both cases

**Workaround**:
The game build completes successfully before this error. The game is fully playable - only the itch.io publishing metadata fails to generate.

---

### 2. Invalid `--add-file` CLI Flag (FIXED)

**Status**: Fixed
**Fixed in**: `src/game_workflow/utils/subprocess.py`

**Description**:
The `ClaudeCodeRunner` was using `--add-file` flag which doesn't exist in Claude Code CLI.

**Fix Applied**:
Context file contents are now embedded directly in the prompt instead of using a non-existent CLI flag.

---

## Future Improvements

- [ ] Add `--output-dir` option to CLI (partially implemented, needs testing)
- [ ] Add `--auto-approve` flag documentation
- [ ] Improve error messages for template rendering failures
- [ ] Add retry logic for publish phase
