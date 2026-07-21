# الوكلاء ووكلاء الفِرق

ينفِّذ الوكيل حلقة **التخطيط ← التنفيذ ← الملاحظة ← التكرار**: يقرأ تعليماته، ويختار الأدوات، ويستدعي النماذج/الأدوات، ثم يعيد نصًّا أو markdown أو JSON. أمّا "وكيل الفريق" فهو **نفس الصنف `Agent`** — وتمرير `agents=[...]` هو ما يحوّله إلى فريق. لا يوجد صنف منفصل باسم `TeamAgent`.

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

معاملات المُنشئ (جميعها متحقَّق منها مقابل الـ SDK):

| المعامل | القيمة الافتراضية | ملاحظات |
|---|---|---|
| `name` | — | مطلوب. تكرار اسمٍ يثير `name_already_exists`. |
| `description` | — | الغرض الظاهر للمستخدم؛ في الفِرق يستخدمه المخطِّط (Planner) لتوجيه العمل. |
| `instructions` | `None` | إرشاد داخلي لا يُعرض للمستخدمين. يدعم `{{placeholders}}`. |
| `tools` | `[]` | أدوات السوق، والنماذج-كأدوات، والتكاملات، وأدوات فهرسة قواعد المعرفة. |
| `llm` | الافتراضي للمنصّة | كائن `Model` أو معرّف/مسار نموذج. **احذفه ما لم يطلب المستخدم نموذجًا محدّدًا.** |
| `output_format` | `"text"` | `"text"` \| `"markdown"` \| `"json"`. |
| `expected_output` | `""` | مخطّط (str/dict/Pydantic model). مطلوب عند `output_format="json"`. |
| `agents` | `[]` | الوكلاء الفرعيون — تمرير هذا يجعله **فريقًا**. |
| `tasks` | `[]` | مهام سير العمل المنظّم (راجع قسم الفِرق أدناه). |
| `inspectors` | `[]` | ضوابط حماية أثناء التشغيل (راجع `references/governance.md`). |
| `max_iterations` | `5` | حدّ حلقة الاستدلال. ارفعه للأعمال المعقّدة/الجماعية. |
| `max_tokens` | `2048` | يحدّ من رموز **المخرجات**. |

إن `max_iterations` / `max_tokens` هما إعدادان للوكيل: اضبطهما في المُنشئ أو بوصفهما خاصيتين، ثم نفّذ `save()`. تمريرهما إلى `run()` لا أثر له.

## دورة الحياة

| الحالة | المعنى |
|---|---|
| `DRAFT` | لم يُحفظ بعد. نقطة نهاية مؤقتة، **تنتهي خلال 24 ساعة**. |
| `ONBOARDED` | محفوظ — نقطة نهاية دائمة ومُصدَّرة وإنتاجية. |
| `DELETED` | محذوف. |

```python
agent.save()                       # promote DRAFT -> ONBOARDED
agent.description = "new purpose"   # mutate then re-save to persist
agent.save()
agent.delete()
```

`save()` هي خطوة النشر — لا توجد خطوة منفصلة باسم `agent.deploy()`. بعد الحفظ، شارك روابط Studio (راجع SKILL.md).

## التشغيل

```python
r = agent.run(query="Search for AI news")
r.data.output        # final answer
r.status             # "SUCCESS" | "FAILED" | "IN_PROGRESS"
r.completed          # bool
r.error_message      # None on success
r.used_credits       # float — NOTE: often 0.0 for agents; read cost from execution_stats instead
r.run_time           # seconds
```

> للحصول على التكلفة الموثوقة للتشغيل، استخدم `r.data.execution_stats["credits"]` — فالقيمة `r.used_credits` كثيرًا ما تكون `0.0` في تشغيلات الوكلاء.

