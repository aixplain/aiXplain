# أدلة التكامل العملية

أنماط الاتصال حسب نوع التكامل.
مرتبط من المهارة الرئيسية — يُستشار عند توصيل الأدوات.

nقطة الدخول الأساسية v2:
- استخدم `from aixplain import Aixplain`.
- استخدم `aix.Tool` و`aix.Integration` مباشرةً من واجهة عميل v2.

استخدم `integration.list_actions()` و`integration.list_inputs(action_name)` قبل الاتصال في تدفقات SDK. احرص دائمًا على تحديد نطاق الإجراءات بمجموعة غير فارغة ذات أقل صلاحيات.

---

## 1. قاعدة المعرفة aiR (`6904bcf672a6e36b68bb72fb`)

اتصل بملفات مرفوعة (`.pdf`، `.docx`، `.txt`، `.md`، `.html`، `.csv`) أو ابدأ فارغًا واكتب باستخدام `upsert`.

**الإجراءات النموذجية:** `search`، `get`، `count`، `metadata`، واختياريًا `upsert`.
**أفضل الممارسات:** حافظ على نطاق الاسترجاع أولًا (`search`، `get`، `metadata`) ما لم تكن الكتابة أثناء التشغيل مطلوبة صراحةً.

```python
index_tool = aix.Tool(
    name="My Knowledge Base",
    description="Semantic search over uploaded documents",
    integration="6904bcf672a6e36b68bb72fb",
).save()

# Populate
records = [
    {"id": "doc1", "text": "Python is a programming language", "metadata": {"category": "tech"}},
    {"id": "doc2", "text": "Machine learning uses algorithms", "metadata": {"category": "ai"}},
]
index_tool.run(action="upsert", data={"records": records})

# Query
index_tool.run(action="search", data={"query": "programming", "filters": []})
index_tool.run(action="count", data={})
```

يعمل البحث الدلالي فورًا بعد `upsert`؛ ويُعيد `count` إجمالي المستندات المفهرسة.

---

## 2. PostgreSQL (`693ac6e8217c7b13b480970f`)

اتصل باستخدام عنوان URL لقاعدة البيانات: `postgresql://username:password@host:port/database`.

- يُفضَّل استخدام مستخدمي قاعدة بيانات للقراءة فقط لمساعدي التحليل.
- حدِّد نطاق إجراءات الاستعلام أولًا؛ وفعِّل إجراءات الكتابة فقط عند الحاجة الصريحة.

---

## 3. قاعدة بيانات SQLite (`689e06ed3ce71f58d73cc999`)

اتصل باستخدام عنوان URL لملف `.db` عبر `config={"url": "<download_url_to_db_file>"}`.

- الإجراءات الصالحة: `query`، `schema`، `commit`.
- النطاق الآمن الافتراضي: `["query", "schema"]`.
- يرفض اتصال SQLite أنواع الملفات غير `.db`.

```python
from aixplain.v2.upload_utils import FileUploader

integration = aix.Integration.get("689e06ed3ce71f58d73cc999")
uploader = FileUploader(api_key=api_key, backend_url=aix.backend_url)
db_url = uploader.upload("/absolute/path/to/data.db", is_temp=True, return_download_link=True)

sqlite_tool = aix.Tool(
    name="SQLite Reader",
    description="Read-only DB access",
    integration=integration,
    config={"url": db_url},
    allowed_actions=["query", "schema"],
).save()
```

---

## 4. صندوق حماية Python (`688779d8bfb8e46c273982ca`)

اتصل بملف `.py` أو شيفرة مصدرية مضمّنة وعيِّن `function_name` للدالة المكشوفة.

### قيود التأليف

تم التحقق منها مقابل aiXplain SDK v0.2.44. اتبع قيود التأليف التالية:

1. **يجب أن يتطابق `function_name` مع دالة معرَّفة في `code`.** إذا ضمّنت عدة دوال في كتلة شيفرة واحدة، فإن الدالة التي يساوي اسمها `function_name` فقط هي التي تُسجَّل كأداة.
2. **استخدم `int` (0/1) بدلًا من معاملات `bool`.** يمرر مُسلسِل وقت التشغيل JSON `true`/`false` (بأحرف صغيرة)، والتي يفسرها Python كأسماء غير معرَّفة. استخدام `int` يتجنب ذلك.
3. **أعِد `dict` أو `list`، وليس tuples.** يُحوَّل `return a, b` إلى السلسلة النصية `"(a, b)"` عند النقل ذهابًا وإيابًا. للمخرجات المهيكلة، أعِد دائمًا `dict` أو `list`.

### ملاحظات v2

- تُكتشف مواصفات الإجراءات/المدخلات الخاصة بالتكامل بعد الاتصال (`list_actions`/`list_inputs`).
- الشيفرة المساعدة المخصصة (`aix.Utility`) لها قواعد تحليل منفصلة وتتطلب `def main(...)`؛ لا تخلط بينها وبين أدوات تكامل صندوق حماية Python.

```python
script_content = """def sum_then_square(first_number: int, second_number: int):
    total = first_number + second_number
    return total * total
"""
tool = aix.Tool(
    name="Sum and Square",
    description="Sums two numbers and squares the result.",
    integration="688779d8bfb8e46c273982ca",
    config={"code": script_content, "function_name": "sum_then_square"},
).save()

result = tool.run(action="sum_then_square", data={"first_number": 2, "second_number": 3})
```

---

## 5. تكاملات OAuth (Gmail، Slack، Jira، Google Drive)

سير العمل موصوف في SKILL.md § 3 (إنشاء الأدوات، المسار C). يوفر هذا القسم الشيفرة.

```python
import warnings

integration = aix.Integration.get("6864328d1223092cb4294d30")  # Gmail
actions = integration.list_actions()

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    gmail_tool = aix.Tool(
        name="My Gmail Tool",
        description="Send emails",
        integration=integration,
        allowed_actions=["GMAIL_SEND_EMAIL"],
    ).save()
    oauth_url = next((str(x.message) for x in w if "http" in str(x.message)), None)

print(f"Connect Gmail: {oauth_url}")
# User completes OAuth, then attach to agent:
agent = aix.Agent(
    name="Gmail Agent", instructions="Use Gmail to send emails.",
    tools=[gmail_tool], output_format="markdown",
).save()
```

<!-- ملاحظات الترجمة: استخدام "صندوق حماية" لـ Sandbox للوضوح التقني | "مُسلسِل" لـ serializer | kept EN: PostgreSQL, SQLite, Gmail, Slack, Jira, Google Drive, OAuth, Python, JSON — أسماء علامات تجارية/تقنيات | kept EN: upsert, query, schema, commit, search, get, count, metadata — أسماء إجراءات برمجية | "أقل صلاحيات" لـ least-privilege -->
