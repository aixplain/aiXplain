# التقييم — عمليات التقييم والمقاييس

جديد في SDK 0.2.48: `aix.Eval` (مشغّل التجارب) و `aix.Metric` (أصول الحَكَم المعتمِد على النماذج اللغوية) لقياس جودة الوكيل.

> ⚠️ **متاح في حزمة التطوير فقط وغير موثّق.** لا يظهر `aix.Eval` ولا `aix.Metric` في أي موضع من وثائق aiXplain المنشورة حتى 2026-09، كما أن مرجع Python API المُولَّد لا يتضمن صفحة لهما. وكل ما يلي تم التحقق منه عبر **استبطان حزمة التطوير المثبّتة** — فالتواقيع وأسماء الدوال حقيقية، لكن سير العمل من طرف إلى طرف مستنتَج من تلك التواقيع، لا من مثال موثّق. تعامل معه كنقطة انطلاق: شغّل تجربة صغيرة أولًا وتأكد من بنى البيانات قبل الاعتماد عليه. ولا تقدّمه للمستخدم على أنه واجهة برمجية مستقرة.

## المقاييس — أصول الحَكَم المعتمِد على النماذج اللغوية

المقياس `Metric` هو أصل في السوق يمكنك جلبه أو تشغيله أو إرفاقه كأداة.

```python
metric = aix.Metric.get("<metric_id_or_path>")     # or: aix.Metric.search("relevance")
metric.list_actions()                               # discover actions
metric.run(data={...})                              # score something
tool = metric.as_tool()                             # attach to an agent like any other tool
```

### إنشاء حَكَم مخصّص

```python
m = aix.Metric.create(
    name="Answer relevance",
    llm_path="openai/gpt-4o",              # the judging model
    metric_description="Scores how well the answer addresses the question.",
    prompt_template="...",                  # your rubric prompt
    score_type="number",                    # or categories=[...] for labels
    start_number=1, end_number=5,           # numeric range
    # categories=["good","bad"], detailed_rubric={...}, instruction="...", auto_complete=False
)
```

التوقيع المُتحقَّق منه: `Metric.create(name, llm_path, metric_description="", prompt_template=None, score_type=None, instruction=None, start_number=None, end_number=None, categories=None, detailed_rubric=None, auto_complete=False, allowed_actions=None, **kwargs)`.

> مزلق: `Metric.create` **يتجاهل `allowed_actions` بصمت**، كما تُنشأ المقاييس على تكامل `aixplain/custom-llm-prompt/aixplain`.

## عمليات التقييم — تشغيل التجارب

```python
ev = aix.Eval(
    cache_experiments=True,        # cache runs locally (default True)
    experiment_cache_dir=None,     # where to cache
    autosave_eval_runs=None,       # persist runs server-side
)
```

الدوال المُتحقَّق منها في `aix.Eval`:

| الدالة | الغرض |
|---|---|
| `create_experiment(...)` | تعريف تجربة (وكيل أو أكثر + حالات + مقاييس). |
| `evaluate(...)` | تشغيل التقييم واحتساب الدرجات. |
| `load_from_csv(...)` | بناء حالات التقييم من ملف CSV يضم المدخلات والمخرجات المتوقعة. |
| `list_cached_experiments()` | سرد التجارب المخزّنة محليًا. |
| `load_cached_experiment(...)` | إعادة تحميل تجربة مخزّنة بدلًا من إعادة تشغيلها. |

الأنواع الداعمة موجودة في `aixplain.v2.eval_experiment` — وهي `Experiment` و `ExperimentRun` و `EvalCase` و `Dataset` و `AgentEvaluationRow` و `AgentEvaluationRun` و `ExperimentLocalCache` — وفي `aixplain.v2.agent_evaluator` (`AgentEvaluationResultsChatbot` و `BASE_METRIC_PROMPT_TEMPLATE` و…). افحص هذه الأنواع قبل كتابة أي سير عمل:

```python
import inspect, aixplain.v2.eval_experiment as ee
print(inspect.signature(ee.Experiment.__init__))
print(inspect.signature(aix.Eval.create_experiment))
```

## كيف تستخدم هذا بمسؤولية

لأن هذه الواجهة غير موثّقة، فإن التصرف الأمين حين يطلب المستخدم تقييم وكيل هو:

1. أن توضّح أن aiXplain تشحن واجهة تقييم داخل حزمة التطوير لكنها لم توثّقها بعد.
2. أن تستبطن التواقيع الدقيقة في النسخة المثبّتة لدى *المستخدم* (فقد تختلف عن 0.2.48) وتبني انطلاقًا منها.
3. أن تبدأ بمقياس واحد وحفنة من الحالات، وتتأكد من بنية النتيجة، ثم توسّع النطاق.
4. أن تتبع عادة "الإبلاغ عن مشكلات aiXplain" الواردة في `SKILL.md` إذا أساءت الواجهة التصرف بطريقة يبدو أن سببها من aiXplain.

وللحوكمة/الضوابط الوقائية في زمن التشغيل (بخلاف احتساب الدرجات دون اتصال)، راجع `references/governance.md`.
