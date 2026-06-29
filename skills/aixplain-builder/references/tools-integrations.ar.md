# الأدوات والتكاملات

الأدوات هي ما يستدعيه الوكيل لتنفيذ الإجراءات. هناك ثلاثة أنواع:

1. **أدوات السوق (Marketplace tools)** — جاهزة مسبقًا (البحث على الويب، الكشط، تحليل ملفات PDF). يتم جلبها عبر `aix.Tool.get(path|id)`.
2. **التكاملات (Integrations)** — تربط الأنظمة الخارجية (Slack، Gmail، قواعد البيانات، خوادم MCP). يتم إنشاؤها عبر `aix.Tool(integration=..., config=...)`.
3. **Python Sandbox** — تغليف دالة Python خاصة بك كأداة معزولة (sandboxed).

يمكن للنماذج أيضًا أن تعمل كأدوات عبر `model.as_tool()` (راجع `references/models.md`).

## القاعدة الذهبية: حدِّد نطاق `allowed_actions`

تعرض الأداة المُستخرجة عبر `.get()` **جميع** إجراءاتها افتراضيًا — وهذا يمنح امتيازات زائدة عن الحاجة ويُضعف قدرة الوكيل على الاستدلال. قلِّص الإجراءات دائمًا إلى الحد الأدنى الذي تحتاجه المهمة قبل الإرفاق:

```python
tool = aix.Tool.get("<id>")
print(tool.list_actions())                 # discover available actions
tool.allowed_actions = ["search", "get"]   # scope to task
```

تعيين `allowed_actions = None` أو `[]` يعرض كل شيء — لا تفعل ذلك إلا عن قصد، وأبلغ المستخدم بذلك.

## أدوات السوق (Marketplace tools)

```python
tool = aix.Tool.get("tavily/tavily-search-api")     # by path
tool = aix.Tool.get("6931bdf462eb386b7158def3")     # by ID

# Test before attaching (optional)
print(tool.run({"query": "AI news today", "num_results": 2}).data)

results = aix.Tool.search(query="web search").results   # discover by keyword
```

## البحث في السوق من خلال الـ SDK

تتيح لك كل من `aix.Tool.search(...)` و`aix.Model.search(...)` و`aix.Integration.search()["results"]` العثور على الأصول. **ابحث دائمًا قبل القول بأن شيئًا ما غير متاح، وقبل ترميز أي معرّف (ID) بشكل ثابت.** قد تكون أسماء الأصول متصلة (مثل "Googledrive") — قم بتطبيعها (normalize) قبل المقارنة.

## أشكال استدعاء `tool.run(...)`

```python
tool.run(data={"a": 4, "b": 6}, action="add_numbers")          # data + explicit action
tool.run({"text": "Hi", "channel": "x"}, action="SLACK_...")    # positional data
tool.run({"text": "Hi", "channel": "x"})                        # implicit (only if ONE allowed_action)
tool.run(action="query", data="SELECT * FROM products")         # data as plain string (SQL tools)
```

اقرأ النتيجة عبر `result.data`. إذا كان هناك أكثر من إجراء مسموح به وأغفلت تحديد `action`، فسيحدث خطأ.

## التكاملات — ربط الأنظمة الخارجية

```python
integration = aix.Integration.get("composio/gmail")    # or by ID
integration.list_actions()                              # discover action names
```

ثم أنشئ أداة متصلة عبر `aix.Tool(integration=..., config=...)` و`.save()`. يقبل الحقل `integration=` معرّفًا (ID)، أو مسارًا (`"composio/slack"`، `"aixplain/postgresql"`)، أو كائن `Integration`.

### أنظمة المصادقة

| النظام | كيفية الاتصال | حمولة `config` |
|---|---|---|
| OAuth2 / OAuth1 | إعادة التوجيه عبر المتصفح | لا شيء — التفويض يتم في المتصفح (انظر أدناه) |
| API key | SDK | `{"api_key": "..."}` (بعضها يستخدم `{"token": "..."}`) |
| Bearer token | SDK | `{"token": "..."}` |
| Basic | SDK | `{"username": "...", "password": "..."}` |
| No auth | SDK | لا شيء |

