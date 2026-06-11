# أنماط الوكلاء

أنماط متقدمة للوكلاء — وكلاء الفريق، تحديث الوكلاء المنشورين، المراقبون، التصدير، وتفاصيل الأدوات.
مرتبط من المهارة الرئيسية — يُرجع إليه عند الحاجة.

---

## وكيل الفريق

```python
sub1 = aix.Agent(name="Researcher", instructions="Search and summarize.", tools=[search_tool]).save()
sub2 = aix.Agent(name="Writer", instructions="Write the final report.").save()
team = aix.Agent(name="Team Lead", instructions="Route to specialists.", subagents=[sub1, sub2]).save()
```

---

## تحديث وكيل منشور

الوكلاء المنشورون قابلون للتعديل. لا تُعِد إنشاء الوكيل لتغيير سلوكه — قم بتحميله، وعدّله، ثم استدعِ `save()`. يبقى معرّف الوكيل والسجل والمراجع الخارجية كما هي.

الحقول القابلة للتحديث:
- `agent.instructions` — موجِّه النظام
- `agent.description` — ملخص عام
- `agent.tools` — إضافة أو إزالة أو استبدال الأدوات
- `agent.output_format` — `"markdown"` / `"text"` / `"json"`
- `agent.llm` — تبديل النموذج اللغوي الكبير الأساسي (اسم الخاصية هو `llm`، وليس `llm_id`)

يمكنك أيضًا تحديث الأدوات المرفقة دون فصلها — غيّر `description` الخاصة بالأداة، أو أضف ملفات إلى أداة قاعدة المعرفة، أو عدّل `allowed_actions`. عدّل كائن الأداة، واستدعِ `tool.save()`، وسيلتقط الوكيل التغيير في التشغيل التالي.

```python
agent = aix.Agent.get("<AGENT_ID>")
agent.instructions = "New system prompt..."
agent.output_format = "json"
agent.save()

# Update an attached tool in place (no detach/reattach):
kb_tool = next(t for t in agent.tools if t.name == "Product KB")
kb_tool.description = "Updated KB scope: includes 2026 docs."
kb_tool.save()
```

---

## إضافة مراقب

```python
from aixplain.modules.team_agent import InspectorTarget
from aixplain.modules.team_agent.inspector import Inspector, InspectorPolicy, InspectorAuto

inspector = Inspector(
    name="Content Gate",
    auto=InspectorAuto.ALIGNMENT,
    model_params={"prompt": "Validate output meets policy. Fail if non-compliant."},
    policy=InspectorPolicy.ABORT,
)
team.inspectors = [inspector]
team.inspector_targets = [InspectorTarget.OUTPUT]
team.save()
```

بعد إضافة المراقبين، تحقق من الصحة باستخدام 3 موجِّهات: مسموح، ومرفوض، وغامض. راجع `references/inspector-analytics.md` لمصفوفة التحقق الكاملة.

---

## تصدير الوكيل إلى Python

1. `GET https://platform-api.aixplain.com/sdk/agents/{ID}` مع `x-api-key`
2. تتبع `agents[].assetId` بشكل تكراري للوكلاء الفرعيين
3. ربط حقول API بوسيطات مُنشئ SDK
4. إنشاء ملف `.py` مستقل مع تحميل المفتاح عبر متغيرات البيئة

---

## تنفيذ الشيفرة مقابل صندوق حماية Python

**تنفيذ الشيفرة** (أداة من السوق `698cda188bbb345db14ac13b`) — يكتب الوكيل شيفرة Python عشوائية وينفّذها أثناء التشغيل. صندوق حماية سحابي آمن مع اتصال بالإنترنت. يُستخدم للحسابات، وتحويلات البيانات، والتصورات البيانية، ومعالجة الملفات، وجلب البيانات من عناوين URL أو واجهات API.

- استخدم `print()` لإرجاع النتائج النهائية.
- إذا أنشأت الشيفرة ملفات (رسوم بيانية، ملفات CSV)، اطبع قائمة بيانات وصفية بتنسيق JSON إلى stdout: `[{"name":"<display_name>","file":"<filename>"}]`. بدون ذلك، تُفقد الملفات المُنشأة بصمت.

**صندوق حماية Python** (تكامل `688779d8bfb8e46c273982ca`) — نفس صندوق الحماية لكن مع سكربت مُعرَّف مسبقًا يُكتب وقت البناء، وليس وقت التشغيل. يُستخدم للأدوات الحتمية ذات المدخلات والمخرجات الثابتة عندما لا تغطي أي أداة في السوق القدرة المطلوبة. راجع `references/integration-playbooks.md § 4` لشكل التهيئة وقيود التأليف.

<!-- ملاحظات الترجمة: [استخدام "موجِّه النظام" لـ system prompt] | ["صندوق حماية" لـ sandbox للدلالة على البيئة المعزولة] | [kept EN: aiXplain, SDK, API, Python, JSON, CSV, URL, Markdown — brand/tech terms per rules] | ["شيفرة" لـ code في السياق العام و"تنفيذ الشيفرة" لـ Code Execution] | [kept EN: InspectorTarget, InspectorPolicy, InspectorAuto — enum values] -->