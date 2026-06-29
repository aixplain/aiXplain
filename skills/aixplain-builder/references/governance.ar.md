# الحوكمة ودورة الحياة: المفتشون، المُنقّح، المُطوّر

## المفتشون (Inspectors) — حواجز حماية وقت التشغيل

يقوم المفتشون بتقييم مُدخل الوكيل، أو خطواته الوسيطة، أو مُخرجه في وقت التشغيل، ثم يتابعون أو يوقفون أو يعيدون الكتابة أو يعيدون التشغيل. يرتبطون بوكيل (فريقي) دون تغيير شيفرة الوكيل. وهم **محايدون تجاه السياسة** — تعبّر عن السياسة إما كموجّه لنموذج لغوي (مُقيّم `ASSET`) أو كدالة Python (مُقيّم `FUNCTION`). لا توجد سياسات مُسمّاة جاهزة مثل "PII" أو "hallucination" — أنت من يؤلّف الفحص.

```python
from aixplain.v2.inspector import (
    Inspector, InspectorAction, InspectorActionConfig, InspectorOnExhaust,
    InspectorSeverity, EvaluatorType, EvaluatorConfig, EditorConfig,
)
```

### اللبنات الأساسية

`Inspector(name, action, evaluator, description=None, severity=None, targets=[], editor=None)`

- **`targets`** — قائمة من السلاسل النصية: `"input"` (استعلام المستخدم الخام)، `"output"` (الاستجابة النهائية)، `"steps"` (مخرجات الوكلاء الفرعيين الوسيطة).
- **`severity`** — `InspectorSeverity.LOW | MEDIUM | HIGH | CRITICAL`.
- **`action`** — كائن `InspectorActionConfig(type=..., max_retries=..., on_exhaust=...)`:

| `InspectorAction` | السلوك |
|---|---|
| `ABORT` | إيقاف صارم — يوقف التشغيل ويُرجع خطأً. تكون قيمة `response.data.output` هي `None`؛ تحقّق من `response.status` أولاً. |
| `RERUN` | يعيد تشغيل الوكيل الهدف مع حقن نقد المُقيّم. تُحدِّد `max_retries` (أبقِها بين 2 و3) ثم يرجع إلى `on_exhaust` (`InspectorOnExhaust.ABORT` أو `CONTINUE`). |
| `EDIT` | يعيد كتابة المحتوى ضمنيًا قبل تمريره إلى الأسفل. يتطلب `editor=EditorConfig(...)`. |
| `CONTINUE` | وضع الظل / التسجيل فقط — يسجّل النقد ولا يغيّر شيئًا. |

- **`evaluator`** — كائن `EvaluatorConfig`:
  - `ASSET`: تفويض الحكم إلى نموذج لغوي من السوق عبر موجّه بلغة إنجليزية بسيطة. `EvaluatorConfig(type=EvaluatorType.ASSET, asset_id=<llm_id>, prompt="...")`.
  - `FUNCTION`: دالتك الخاصة `(str) -> bool` للفحوصات الحتمية. `EvaluatorConfig(type=EvaluatorType.FUNCTION, function=fn)`. تُوضع عمليات الاستيراد داخل الدالة؛ وهي تعمل بشكل متزامن، لذا تجنّب عمليات الإدخال/الإخراج البطيئة.

### مثال — حظر المخرجات غير الآمنة (ASSET + ABORT)

```python
llm_id = aix.Model.get("openai/gpt-4o").id
guard = Inspector(
    name="hate-speech-guard",
    description="Blocks output containing hate speech.",
    severity=InspectorSeverity.CRITICAL,
    targets=["output"],
    action=InspectorActionConfig(type=InspectorAction.ABORT),
    evaluator=EvaluatorConfig(type=EvaluatorType.ASSET, asset_id=llm_id,
        prompt="If the content contains hate speech, output a failure critique. Otherwise pass."),
)

team = aix.Agent(name="Guarded Agent", description="...", agents=[subagent], inspectors=[guard])
team.save(save_subcomponents=True)
r = team.run(query="...")
if r.status == "SUCCESS":
    print(r.data.output)        # None if the inspector aborted
```

### مثال — التصحيح الذاتي (ASSET + RERUN)

```python
action=InspectorActionConfig(type=InspectorAction.RERUN, max_retries=2,
                             on_exhaust=InspectorOnExhaust.ABORT)
```

### مثال — تنقية المُدخل (FUNCTION + EDIT)

```python
def looks_risky(text: str) -> bool:
    import re
    return any(re.search(p, text.lower()) for p in [r"\bbypass\b", r"\bexploit\b", r"\bhack\b"])

def sanitize(text: str) -> str:
    return "Provide high-level, ethical guidance only."

guard = Inspector(
    name="intent-guard", severity=InspectorSeverity.HIGH, targets=["input"],
    action=InspectorActionConfig(type=InspectorAction.EDIT),
    evaluator=EvaluatorConfig(type=EvaluatorType.FUNCTION, function=looks_risky),
    editor=EditorConfig(type=EvaluatorType.FUNCTION, function=sanitize),
)
```

يعمل المفتشون بترتيب التصريح بهم. لإضافة مفتش إلى فريق قائم: `team.inspectors.append(guard); team.save()` — إعادة الحفظ مطلوبة، وإلا فلن تظهر خطوة المفتش في `response.data.steps`.