أسماء حقول بيانات الاعتماد الدقيقة تختلف حسب كل تكامل — تأكّد منها في Studio → Discover → Integrations، أو اسأل المستخدم. لا تخترع بيانات اعتماد وهمية أبدًا.

### سير عمل OAuth (Gmail، Slack، Jira، Google Drive…)

يؤدي حفظ أداة OAuth إلى إرجاع `redirect_url`. يجب على المستخدم فتحه والتفويض قبل أن تعمل الأداة:

```python
gmail_tool = aix.Tool(name="Gmail Tool", description="Reads and sends email.",
                      integration="composio/gmail")
gmail_tool.save()
print(gmail_tool.redirect_url)   # -> user opens this, completes OAuth
gmail_tool.allowed_actions = ["GMAIL_SEND_EMAIL"]
```

في بعض إصدارات الـ SDK يُصدَر رابط إعادة التوجيه على هيئة **تحذير (warning)** عند استدعاء `save()` بدلًا من `tool.redirect_url` (أو بالإضافة إليه). التقطه بطريقة متينة كما يلي — حدِّد نطاق `allowed_actions` في المُنشئ (constructor)، ثم سلِّم الرابط للمستخدم:

```python
import warnings
integration = aix.Integration.get("6864328d1223092cb4294d30")   # Gmail (numeric id also works)
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    gmail_tool = aix.Tool(name="My Gmail Tool", description="Send emails.",
                          integration=integration, allowed_actions=["GMAIL_SEND_EMAIL"]).save()
    oauth_url = getattr(gmail_tool, "redirect_url", None) or \
                next((str(x.message) for x in w if "http" in str(x.message)), None)
print(f"Connect Gmail: {oauth_url}")     # user opens this, authorizes, then the tool is usable
agent = aix.Agent(name="Gmail Agent", instructions="Use Gmail to send emails.",
                  tools=[gmail_tool], output_format="markdown").save()
```

### تكامل بمفتاح API (بدون متصفح)

```python
slack_tool = aix.Tool(name="Slack Notifier", description="Sends Slack messages.",
                      integration="composio/slack", config={"token": "YOUR_SLACK_TOKEN"})
slack_tool.allowed_actions = ["SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL"]
slack_tool.save()
slack_tool.run({"text": "Hello :)", "channel": "general"},
               action="SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL")
```

تغطي التكاملات التجارية أكثر من 230 خدمة عبر Composio: التواصل (Slack، Teams، Discord)، إدارة علاقات العملاء CRM (Salesforce، HubSpot)، إدارة المشاريع PM (Jira، Asana، Trello)، التخزين (S3، Google Drive، Dropbox)، قواعد البيانات، التقويمات.

## Python Sandbox — تغليف دالة Python

معرّف التكامل `688779d8bfb8e46c273982ca`. الإعداد هو `{"code": <source string>, "function_name": <name>}`. يُستنتج مخطّط (schema) الدالة من تلميحات الأنواع (type hints).

```python
import inspect, time

def calculate_bmi(weight_kg: float, height_m: float) -> dict:
    """Calculate Body Mass Index."""
    bmi = weight_kg / (height_m ** 2)
    category = "underweight" if bmi < 18.5 else "normal" if bmi < 25 else "overweight" if bmi < 30 else "obese"
    return {"bmi": round(bmi, 2), "category": category}

bmi_tool = aix.Tool(
    name=f"BMI Tool {int(time.time())}",          # timestamp keeps the name unique
    integration="688779d8bfb8e46c273982ca",
    config={"code": inspect.getsource(calculate_bmi), "function_name": "calculate_bmi"},
)
bmi_tool.save()
print(bmi_tool.run(data={"weight_kg": 70, "height_m": 1.75}, action="calculate_bmi").data)
```

