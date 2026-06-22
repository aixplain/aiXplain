---
name: aixplain-agent-builder
description: A skill to build, deploy, and run production-grade AI agents on aiXplain.
metadata: {"requires": {"env": ["AIXPLAIN_API_KEY"], "bins": ["python3", "pip"]}}
---

# aiXplain Agent Builder

بناء ونشر وتشغيل وإدارة وكلاء aiXplain — الوكلاء المنفردون، وكلاء الفريق، الأدوات، وتكاملات OAuth.

## كيف يعمل

تقبل هذه المهارة الأوامر التالية:

- **بناء وكيل** — التخطيط، والبحث عن الأدوات، وإنشاء الأدوات، وتجميع الوكيل وحفظه
- **نشر وكيل** — الحفظ ومشاركة روابط Studio للتحرير المرئي والتحليلات
- **تشغيل وكيل** — التنفيذ المتزامن أو غير المتزامن وإرجاع المخرج
- **تصحيح أخطاء وكيل** — تشخيص مشاكل الأدوات أو الإجراءات أو OAuth أو وقت التشغيل
- **تصدير وكيل** — إنشاء سكريبت Python مستقل من وكيل منشور

## 1. الإعداد

قم دائمًا بتثبيت/ترقية أحدث إصدار من SDK قبل القيام بأي شيء: `pip install --upgrade aixplain`.

هذه المهارة مُتحقق منها مقابل **SDK v0.2.44**. إذا اختلف الإصدار المُثبَّت، أبلغ المستخدم.

```python
import os
from pathlib import Path
from dotenv import load_dotenv
from aixplain import Aixplain

env_path = Path(".env")
if env_path.exists():
    load_dotenv(env_path)
else:
    env_path.write_text("# Get your key from https://platform.aixplain.com → Settings → API Keys\nAIXPLAIN_API_KEY=\n")
    print(f"Created {env_path.resolve()} — paste your API key, then re-run.")
    raise SystemExit(1)

api_key = os.getenv("AIXPLAIN_API_KEY") or os.getenv("AIXPLAIN_KEY_NUR")
if not api_key:
    print(f"No API key found. Open {env_path.resolve()} and paste your key.")
    raise SystemExit(1)

os.environ["AIXPLAIN_API_KEY"] = api_key
aix = Aixplain(api_key=api_key)
```

## 2. التخطيط

قبل البناء، قدِّم خطة للمستخدم تتضمن: اسم الوكيل، والوصف، والتعليمات، والأدوات/التكاملات المستخدمة، وما إذا كان وكيلًا منفردًا أو وكيل فريق. انتظر الموافقة قبل المتابعة.

**ابحث دائمًا قبل إنشاء أو ترميز أداة أو تكامل بشكل ثابت.** كل من `Tool` و`Model` و`Integration` تدعم `.search(query=...).results`. لا تقل أبدًا "غير متاح" دون البحث أولًا.

```python
results = aix.Tool.search(query="web search").results
# Names may be concatenated (e.g. "Googledrive"). Normalize before comparing.
```

إذا لم يتوفر أداة أو تكامل في السوق للقدرة المطلوبة، أعلن أنك ستبنيها كدالة **Python Sandbox** (انظر `references/integration-playbooks.md § 4`).

## 3. إنشاء الأدوات

ثلاثة مسارات، بترتيب الأفضلية:

```python
# Path A: Marketplace tool by ID
tool = aix.Tool.get("698cda188bbb345db14ac13b")  # Code Execution

# Path B: Non-OAuth integration (KB, SQLite)
# READ references/integration-playbooks.md for config payloads.
# Ask the user for any missing inputs — never invent placeholders.
# Always create fresh; do not reuse by name unless explicitly asked.
tool = aix.Tool(name="KB Search", description="Search product docs",
    integration="6904bcf672a6e36b68bb72fb", allowed_actions=["search", "get"]).save()

# Path C: OAuth integration (Gmail, Slack, Jira, Google Drive)
# READ references/integration-playbooks.md § 5 for full workflow.
# (1) integration = aix.Integration.get("<ID>")
# (2) integration.list_actions() → discover action names
# (3) Create tool with allowed_actions in constructor
# (4) User completes OAuth via redirect URL emitted at .save()
# (5) Attach in-memory tool object to agent and save

# Path D: Python Sandbox (last resort)
# READ references/integration-playbooks.md § 4 for config shape.
```

