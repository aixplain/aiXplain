# الأدوات والتكاملات

الأدوات هي ما يستدعيه الوكيل لينفّذ إجراءً ما. وهي ثلاثة أنواع:

1. **أدوات السوق (Marketplace tools)** — جاهزة مسبقًا (البحث على الويب، كشط المحتوى، تحليل ملفات PDF). تُجلب عبر `aix.Tool.get(path|id)`.
2. **التكاملات (Integrations)** — تربط الأنظمة الخارجية (Slack، Gmail، قواعد البيانات، خوادم MCP). تُنشأ عبر `aix.Tool(integration=..., config=...)`.
3. **Python Sandbox** — لتغليف دالة Python الخاصة بك كأداة تعمل في بيئة معزولة.

يمكن للنماذج أيضًا أن تعمل كأدوات عبر `model.as_tool()` (انظر `references/models.md`).

## القاعدة الذهبية: حدِّد نطاق `allowed_actions`

الأداة القادمة من `.get()` تكشف **جميع** إجراءاتها افتراضيًا — وهذا امتياز زائد عن الحاجة ويُضعف قدرة الوكيل على الاستدلال. قلِّص النطاق دائمًا إلى الحد الأدنى الذي تحتاجه المهمة قبل الربط:

```python
tool = aix.Tool.get("<id>")
print(tool.list_actions())                 # discover available actions
tool.allowed_actions = ["search", "get"]   # scope to task
```

ضبط `allowed_actions = None` أو `[]` يكشف كل شيء — لا تفعل ذلك إلا عن قصد، وأبلغ المستخدم به.

### تعبئة وسائط الإجراء مسبقًا (`.actions` / `.inputs`)

ثبِّت وسائط الإجراء وقت البناء حتى لا يضطر الوكيل إلى تزويدها. الوصول عبر `tool.actions[...]` غير حسّاس لحالة الأحرف، والقيم تقيم في تخطيط **`.inputs`** الخاص بالإجراء:

```python
tool.actions['SLACK_SEND_MESSAGE'].inputs.channel = '#general'    # dot notation
tool.actions['SLACK_SEND_MESSAGE'].inputs['text'] = 'Hello'       # item notation
tool.actions['SLACK_SEND_MESSAGE'].inputs.update(channel='#general', text='Hello')   # kwargs only

tool.set_inputs({                                   # bulk, across several actions
    'SLACK_SEND_MESSAGE': {'channel': '#general', 'text': 'Hello'},
    'SLACK_UPLOAD_FILE':  {'channels': '#general'},
})

inputs = tool.actions['SLACK_SEND_MESSAGE'].inputs
print(inputs.keys(), inputs.required)               # introspect the schema
inputs['channel'].reset()                           # clear one
inputs.reset()                                      # clear all
```

> اضبط القيمة على `.inputs`، **لا** على الإجراء نفسه — فـ `tool.actions['X'].channel = '…'` يضبط سمة شاردة بصمت ويُتجاهَل، بينما `tool.actions['X']['text'] = …` يرفع `TypeError`. كائنات `Integration` تحمل الوسيط `.actions` نفسه ودالة `set_inputs()`. ولا تزال `tool.list_inputs(*actions)` موجودة لكنها **مهمَلة** لصالح `.actions[...].inputs`. أما النماذج فليس لديها `.actions` — إذ تستخدم `model.inputs` مباشرةً.

## أدوات السوق

```python
tool = aix.Tool.get("tavily/tavily-search-api")     # by path
tool = aix.Tool.get("6931bdf462eb386b7158def3")     # by ID

# Test before attaching (optional)
print(tool.run({"query": "AI news today", "num_results": 2}).data)

results = aix.Tool.search(query="web search").results   # discover by keyword
```

## البحث في السوق من داخل الـ SDK

تتيح لك كلٌّ من `aix.Tool.search(...)` و`aix.Model.search(...)` و`aix.Integration.search()["results"]` العثور على الأصول. **ابحث دائمًا قبل أن تقول إن شيئًا غير متوفّر، وقبل أن تُضمِّن معرّفًا ثابتًا في الشيفرة.** قد تأتي أسماء الأصول ملتصقة (مثل "Googledrive") — فطبِّع الاسم قبل المقارنة.

## صيغ استدعاء `tool.run(...)`

