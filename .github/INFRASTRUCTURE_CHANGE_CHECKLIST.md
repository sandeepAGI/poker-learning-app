# Infrastructure Change Checklist

Use this checklist for changes to:
- CI workflows (`.github/workflows/*.yml`)
- Test configuration (`jest.config.ts`, `pytest.ini`, `conftest.py`)
- Build configuration (`package.json`, `requirements.txt`)
- Pre-commit hooks (`hooks/pre-commit`)

## Pre-Change

- [ ] Document current state (test count, runtime, coverage %)
- [ ] Create rollback plan (know the commit hash to revert to)
- [ ] Test in fork if changing CI workflows
- [ ] Identify affected systems (backend/frontend/E2E/CI)

## During Change

- [ ] Make minimal change (one thing at a time)
- [ ] Add comments explaining WHY, not just WHAT
- [ ] Update documentation immediately (docs/TEST-SUITE-REFERENCE.md, CLAUDE.md)
- [ ] Test locally if possible (run affected tests)

## Post-Change

- [ ] Run affected tests locally (100% pass rate required)
- [ ] Monitor first CI run closely (don't walk away)
- [ ] Compare metrics (before vs after: test count, runtime, failures)
- [ ] Update STATUS.md with changes made

## Rollback Plan

If CI fails after merge:

1. **Revert immediately**: `git revert HEAD && git push`
2. **Investigate locally**: Reproduce the failure
3. **Re-apply with fix**: Test thoroughly before pushing
4. **Document**: Add to docs/CI-failure-fixes.md what went wrong

## Platform-Specific Changes

### For Visual/Snapshot Tests

- [ ] Generate baselines in CI environment (Linux), NEVER locally (macOS)
- [ ] Test on target platform before committing
- [ ] Use `generate-visual-baselines.yml` workflow for baseline updates
- [ ] Document baseline generation process in test comments

### For Coverage Thresholds

- [ ] Set to current baseline (NOT aspirational targets)
- [ ] Increase gradually (+5% per sprint maximum)
- [ ] Test that thresholds pass locally before enforcing in CI
- [ ] Never add thresholds without having tests that meet them

### For Pytest Markers

- [ ] Define marker in `backend/conftest.py` before using
- [ ] Use `@pytest.mark.slow` for tests >60 seconds
- [ ] Verify marker works: `pytest --markers` shows your marker
- [ ] Test collection: `pytest -m "not slow" --collect-only`

### For Workflow File Lists

- [ ] **Prefer auto-discovery** over explicit file lists
- [ ] Use pytest markers (`-m "not slow"`) instead of listing files
- [ ] If using explicit lists, document WHY in comments
- [ ] Validate all referenced files exist before committing

## Common Mistakes (Avoid These!)

### ❌ Don't: Add configuration without testing
```yaml
# Bad: Added coverage thresholds without having tests
coverageThreshold: { global: { lines: 70 } }
```

### ✅ Do: Test configuration locally first
```bash
# Good: Test coverage meets threshold before enforcing
npm test -- --coverage
# Check if it passes, then add threshold
```

### ❌ Don't: Generate platform-specific baselines locally
```bash
# Bad: Generated on macOS, will fail on Linux CI
npx playwright test --update-snapshots
```

### ✅ Do: Generate baselines in CI environment
```bash
# Good: Use workflow or SSH into CI environment
gh workflow run generate-visual-baselines.yml
```

### ❌ Don't: Use explicit file lists that get stale
```yaml
# Bad: Must manually update when adding tests
pytest test_a.py test_b.py test_c.py
```

### ✅ Do: Use auto-discovery with markers
```yaml
# Good: Automatically includes new tests
pytest backend/tests/ -m "not slow"
```

## Velocity Guidelines

- **Maximum 5-7 commits per day** during infrastructure work
- **Pause every 5 commits** to validate (run full test suite)
- **Don't merge large changes on Fridays** (need monitoring time)
- **One logical change per commit** (not "fix multiple issues")

## Code Review for Test Infrastructure

Test infrastructure changes get same rigor as production code:

- [ ] All file references validated (files exist)
- [ ] Test counts documented and accurate
- [ ] Runtime estimates realistic (test them)
- [ ] Failure modes considered (what breaks if this fails?)
- [ ] Rollback plan documented

## Success Criteria

Before marking infrastructure change as "done":

- ✅ CI passes (all green)
- ✅ Documentation updated
- ✅ Metrics documented (before/after)
- ✅ No regressions (test count didn't decrease unexpectedly)
- ✅ Runtime acceptable (comprehensive <10 min, nightly <180 min)

---

**Remember**: CI should be a safety net, not your primary validation tool. Test locally first!