قيود الـ Sandbox (تجنّبها):
- **لا تستخدم معاملات من نوع `bool`** — يُصدِر المُسلسِل (serializer) القيمتين `true`/`false` بأحرف صغيرة → `NameError`. استخدم `int` (`0`/`1`).
- **لا تُرجع tuple / ولا تفكيك قيم متعددة (multi-value unpacking)** — أرجِع `dict` أو `list`. يجب أن تكون القيم المُرجَعة قابلة للتسلسل بصيغة JSON.
- يجب أن تكون عبارات الاستيراد (imports) **داخل جسم الدالة** (فهي تعمل في عزلة).
- يحتاج `inspect.getsource()` إلى أن تكون الدالة معرّفة في ملف أو خلية notebook (وليس في REPL مجرّد). يمكنك أيضًا قراءة المصدر من ملف: `config={"code": open("fn.py").read(), ...}`.
- المكتبة القياسية (stdlib) فقط بالإضافة إلى الحزم المتوفرة عادةً؛ يؤدي أي استيراد غير متاح إلى رفع `ImportError` وقت الاستدعاء.

### Code Execution مقابل Python Sandbox

طريقتان لمنح الوكيل قدرات برمجية — اختر بناءً على *متى* تُكتب الشيفرة:

- **Code Execution** (أداة السوق `698cda188bbb345db14ac13b`) — يقوم الوكيل بـ**كتابة وتشغيل شيفرة Python عشوائية في وقت التشغيل** داخل sandbox سحابي آمن مع وصول إلى الإنترنت. تُستخدم في الحسابات وتحويلات البيانات والرسوم البيانية ومعالجة الملفات والجلب من عناوين URL/واجهات API. ينبغي للوكيل أن ينفّذ `print()` للنتائج النهائية؛ وإذا أنشأ ملفات (رسوم بيانية، ملفات CSV)، فيجب أن يطبع قائمة بيانات وصفية بصيغة JSON إلى stdout — `[{"name":"<display_name>","file":"<filename>"}]` — وإلا ضاعت الملفات بصمت. أرفقها عبر `aix.Tool.get("698cda188bbb345db14ac13b")` وحدِّد نطاق `allowed_actions`.
- **Python Sandbox** (التكامل `688779d8bfb8e46c273982ca`، أعلاه) — **دالة ثابتة مُؤلَّفة في وقت البناء**، لا تُكتب في وقت التشغيل. تُستخدم للأدوات الحتمية ذات المدخلات/المخرجات المعروفة عندما لا تناسبها أي أداة سوق.

> بشكل منفصل، يمتلك `aix.Utility` (شيفرة الأداة المساعدة المخصّصة) قواعد محلِّل (parser) خاصة به ويتطلب نقطة دخول `def main(...)` — لا تخلط بينه وبين تكامل Python Sandbox.

## خوادم MCP

### MCP البعيد (سحابي)

```python
mcp_tool = aix.Tool(integration="aixplain/mcp-server", name="Remote MCP Tool",
                    config={"url": "https://remote.mcpservers.org/fetch/mcp"})
mcp_tool.save()
mcp_tool.allowed_actions = ["fetch"]
print(mcp_tool.list_actions())
mcp_tool.run(data={"url": "https://www.aixplain.com"})
```

مفتاح الإعداد هو `"url"`. وسائل النقل: HTTP (`.../mcp`، عديم الحالة stateless) و SSE (`.../sse`، تدفقي streaming). التزم بنحو 10 إجراءات لكل خادم.

### MCP المحلي — للبيئات المحلية (on-prem) فقط (STDIO)

احزم خادم MCP في صورة Docker، ثم نفّذ `docker save`/`docker load` على مضيف aiXplain المحلي (on-prem)، ثم سجّله في `mcpservers.json`:

```json
{"mcpServers": {"math_tools": {"command": "docker", "args": ["run","-i","--rm","aixplain-mcp_math:1.0.1"]}}}
```

يُحمَّل تلقائيًا خلال نحو 30 ثانية.

## قواعد بيانات SQL

### SQLite — التكامل `689e06ed3ce71f58d73cc999`

ارفع ملف `.db` كمورد (Resource) أولًا (أبقِه أقل من 100 ميغابايت)، ثم وجِّه الأداة إلى عنوان URL الخاص بالمورد.

```python
import time
resource = aix.Resource(name=f"DB {int(time.time())}", file_path="business.db")
resource.save()                                # uploads to S3, sets resource.url
sqlite_tool = aix.Tool(name="Business Database", description="Company sales data.",
                       integration="689e06ed3ce71f58d73cc999", config={"url": resource.url})
sqlite_tool.save()
sqlite_tool.list_actions()                     # query, commit, schema
sqlite_tool.run(action="query", data="SELECT * FROM products")
```

