# قواعد المعرفة (RAG) والذاكرة

## قاعدة المعرفة = أداة فهرسة على aiR

قاعدة المعرفة هي فهرس متجهي يُنشأ بوصفه `Tool` مرتبطًا بتكامل قاعدة بيانات المتجهات aiR ذي المعرّف `6904bcf672a6e36b68bb72fb`. ولا يوجد صنف `Index` منفصل — بل هو `aix.Tool(...)`. سير العمل: **الإنشاء ← إدراج المستندات ← التقييد بالقراءة فقط ← الإرفاق بالوكيل.**

### 1. الإنشاء

```python
import time
index = aix.Tool(
    name=f"Product Index {int(time.time())}",
    description="Vector database for product information.",
    integration="6904bcf672a6e36b68bb72fb",     # aiR vector database — always this ID
    # optional: pick the embedding model used at upsert time
    # config={"model": "67efd4f92a0a850afa045af7"},
)
index.save()
index.list_actions()    # exactly six: search, count, upsert, get, delete, metadata
```

### 2. استيعاب المستندات (`upsert`)

السجلات عبارة عن قواميس تضم `id` و`text` (مطلوبان) و`metadata` اختياريًّا (يتيح الترشيح). والنص محدود بمئة ألف حرف لكل مستند.

```python
documents = [
    {"id": "doc1", "text": "Wireless headphones, $79, electronics", "metadata": {"category": "electronics", "price": 79}},
    {"id": "doc2", "text": "Cotton t-shirt, $19, apparel",          "metadata": {"category": "apparel", "price": 19}},
]
index.run(action="upsert", data={"records": documents})

# Override the default chunking (defaults are sentence / 10 / 3 — see the table):
index.run(action="upsert", data={
    "records": documents,
    "chunking": {"split_by": "sentence", "split_length": 3, "split_overlap": 1},
})

# Store each document as one record — no chunking at all:
index.run(action="upsert", data={"records": documents, "chunking": {"enabled": False}})

# Delimiter / regex splitting:
index.run(action="upsert", data={
    "records": documents,
    "chunking": {"split_by": "regex", "split_delimiter": r"\n#{1,3}\s",
                 "split_length": 1, "split_overlap": 0},
})
```

وإغفال `chunking` كليًّا يطبّق القيم الافتراضية أدناه — **لا** القيمتين `3`/`1` الموضحتين أعلاه.

| `chunking.*` | النوع | الافتراضي | ملاحظات |
|---|---|---|---|
| `enabled` | `bool` | `true` | `false` = سجل واحد لكل مستند، دون تقسيم |
| `split_by` | `str` | `"sentence"` | `word` \| `sentence` \| `passage` \| `page` \| `line` \| `string` \| `regex` — ولا وجود **إطلاقًا** لـ `"character"` |
| `split_length` | `int` | `10` | عدد الوحدات في كل مقطع، `>= 1` |
| `split_overlap` | `int` | `3` | `>= 0` **و** `< split_length` |
| `split_delimiter` | `str` | — | مطلوب عندما تكون `split_by` بقيمة `"string"` أو `"regex"` |

التحميل من ملف CSV (أعمدة البيانات الوصفية تعود بصيغة سلاسل نصية — أعد تحليلها):

```python
import ast, pandas as pd
df = pd.read_csv("documents.csv")
df["metadata"] = df["metadata"].apply(ast.literal_eval)
documents = df.to_dict(orient="records")
```

> المستندات المصدرية (ملفات PDF، وصفحات الويب، وغيرها) تعالجها أنت مسبقًا وتضعها في حقل `text` — فالفهرس يستوعب السجلات، لا الملفات أو الروابط الخام مباشرةً.

### 3. البحث المباشر

```python
r = index.run(action="search", data={"query": "yellow fruit"})
for rec in r.data:
    print(rec["id"], rec["text"], rec.get("score"))

# With top_k + metadata filters
r = index.run(action="search", data={
    "query": "headphones", "top_k": 5,
    "filters": [{"field": "category", "operator": "==", "value": "electronics"}],
})
```

> **مفتاح عدد النتائج — `top_k` مقابل `num_results`.** يمرّر مثال الترشيح في الوثائق الحالية `num_results`، غير أن المُستدعي الأصلي في حزمة SDK نفسها (`aixplain/v2/rlm.py`) يبني استعلامات الفهرس بـ `top_k`. وكلاهما مفتاحان في `data` يُمرَّران كما هما إلى خدمة aiR. استمر في استخدام `top_k`؛ وإن تجاهله استعلام ما، فجرّب `num_results` قبل أن تفترض أن الحد غير مدعوم.

معاملات الترشيح: `==` و`!=` و`>` و`<` و`>=` و`<=` و`in` و`not in`.

إجراءات أخرى — `get` و`delete` و`count` و`metadata` (لفحص إعدادات الفهرس). ويقبل `get` سلسلة معرّف مجرَّدة، في حين لا يحتاج `count`/`metadata` إلى `data` إطلاقًا:

