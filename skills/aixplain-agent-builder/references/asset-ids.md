# Curated IDs

Model, tool, and integration ID lookup tables for fast deployment.
Linked from the main skill — use for asset discovery.

---

## Top 10 Models (updated 2026-04-01)

| Rank | Model | ID | Context |
|------|-------|----|---------|
| 1 | GPT-5.4 | `69b7e5f1b2fe44704ab0e7d0` | 1M |
| 2 | GPT-4.1 Nano | `67fd9e2bef0365783d06e2f0` | 1M |
| 3 | Claude Opus 4.6 | `698c87701239a117fd66b468` | 200K |
| 4 | Gemini 3.1 Pro | `6999aedf6103733bc067e0b2` | 1M |
| 5 | GPT-5 Nano | `6895d70ed50c89537c1cf238` | 1M |
| 6 | Qwen3 32B | `6810d0f4a289e15e3e5dd143` | 128K |
| 7 | GPT-4o | `6646261c6eb563165658bbb1` | 128K |
| 8 | Claude 3.5 Sonnet v2 | `671be4c46eb563a2736ded61` | 200K |
| 9 | Gemini 2.0 Flash | `6759db476eb56303857a07c1` | 1M |
| 10 | Llama 3.1 70B | `671932146eb5638ce20300a1` | 128K |

---

## Top 10 Connectors (Integrations)

| Rank | Integration | ID |
|------|-------------|----|
| 1 | Slack | `686432941223092cb4294d3f` |
| 2 | Gmail | `6864328d1223092cb4294d30` |
| 3 | GitHub | `6864328f1223092cb4294d33` |
| 4 | Notion | `686432921223092cb4294d39` |
| 5 | Google Sheets | `686432931223092cb4294d3c` |
| 6 | Google Drive | `6864329b1223092cb4294d4e` |
| 7 | Jira | `686432a31223092cb4294d60` |
| 8 | HubSpot | `6864329e1223092cb4294d54` |
| 9 | Confluence | `686432cf1223092cb4294ddb` |
| 10 | Salesforce | `686432bb1223092cb4294da2` |

---

## Core Integrations (Pinned)

| Integration | ID |
|-------------|----|
| PostgreSQL | `693ac6e8217c7b13b480970f` |
| aiR Knowledge Base | `6904bcf672a6e36b68bb72fb` |
| SQLite Database | `689e06ed3ce71f58d73cc999` |
| Python Sandbox | `688779d8bfb8e46c273982ca` |
| MCP Server | `686eb9cd26480723d0634d3e` |

---

## Core Tools (Pinned)

| Tool | ID |
|------|----|
| Google Search API | `692f18557b2cc45d29150cb0` |
| Firecrawl API | `69442021f2e6cb73e286ff0f` |
| Tavily Web Search | `6931bdf462eb386b7158def3` |
| Docling Document Parser | `6944350ff2e6cb73e286ff20` |

---

## Utilities

| Utility | ID / Instance |
|---------|--------------|
| Code Execution | `698cda188bbb345db14ac13b` |
| Scrape Website Tool | `crew-ai/scrape-website-tool/crew-ai` |
| Text File Reader | `aixplain/text-file-reader/aixplain` |
| Places API | `google/places-api/google` |
| Current Weather Data | `openweathermap/current-weather-data/openweathermap` |
| YouTube Data API v3 | `google/youtube-data-api-v3/google` |
| Wikimedia API | `wikimedia/wikimedia-api/wikimedia` |

---

## SQLite Integration Notes

- Integration ID: `689e06ed3ce71f58d73cc999`
- Valid actions: `query`, `commit`, `schema`
- Action input shape: each action expects a required `query` text input
- Connection: pass a `.db` file URL as `{"url": "<download_url_to_db_file>"}`
- File requirement: SQLite connect rejects non-`.db` file types
- Read-only scope: `allowed_actions=["query", "schema"]` (omit `commit`)
