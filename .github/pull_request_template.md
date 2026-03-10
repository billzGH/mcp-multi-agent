# Pull Request

## Description
<!-- Provide a brief description of what this PR does -->

## Type of Change
<!-- Mark the relevant option with an 'x' -->
- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 📚 Documentation update
- [ ] 🎨 Code style/formatting
- [ ] ♻️ Refactoring (no functional changes)
- [ ] 🚨 Breaking change (fix or feature that would cause existing functionality to not work as expected)

## Related Issue(s)
<!-- Link to related issues using #issue_number -->
Fixes #
Related to #

## Changes Made
<!-- List the specific changes in this PR -->
-
-
-

## Component Affected
<!-- Which part of the project does this change affect? -->
- [ ] Spike — monitor-agent
- [ ] Spike — engineer-agent
- [ ] Spike — findings / documentation
- [ ] Examples (Phase 1+)
- [ ] Docs / architecture guides
- [ ] Project configuration
- [ ] Other:

## Testing Done
<!-- Describe the testing you've performed -->
- [ ] Server starts without errors: `uv run --directory spike/<agent> server.py`
- [ ] Tested with Claude Desktop — server appears in tool list
- [ ] Tested coordination — both servers configured simultaneously in Claude Desktop
- [ ] Verified tool calls return expected results
- [ ] Ran test suite: `uv run pytest tests/ -v`
- [ ] Tested on OS: <!-- macOS/Windows/Linux -->

## Claude Desktop Config Used
<!-- Optional: share the relevant snippet from your claude_desktop_config.json -->
```json

```

## Screenshots/Examples (if applicable)
<!-- Add screenshots or example Claude Desktop session output showing agent coordination -->

## Checklist

- [ ] My code follows the project's style guidelines
- [ ] I have added/updated tests as needed
- [ ] I have updated documentation as needed
- [ ] I have added comments for complex logic
- [ ] My changes generate no new warnings
- [ ] I have tested this with the latest version of dependencies
- [ ] CLAUDE.md updated if architectural decisions were made

## Additional Notes
<!-- Any additional information reviewers should know -->