```python
index.run(action="get", data={"id": "doc1"})
index.run(action="get", data="doc1")     # bare string, equivalent to the above
index.run(action="count")                 # no `data`
index.run(action="metadata")              # no `data` -> distinct values per metadata field, e.g.
                                          # {'type': ['simple','aggregate'], 'color': ['green','yellow','red']}
```

### 4. الإرفاق بوكيل (RAG الوكيلي)

قيّد الصلاحيات بالقراءة فقط أولًا، و**اطلب من الوكيل صراحةً في تعليماته أن يبحث في الفهرس** — وإلا فقد لا يستدعي الأداة.

```python
index.allowed_actions = ["search", "get"]
agent = aix.Agent(
    name="Product Assistant",
    description="Helps users find products.",
    instructions="Search the product index to answer questions. Include price and category.",
    tools=[index],
)
agent.save()
print(agent.run("Find affordable electronics under $200.").data.output)
```

> البحث الدلالي **المتجهي** وحده هو الموثَّق لأداة الفهرس. وتصف المنصة كذلك الاسترجاع عبر الرسوم البيانية وSQL (GraphRAG) على مستوى أعلى، غير أن هذين غير متاحين بوصفهما نمطي فهرسة متمايزين في وثائق SDK — فاستخدم تكاملات SQL (`references/tools-integrations.md`) للبيانات العلائقية.

## الذاكرة

| النوع | الآلية | النطاق |
|---|---|---|
| قصيرة المدى / الجلسة | `aix.Session` — انظر **`references/agents.md`** | محادثة واحدة |
| طويلة المدى، عبر الجلسات | أداة الذاكرة المشتركة | دائمة عبر عمليات التشغيل والجلسات |
| مشتركة بين الوكلاء | أداة الذاكرة المشتركة مرفقة بعدة وكلاء | أي وكيل يحمل الأداة |

### ذاكرة الجلسة (قصيرة المدى) — نُقلت

لم تعد حالة المحادثة متعددة الأدوار شأنًا يخص الذاكرة. فقد **أُزيلت** `Agent.generate_session_id()`، ولم تعد `session_id=` معاملًا في `agent.run()` — بل تُهمَل بصمت إن مُرِّرت، بحيث يكون التشغيل الذي يبدو مقيَّدًا بجلسة عديمَ الحالة في الواقع. والبديل هو `aix.Session`، الذي يُمرَّر عبر `agent.run(session=...)`.

**انظر `references/agents.md`** للاطلاع على واجهة Session. (وعبر REST ما زال حقل الإرسال هو `sessionId` — انظر `references/deployment-access.md`.)

### الذاكرة المشتركة (طويلة المدى / عبر الوكلاء)

تديرها aiXplain، وتستمر عبر عمليات التشغيل والجلسات، ولا تتطلب مفتاح طرف ثالث (فتوصيلها لا يعدو إنشاء أصل أداة خاص تديره aiXplain في مساحة عملك). مسار التكامل هو `aixplain/shared-memory/aixplain`؛ وأصل السوق هو `69a59de88e25a303cbf1b8c6` (`https://app.aixplain.com/marketplace/integrations/69a59de88e25a303cbf1b8c6`).

```python
shared = aix.Tool(
    integration="aixplain/shared-memory/aixplain",
    name="Account Memory",
    description="Persistent memory for account context.",
    config={
        "max_memory_size": 256,                         # words; default 1028, max 4096
        "memory_manager_model": "6895d6d1d50c89537c1cf237",  # GPT-5 Mini (default)
        # default is "forget" (drops oldest lines); "summarize" compresses via the manager model
        "size_management_policy": "summarize",
    },
    allowed_actions=["insert", "get", "optimize"],
)
shared.save()

shared.run(action="insert", data={"content": "ACME Corp prefers weekly updates."})
shared.run(action="get", data={})           # -> stored text in .data
shared.run(action="optimize", data={})       # compress/summarize stored memory
```

افحص ما يتطلبه كل إجراء عبر `Tool.list_inputs(*actions)`:

```python
for action in shared.list_inputs("insert", "get", "optimize"):
    print(action.name, [(p.code or p.name, p.required) for p in action.inputs or []])
# get      -> identifier (optional)
# insert   -> content (required), identifier (optional)
# optimize -> identifier (optional)
```

العزل لكل مستخدم: مرّر `identifier` إلى `insert` و`get` **و**`optimize` (مثل `data={"identifier": "customer-123", "content": "..."}`). وهو حقل يعمل في وقت التشغيل فقط — فليس مفتاحًا في `config` ولا يظهر في مربع حوار الاتصال في Studio. أرفق الأداة بوكيل واحد أو أكثر (غالبًا بـ `allowed_actions=["insert"]`) فيُحقن السياق المخزَّن في موجّه الوكيل:

```python
agent = aix.Agent(name="Support Agent", description="...", instructions="...", tools=[shared])
agent.save()
agent.run(query="What pattern should we use for ACME Corp?")
```
