# الوكلاء ووكلاء الفِرَق

[الإنشاء](#create-a-single-agent) · [دورة الحياة](#lifecycle) · [التشغيل](#run) · [الميزانية](#budget-cost--time--iteration-caps) · [الجلسات](#sessions-multi-turn-memory) · [المهارات](#skills) · [المُشغِّلات](#triggers-scheduled--event-driven-runs) · [الفِرَق](#team-agents-multi-agent) · [التحديث](#update-a-deployed-agent) · [معالجة المشكلات](#troubleshooting)

يُنفِّذ الوكيل حلقة **تخطيط ← تنفيذ ← ملاحظة ← تكرار**: يقرأ تعليماته، ويختار الأدوات، ويستدعي النماذج/الأدوات، ثم يُعيد نصًّا أو markdown أو JSON. و"وكيل الفريق" هو **الصنف `Agent` نفسه** — تمرير `agents=[...]` هو ما يجعله فريقًا. لا يوجد صنف `TeamAgent` منفصل.

## إنشاء وكيل مفرد

```python
agent = aix.Agent(
    name="Research Assistant",            # required; unique in your workspace
    description="Answers questions with research and citations",  # used to route work in teams
    instructions="Always cite sources. Be concise but thorough.",  # behaviour / system prompt
    tools=[search_tool],                  # optional
    output_format="text",                 # "text" (default) | "markdown" | "json"
)
agent.save()                              # DRAFT -> ONBOARDED (persistent endpoint)
print(agent.run(query="What is ML?").data.output)
```

مُعاملات المُنشئ (جميعها مُتحقَّق منها مقابل الـ SDK):

| المُعامل | القيمة الافتراضية | ملاحظات |
|---|---|---|
| `name` | — | إلزامي. إعادة استخدام اسمٍ ما تُطلق `name_already_exists`. |
| `description` | — | الغرض الظاهر للمستخدم؛ في الفِرَق يستخدمه المُخطِّط (Planner) لتوجيه العمل. |
| `instructions` | `None` | إرشادات داخلية لا تُعرَض على المستخدمين. تدعم `{{placeholders}}`. |
| `tools` | `[]` | أدوات المتجر، والنماذج كأدوات، والتكاملات، وأدوات فهرسة قواعد المعرفة. |
| `llm` | الافتراضي في المنصّة | كائن `Model` أو معرِّف/مسار نموذج. **لا تُمرِّره إلا إذا طلب المستخدم نموذجًا بعينه.** |
| `output_format` | `"text"` | `"text"` \| `"markdown"` \| `"json"`. |
| `expected_output` | `None` | مخطَّط (str/dict/نموذج Pydantic). إلزامي عندما يكون `output_format="json"`. |
| `agents` | `[]` | وكلاء فرعيون — تمرير هذا يجعله **فريقًا**. |
| `tasks` | `[]` | مهام سير العمل المُهيكَل (انظر قسم الفِرَق أدناه). |
| `inspectors` | `[]` | ضوابط أمان أثناء التشغيل (انظر `references/governance.md`). |
| `skills` | `[]` | كائنات `aix.Skill` أو معرِّفات — يجب استدعاء `save()` لكلٍّ منها أولًا (انظر المهارات). |
| `files` | `[]` | كائنات/قواميس/معرِّفات `aix.File` مرفقة بالوكيل بشكل دائم — يجب استدعاء `save()` لكلٍّ منها أولًا. |
| `budget` | `Budget(None, None, None)` | حدود التكلفة/المدّة/التكرارات. موجود دائمًا؛ كون القيم كلها `None` يعني عدم وجود أي إنفاذ. |
| `context_overflow_strategy` | `None` | `"truncate"` (افتراضي المحرّك) \| `"summarize"` — كيفية تقليم سياق العمل. |
| `planner` / `supervisor` / `response_generator` | `None` | تجاوزات نموذج اللغة للوكلاء الدقيقة الخاصة بالتنسيق. كائن `Model` أو نص معرِّف نموذج أو قاموس. (أُعيدت تسميتها من `planner_id` / `supervisor_id`؛ و`response_generator` جديد ويُسلسَل إلى مفتاح الإرسال `responder`.) |
| `max_iterations` | `None` | **مهجور.** تُدمج قيمة المُنشئ داخل `budget.max_iterations` مع إطلاق `DeprecationWarning`. |
| `max_tokens` | `2048` | يحدّ رموز **الإخراج**. |

`max_tokens` إعدادٌ على مستوى الوكيل: اضبطه في المُنشئ أو كسِمة، ثم استدعِ `save()`. تمريره إلى `run()` لا أثر له. أمّا حدّ حلقة الاستدلال فاستخدم له `agent.budget.max_iterations` — **إذ إن إسناد `agent.max_iterations` بعد الإنشاء لا يفعل شيئًا في صمت** (انظر الميزانية).

## دورة الحياة

| الحالة | المعنى |
|---|---|
| `DRAFT` | لم يُحفظ بعد. نقطة نهاية مؤقتة **تنتهي صلاحيتها خلال ٢٤ ساعة**. |
| `ONBOARDED` | محفوظ — نقطة نهاية دائمة ومُصدَّرة بإصدارات وجاهزة للإنتاج. |
| `DELETED` | محذوف. |

```python
agent.save()                       # promote DRAFT -> ONBOARDED
agent.description = "new purpose"   # mutate then re-save to persist
agent.save()
agent.delete()
```

`save()` هي خطوة النشر — لا توجد دالّة `agent.deploy()` منفصلة. بعد الحفظ، شارِك روابط Studio (انظر SKILL.md).

## التشغيل

```python
r = agent.run(query="Search for AI news")
r.data.output        # final answer
r.status             # "SUCCESS" | "FAILED" | "IN_PROGRESS"
r.completed          # bool
r.error_message      # None on success
r.used_credits       # float — NOTE: often 0.0 for agents; read cost from execution_stats instead
r.run_time           # seconds
r.request_id         # backend run id — quote this in support tickets
r.session_id         # set when the run went through a session
r.diagnostic_error_codes
r.data.artifacts     # files the run produced (id, name, mime_type, url, sha256, byte_size, …)
r.data.critiques     # inspector feedback
r.data.governance    # budget/policy verdict — see below
```

> للحصول على التكلفة الموثوقة للتشغيل، استخدم `r.data.execution_stats["credits"]` — فقيمة `r.used_credits` كثيرًا ما تكون `0.0` في تشغيلات الوكلاء.

مُعاملات مفيدة في `run()`: `query` (نص أو قاموس)، `session` (متعدّد الأدوار — كائن `Session` أو معرِّف جلسة)، `attachments` (روابط أو مسارات محلية؛ تُرفَع الملفات المحلية تلقائيًا)، `history` (قائمة من `{"role","content"}` لتهيئة السياق)، `variables` (قاموس يُستبدَل داخل `{{placeholders}}` في التعليمات/الوصف)، `run_response_generation` (اضبطه على `True` لإخراج JSON)، `execution_params` (تجاوزات لكل تشغيل، مثل `{"context_overflow_strategy": "truncate"}`)، `criteria`، `evolve`، `identifier`، `progress_format` (`"status"` \| `"logs"`)، `progress_verbosity` (١–٣)، `progress_truncate`، `run_retries` / `run_retry_wait` (محاولات إرسال إضافية؛ الإجمالي = 1 + n)، `timeout` (الافتراضي ٣٠٠ ثانية)، `wait_time` (فاصل الاستقصاء).

> **`session_id=` لم يعد مستخدَمًا.** فقد **أُزيلت** `generate_session_id()` و`create_session()` من `Agent`، كما أن الوسيط `session_id=` المُمرَّر إلى `run()` **يُحذَف بصمت من الحمولة** — فيُنفَّذ التشغيل بلا حالة دون خطأ ودون تحذير. تظل الشيفرة القديمة "تعمل" بينما تفقد الذاكرة كلها بهدوء. استخدم `session=` (انظر الجلسات).

**غير متزامن:**
```python
ar = agent.run_async(query="...")
r = agent.sync_poll(ar.url)        # blocks until done; same shape as run()
print(r.data.output)
# or manual: while not (res := agent.poll(ar.url, timeout=600)).completed: time.sleep(5)
```

تقبل `poll()` مُعاملًا اختياريًا هو `timeout` (بالثواني)، كما تقبل معرِّف تنفيذ مجرَّدًا إضافةً إلى الرابط الكامل.

**إخراج JSON** يتطلّب معًا `output_format="json"` + `expected_output=<schema>` على الوكيل، إضافةً إلى `run_response_generation=True` وقت التشغيل — وإلا رفضت الخدمة الخلفية الطلب بالرمز `AX-VAL-1000`.

> **الخصوصية:** تُرفق كل حمولة تشغيل تلقائيًا بكتلة `metaData` يبنيها الـ SDK وتحمل **عنوان IP الخاص بالمُستدعي، وخط العرض/الطول، والمنطقة الزمنية، واللغة/المنطقة، ووكيل المستخدم**. نبِّه إلى ذلك في عمليات النشر الحسّاسة للخصوصية.

## الميزانية (حدود التكلفة / الوقت / التكرارات)

```python
from aixplain.v2.agent import Budget

agent = aix.Agent(name="Governed", description="...",
                  budget=Budget(max_cost=0.5, max_duration_seconds=120, max_iterations=12))
agent.budget.max_cost = 1.0          # or set field-by-field, then save()
```

لكل وكيل كائن `budget` دائمًا؛ وترك حقوله `None` يعني عدم وجود إنفاذ. **لا** تفترض وجود قيمة افتراضية في الـ SDK بمقدار `5` تكرارات — فتلك قيمة افتراضية في الخدمة الخلفية لا في الـ SDK.

> **عملية صامتة بلا أثر:** `agent.max_iterations = 30` بعد الإنشاء لا تصل أبدًا إلى حمولة الحفظ — فتضيع القيمة دون خطأ. وحدها `agent.budget.max_iterations = 30` تعمل. (لا يزال وسيط المُنشئ `max_iterations=` يعمل لكنه مهجور؛ وإذا مُرِّر الاثنان فإن `budget` يفوز مع إطلاق `UserWarning`.)

الميزانية المُمرَّرة لكل تشغيل عبر `execution_params={"budget": {...}}` **تُستبدَل** بميزانية الوكيل نفسه متى كان لتلك الميزانية أي حقل مضبوط. ولتغيير الميزانية من تشغيل لآخر، عدِّل `agent.budget.<field>` قبل `run()` (ولا يُحفظ ذلك إلا باستدعاء `save()`).

قراءة الحُكم:

```python
r = agent.run("...")
r.data.governance.get("status")      # e.g. "BLOCKED_BY_BUDGET"
```

> **مأزقان.** التشغيل المحجوب بسبب الميزانية لا يزال يُبلِّغ عن `r.status == "SUCCESS"`. كما أن `data.governance` هو *دائمًا* قاموس — فحين لا ترسل الخدمة الخلفية شيئًا يكون `{'status': None, 'source': None, 'reason': None}`، وهو قاموس صائب منطقيًّا (truthy). اختبِر `r.data.governance.get("status")`، ولا تكتب أبدًا `if r.data.governance:`.

## الجلسات (ذاكرة متعدّدة الأدوار)

```python
session = aix.Session(agent=agent, name="Review Chat")
session.save()
agent.run("My name is Adam.", session=session)
agent.run("What is my name?", session=session)     # remembers; or session=session.id
```

يقبل `session=` كائن `Session` أو نص معرِّف. حمولة الحفظ هي `{'agentId', 'name', 'status'}` (زائد `executionConfig` إن ضُبط)؛ والحالات هي `active | completed | failed | archived`.

احفظ إعدادات التشغيل لكل جلسة بدلًا من تكرارها في كل استدعاء:

```python
from aixplain.v2 import ExecutionConfig
cfg = ExecutionConfig(execution_params={"max_tokens": 1024, "output_format": "text"},
                      criteria="Be concise.", identifier="support-desk")   # also: evolve, run_response_generation, budget
aix.Session(agent=agent, name="Configured", execution_config=cfg)
```

إدارة الرسائل: `session.messages()`، و`add_message(role, content, attachments=[...])`، و`get_message(id)`، و`delete_message(id)`، و`react(message_id, reaction)`؛ إضافةً إلى `aix.Session.get/search(agent=, status=, …)`، و`clone()`، و`delete()`.

**القيود (مُنفَّذة داخل الـ SDK):**

- وسائط التشغيل التالية تُطلق `ValueError` عند دمجها مع `session=`: `tasks`، و`prompt`، و`inspectors`، و`history`، و`variables`.
- يجب أن يكون `query` نصًّا بسيطًا، ووجود استعلام أو `attachments` إلزامي.
- `run_async(session=...)` تُطلق `NotImplementedError` — فتشغيلات الجلسات متزامنة فقط.
- تمرير `execution_params` إلى جانب `session=` يُطلق تحذيرًا و**يُعدِّل `executionConfig` الخاص بالجلسة ويُعيد حفظه**، مما يؤثّر في كل رسالة لاحقة في تلك الجلسة.

وللذاكرة الدائمة العابرة للجلسات/الوكلاء، استخدم أداة الذاكرة المشتركة — انظر `references/knowledge-memory.md`.

## المهارات

تُغلِّف المهارةُ خبرةً قابلة لإعادة الاستخدام في مجلد على طراز Claude (`SKILL.md` مع `scripts/` و`resources/` اختياريين) يُرفَع كأصل واحد. تُحلَّل الواجهة الأمامية (frontmatter) محليًّا وقت الإنشاء.

```python
skill = aix.Skill(file_path="pdf-filler/", tags=["forms"], privacy=aix.Privacy.PRIVATE)
skill.name            # from frontmatter `name`
skill.description     # the ONLY field the agent sees for routing — make it specific
skill.required_tools  # from frontmatter `requires:`
skill.save()          # uploads the whole tree

agent = aix.Agent(name="Forms Assistant", description="...", skills=[skill])   # Skill object or id str
```

المهارة غير المحفوظة تُطلق `ValueError: All skills must be saved before saving the agent.` والقاعدة نفسها تنطبق على `files=[...]` (`aix.File`). دوالّ أخرى: `Skill.get/search`، و`download()`، و`clone()`، و`update()`، و`refresh()`، و`list_files()`، و`as_tool()`، و`delete()`.

## المُشغِّلات (تشغيلات مجدولة / مدفوعة بالأحداث)

يُطلق `aix.Trigger` وكيلًا بمُدخَل ثابت `input` وفق جدول زمني أو عند وقوع حدث في تكامل. ويشتقّ الـ SDK نوع الجدولة من وسائط مقروءة — بلا cron خام.

```python
aix.Trigger(name="Daily digest", agent=agent, input="Summarise today's AI news.",
            every="day", at="09:00", timezone="Europe/London").save()
```

| استدعاء الـ SDK | `schedule_type` |
|---|---|
| `run_at="<iso>"` | `once` |
| `every="minute"` / `"hour"` (+ `interval`) | `recurring` |
| `every="day", at="HH:MM"` | `daily` |
| `every="week", on=["mon","thu"], at=` | `weekly` |
| `every="month", on=[1, 15], at=` | `monthly` |

تُطلَق مُشغِّلات الأحداث عند وقوع شيء في تكامل مُتّصل. استعرض الخيارات عبر `integration.triggers` (كما يوفّر الـ SDK الدالّة `Integration.list_trigger_types()`)، ثم مرِّر أحدها من *الأداة المتصلة*:

```python
aix.Trigger(name="Triage inbox", agent=agent,
            input="Triage this email and flag anything urgent.",
            event=tool.triggers["NEW_EMAIL"]).save()
```

وسائط أخرى: `notifications` (الافتراضي `False`)، و`enabled` (الافتراضي `True`). وتتوفّر `get`/`search`/`delete` القياسية.

> تقول الوثائق إن المُشغِّلات الزمنية تُبلِّغ عن `trigger_type="scheduled"`؛ لكن الـ SDK يُصدر فعليًّا **`"time"`** (`triggerType: 'time'` في حمولة الحفظ). أمّا مُشغِّلات الأحداث فتُبلِّغ عن `external` وتحمل `trigger_id`.

## التصحيح: فحص أثر الاستدلال

```python
r = agent.run(query="...")
for step in r.data.steps or []:
    print(step.get("agent"), step.get("thought"))
    print(step.get("unit"), step.get("input"), str(step.get("output"))[:200], step.get("error"))

stats = r.data.execution_stats or {}
print(stats.get("runtime"), stats.get("api_calls"), stats.get("credits"), stats.get("assets_used"))
```

يمكنك أيضًا تحليل تشغيلٍ منتهٍ باستخدام الوكيل الفوقي Debugger — إذ تُعيد `aix.Debugger().debug_response(r)` قيمة `.analysis` بلغة واضحة (انظر `references/governance.md`).

## وكلاء الفِرَق (متعدّد الوكلاء)

اجمع المتخصّصين في فريق. وتتولى الوكلاء الدقيقة المدمجة للتنسيق بقية العمل: **المُخطِّط/Mentalist** يُفكّك الهدف، و**المُنسِّق (Orchestrator)** يوجّه المهام إلى الوكلاء الفرعيين، و**المُفتِّش (Inspector)** يتحقّق من الجودة، و**مُولِّد الاستجابة (Response Generator)** يُركّب الإجابة النهائية.

```python
researcher = aix.Agent(name="Researcher", description="Finds and gathers information", tools=[search_tool])
writer     = aix.Agent(name="Writer", description="Writes clear reports", output_format="markdown")

team = aix.Agent(name="Research Team", description="Researches topics and writes reports",
                 agents=[researcher, writer])
team.save(save_subcomponents=True)     # REQUIRED for teams — saves subagents first, then the team
print(team.run(query="Research quantum computing and write a summary").data.output)
```

امنح كل وكيل فرعي **`description` مميّزًا** — فالتوجيه المستقل يعتمد عليه. وارفع `team.budget.max_iterations` (مثلًا ٣٠–٥٠) للفِرَق المعقّدة، ثم استدعِ `save()`.

### سير العمل المُهيكَل (رسم بياني حتمي للمهام)

استخدم كائنات `Task` لتحديد التبعيات صراحةً بدل التخطيط المستقل. ويجب أن تُشكّل التبعيات رسمًا بيانيًّا موجَّهًا غير دوري (DAG). **وإذا كان لأي وكيل فرعي مهمة، فيجب أن يكون لكل وكيل فرعي مهمة واحدة على الأقل.**

```python
find = aix.Agent.Task(name="find_leads", instructions="Find EdTech companies",
                      expected_output="List of companies with contact info")
analyze = aix.Agent.Task(name="analyze_leads", instructions="Prioritise leads",
                         expected_output="Qualified list", dependencies=[find])

finder   = aix.Agent(name="Lead Finder",   description="Finds leads",   tools=[search_tool], tasks=[find])
analyzer = aix.Agent(name="Lead Analyzer", description="Qualifies leads", tasks=[analyze])

team = aix.Agent(name="Lead Gen Team", description="Generates and qualifies leads",
                 agents=[finder, analyzer])
team.save(save_subcomponents=True)
```

## تحديث وكيل منشور

الوكلاء المنشورون قابلون للتعديل — لا تُعِد إنشاء وكيل لتغيير سلوكه أبدًا. حمِّله، وعدِّل حقوله، ثم استدعِ `save()`؛ فيبقى معرِّف الوكيل وسجلّه ومراجعه الخارجية سليمة.

```python
agent = aix.Agent.get("<AGENT_ID>")
agent.instructions = "New system prompt..."
agent.output_format = "json"
agent.llm = "<MODEL_ID>"     # swap the LLM — assign to .llm (model id string or Model object)
agent.save()
```

> **`.llm` وليس `.llm_id`:** أسنِد النموذج إلى `agent.llm`. فالسِمة `agent.llm_id` موجودة، لكن الإسناد إليها **لا** ينتقل إلى حمولة الحفظ — وتُبقي `save()` على النموذج القديم بصمت.

يمكنك أيضًا تحديث أداة مرفقة في مكانها (بلا فصل وإعادة ربط) — غيِّر `description` أو `allowed_actions` الخاص بها، واستدعِ `tool.save()`، فيلتقط الوكيل التغيير في التشغيل التالي:

```python
kb_tool = next(t for t in agent.tools if t.name == "Product KB")
kb_tool.description = "Updated scope: includes 2026 docs."
kb_tool.save()
```

وللتفرّع إلى نسخة بدل تعديل الأصل، تُنشئ `agent.duplicate(duplicate_subagents=False, name=None)` نسخةً على جانب الخادم. (متاحة في الـ SDK فقط — وليست في صفحات الوثائق.)

## تصدير وكيل منشور إلى سكربت مستقل

أعِد بناء أي وكيل منشور كشيفرة Python قابلة للنقل باستخدام الـ SDK — بلا REST خام. تُعيد `Agent.get()` الإعداد الكامل؛ سَلسِله وتعمَّق تكراريًّا داخل الوكلاء الفرعيين.

```python
agent = aix.Agent.get("<AGENT_ID>")
config = agent.to_dict()     # full config: name, description, instructions, output_format, llm, tools, max_tokens, inspectors
subs   = agent.subagents     # subagent objects for a team — recurse the same way
```

ثم اربط تلك الحقول بوسائط المُنشئ وأصدِر ملف `.py` يُحمِّل المفتاح من `AIXPLAIN_API_KEY` ويُعيد بناء الوكيل: `aix.Agent(name=..., description=..., instructions=..., tools=[aix.Tool.get(...)], llm=..., output_format=...)` (وأعِد إنشاء المُفتِّشين وفق `references/governance.md`)، منتهيًا بـ `.save()`. يمنح هذا المستخدمَ تعريفًا قابلًا لإعادة الإنتاج وللتحكّم بالإصدارات لوكيلٍ بُني في Studio أو نُشر سابقًا.

## السرد والفحص

```python
for a in aix.Agent.search()["results"]:
    print(a.name, a.id)
agent = aix.Agent.get("YOUR_AGENT_ID")
print(agent.name, agent.status, agent.tools)
```

## معالجة المشكلات

| العَرَض | الحل |
|---|---|
| "maximum number of iterations" | `agent.budget.max_iterations = 20` (للفِرَق ٥٠)، ثم `save()`. **أمّا `agent.max_iterations = 20` فعملية صامتة بلا أثر.** |
| وكيل متعدّد الأدوار بلا ذاكرة | مرَّرت `session_id=` — وهو يُحذَف بصمت. استخدم `session=` مع كائن `aix.Session`. |
| `ValueError: session=… runs do not support legacy run kwargs` | احذف `tasks`/`prompt`/`inspectors`/`history`/`variables`، أو شغِّل بلا جلسة. |
| الإخراج مبتور | ارفع `agent.max_tokens` (الافتراضي ٢٠٤٨)، أو `inputs.max_tokens` الخاص بنموذج اللغة، ثم `save()`. |
| الوكيل يتجاهل أداة | افحص `r.data.steps`؛ وحدِّد `name`/`description` الأداة بدقة أكبر. وأبقِ إجمالي مُعاملات الأدوات منخفضًا. |
| وكيل فرعي في الفريق لا يُستخدَم أبدًا | اجعل `description` كل وكيل فرعي مميّزًا؛ وفي الوضع المُهيكَل تأكّد من إسناد المهام. |
| المهام تُنفَّذ بترتيب خاطئ | صرِّح بكل حافة في `dependencies` — فالحواف المفقودة هي السبب المعتاد. |
| رفض JSON بالرمز `AX-VAL-1000` | تحتاج إلى `output_format="json"` + `expected_output` + `run_response_generation=True`. |
| `name_already_exists` عند الحفظ | غيِّر الاسم، أو اسأل المستخدم عمّا إذا كان يريد تحديث الوكيل الموجود. |
