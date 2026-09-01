# Reliability Guidelines

Use these proven practices to build and maintain aixplain agents safely with SDK v2. They capture behavior verified against `aixplain==0.2.47` and help the agent choose dependable paths without exposing an internal defect log.

## Build against the released SDK

- Use `from aixplain import Aixplain` and SDK v2 objects only.
- Validate generated Python with `py_compile` and inspect constructors from the installed package before presenting exports.
- Use `llm=`, never `llm_id=`, in exported agent constructors. Keep iteration limits in `agent.budget`; do not set a top-level `max_iterations` field.

## Configure budgets as guardrails, not invoices

- Set durable controls on `agent.budget`; `agent.run(budget=...)` is not a reliable one-off override.
- Treat `max_cost` as a circuit breaker rather than an exact billing ceiling, especially for teams.
- Report actual usage from `result.data.execution_stats["credits"]` after every consequential run.

## Verify capabilities from live schemas

- Inspect Marketplace Search results through each kind's `results` collection, not `items`.
- Before generating Web Search or integration code, inspect the exact actions and input schemas.
- If Marketplace Search is unavailable, continue with SDK discovery and state only material limitations.

## Keep integrations safe in real agent runs

- Test each integration directly and again inside the agent. A connector that works alone may need a compatible model or deterministic application code when its structured output cannot be consumed in an agent loop.
- Request explicit user consent before connecting an external service, and use the smallest supported action scope.
- Call `resource.save()` before relying on a file resource URL. Set explicit MIME types for `.html` and `.zip` uploads when needed.

## Preserve least privilege during updates

Before a get → mutate → save update, fetch the raw agent payload and restore each tool's stored `actions` onto the hydrated tool's `allowed_actions`. Then verify the raw persisted scopes after saving. This prevents an update from unintentionally broadening tool permissions.

## Prove required tool use

A successful result is not proof that a required tool ran. For every realistic verification:

1. Check the output and governance status.
2. Inspect `result.data.steps` for the intended tool unit.
3. When tool invocation is mandatory, prefer adaptive or planner execution and assert the unit is present.

## Keep final-answer behavior explicit

Do not rely on `response_generator` or a deprecated separate response-generation pass. Put final-answer requirements in the primary agent instructions, or model a visible task/subagent when a separate synthesis step is required.

## Escalate responsibly

If observed behavior contradicts these guidelines, preserve a minimal, redacted reproduction in local engineering notes, use the safest confirmed workaround, and draft a public issue only when the user asks. Never include API keys, customer data, or workspace-bound IDs.