```python
tool.run(data={"a": 4, "b": 6}, action="add_numbers")          # data + explicit action
tool.run({"text": "Hi", "channel": "x"}, action="SLACK_...")    # positional data
tool.run({"text": "Hi", "channel": "x"})                        # implicit (only if ONE allowed_action)
tool.run(action="query", data="SELECT * FROM products")         # data as plain string (SQL tools)
```

اقرأ النتيجة عبر `result.data`. وإذا كانت هناك عدة إجراءات مسموح بها وأغفلت `action`، فسيقع خطأ.

## التكاملات — ربط الأنظمة الخارجية

```python
integration = aix.Integration.get("composio/gmail")    # or by ID
integration.list_actions()                              # discover action names
```

ثم أنشئ أداة موصولة عبر `aix.Tool(integration=..., config=...)` و`.save()`. يقبل الحقل `integration=` معرّفًا، أو مسارًا (`"composio/slack"`، `"aixplain/postgresql"`)، أو كائن `Integration`.

### مخطّطات المصادقة

| المخطّط | طريقة الاتصال | حمولة `config` |
|---|---|---|
| OAuth2 / OAuth1 | إعادة توجيه عبر المتصفح | لا شيء — التخويل يتم في المتصفح (انظر أدناه) |
| مفتاح API | عبر الـ SDK | `{"api_key": "..."}` (بعضها يستخدم `{"token": "..."}`) |
| رمز Bearer | عبر الـ SDK | `{"token": "..."}` |
| Basic | عبر الـ SDK | `{"username": "...", "password": "..."}` |
| بلا مصادقة | عبر الـ SDK | لا شيء |

أسماء حقول بيانات الاعتماد الدقيقة تختلف حسب كل تكامل — تحقّق منها في Studio ← Discover ← Integrations، أو اسأل المستخدم. لا تختلق أبدًا بيانات اعتماد بديلة.

### سير عمل OAuth (Gmail، Slack، Jira، Google Drive…)

حفظ أداة OAuth يُرجع `redirect_url`. وعلى المستخدم فتحه ومنح التخويل قبل أن تعمل الأداة:

```python
gmail_tool = aix.Tool(name="Gmail Tool", description="Reads and sends email.",
                      integration="composio/gmail")
gmail_tool.save()
print(gmail_tool.redirect_url)   # -> user opens this, completes OAuth
gmail_tool.allowed_actions = ["GMAIL_SEND_EMAIL"]
```

في بعض إصدارات الـ SDK يصدر رابط إعادة التوجيه على هيئة **تحذير (warning)** عند `save()` بدلًا من `tool.redirect_url` (أو إضافةً إليه). التقطه بطريقة متينة كما يلي — حدِّد نطاق `allowed_actions` في الباني، ثم سلِّم الرابط للمستخدم:

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

### التكامل بمفتاح API (دون متصفح)

```python
slack_tool = aix.Tool(name="Slack Notifier", description="Sends Slack messages.",
                      integration="composio/slack", config={"token": "YOUR_SLACK_TOKEN"})
slack_tool.allowed_actions = ["SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL"]
slack_tool.save()
slack_tool.run({"text": "Hello :)", "channel": "general"},
               action="SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL")
```

تغطي التكاملات التجارية أكثر من 230 خدمة عبر Composio: التواصل (Slack، Teams، Discord)، وإدارة علاقات العملاء (Salesforce، HubSpot)، وإدارة المشاريع (Jira، Asana، Trello)، والتخزين (S3، Google Drive، Dropbox)، وقواعد البيانات، والتقاويم.

## Python Sandbox — تغليف دالة Python

معرّف التكامل هو `688779d8bfb8e46c273982ca`. وإعداد `config` هو `{"code": <source string>, "function_name": <name>}`. يُستنتج المخطّط من تلميحات الأنواع حين توجد — لم تعد مفروضة، لكن من دونها يتدهور المخطّط المستنتج، فداوم على كتابتها.

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

كما أن `code=` معامل من الدرجة الأولى في الباني، وليس مجرد مفتاح داخل `config` — وهو مفيد لدالة عابرة:

```python
tool = aix.Tool(integration="688779d8bfb8e46c273982ca", code="def run(data): return data")
```

جرى **تخفيف** معظم قواعد التأليف القديمة — فعمليات الاستيراد في المستوى الأعلى، وغياب تلميحات الأنواع، وتوقيعات `def` الممتدة على عدة أسطر، وأسماء المعاملات القصيرة، والقيم الافتراضية، والدوال المساعِدة داخل المصدر نفسه، والدوال عديمة الوسائط — كلها تعمل الآن. ولم يبقَ سوى قيدين صارمين:

- **لا معاملات من نوع `bool`** — إذ يُصدر المسلسِل القيمتين `true`/`false` بأحرف صغيرة ← `NameError: name 'true' is not defined`. استخدم `int` (`0`/`1`) وحوِّل النوع داخل الدالة.
- **تجنّب إرجاع الـ tuple / فك التعبئة متعدد القيم** — فالـ tuple يعود ممثّلًا بسلسلته النصية (`"(2, 3)"`) لا كبيانات مُهيكَلة. لم يعد يسبب خطأً، بل يتدهور بصمت. أرجِع `dict` أو `list`.

ولا يزال صحيحًا كذلك:
- يجب أن تكون القيم المُرجَعة قابلة للتسلسل بصيغة JSON (قواميس، قوائم، سلاسل نصية، أرقام).
- يجب أن يطابق `function_name` تمامًا دالةً معرَّفة في `code`. ولا مانع من وجود دوال مساعِدة إلى جانبها — فالمسجَّلة هي المسمّاة فقط.
- المكتبة القياسية والحزم الشائعة التوفّر فقط؛ أي استيراد غير متاح يرفع `ImportError` وقت الاستدعاء.
- تحتاج `inspect.getsource()` إلى أن تكون الدالة معرَّفة في ملف أو خلية دفتر (لا في REPL مجرّد). ويمكنك أيضًا قراءة المصدر من ملف: `config={"code": open("fn.py").read(), ...}`.

### Code Execution مقابل Python Sandbox

طريقتان لمنح الوكيل قدرات برمجية — والاختيار بينهما بحسب *متى* تُكتب الشيفرة:

- **Code Execution** (أداة السوق `698cda188bbb345db14ac13b`) — الوكيل **يكتب وينفّذ شيفرة Python اعتباطية وقت التشغيل** في بيئة سحابية معزولة وآمنة متصلة بالإنترنت. استخدمها للحسابات، وتحويل البيانات، والتصوير البياني، ومعالجة الملفات، والجلب من الروابط/واجهات الـ API. وينبغي للوكيل أن يستخدم `print()` للنتائج النهائية؛ وإن ولّد ملفات (رسومًا بيانية أو ملفات CSV) فعليه طباعة قائمة بيانات وصفية بصيغة JSON إلى stdout — `[{"name":"<display_name>","file":"<filename>"}]` — وإلا ضاعت الملفات بصمت. حُلَّ معرّفها عبر `aix.Tool.search(query="code execution")` — فالمعرّف أعلاه غير مُتحقَّق منه حتى 2026-09 (انظر جدول الأصول) — ثم حدِّد نطاق `allowed_actions`.
- **Python Sandbox** (التكامل `688779d8bfb8e46c273982ca`، أعلاه) — **دالة ثابتة تُؤلَّف وقت البناء**، لا تُكتب وقت التشغيل. استخدمها للأدوات الحتمية ذات المدخلات/المخرجات المعروفة حين لا تناسبك أي أداة من السوق.

> بمعزل عن ذلك، لدى `aix.Utility` (شيفرة المنفعة المخصّصة) قواعد تحليل خاصة بها وتتطلّب نقطة دخول `def main(...)` — لا تخلط بينها وبين تكامل Python Sandbox.

## خوادم MCP

### MCP البعيد (السحابي)

```python
mcp_tool = aix.Tool(integration="aixplain/mcp-server", name="Remote MCP Tool",
                    config={"url": "https://remote.mcpservers.org/fetch/mcp"})
mcp_tool.save()
mcp_tool.allowed_actions = ["fetch"]
print(mcp_tool.list_actions())
mcp_tool.run(data={"url": "https://www.aixplain.com"})
```

مفتاح الإعداد هو `"url"`. أما وسائط النقل فهي: HTTP (`.../mcp`، عديم الحالة) وSSE (`.../sse`، تدفّقي). التزم بنحو 10 إجراءات لكل خادم.

### MCP المحلي — للتثبيت داخل المؤسسة فقط (STDIO)

احزم خادم MCP في حاوية Docker، ثم نفّذ `docker save`/`docker load` على مضيف aiXplain داخل المؤسسة، ثم سجّله في `mcpservers.json`:

```json
{"mcpServers": {"math_tools": {"command": "docker", "args": ["run","-i","--rm","aixplain-mcp_math:1.0.1"]}}}
```

يُحمَّل تلقائيًا خلال نحو 30 ثانية.

