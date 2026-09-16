# الحوكمة ودورة الحياة: المُفتِّشون، والمُصحِّح، والمُطوِّر

## المُفتِّشون — ضوابط الأمان أثناء التشغيل

يُقيِّم المُفتِّشون مُدخَل الوكيل أو خطواته الوسيطة أو مُخرجاته أثناء التشغيل، ثم يُتابعون أو يوقفون أو يُعيدون الصياغة أو يُعيدون التشغيل. أرفِقهم عبر `inspectors=[...]` — وهذا يعمل على **الوكيل المفرد كما على الفريق**.

> **تغيّر في SDK 0.2.48.** صار المُفتِّشون يُبنَون مباشرةً من العميل (`aix.Inspector(...)`) باستخدام **نصوص وقواميس بسيطة** — فلا شيء يُستورَد. أمّا الأصناف القديمة `from aixplain.v2.inspector import InspectorAction, InspectorActionConfig, EvaluatorConfig, EvaluatorType, EditorConfig, InspectorSeverity` فقد **أُزيلت من v2** (ولم تبقَ إلا تحت `aixplain.v1.*`). فإن رأيت ذلك الاستيراد فهو شيفرة سابقة للإصدار 0.2.48 — أعِد كتابتها كما هو موضّح أدناه.

### اللبنات الأساسية

```python
inspector = aix.Inspector(
    name="hate-speech-guard",
    description="Blocks output containing hate speech.",
    severity="critical",                 # "low" | "medium" | "high" | "critical"  (plain string)
    targets=["output"],                  # "input" | "output" | "steps"
    action="abort",                      # "abort" | "rerun" | "edit" | "continue"
    metric={"assetId": LLM_ASSET_ID,     # the evaluator — an LLM judge…
            "prompt": "If the content contains hate speech, output a failure critique. Otherwise pass."},
)
```

| الحقل | ما يقبله |
|---|---|
| `action` | `"abort"` \| `"rerun"` \| `"edit"` \| `"continue"`، أو قاموس للخيارات (انظر RERUN). |
| `metric` | المُقيِّم. حَكَم من نموذج لغوي ← `{"assetId": <model id>, "prompt": "..."}`؛ فحص Python ← `{"function": fn}` حيث `fn(str) -> bool`. |
| `editor` | إلزامي مع `"edit"` ← `{"function": fn}` حيث `fn(str) -> str`. |
| `severity` | نص بسيط. |
| `targets` | قائمة المسارات المطلوب مراقبتها. |
| `preset_id` | يُضبط تلقائيًّا لضوابط الأمان المأخوذة من المتجر (انظر الجاهزة مسبقًا). |

| الإجراء | السلوك |
|---|---|
| `abort` | إيقاف تام — يُنهي التشغيل. تكون `response.data.output` بقيمة `None`؛ افحص `response.status` أولًا. |
| `rerun` | يُعيد تشغيل الهدف مع حقن نقد المُقيِّم، ثم يرتدّ إلى `on_exhaust`. |
| `edit` | يُعيد كتابة المحتوى في مكانه قبل تمريره إلى المرحلة التالية. يتطلّب `editor`. |
| `continue` | وضع الظل / التسجيل فقط — يُسجِّل النقد ولا يُغيّر شيئًا. |

احصل على معرِّف الحَكَم اللغوي عبر `LLM_ASSET_ID = aix.Model.get("openai/gpt-4o").id`، أو استخدم الافتراضي المدمج: `from aixplain.v2.inspector import AUTO_DEFAULT_MODEL_ID` (هذا الثابت *لا يزال* موجودًا فعلًا).

### ABORT — الإيقاف التام

```python
guard = aix.Inspector(name="hate-speech-guard", severity="critical", targets=["output"],
    action="abort",
    metric={"assetId": LLM_ASSET_ID,
            "prompt": "If the content contains hate speech, output a failure critique. Otherwise pass."})

agent = aix.Agent(name="Guarded Agent", instructions="You are a helpful assistant.", inspectors=[guard])
agent.save()

r = agent.run(query="...")
print(r.data.output if r.status == "SUCCESS" else f"Run halted: {r.status}")
```

