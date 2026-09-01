# Integration connections (SDK v2)

Read only the section needed for the current agent. All examples assume:

```python
from aixplain import Aixplain

aix = Aixplain(api_key=api_key)
```

Never use v1 factories. Before connecting, call `integration.list_actions()` and `integration.list_inputs(action_name)`. Scope every attached tool to a non-empty least-privilege `allowed_actions` list.

## Discover before connecting

```python
matches = aix.Integration.search(query="slack").results
for item in matches:
    print(item.name, item.id, item.path)

integration = aix.Integration.get(matches[0].id)
print(integration.list_actions())
```

## Slack: discover and scope the exact action

Preserve the explicit connection checkpoint. After the user agrees to connect Slack, inspect the action list and use the exact platform action name—not a conceptual alias:

```python
slack = aix.Integration.get("686432941223092cb4294d3f")
actions = list(slack.list_actions())
assert "SLACK_SEND_MESSAGE" in actions

slack_tool = aix.Tool(
    name="Approved Slack Sender",
    description="Sends an approved message to the selected Slack destination.",
    integration=slack,
    allowed_actions=["SLACK_SEND_MESSAGE"],
).save()
```

Request only the minimum `chat:write` permission needed to send the approved message. Do not use `send_message` as an action name.

## Web Search: inspect before generating runnable code

Prefer the first-party aixplain Web Search tool when it satisfies the request. With this unified plugin, use Marketplace Search to find the tool, then call `list_actions_tools` and `list_inputs_tools` for the selected asset before writing code. Emit only the returned action name and input fields; never invent nested parameters. Validate the resulting SDK snippet before presenting it.

Do not choose solely by display name. Prefer `aixplain/...` first-party paths over brokered connectors when both meet the requirement.

## Existing marketplace tool

```python
tool = aix.Tool.get("<TOOL_ID_OR_PATH>")
print(list(tool.actions))
tool.allowed_actions = ["required_action"]
```

`tool.actions` is an `Actions` collection. Use `list(tool.actions)`; `.keys()` and numeric indexing are not reliable.

## OAuth integration

Ask before initiating the external connection. State the minimum actions and why they are needed.

```python
import warnings

integration = aix.Integration.get("6864328d1223092cb4294d30")  # Gmail
print(integration.list_actions())

with warnings.catch_warnings(record=True) as captured:
    warnings.simplefilter("always")
    tool = aix.Tool(
        name="Customer Email Sender",
        description="Sends the final approved customer email.",
        integration=integration,
        allowed_actions=["GMAIL_SEND_EMAIL"],
    ).save()

connect_url = next(
    (str(item.message) for item in captured if "http" in str(item.message)),
    None,
)
print(connect_url)
```

The connection is workspace-specific. Create the tool fresh from the integration in each workspace; do not ship a saved connector tool ID in portable build code.

OAuth is a deliberate two-phase checkpoint: print/present the connect URL and stop that execution. Never call `input()` or wait interactively inside generated scripts. After the user confirms authorization, continue agent creation or verification in a new execution using the in-memory tool when available or its recorded workspace-local ID.

## Provider API-key integration

Ask for the provider key only after the user agrees to connect the provider. Keep it in memory/environment and never commit or print it.

```python
integration = aix.Integration.get("<INTEGRATION_ID>")
connected = integration.run(
    name="Provider Tool",
    authScheme="API_KEY",
    data={"generic_api_key": provider_api_key},
)
tool = aix.Tool.get(connected.data.id)
tool.allowed_actions = ["MINIMUM_REQUIRED_ACTION"]
tool.save()
```

The authentication field is `generic_api_key`; `api_key` and `apiKey` can fail with an unhelpful generic error.


## Remote MCP server

```python
mcp = aix.Tool(
    name="Remote MCP Tool",
    description="Uses the approved remote MCP capability.",
    integration="aixplain/mcp-server",
    config={"url": "https://example.com/mcp"},
).save()
mcp.allowed_actions = ["required_action"]
mcp.save()
```

Keep the exposed action set small; large MCP surfaces degrade tool selection.

## Verification sequence

For every connected or custom tool:
1. Run it directly with realistic input.
2. Attach it to the agent.
3. Run an agent prompt that requires it.
4. Confirm its unit name appears in `result.data.steps`.
5. Confirm governance allowed the run.
6. If observed behavior differs, follow the safe fallback in `reliability-guidelines.md` and keep a redacted local reproduction.