## قواعد بيانات SQL

### SQLite — التكامل `689e06ed3ce71f58d73cc999`

ارفع ملف `.db` أولًا كمورد Resource (أبقِه أقل من 100 ميغابايت)، ثم وجّه الأداة إلى رابط المورد.

```python
import time
resource = aix.Resource(source="business.db", name=f"DB {int(time.time())}")
resource.save()                                # uploads to S3, sets resource.url
sqlite_tool = aix.Tool(name="Business Database", description="Company sales data.",
                       integration="689e06ed3ce71f58d73cc999", config={"url": resource.url})
sqlite_tool.save()
sqlite_tool.list_actions()                     # query, commit, schema
sqlite_tool.run(action="query", data="SELECT * FROM products")
```

عمليات الكتابة تُطبَّق على نسخة في الذاكرة و**لا** تُحفَظ بشكل دائم — أعد الرفع للإبقاء عليها. ويقبل `data` إما سلسلة SQL مجرّدة أو `{"query": "..."}` (والأمر نفسه ينطبق على PostgreSQL).

**توقيع `aix.Resource` — `(source=None, name=None, is_temp=True, **kwargs)`.** وهو الآن صنف فرعي من `aixplain.v2.file.File`، وهو ما يغيّر أمرين:

- **`name` يشغل الموضع الترتيبي الثاني.** الترتيب الترتيبي القديم ينهار: فـ `aix.Resource("DB", "business.db")` صار يضبط `source="DB"` ويرفع خطأً. مرِّر `source=`/`name=` بالكلمات المفتاحية دائمًا.
- **`file_path` خاصية للقراءة فقط** — والإسناد إليها بعد الإنشاء يرفع `AttributeError`. ولا تزال الكلمة المفتاحية `file_path=` تعمل عند الإنشاء بوصفها اسمًا مستعارًا مهمَلًا للتوافق (وأمثلة SQLite في التوثيق نفسه لا تزال تستخدمها)، لكن اكتب الشيفرة الجديدة بـ `source=`.

يقبل `source` أيضًا **رابط HTTP(S)** (ويُستنتج الاسم من مسار الرابط؛ أما المخطّطات الأخرى فترفع `ValidationError: Unsupported File URL scheme`) أو **مجلدًا** (فتصير `is_dir` بقيمة `True`). والتحقّق فوري: فالمسار المفقود يرفع `ValidationError: File source does not exist: …` عند الإنشاء، قبل أي رفع، كما أن `aix.Resource()` بلا وسائط يرفع خطأً أيضًا.

### PostgreSQL — التكامل `aixplain/postgresql`

يتصل بقاعدة بيانات حية عبر سلسلة اتصال (دون رفع).

```python
pg = aix.Tool(name="Postgres Tool", integration="aixplain/postgresql",
              config={"url": "postgresql://user:password@host:5432/mydb"})
pg.save()
pg.list_actions()                              # schema, query
pg.run(action="query", data={"query": "SELECT * FROM customers LIMIT 3"})
```

استخدم بيانات اعتماد للقراءة فقط متى أمكن، وعزِّز مبدأ القراءة فقط في `instructions` الخاصة بالوكيل.

> **لا تستخدم `enable_commit`.** توصي نظرة التوثيق العامة بـ `enable_commit=False` لأدوات SQL للقراءة فقط، غير أنه **معامل خاص بـ `SQLTool` في الإصدار v1 فقط** — فهو ليس ضمن `aix.Tool.__init__` في 0.2.48 ولا يظهر في أي موضع من صفحات v2 الخاصة بـ SQLite أو PostgreSQL. إنفاذ القراءة فقط يكون على مستوى بيانات الاعتماد (مستخدم `readonly_user` في Postgres) إضافةً إلى مستوى التعليمات.

## أدوات المنفعة المدمجة (تُجلب بالمعرّف، بلا مصادقة)

| الأداة | المعرّف / المسار | الإجراءات الرئيسية |
|---|---|---|
| File Manager | `6a0216cffb2a801f1c41e32e` | `save_content`, `save_files` |
| Web Search | `6a0c9044beac0e7cdc60122a` · `aixplain/aixplain-web-search/aixplain` | `search` |
| Marketplace Search / Browse | `6960f934f316da19e5f22494` · `aixplain/aixplain-browse/aixplain` | `search`, `search_models`, `search_tools`, `search_agents`, `search_integrations`, `get_asset_details`, `list_filters` |

### File Manager

