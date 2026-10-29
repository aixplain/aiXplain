# Pattern cookbook

Canonical, copy-pasteable recipes. All assume the setup in SKILL.md (`aix = Aixplain(api_key=...)`). Pick the closest pattern, then adapt. Always scope `allowed_actions`, and prefer searching the marketplace over hardcoding IDs.

> Integrations are identified by their three-segment **asset path** (`<developer>/<slug>/<host>`) throughout — that is what the docs now use everywhere. The hex asset IDs still resolve, so old code keeps working.

## 1. Web research agent
Answer questions with current information.
```python
search = aix.Tool.get("tavily/tavily-web-search/tavily")
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
                 integration="aixplain/air-knowledge-base/aixplain")
index.save()
index.run(action="upsert", data={"records": [{"id": "1", "text": "...", "metadata": {"category": "pricing"}}]})
index.allowed_actions = ["search", "get"]
agent = aix.Agent(name="Docs Assistant", description="Answers from product docs",
    instructions="Search the index to answer. Cite the document id.", tools=[index])
agent.save()
```
For **long-form** documents (papers, PDFs), chunk on upsert so retrieval stays precise — same recipe, one extra key:
```python
index.run(action="upsert", data={"records": documents,
    "chunking": {"split_by": "sentence", "split_length": 3, "split_overlap": 1}})
```

## 3. SQL data agent
Natural-language queries over a database.
```python
from aixplain.v2 import FileUploader
db_url = FileUploader(api_key=aix.api_key).upload("sales.db", return_download_link=True)
db = aix.Tool(name="Sales DB", description="Sales database",
              integration="aixplain/sqlite/aixplain", config={"url": db_url})
db.save(); db.allowed_actions = ["query", "schema"]
agent = aix.Agent(name="Data Analyst", description="Answers questions about sales data",
    instructions=("Table orders(id INTEGER, product TEXT, quantity INTEGER, revenue REAL). "
                  "Inspect the schema, then query. Read-only — never modify data."), tools=[db])
agent.save()
```
Put the table schema in `instructions`: it keeps the generated SQL on real columns. For a live database use PostgreSQL (`integration="aixplain/postgresql/aixplain"`, `config={"url": "postgresql://..."}`).

## 4. Custom business logic agent
Wrap a Python function as a sandboxed tool. Full constraints in `references/tools-integrations.md`.
```python
import inspect, time
def shipping_cost(weight_kg: float, distance_km: float) -> dict:
    """Compute shipping cost."""
    return {"cost": round(2.5 + 0.1 * weight_kg + 0.05 * distance_km, 2)}
tool = aix.Tool(name=f"Shipping {int(time.time())}", description="Computes shipping cost.",
                integration="aixplain/python-sandbox/aixplain",
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
llm_id = aix.Model.get("openai/gpt-4o-mini/openai").id
guard = aix.Inspector(name="safety", description="Block unsafe output",
    severity="critical", targets=["output"],
    action={"type": "rerun", "max_retries": 2, "on_exhaust": "abort"},
    metric={"assetId": llm_id,
            "prompt": "Fail if the response is unsafe or off-policy; otherwise pass."})
team = aix.Agent(name="Guarded", description="...", agents=[worker], inspectors=[guard])
team.save(save_subcomponents=True)
```
Or skip authoring one and attach a managed marketplace guardrail:
```python
guard = aix.Inspector.get("aws/detect-prompt-attacks-guardrail/aws")   # aix.Inspector.search("guard")
agent = aix.Agent(name="Guarded", description="...", inspectors=[guard])   # works on a single agent too
agent.save()
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

## 8. Integration agent
(Canonically renamed from "Commercial integration agent".) Act in Slack/Gmail/Salesforce/etc. OAuth flow in `references/tools-integrations.md`.
```python
slack = aix.Tool(name="Slack Notifier", description="Sends Slack messages",
                 integration="composio/slack/composio", config={"token": "YOUR_SLACK_TOKEN"})
slack.allowed_actions = ["SLACK_SEND_MESSAGE"]; slack.save()
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
from aixplain.v2 import FileUploader          # NOT aixplain.v2.file — that raises ImportError
url = FileUploader(api_key=aix.api_key).upload(file_path="meeting.mp3", is_temp=True, return_download_link=True)
model = aix.Model.get("66311fda6eb563279c574b71")
r = model.run(source_audio=url, sourcelanguage="en", options={"includeRawData": True})
print(r.data)                                  # transcript
print(r._raw_data["rawData"]["language"])      # auto-detected language
# If passing a public URL directly fails with err.invalid_input_data_or_input_url,
# the host is likely bot-protected (WAF) — download it and re-host via FileUploader (above).
```

## 11. Travel / multi-source planner
Combine a marketplace search tool with a custom planning function tool (patterns #1 + #4), `output_format="markdown"`, and clear step-by-step instructions in the agent.
```python
import inspect, time
search = aix.Tool.get("tavily/tavily-web-search/tavily")
def trip_budget(nights: int, nightly_rate: float, flight: float) -> dict:
    """Total a trip's cost."""
    return {"total": round(nights * nightly_rate + flight, 2), "per_night": nightly_rate}
budget = aix.Tool(name=f"Trip Budget {int(time.time())}", description="Totals a trip's cost.",
                  integration="aixplain/python-sandbox/aixplain",
                  config={"code": inspect.getsource(trip_budget), "function_name": "trip_budget"})
budget.save()
agent = aix.Agent(name="Travel Planner", description="Plans trips and budgets them",
    instructions=("1) search flights, stays and things to do; 2) call the budget tool with the "
                  "numbers you found; 3) return a day-by-day itinerary plus a cost table. Cite sources."),
    tools=[search, budget], output_format="markdown")
agent.save()
```
