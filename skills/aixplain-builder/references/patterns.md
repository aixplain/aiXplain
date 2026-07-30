# Pattern cookbook

Canonical, copy-pasteable recipes. All assume the setup in SKILL.md (`aix = Aixplain(api_key=...)`). Pick the closest pattern, then adapt. Always scope `allowed_actions`, and prefer searching the marketplace over hardcoding IDs.

## 1. Web research agent
Answer questions with current information.
```python
search = aix.Tool.get("tavily/tavily-search-api")
agent = aix.Agent(name="Research Agent", description="Answers questions using web search",
    instructions="Use web search when needed. Always cite your sources.", tools=[search])
agent.save()
print(agent.run("What's the latest in AI regulation?").data.output)
```

## 2. Knowledge base agent (RAG)
Answer from private documents. Full detail in `references/knowledge-memory.md`.
```python
import time
index = aix.Tool(name=f"KB {int(time.time())}", description="Product docs index",
                 integration="6904bcf672a6e36b68bb72fb")
index.save()
index.run(action="upsert", data={"records": [{"id": "1", "text": "..."}]})
index.allowed_actions = ["search", "get"]
agent = aix.Agent(name="Docs Assistant", description="Answers from product docs",
    instructions="Search the index to answer. Cite the document id.", tools=[index])
agent.save()
```

## 3. SQL data agent
Natural-language queries over a database.
```python
import time
resource = aix.Resource(name=f"DB {int(time.time())}", file_path="sales.db"); resource.save()
db = aix.Tool(name="Sales DB", description="Sales database",
              integration="689e06ed3ce71f58d73cc999", config={"url": resource.url})
db.allowed_actions = ["query", "schema"]; db.save()
agent = aix.Agent(name="Data Analyst", description="Answers questions about sales data",
    instructions="Inspect the schema, then query. Read-only — never modify data.", tools=[db])
agent.save()
```
For a live database use PostgreSQL (`integration="aixplain/postgresql"`, `config={"url": "postgresql://..."}`).

## 4. Custom business logic agent
Wrap a Python function as a sandboxed tool. Full constraints in `references/tools-integrations.md`.
```python
import inspect, time
def shipping_cost(weight_kg: float, distance_km: float) -> dict:
    """Compute shipping cost."""
    return {"cost": round(2.5 + 0.1 * weight_kg + 0.05 * distance_km, 2)}
tool = aix.Tool(name=f"Shipping {int(time.time())}", integration="688779d8bfb8e46c273982ca",
                config={"code": inspect.getsource(shipping_cost), "function_name": "shipping_cost"})
tool.save()
agent = aix.Agent(name="Logistics Agent", description="Quotes shipping costs", tools=[tool])
agent.save()
```

## 5. Multi-agent team
Coordinate specialists. Full detail in `references/agents.md`.
```python
researcher = aix.Agent(name="Researcher", description="Finds information", tools=[search])
writer     = aix.Agent(name="Writer", description="Writes clear markdown reports", output_format="markdown")
team = aix.Agent(name="Content Team", description="Researches a topic and writes a report",
                 agents=[researcher, writer])
team.save(save_subcomponents=True)
print(team.run("Research and summarize quantum computing").data.output)
```

## 6. Governed agent
Enforce a policy before delivery. Full detail in `references/governance.md`.
```python
from aixplain.v2.inspector import (Inspector, InspectorAction, InspectorActionConfig,
    InspectorOnExhaust, InspectorSeverity, EvaluatorType, EvaluatorConfig)
llm_id = aix.Model.get("openai/gpt-4o").id
guard = Inspector(name="safety", description="Block unsafe output",
    severity=InspectorSeverity.CRITICAL, targets=["output"],
    action=InspectorActionConfig(type=InspectorAction.RERUN, max_retries=2,
        on_exhaust=InspectorOnExhaust.ABORT),
    evaluator=EvaluatorConfig(type=EvaluatorType.ASSET, asset_id=llm_id,
        prompt="Fail if the response is unsafe or off-policy; otherwise pass."))
team = aix.Agent(name="Guarded", description="...", agents=[worker], inspectors=[guard])
team.save(save_subcomponents=True)
```

## 7. MCP integration agent
Use a remote MCP server's tools.
```python
mcp = aix.Tool(integration="aixplain/mcp-server", name="Web Fetch MCP",
               config={"url": "https://remote.mcpservers.org/fetch/mcp"})
mcp.save(); mcp.allowed_actions = ["fetch"]
agent = aix.Agent(name="Fetcher", description="Fetches and summarizes web pages", tools=[mcp])
agent.save()
```

## 8. Commercial integration agent
Act in Slack/Gmail/Salesforce/etc. OAuth flow in `references/tools-integrations.md`.
```python
slack = aix.Tool(name="Slack Notifier", description="Sends Slack messages",
                 integration="composio/slack", config={"token": "YOUR_SLACK_TOKEN"})
slack.allowed_actions = ["SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL"]; slack.save()
agent = aix.Agent(name="Notifier", description="Searches and posts updates to Slack",
                  tools=[search, slack])
agent.save()
```

## 9. Code quality agent
Pure-LLM agent (no tools). Pass source via `content=`.
```python
agent = aix.Agent(name="Code Quality Agent",
    description="Writes pytest tests and docstrings",
    instructions="Given Python code: 1) write a complete pytest test file; 2) add a docstring.",
    output_format="markdown")
agent.save()
print(agent.run(query="Write unit tests and a docstring for this function.",
                content=[source_code]).data.output)
```

## 10. Speech-to-text (Whisper)
Direct model call — no agent. Full detail in `references/models.md`.
```python
from aixplain.v2.file import FileUploader
url = FileUploader(api_key=API_KEY).upload(file_path="meeting.mp3", is_temp=True, return_download_link=True)
model = aix.Model.get("66311fda6eb563279c574b71")
r = model.run(source_audio=url, sourcelanguage="en", options={"includeRawData": True})
print(r.data)                                  # transcript
print(r._raw_data["rawData"]["language"])      # auto-detected language
# If passing a public URL directly fails with err.invalid_input_data_or_input_url,
# the host is likely bot-protected (WAF) — download it and re-host via FileUploader (above).
```

## 11. Travel / multi-source planner
Combine a marketplace search tool with a custom planning function tool (patterns #1 + #4), `output_format="markdown"`, and clear step-by-step instructions in the agent.
