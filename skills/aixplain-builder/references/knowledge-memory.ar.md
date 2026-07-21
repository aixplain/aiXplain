# قواعد المعرفة (RAG) والذاكرة

## قاعدة المعرفة = أداة فهرسة على aiR

قاعدة المعرفة هي فهرس متجهي (vector index) يُنشأ كـ `Tool` مرتبط بتكامل قاعدة بيانات aiR المتجهية `6904bcf672a6e36b68bb72fb`. لا يوجد صنف `Index` منفصل — إنها `aix.Tool(...)`. سير العمل: **إنشاء ← إدراج/تحديث المستندات (upsert) ← تحديد النطاق ليكون للقراءة فقط ← الإرفاق بالوكيل.**

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
index.list_actions()    # search, count, upsert, get, delete, metadata (also: split)
```

### 2. إدراج المستندات (`upsert`)

السجلات عبارة عن قواميس (dicts) تحتوي على `id` و`text` (مطلوبان) و`metadata` اختياري (يتيح التصفية). يقتصر النص على 100,000 حرف لكل مستند.

```python
documents = [
    {"id": "doc1", "text": "Wireless headphones, $79, electronics", "metadata": {"category": "electronics", "price": 79}},
    {"id": "doc2", "text": "Cotton t-shirt, $19, apparel",          "metadata": {"category": "apparel", "price": 19}},
]
index.run(action="upsert", data={"records": documents})

# Chunk long texts on the way in:
index.run(action="upsert", data={
    "records": documents,
    "chunking": {"split_by": "sentence",   # "word" | "sentence" | "character"
                 "split_length": 3, "split_overlap": 1},
})
```

التحميل من ملف CSV (تعود أعمدة البيانات الوصفية metadata كسلاسل نصية — أعد تحليلها):

```python
import ast, pandas as pd
df = pd.read_csv("documents.csv")
df["metadata"] = df["metadata"].apply(ast.literal_eval)
documents = df.to_dict(orient="records")
```

> تُعالَج المستندات المصدرية (ملفات PDF، صفحات الويب، إلخ) مسبقًا من قِبلك ضمن الحقل `text` — يستوعب الفهرس سجلات، لا ملفات/عناوين URL خامة مباشرة.

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

عوامل التصفية: `==`، `!=`، `>`، `<`، `>=`، `<=`، `in`، `not in`. إجراءات أخرى: `get` (`data={"id": "doc1"}`)، و`delete`، و`count`، و`metadata` (لفحص إعدادات الفهرس).

### 4. الإرفاق بالوكيل (RAG وكيلي)

حدّد النطاق ليكون للقراءة فقط أولًا، و**أخبر الوكيل في تعليماته بأن يبحث في الفهرس** — وإلا فقد لا يستدعي الأداة.

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

> الموثّق فقط لأداة الفهرس هو البحث الدلالي **المتجهي** (vector). تصف المنصة أيضًا الاسترجاع عبر الرسوم البيانية وعبر SQL (GraphRAG) على مستوى أعلى، لكن هذه الأنماط ليست مكشوفة كأوضاع متمايزة لأداة الفهرس في وثائق الـ SDK — استخدم تكاملات SQL (`references/tools-integrations.md`) للبيانات العلائقية.

## الذاكرة

| النوع | الآلية | النطاق |
|---|---|---|
| قصيرة المدى / للجلسة | `agent.run(session_id=...)` + `generate_session_id()` | محادثة واحدة |
| طويلة المدى، عبر الجلسات | أداة Shared Memory | دائمة عبر التشغيلات/الجلسات |
| مشتركة بين الوكلاء | أداة Shared Memory مرفقة بعدة وكلاء | أي وكيل يحمل الأداة |

### ذاكرة الجلسة (قصيرة المدى)

```python
session_id = agent.generate_session_id()          # or generate_session_id(history=[{"role","content"}, ...])
agent.run(query="My name is Sam.", session_id=session_id)
agent.run(query="What's my name?", session_id=session_id)   # remembers within the session
```

### الذاكرة المشتركة (طويلة المدى / عبر الوكلاء)

تُدار من قِبل aiXplain، وتدوم عبر التشغيلات والجلسات، دون مفتاح طرف ثالث. مسار التكامل `aixplain/shared-memory/aixplain`.

```python
shared = aix.Tool(
    integration="aixplain/shared-memory/aixplain",
    name="Account Memory",
    description="Persistent memory for account context.",
    config={
        "max_memory_size": 256,                         # words; default 1028, max 4096
        "memory_manager_model": "6895d6d1d50c89537c1cf237",  # GPT-5 Mini (default)
        "size_management_policy": "summarize",          # "summarize" | "forget" (default)
    },
    allowed_actions=["insert", "get", "optimize"],
)
shared.save()

shared.run(action="insert", data={"content": "ACME Corp prefers weekly updates."})
shared.run(action="get", data={})           # -> stored text in .data
shared.run(action="optimize", data={})       # compress/summarize stored memory
```

العزل لكل مستخدم: مرّر `identifier` إلى `insert`/`get` (مثل `data={"identifier": "customer-123", "content": "..."}`). أرفق الأداة بوكيل واحد أو أكثر (غالبًا `allowed_actions=["insert"]`)، ويُحقن السياق المخزَّن في موجّه (prompt) الوكيل:

```python
agent = aix.Agent(name="Support Agent", description="...", instructions="...", tools=[shared])
agent.save()
agent.run(query="What pattern should we use for ACME Corp?")
```