```python
fm = aix.Tool.get("6a0216cffb2a801f1c41e32e")
fm.run(action="save_content", data={"contents": ["report text"], "names": ["q3.txt"]})
fm.run(action="save_files", data={"urls": ["https://.../report.pdf"], "names": ["report.pdf"]})
# returns [{id, name, signedUrl}] — time-limited presigned download links
```

يتطلّب `save_content` وجود `contents` **و** `names` بالطول نفسه؛ ويقبل كلا الإجراءين قائمة `tags` اختيارية. وعند الإخفاق يعود العنصر حاملًا حقل `error` **بدلًا من** `id`/`signedUrl` — مثلًا `[{'url': ..., 'name': 'report.pdf', 'error': 'Failed to create file resource'}]`، وسبب ذلك عادةً رابط مصدر يتعذّر الوصول إليه. تحقّق على مستوى كل عنصر، لا على مستوى الاستدعاء وحده. وللمحتوى المولَّد وقت التشغيل استخدم `save_content` لا `save_files`.

### Web Search

استدعاء واحد يؤدي البحث والكشط المتوازي معًا، ويغني عن اقتران أداة بحث بأداة كشط.

| المدخل | مطلوب | الافتراضي | ما يتحكّم فيه |
|---|---|---|---|
| `query` | نعم | — | استعلام البحث |
| `num_results` | لا | `5` | أعلى N نتيجة تُجلب **وتُكشَط على التوازي** |
| `word_limit` | لا | `100` | أقصى عدد كلمات يُحتفظ به لكل صفحة مكشوطة (للتحكّم في الرموز) |
| `timeout` | لا | — | مهلة الكشط لكل رابط (بالثواني)؛ يُرجع ما اكتمل |
| `result_type` | لا | `answer` | `answer` = إجابة موثّقة يركّبها نموذج لغوي؛ `raw` = روابط ونص مكشوط نظيف، بلا خطوة نموذج لغوي |
| `search_asset_id` | لا | افتراضي المنصّة | المحرّك الأساسي (Google / Bing / DuckDuckGo) |
| `llm` | لا | — | أصل النموذج اللغوي المستخدَم في التركيب (وضع `answer`) |
| `max_answer_words` | لا | — | يحدّ من طول الإجابة المركَّبة |

اختر `answer` لأقل عدد من الأجزاء المتحركة؛ و`raw` حين يُراد للوكيل أن يقرأ المصادر ويستشهد بها بنفسه — وأبقِ `num_results`/`word_limit` معتدلَين في وضع `raw` كي لا تتضخّم الحمولات في سياق الوكيل.

### Marketplace Search

- الإجراء **`search`** وحده يُرجع `total` لكل نوع أصل (`{agent, model, tool, integration}`، ولكلٍّ منها `{items, total}`). أما إجراءات `search_models` / `search_tools` / `search_agents` / `search_integrations` فهي **محدودة بعشر نتائج ولا تدعم التصفّح بالصفحات** — استخدمها للأمثلة، لا للأعداد أبدًا.
- يتطلّب `search` وجود `query`؛ مرِّر `""` كحرف بدل حين تريد التصفية أو العد فقط.
- مرشّحات المصفوفات الاختيارية على `search` / `search_models` / `search_tools`: `categories` (LLM، Speech، Image، Video، OCR، Classification، Language)، و`developers`، و`suppliers`، و`hosts`، إضافةً إلى `function`.
- يأخذ `get_asset_details` المعامل **`assetId`** (لا `query`) ← `asset_type`، `function`، `supplier`، `hosted_by`، `developed_by`، `supports_streaming`، `pricing {price, unitType}`، `status`. ولا يأخذ `list_filters` أي بيانات.
- مطابقة الكلمات المفتاحية **حرفية** — أعد المحاولة برمز مميّز واحد قبل أن تستنتج أن الأصل غير موجود.

## ربط الأدوات بوكيل

```python
agent = aix.Agent(name="...", description="...", instructions="...", tools=[tool1, tool2])
agent.tools.append(another_tool)   # add later
agent.save()
```

يجب أن تكون أسماء الأدوات فريدة داخل كل وكيل (`Duplicate tool names found: [Tool Name]. Make sure all tool names are unique.`). وللفحص استخدم `tool.name` و`tool.description` و`tool.status` و`tool.id`.

## مُطلِقات الأحداث — الخطّافات من جهة الأداة

