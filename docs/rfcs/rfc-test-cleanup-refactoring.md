# RFC: Fixture-Based Test Resource Cleanup for Agent and Team Agent Tests

**Status**: Draft
**Created**: 2026-02-06

## Abstract

This RFC proposes replacing the global "delete all agents" test cleanup strategy with per-fixture resource management using pytest's `yield` + `try/finally` pattern. This eliminates the production environment safety blocker that causes all agent and team agent tests to fail on the `main` branch, while making tests self-contained, parallel-safe, and environment-agnostic.

## Problem Statement

### Current Challenges

- **Tests fail on `main` branch**: The `safe_delete_all_agents_and_team_agents()` utility in `tests/test_deletion_utils.py` raises a `RuntimeError` when `BACKEND_URL` points to production (`https://platform-api.aixplain.com`). Since the `main` branch CI uses production credentials, nearly every agent and team agent test fails before any test logic runs.

- **Global nuke is unsafe for production**: The current cleanup strategy deletes *all* agents and team agents associated with the API key -- not just those created by the test. This is inherently unsafe for shared environments and makes production testing impossible.

- **Leaked resources on test failure**: Many tests call `agent.delete()` at the end of the test body, outside any `try/finally` block. If an assertion fails mid-test, cleanup is skipped and agents leak, potentially causing name collisions in subsequent runs.

- **Cross-test coupling**: The `delete_agents_and_team_agents` fixture with `scope="function"` runs a global wipe before *and* after every test. This masks resource leaks and creates implicit dependencies between tests.

### Business Context

The CI pipeline runs tests on both the `test` and `main` branches. The `main` branch targets production and uses `TEAM_API_KEY_PROD`. With the current approach, 10 out of 17 test jobs fail on every merge to `main`, degrading confidence in the release process.

### Impact of Not Solving This

- Every merge to `main` produces a red CI status.
- Agent and team agent tests provide zero coverage validation against the production environment.
- Developers lose trust in CI and may ignore legitimate failures.

## Goals

### Primary Goals

1. **All agent/team agent tests pass on both `test` and `main` branches** without environment-specific workarounds.
2. **Every test cleans up its own resources** using pytest `yield` fixtures with `try/finally` teardown.
3. **No global "delete all" operations** -- each test is responsible only for resources it creates.
4. **Cleanup runs even when tests fail** -- resources never leak.

### Non-Goals / Out of Scope

- Changing test logic or assertions -- only the resource lifecycle management is being refactored.
- Adding new test coverage -- this is a structural cleanup of existing tests.
- Modifying the `test_deletion_utils.py` for use outside of tests -- it may be kept as a standalone utility but is no longer imported by test fixtures.
- Refactoring tests in other suites (model, pipeline, benchmark, etc.).

## Proposed Solution

### Core Design Principle

**Every resource created in a test must be cleaned up by the same fixture that created it**, using pytest's `yield` mechanism with `try/except` in the teardown phase.

### Pattern 1: Single-Resource Fixture

For tests that need a single agent:

```python
@pytest.fixture
def agent(run_input_map):
    tools = build_tools_from_input_map(run_input_map)
    agent = AgentFactory.create(
        name=run_input_map["agent_name"],
        llm_id=run_input_map["llm_id"],
        tools=tools,
        ...
    )
    yield agent
    try:
        agent.delete()
    except Exception:
        pass
```

### Pattern 2: Multi-Resource Fixture

For tests that need agents + a team agent:

```python
@pytest.fixture
def team_with_agents(run_input_map):
    agents = create_agents_from_input_map(run_input_map)
    team_agent = create_team_agent(TeamAgentFactory, agents, run_input_map)
    yield team_agent, agents
    # Delete team agent first (references agents)
    try:
        team_agent.delete()
    except Exception:
        pass
    for agent in agents:
        try:
            agent.delete()
        except Exception:
            pass
```

### Pattern 3: Resource Tracker for Ad-Hoc Resources

For tests that create additional resources dynamically:

```python
@pytest.fixture
def resource_tracker():
    """Tracks resources created during a test for guaranteed cleanup."""
    resources = []
    yield resources
    for resource in reversed(resources):
        try:
            resource.delete()
        except Exception:
            pass
```

### Key Components and Responsibilities

| Component | Responsibility |
|-----------|---------------|
| `@pytest.fixture` with `yield` | Creates resources, yields to test, cleans up in teardown |
| `try/except` in teardown | Ensures cleanup is best-effort and never crashes the teardown |
| `resource_tracker` fixture | Handles dynamic resource creation within test bodies |
| `build_tools_from_input_map()` | Shared helper extracted from duplicated tool-building logic |
| Reverse-order deletion | Team agents deleted before agents (respects dependencies) |

### Files Changed

| File | Change |
|------|--------|
| `tests/functional/agent/agent_functional_test.py` | Remove `delete_agents_and_team_agents` fixture. Add `yield`-based fixtures. Wrap ~13 tests. |
| `tests/functional/agent/agent_mcp_deploy_test.py` | Remove `cleanup_agents` fixture. Add cleanup to `mcp_tool` and `test_agent` fixtures. |
| `tests/functional/team_agent/team_agent_functional_test.py` | Remove `delete_agents_and_team_agents` fixture. Add `yield`-based fixtures. Wrap ~12 tests. |
| `tests/functional/team_agent/evolver_test.py` | Remove `delete_agents_and_team_agents` fixture. Add cleanup to `team_agent` fixture. |
| `tests/test_deletion_utils.py` | Remove the global deletion utility (no longer needed by tests). |

## Alternatives Considered

| Approach | Pros | Cons | Why Not Chosen |
|----------|------|------|----------------|
| Allow global delete in prod | Simple one-line fix | Deletes production agents; unsafe | Too risky for shared production environments |
| Skip tests on main branch | No code changes needed | Zero prod test coverage | Defeats the purpose of having prod CI |
| Skip cleanup on prod (return early) | Minimal change | Agents leak on prod; name collisions over time | Doesn't solve the root lifecycle problem |
| `try/finally` inside each test body | No fixtures needed | Massive code duplication; easy to forget | Fixtures provide cleaner, DRY solution |
| **Yield fixtures with per-resource cleanup** | Safe everywhere; no leaks; DRY; parallel-safe | Requires refactoring all test files | **Chosen** |

## Implementation Plan

### Phase 1: Core Refactoring (This PR)

1. Add shared helper `build_tools_from_input_map()` to reduce duplication in `agent_functional_test.py`.
2. Replace `delete_agents_and_team_agents` fixture in all four test files with `yield`-based resource fixtures.
3. Add `resource_tracker` fixture for tests that create resources dynamically.
4. Remove `tests/test_deletion_utils.py` (or stop importing it from test fixtures).
5. Verify all tests pass locally against the test environment.

### Phase 2: CI Validation

1. Push to `test` branch and verify all agent/team_agent jobs pass.
2. Merge to `main` and verify all agent/team_agent jobs pass against production.

### Migration Strategy

This is a non-breaking change. The test behavior is identical -- only the cleanup mechanism changes. No production code is modified.

## Success Criteria

1. **CI green on `main`**: All 17 test jobs pass, including `agent` and `team_agent`.
2. **No leaked agents**: After a test run (pass or fail), no orphaned agents remain on the account.
3. **No environment checks in tests**: Tests work identically regardless of `BACKEND_URL`.
4. **No global delete operations**: `safe_delete_all_agents_and_team_agents()` is not called by any test.

## Open Questions

1. **Should `test_deletion_utils.py` be deleted entirely or kept as a standalone CLI utility?** It could be useful for manual cleanup, but is no longer needed by tests.
2. **Should we add a CI step to verify no agents leaked after the test suite completes?** This would catch future regressions in cleanup logic.

## References

- Failing CI run: https://github.com/aixplain/aiXplain/actions/runs/21722749150/
- pytest fixture teardown docs: https://docs.pytest.org/en/stable/how-to/fixtures.html#teardown-cleanup-aka-fixture-finalization