تُطبَّق عمليات الكتابة على نسخة في الذاكرة (in-memory) و**لا** تُحفَظ بشكل دائم — أعد الرفع للحفظ الدائم.

### PostgreSQL — التكامل `aixplain/postgresql`

يتصل بقاعدة بيانات حية عبر سلسلة اتصال (connection string) (دون رفع).

```python
pg = aix.Tool(name="Postgres Tool", integration="aixplain/postgresql",
              config={"url": "postgresql://user:password@host:5432/mydb"})
pg.save()
pg.list_actions()                              # schema, query
pg.run(action="query", data={"query": "SELECT * FROM customers LIMIT 3"})
```

استخدم بيانات اعتماد قاعدة بيانات للقراءة فقط (read-only) متى أمكن، وعزّز مبدأ القراءة فقط في `instructions` الخاصة بالوكيل.

## أدوات مساعدة مدمجة (تُجلب بالمعرّف، بدون مصادقة)

| الأداة | المعرّف (ID) | الإجراءات الرئيسية |
|---|---|---|
| File Manager | `6a0216cffb2a801f1c41e32e` | `save_content`, `save_files` |
| Web Search | `6a0c9044beac0e7cdc60122a` | `search` |
| Marketplace Search / Browse | `6960f934f316da19e5f22494` | `search`, `search_models`, `search_tools`, `search_agents`, `search_integrations`, `get_asset_details`, `list_filters` |

```python
fm = aix.Tool.get("6a0216cffb2a801f1c41e32e")
fm.run(action="save_content", data={"contents": ["report text"], "names": ["q3.txt"]})
fm.run(action="save_files", data={"urls": ["https://.../report.pdf"], "names": ["report.pdf"]})
# returns [{id, name, signedUrl}] — time-limited presigned download links
```

## إرفاق الأدوات بوكيل

```python
agent = aix.Agent(name="...", description="...", instructions="...", tools=[tool1, tool2])
agent.tools.append(another_tool)   # add later
agent.save()
```

يجب أن تكون أسماء الأدوات فريدة لكل وكيل (الأسماء المكررة → خطأ). افحص عبر `tool.name` و`tool.description` و`tool.status` و`tool.id`.

## معرّفات الأصول الشائعة

| النوع | الاسم | المعرّف / المسار |
|------|------|----|
| Tool | Tavily Web Search | `tavily/tavily-search-api` · `6931bdf462eb386b7158def3` |
| Tool | Code Execution (runtime Python) | `698cda188bbb345db14ac13b` |
| Tool | Google Search API | `692f18557b2cc45d29150cb0` |
| Tool | Firecrawl API (scrape) | `69442021f2e6cb73e286ff0f` |
| Tool | Docling Document Parser | `6944350ff2e6cb73e286ff20` |
| Integration | aiR Knowledge Base (vector DB) | `6904bcf672a6e36b68bb72fb` |
| Integration | Python Sandbox / Script | `688779d8bfb8e46c273982ca` |
| Integration | SQLite | `689e06ed3ce71f58d73cc999` |
| Integration | PostgreSQL | `aixplain/postgresql` · `693ac6e8217c7b13b480970f` |
| Integration | Remote MCP Server | `aixplain/mcp-server` |
| Integration | Shared Memory | `aixplain/shared-memory/aixplain` |
| Integration | Slack (Composio) | `composio/slack` · `686432941223092cb4294d3f` |
| Integration | Gmail (Composio) | `composio/gmail` · `6864328d1223092cb4294d30` |
| Integration | Google Drive | `6864329b1223092cb4294d4e` |
| Integration | Google Sheets | `686432931223092cb4294d3c` |
| Integration | Google Docs | `6864329c1223092cb4294d51` |
| Integration | Google Calendar | `686432901223092cb4294d36` |

> تتغير المعرّفات مع مرور الوقت. عامِل هذا الجدول كنقطة بداية وتحقّق عبر `aix.*.search(...)` / `.get(...)`. إذا أرجع أحد المعرّفات خطأ 404، فابحث عن الأصل بالاسم بدلًا من ذلك.
