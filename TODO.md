# TODO

## Known Issues

### 1. Publish Phase Template Error (FIXED)

**Status**: Fixed
**Fixed in**: PR #34

**Description**:
The publish phase failed when rendering the itch.io store page template with:
```
jinja2.exceptions.UndefinedError: 'dict object' has no attribute 'label'
```

**Fix Applied**:
Added proper Pydantic models for nested structures that the template expects:
- `ChangelogEntry` model with `version`, `date`, `description` fields
- `SupportLink` model with `label`, `url` fields
- Updated `VersionInfo.changelog` to use `list[ChangelogEntry]`
- Updated `SupportInfo.links` to use `list[SupportLink]`

This ensures that when `model_dump()` is called, the nested objects have the expected attribute structure for Jinja2 template rendering.

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

- [x] Add `--output-dir` option to CLI (PR #35)
- [ ] Add `--auto-approve` flag documentation
- [ ] Improve error messages for template rendering failures
- [ ] Add retry logic for publish phase
