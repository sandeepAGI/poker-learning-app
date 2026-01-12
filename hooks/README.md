# Git Hooks

This directory contains Git hooks for the project. These hooks run automatically at specific points in the Git workflow to ensure code quality.

## Available Hooks

### pre-commit

Runs fast regression tests before allowing a commit.

**What it does:**
- Runs 4 core regression test files (~30 seconds)
- If `poker_engine.py` is being modified, runs infinite loop guard test (~2 seconds)
- Blocks commit if any test fails

**Installation:**
```bash
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**Bypass (emergency only):**
```bash
git commit --no-verify -m "your message"
```

**Tests run:**
1. `test_action_processing.py` - Core poker action logic
2. `test_state_advancement.py` - Game state transitions
3. `test_turn_order.py` - Turn order enforcement
4. `test_fold_resolution.py` - Fold handling
5. `test_property_based_enhanced.py` (conditional) - Infinite loop guard

## Why Use Hooks?

Git hooks provide an **automated safety net** that:
- Catches bugs before they reach CI
- Prevents infinite loop regressions (historical issue)
- Saves time by failing fast locally
- Enforces quality standards consistently

## Hook Philosophy

**Fast, not comprehensive:** Hooks run only critical tests (<60 seconds total).

**Local validation, not replacement:** Hooks complement CI, don't replace it. Full test suite runs in CI.

**Bypassable when needed:** Use `--no-verify` for emergency commits, but investigate failures afterward.

## Maintenance

**When to update the hook:**
- New critical test file added (must be fast <5 seconds)
- poker_engine.py renamed or moved
- Additional conditional checks needed (like the poker_engine.py check)

**What NOT to add:**
- Slow tests (>5 seconds per file)
- Tests requiring network/database
- Tests with external dependencies
- Formatting/linting (use CI for this)

## Troubleshooting

**Hook not running:**
```bash
# Check if hook exists and is executable
ls -la .git/hooks/pre-commit

# Re-install if needed
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**Hook fails with "pytest not found":**
```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt
```

**Hook fails with "No module named game":**
```bash
# Hook uses PYTHONPATH=backend automatically
# If it still fails, check you're in the repo root
git rev-parse --show-toplevel
```

## Contributing

When modifying hooks:
1. Test the hook locally before committing
2. Document changes in this README
3. Keep total runtime <60 seconds
4. Update CLAUDE.md if workflow changes