### RERUN — التصحيح الذاتي مع إعادات المحاولة

تُوضَع `max_retries` / `on_exhaust` **داخل قاموس الإجراء**. أمّا تمريرها كوسائط مفتاحية على المستوى الأعلى فيُطلق `TypeError` في الإصدار 0.2.48 (والوثائق المنشورة تعرض تلك الصيغة — وهي خاطئة).

```python
guard = aix.Inspector(name="customer-name-enforcer", severity="medium", targets=["output"],
    action={"type": "rerun", "max_retries": 2, "on_exhaust": "abort"},   # or "continue"
    metric={"assetId": LLM_ASSET_ID,
            "prompt": "If the output does NOT include the customer name 'John', instruct to add it."})
```

أبقِ `max_retries` بين ٢ و٣ واضبط `on_exhaust` دائمًا: `"abort"` حين يكون التقارب إلزاميًّا، و`"continue"` حين يكون الإخراج بأفضل جهد ممكن مقبولًا.

### EDIT — التنقية بدوالّك الخاصة

```python
def looks_risky(text: str) -> bool:
    import re                                   # imports go INSIDE — the function runs in isolation
    return any(re.search(p, text.lower()) for p in [r"\bbypass\b", r"\bexploit\b", r"\bhack\b"])

def sanitize(text: str) -> str:
    return "Provide high-level, ethical guidance only."

guard = aix.Inspector(name="intent-guard", severity="high", targets=["input"],
    action="edit",
    metric={"function": looks_risky},           # True  -> rewrite
    editor={"function": sanitize})              # performs the rewrite
```

تعمل مُقيِّمات الدوالّ بشكل متزامن وتحجب خطّ المعالجة — فتجنَّب عمليات الإدخال/الإخراج البطيئة.

## المُفتِّشون الجاهزون مسبقًا (ضوابط أمان من المتجر)

بدلًا من تأليف مُقيِّم بنفسك، اجلب ضابط أمان مُدارًا وأرفِقه. ويأتي كلٌّ منها بقيم افتراضية معقولة لـ `targets` وللإجراء — فلا تتجاوز إلا ما تحتاج إليه.

```python
aix.Inspector.search("guard")        # discover what's available

guard    = aix.Inspector.get("aws/detect-prompt-attacks-guardrail/aws")   # prompt-injection / jailbreak
redactor = aix.Inspector.get("aws/sensitive-information-guardrail/aws")   # PII
redactor.targets = ["output"]                                            # default is ["input"]

team = aix.Agent(name="Research Team", description="...", agents=[research_agent],
                 inspectors=[guard, redactor])
team.save(save_subcomponents=True)     # needed so a sub-agent fetched via Agent.get is saved too
```

مسارات معروفة: `aws/detect-prompt-attacks-guardrail/aws`، و`aws/sensitive-information-guardrail/aws`، و`aws/content-moderation-guardrail/aws`. ابحث بدل ترميز المسارات بشكل ثابت — فالكتالوج ينمو.

يُعيد ضابط أمان البيانات الشخصية (PII) كتابة القيم المُعلَّمة في مكانها (`"...your phone number is {PHONE}"`) بدلًا من الحجب.

## قراءة نتائج الحوكمة

تُبلِّغ `response.data.governance` عمّا نفّذته الحوكمة على الطلب — بما في ذلك التشغيلات التي لم يُرفَق بها أي مُفتِّش. استخدمها لتأكيد أن ضابط الأمان قد عمل فعلًا، إلى جانب خطوة وكيل النظام الخاصة بالمُفتِّش في `response.data.steps`.

يعمل المُفتِّشون بترتيب التصريح. ولإضافة مُفتِّش إلى وكيل قائم: `agent.inspectors.append(guard); agent.save()` — فإعادة الحفظ إلزامية، وإلا لم تظهر خطوة المُفتِّش في الأثر.