يمكن للتكامل أن يكشف أحداثًا ينطلق الوكيل عندها (رسالة بريد جديدة، ملف جديد). والاكتشاف يقيم على الأداة/التكامل:

```python
integration.list_trigger_types()      # -> List[TriggerTypeSpec]; also on Tool
list(integration.triggers)            # discovery only: ['NEW_EMAIL', 'NEW_LABELED_EMAIL', ...]
tool.triggers["NEW_EMAIL"]            # -> TriggerEventOption, case-insensitive; needs a CONNECTED tool
```

مرِّر ذلك الخيار بوصفه `event=` إلى `aix.Trigger`. **انظر `references/agents.md` للاطلاع على واجهة Trigger كاملة** (المُطلِقات الزمنية والحدثية، والجداول، والحفظ/الإيقاف المؤقت/الحذف).

## معرّفات الأصول الشائعة

| النوع | الاسم | المعرّف / المسار |
|------|------|----|
| Tool | Tavily Web Search | `tavily/tavily-search-api` · `6931bdf462eb386b7158def3` |
| Tool | Web Search | `6a0c9044beac0e7cdc60122a` · `aixplain/aixplain-web-search/aixplain` |
| Tool | Marketplace Search / Browse | `6960f934f316da19e5f22494` · `aixplain/aixplain-browse/aixplain` |
| Tool | File Manager | `6a0216cffb2a801f1c41e32e` |
| Tool | Scrape Website Tool | `69443180f2e6cb73e286ff16` · `crewai/scrape-website-tool/aixplain` |
| Tool | Code Execution (runtime Python) | `698cda188bbb345db14ac13b` ⚠️ |
| Tool | Google Search API | `692f18557b2cc45d29150cb0` ⚠️ |
| Tool | Firecrawl API (scrape) | `69442021f2e6cb73e286ff0f` ⚠️ |
| Tool | Docling Document Parser | `6944350ff2e6cb73e286ff20` ⚠️ |
| Model | GPT-5 Mini (default memory manager) | `6895d6d1d50c89537c1cf237` |
| Model | text-embedding-3-large | `699de0ad8be7bf2a80e80234` · `openai/text-embedding-3-large/openai` |
| Model | text-embedding-3-small | `699de0218be7bf2a80e80233` · `openai/text-embedding-3-small/openai` |
| Model | text-embedding-ada-002 | `6734c55df127847059324d9e` · `openai/text-embedding-ada-002/openai` |
| Integration | aiR Knowledge Base (vector DB) | `6904bcf672a6e36b68bb72fb` |
| Integration | Python Sandbox / Script | `688779d8bfb8e46c273982ca` |
| Integration | SQLite | `689e06ed3ce71f58d73cc999` |
| Integration | PostgreSQL | `aixplain/postgresql` · `693ac6e8217c7b13b480970f` ⚠️ |
| Integration | Remote MCP Server | `aixplain/mcp-server` |
| Integration | Shared Memory | `aixplain/shared-memory/aixplain` · `69a59de88e25a303cbf1b8c6` |
| Integration | Slack (Composio) | `composio/slack` · `686432941223092cb4294d3f` |
| Integration | Gmail (Composio) | `composio/gmail` · `6864328d1223092cb4294d30` |
| Integration | Google Drive | `6864329b1223092cb4294d4e` |
| Integration | Google Sheets | `686432931223092cb4294d3c` |
| Integration | Google Docs | `6864329c1223092cb4294d51` |
| Integration | Google Calendar | `686432901223092cb4294d36` |

> ⚠️ **غير مُتحقَّق منها حتى 2026-09** — هذه المعرّفات لا تظهر في أي موضع من شجرة التوثيق الحالية وقد تكون قديمة. أُبقيت لأن لا شيء يناقضها، لكن **حلَّها عبر `aix.Tool.search(query="…")` قبل الاستخدام** بدل تضمينها ثابتةً في الشيفرة. (لا تزال Code Execution مذكورة في النص بوصفها قدرة، فالأداة موجودة؛ والمعرّف وحده هو غير المؤكَّد.)
>
> المعرّفات تتغيّر مع الوقت. عامِل هذا الجدول كله كنقطة انطلاق وتحقّق عبر `aix.*.search(...)` / `.get(...)`. وإذا أعاد معرّف ما الخطأ 404، فابحث عن الأصل بالاسم بدلًا من ذلك. المعرّف `6736411cf127849667606689` صار الآن **"Tavily Web Search (Legacy)"** — لا تستخدمه لأدوات جديدة.