معاملات مفيدة في `run()`: `query` (نص أو dict)، و`session_id` (ذاكرة متعدّدة الأدوار)، و`history` (قائمة من `{"role","content"}` لتهيئة السياق)، و`variables` (dict يُستبدَل في `{{placeholders}}` داخل التعليمات/الوصف)، و`run_response_generation` (اضبطه إلى `True` لمخرجات JSON)، و`progress_format` (`"status"` | `"logs"`)، و`progress_verbosity` (1–3)، و`timeout` (الافتراضي 300 ثانية)، و`wait_time` (فترة الاستعلام). تمرّر بعض الأنماط أيضًا `content=[...]` لتوفير المادة المصدرية بمعزل عن `query`.

**غير متزامن:**
```python
ar = agent.run_async(query="...")
r = agent.sync_poll(ar.url)        # blocks until done; same shape as run()
print(r.data.output)
# or manual: while not (res := agent.poll(ar.url)).completed: time.sleep(5)
```

**مخرجات JSON** تتطلّب كلًّا من `output_format="json"` + `expected_output=<schema>` على الوكيل، و`run_response_generation=True` عند التشغيل — وإلا ترفضها الخلفية بالخطأ `AX-VAL-1000`.

## ذاكرة الجلسة (متعدّدة الأدوار)

```python
session_id = agent.generate_session_id()      # or generate_session_id(history=[...])
agent.run(query="What is the capital of France?", session_id=session_id)
agent.run(query="What did I just ask?", session_id=session_id)   # remembers
```

للذاكرة الدائمة عبر الجلسات/الوكلاء، استخدم أداة الذاكرة المشتركة (Shared Memory) — راجع `references/knowledge-memory.md`.

## التنقيح: فحص أثر الاستدلال

```python
r = agent.run(query="...")
for step in r.data.steps or []:
    print(step.get("agent"), step.get("thought"))
    print(step.get("unit"), step.get("input"), str(step.get("output"))[:200], step.get("error"))

stats = r.data.execution_stats or {}
print(stats.get("runtime"), stats.get("api_calls"), stats.get("credits"), stats.get("assets_used"))
```

يمكنك أيضًا تحليل تشغيلٍ منتهٍ باستخدام وكيل التنقيح الفائق (Debugger meta-agent) — تُعيد `aix.Debugger().debug_response(r)` تحليلًا بلغة طبيعية واضحة عبر `.analysis` (راجع `references/governance.md`).

## الوكلاء الجماعيون (متعدّدو الوكلاء)

ركّب المتخصّصين في فريق. وتتولّى الوكلاء الدقيقة المدمجة للتنسيق الباقي: **المخطِّط/المُفكِّر (Planner/Mentalist)** يفكّك الهدف، و**المنسّق (Orchestrator)** يوجّه المهام إلى الوكلاء الفرعيين، و**المفتّش (Inspector)** يتحقّق من الجودة، و**مولّد الاستجابة (Response Generator)** يصوغ الإجابة النهائية.

```python
researcher = aix.Agent(name="Researcher", description="Finds and gathers information", tools=[search_tool])
writer     = aix.Agent(name="Writer", description="Writes clear reports", output_format="markdown")

team = aix.Agent(name="Research Team", description="Researches topics and writes reports",
                 agents=[researcher, writer])
team.save(save_subcomponents=True)     # REQUIRED for teams — saves subagents first, then the team
print(team.run(query="Research quantum computing and write a summary").data.output)
```

امنح كل وكيل فرعي **وصفًا (`description`) مميّزًا** — فالتوجيه الذاتي يعتمد عليه. ارفع `team.max_iterations` (مثلًا 30–50) للفِرق المعقّدة.

### سير العمل المنظّم (مخطّط مهام حتمي)

استخدم كائنات `Task` للتبعيات الصريحة بدلًا من التخطيط الذاتي. يجب أن تشكّل التبعيات مخططًا موجّهًا غير دوري (DAG). **إذا كان لأي وكيل فرعي مهمة، فيجب أن يملك كل وكيل فرعي مهمة واحدة على الأقل.**

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