> **التحقّق من أن المُفتِّش يعمل:** مُولِّد الاستجابة الخاص بالمنصّة مُواءَم للسلامة، وكثيرًا ما يرفض الطلبات السيئة الواضحة قبل أن يتعثّر مُفتِّشك، لذا قد يُسجِّل المُفتِّش `continue` (نجاح) بدل `abort` أمام استعلام خصومي صريح. وهذا لا يعني أنه معطّل. ولإثبات أن البوابة تعمل، استخدم مُدخَلًا ينتهك السياسة *بشكل حتمي* (مثل وكيل فرعي مأمور بإصدار القيمة المحظورة).

خريطة موصى بها من الخطورة إلى الإجراء: `low`←`continue`؛ `medium`←`rerun`(`on_exhaust="continue"`) أو `edit`؛ `high`←`rerun`(`on_exhaust="abort"`) أو `edit`؛ `critical`←`abort`.

### تحقَّق بعد كل تغيير في المُفتِّشين

| الاختبار | السلوك المتوقَّع |
|---|---|
| موجّه **مسموح** | مسار المتابعة؛ إجابة عادية ملتزمة |
| موجّه **مرفوض** | محجوب/مرفوض؛ لا تسرُّب لأي بيانات أو إجراءات مقيّدة |
| موجّه **ملتبس** | معالجة متحفّظة — الرفض أو طلب التوضيح |

ولكل حالة، سجِّل: الموجّه، والإجراء المتوقَّع، وحالة التشغيل `status` المرصودة، وملخّصًا للإخراج في سطر واحد، والنتيجة نجاح/فشل.

### دلالات الحالات

أبقِ حالة التشغيل في aiXplain كما هي: `IN_PROGRESS | SUCCESS | FAILED`. **لا تعامِل الحجب بموجب السياسة على أنه `FAILED`** — فالمُفتِّش الذي يرفض محتوى غير آمن قد يُعيد مع ذلك `status == "SUCCESS"` مع رفض آمن في `data.output`. هذا حجب حوكمة، لا فشل تشغيل.

## المُصحِّح (Debugger) — تحليل تشغيل

```python
debugger = aix.Debugger()
result = debugger.debug_response(agent.run(query="..."))   # auto-extracts the execution id
print(result.analysis)                                      # plain-English explanation
# also: result.used_credits, result.run_time, result.session_id, result.request_id
debugger.run(content="The agent returned an empty response...").analysis   # arbitrary content
```

> يأتي المُصحِّح ضمن الـ SDK، لكن الخدمة التي يستند إليها غير متاحة في كل بيئة. فإذا أعاد الاستدعاء "Not Found"، فارتدّ إلى `response.data.steps` (انظر `references/agents.md`).

## المُطوِّر (Evolver) — التحسين المستمر

الوكيل الفوقي من aiXplain لتحسين وكيلٍ ما انطلاقًا من إشارات الإنتاج (تنقيح التعليمات، واختيار الأدوات، وتركيب الفريق، وضبط المُعاملات).

> للقياس والتسجيل **غير المتصلين** لجودة الوكيل (خلافًا لضوابط الأمان أثناء التشغيل)، صار الـ SDK يوفّر `aix.Eval` و`aix.Metric` — انظر `references/evaluation.md`.

> لا يزال **غير مكشوف كواجهة برمجية مستقرة في Python** — فلا يوجد صنف `aix.Evolver()`. (تقبل `agent.run(...)` مُعاملًا اسمه `evolve` سلوكه غير موثَّق.) لا تختلق واجهة برمجية للمُطوِّر. وجِّه المستخدمين إلى Studio، واعرض البديل العملي: التكرار باستخدام المُصحِّح وآثار الاستدلال، واختبار تعليمات/أدوات مختلفة بأسلوب A/B.

## Bodyguard / التحكّم في الوصول

يُنفَّذ على مستوى المنصّة/وقت التشغيل وعبر تحديد نطاق مفاتيح الـ API — انظر `references/deployment-access.md § API keys`. وليس صنفًا في Python تُنشئ منه كائنًا.