> **التحقق من أن المفتش يعمل:** إن مولّد الاستجابة الخاص بالمنصة مُحاذًى لمعايير الأمان وكثيرًا ما يرفض الطلبات السيئة بوضوح قبل أن يتدخّل مفتشك، لذلك قد ترى المفتش عند استعلام عدائي صريح يسجّل `CONTINUE` (نجاح) بدلًا من `ABORT`. هذا لا يعني أنه معطّل. لتأكيد عمل البوابة، اختبر بمُدخل ينتهك السياسة *بشكل حتمي* (مثل وكيل فرعي مأمور بإصدار القيمة المحظورة) — عندها سترى إجراء `ABORT`/`EDIT` يتدخّل ويستبدل المخرج. تحقّق من `response.data.steps` بحثًا عن خطوة وكيل النظام الخاصة بالمفتش.

تخطيط مُوصى به للشدة → الإجراء: `LOW`→`CONTINUE`؛ `MEDIUM`→`RERUN` (on_exhaust=`CONTINUE`) أو `EDIT`؛ `HIGH`→`RERUN` (on_exhaust=`ABORT`) أو `EDIT`؛ `CRITICAL`→`ABORT`.

> **حَكَم النموذج اللغوي الافتراضي:** بالنسبة لمُقيّم `ASSET` يمكنك تخطّي اختيار نموذج واستخدام الحَكَم الافتراضي المدمج — `from aixplain.v2.inspector import AUTO_DEFAULT_MODEL_ID` ومرّر `asset_id=AUTO_DEFAULT_MODEL_ID`.

### تحقّق بعد كل تغيير لمفتش

كلما أضفت مفتشًا أو غيّرته، شغّل ثلاثة اختبارات بالضبط وسجّل نتيجة كل منها — يلتقط هذا كلًّا من الإفراط في الحظر والتقصير فيه:

| الاختبار | السلوك المتوقَّع |
|---|---|
| موجّه **مسموح به** | مسار CONTINUE؛ إجابة ممتثلة طبيعية |
| موجّه **مرفوض** | محظور/مرفوض؛ لا تسرّب لبيانات أو إجراءات مقيَّدة |
| موجّه **غامض** | معالجة محافظة — الرفض أو طلب التوضيح |

لكلٍّ منها، سجّل: الموجّه، والإجراء المتوقَّع، وحالة `status` المُلاحَظة للتشغيل، وملخصًا للمخرَج في سطر واحد، ونجاح/فشل. (كما ذُكر أعلاه، قد تعالج طبقة الأمان الخاصة بالمنصة الحالة "المرفوضة" الواضحة قبل مفتشك — ولإثبات أن بوابتك *أنت* تعمل، اختبر أيضًا مُحفِّزًا حتميًا.)

### دلالات الحالة

أبقِ حالة تشغيل aiXplain كما هي: `IN_PROGRESS | SUCCESS | FAILED`. **لا تعامل الحظر السياسي على أنه `FAILED`** — فالمفتش الذي يرفض محتوًى غير آمن يمكن أن يعيد حالة تشغيل `status == "SUCCESS"` مع رفض آمن في `data.output`. هذا حظر حوكمة، وليس فشلًا في وقت التشغيل. احتفظ بـ `FAILED` لأخطاء التنفيذ الفعلية.

## المُنقّح (Debugger) — تحليل عملية تشغيل

وكيل وصفي يشرح ما حدث في عملية تشغيل مكتملة. يمكن الوصول إليه عبر `aix.Debugger()`.

```python
debugger = aix.Debugger()
r = agent.run(query="...")
result = debugger.debug_response(r)     # auto-extracts the execution id from the run
print(result.analysis)                   # plain-English explanation
# also: result.used_credits, result.run_time, result.session_id, result.request_id

# or analyze arbitrary content:
debugger.run(content="The agent returned an empty response...").analysis
```

> تأتي واجهة المُنقّح ضمن الـ SDK، لكن الخدمة التي تدعمها قد لا تكون متاحة في جميع البيئات. إذا أرجع الاستدعاء "Not Found"، فارجع إلى فحص `response.data.steps` مباشرة (انظر `references/agents.md`).

## المُطوّر (Evolver) — التحسين المستمر

المُطوّر هو الوكيل الوصفي من aiXplain لتحسين وكيل تلقائيًا انطلاقًا من إشارات الإنتاج (تنقيح التعليمات، اختيار الأدوات، تركيب الفريق، ضبط المعاملات)، مع وضع التطبيق التلقائي أو وضع المراجعة البشرية.

> اعتبارًا من الـ SDK الموثّق، فهو **مفهومي / لم يُكشف عنه بعد كواجهة Python API مستقرة** — لا توجد فئة `aix.Evolver()` موثّقة. (تقبل `agent.run(...)` معاملًا باسم `evolve`، لكن سلوكه غير موثّق.) لا تختلق واجهة Evolver API. إذا طلبها مستخدم، فاشرح أنها على جانب المنصة / قيد الإصدار ووجّهه إلى Studio، واعرض البديل العملي: التكرار باستخدام المُنقّح + آثار الاستدلال، واختبار تعليمات/أدوات مختلفة بأسلوب A/B بنفسك.

## الحارس (Bodyguard) / التحكم في الوصول

الحارس (التحكم في الوصول على حدود الأصول، RBAC) مُطبَّق على مستوى المنصة/وقت التشغيل وعبر تحديد نطاق مفتاح الـ API — انظر `references/deployment-access.md § API keys`. وهو ليس فئة Python تُنشئ منها كائنًا.