الوكلاء المنشورون قابلون للتعديل — لا تُعِد إنشاء وكيلٍ لتغيير سلوكه أبدًا. حمّله، وعدّل الحقول، ثم نفّذ `save()`؛ يبقى معرّف الوكيل وتاريخه ومراجعه الخارجية سليمة.

```python
agent = aix.Agent.get("<AGENT_ID>")
agent.instructions = "New system prompt..."
agent.output_format = "json"
agent.llm = "<MODEL_ID>"     # swap the LLM — assign to .llm (model id string or Model object)
agent.save()
```

> **`.llm` لا `.llm_id`:** أسنِد النموذج إلى `agent.llm`. توجد السمة `agent.llm_id` لكنّ إسنادها لا **ينتشر** إلى حمولة الحفظ — إذ يُبقي `save()` على النموذج القديم بصمت.

يمكنك أيضًا تحديث أداة مرتبطة في مكانها (دون فصل/إعادة ربط) — غيّر `description` أو `allowed_actions` الخاصة بها، ونفّذ `tool.save()`، وسيلتقطها الوكيل في التشغيل التالي:

```python
kb_tool = next(t for t in agent.tools if t.name == "Product KB")
kb_tool.description = "Updated scope: includes 2026 docs."
kb_tool.save()
```

## تصدير وكيل منشور إلى سكربت مستقل

أعِد بناء أي وكيل منشور بصيغة Python محمولة باستخدام الـ SDK — دون REST خام. يعيد `Agent.get()` التهيئة الكاملة؛ سَلسِلها وكرِّر داخل الوكلاء الفرعيين.

```python
agent = aix.Agent.get("<AGENT_ID>")
config = agent.to_dict()     # full config: name, description, instructions, output_format, llm, tools, max_tokens, inspectors
subs   = agent.subagents     # subagent objects for a team — recurse the same way
```

ثم اربط تلك الحقول بمعاملات المُنشئ وأصدِر ملف `.py` يحمّل المفتاح من `AIXPLAIN_API_KEY` ويعيد بناء الوكيل: `aix.Agent(name=..., description=..., instructions=..., tools=[aix.Tool.get(...)], llm=..., output_format=...)` (أعِد إنشاء المفتشين وفق `references/governance.md`)، منتهيًا بـ `.save()`. يمنح هذا المستخدمَ تعريفًا قابلًا لإعادة الإنتاج وللتحكّم في الإصدارات لوكيلٍ بُني في Studio أو نُشر سابقًا.

## السرد والفحص

```python
for a in aix.Agent.search()["results"]:
    print(a.name, a.id)
agent = aix.Agent.get("YOUR_AGENT_ID")
print(agent.name, agent.status, agent.tools)
```

## استكشاف الأخطاء وإصلاحها

| العَرَض | الحل |
|---|---|
| "maximum number of iterations" | `agent.max_iterations = 20` (للفِرق 50)، ثم `save()`. |
| المخرجات مقطوعة | ارفع `agent.max_tokens` (الافتراضي 2048)، أو `inputs.max_tokens` الخاص بنموذج اللغة، ثم `save()`. |
| الوكيل يتجاهل أداة | افحص `r.data.steps`؛ وحسّن `name`/`description` الخاص بالأداة. أبقِ إجمالي معاملات الأدوات منخفضًا. |
| وكيل فرعي ضمن الفريق لا يُستخدَم أبدًا | اجعل `description` كل وكيل فرعي مميّزًا؛ وفي الوضع المنظّم تأكّد من إسناد المهام. |
| المهام تُنفَّذ خارج الترتيب | صرّح بكل حافة `dependencies` — فالحواف المفقودة هي السبب المعتاد. |
| رفض JSON بالخطأ `AX-VAL-1000` | يلزم `output_format="json"` + `expected_output` + `run_response_generation=True`. |
| `name_already_exists` عند الحفظ | غيّر الاسم، أو اسأل المستخدم عمّا إذا كان يريد تحديث الوكيل الموجود. |