## 4. بناء الوكيل

يستخدم الوكلاء نموذج LLM الافتراضي للمنصة — لا تحدد `llm` إلا إذا طلب المستخدم نموذجًا معينًا.

```python
agent = aix.Agent(
    name="My Agent", description="...", instructions="...",
    tools=[tool], output_format="markdown",
).save()
```

إذا أثار `save()` خطأ `name_already_exists`، اسأل المستخدم: تحديث الوكيل الحالي أو الإنشاء باسم جديد.

## 5. النشر والتشغيل

بعد النشر، شارك هذه الروابط مع المستخدم:
- **المُنشئ المرئي:** `https://studio.aixplain.com/build/<AGENT_ID>/schema`
- **التحليلات:** `https://studio.aixplain.com/dashboard/analytics/?agent=<AGENT_ID>`

```python
# Sync
result = agent.run(query="...", executionParams={"maxTokens": 6000}, runResponseGeneration=True)
print(result.data.output)

# Async polling
import requests, time
ar = agent.run_async(query="...")
for _ in range(30):
    time.sleep(10)
    raw = requests.get(ar.url, headers={"x-api-key": api_key}).json()
    if raw.get("status", "").upper() in ("SUCCESS", "FAILED"):
        print(raw["data"]["output"]); break
```

## 6. تصحيح الأخطاء

### فحص الخطوات الوسيطة

```python
result = agent.run(query="...")

# Step-by-step trace: thought, action, tool used, input/output, tokens
for step in result.data.steps:
    print(step['thought'], step['action'], step['unit']['name'])

# Aggregate costs and timing
stats = result.data.execution_stats
print(stats['credits'], stats['runtime'], stats['api_calls'])
```

أو اعرض التتبعات بصريًا في Studio: `https://studio.aixplain.com/build/<AGENT_ID>/schema`

## معرّفات الأصول السريعة

| النوع | الاسم | المعرّف |
|------|------|---------|
| أداة | Tavily Web Search | `6931bdf462eb386b7158def3` |
| أداة | Code Execution | `698cda188bbb345db14ac13b` |
| أداة | Google Search API | `692f18557b2cc45d29150cb0` |
| أداة | Firecrawl API | `69442021f2e6cb73e286ff0f` |
| أداة | Docling Document Parser | `6944350ff2e6cb73e286ff20` |
| تكامل | Gmail | `6864328d1223092cb4294d30` |
| تكامل | Slack | `686432941223092cb4294d3f` |
| تكامل | Google Drive | `6864329b1223092cb4294d4e` |
| تكامل | Google Sheets | `686432931223092cb4294d3c` |
| تكامل | Google Docs | `6864329c1223092cb4294d51` |
| تكامل | Google Calendar | `686432901223092cb4294d36` |
| تكامل | aiR Knowledge Base | `6904bcf672a6e36b68bb72fb` |
| تكامل | PostgreSQL | `693ac6e8217c7b13b480970f` |
| تكامل | SQLite | `689e06ed3ce71f58d73cc999` |
| تكامل | Python Sandbox | `688779d8bfb8e46c273982ca` |

## الملفات المرجعية

- `references/integration-playbooks.md` — حمولات التهيئة، ورفع الملفات، وقيود التأليف، وسير عمل OAuth لجميع أنواع التكاملات
- `references/agent-patterns.md` — وكلاء الفريق، وتحديث الوكلاء المنشورين، والمراقبون، والتصدير إلى Python، وCode Execution مقابل Python Sandbox
- `references/inspector-analytics.md` — سياسات المراقب ومخطط التحليلات

## الروابط الخارجية

- **التوثيق:** https://docs.aixplain.com
- **الأسعار:** https://aixplain.com/pricing
- **Studio:** https://studio.aixplain.com

<!-- ملاحظات الترجمة: [kept EN: YAML front matter fields (name, description, metadata) — machine-parsed keys] | [kept EN: tool/integration names in table — brand/product identifiers] | [kept EN: OAuth, SDK, API, LLM, Studio — untranslatable brand/technical terms per rules] | [used السوق for Marketplace per glossary] | [used وكيل الفريق for Team Agent per glossary] | [used غير متزامن/متزامن for Async/Sync per glossary] -->
