# النشر والوصول (REST، JS، متوافق مع OpenAI، مفاتيح API)

## نشر الوكلاء

`agent.save()` **هي** خطوة النشر — لا توجد دالة `agent.deploy()` منفصلة. يرفّع الحفظ الوكيل من `DRAFT` إلى `ONBOARDED`، مانحًا إياه نقطة نهاية مستمرة عديمة الخوادم ذاتية التوسّع على سحابة aiXplain المُدارة، يمكن الوصول إليها عبر المُعرّف من خلال REST API أدناه. وللفرق استخدم `team.save(save_subcomponents=True)`.

بعد النشر، وجّه المستخدم إلى Studio:
- البنّاء المرئي / الآثار: `https://studio.aixplain.com/build/<AGENT_ID>/schema`
- التحليلات: `https://studio.aixplain.com/dashboard/analytics/?agent=<AGENT_ID>`

**خاص / محلي (on-prem) / طرفي (edge):** يعمل تعريف الوكيل نفسه دون تغيير عبر السحابة المُدارة، والبيئة المحلية (بما في ذلك المعزولة عن الشبكة، بلا اتصال صادر)، والبيئة الطرفية — وتنتقل الحوكمة والذاكرة معه. تُنشر البيئة المحلية كخدمات محتواة في حاويات (Docker Compose / Kubernetes) ويُرتَّب لها عبر aiXplain، وليس عبر مفتاح في الـ SDK. لا يوجد إعداد SDK موثّق لكل عملية نشر (مثل عنوان URL مخصص للخلفية) — وجّه مستخدمي المؤسسات إلى aiXplain لإعداد البيئة المحلية.

## REST API — تشغيل وكيل منشور

تكون عمليات تشغيل الوكلاء غير متزامنة دائمًا: تُرجع `POST` عنوان URL للاستقصاء، ثم تنفّذ `GET` عليه حتى الاكتمال. ترويسة المصادقة هي `x-api-key`.

```bash
# 1. Submit
curl -X POST 'https://platform-api.aixplain.com/v2/agents/<AGENT_ID>/run' \
  -H 'x-api-key: YOUR_API_KEY' -H 'Content-Type: application/json' \
  -d '{"query": "What is 5 + 5?", "sessionId": "user_123_session"}'
# -> {"requestId": "...", "data": "https://platform-api.aixplain.com/sdk/agents/<REQUEST_ID>/result"}

# 2. Poll the URL returned in "data"
curl -X GET 'https://platform-api.aixplain.com/sdk/agents/<REQUEST_ID>/result' \
  -H 'x-api-key: YOUR_API_KEY'
# -> {"completed": true, "status": "SUCCESS", "data": {"output": "10", "session_id": "...", ...}}
```

- يجب أن يكون `query` على **المستوى الأعلى** (`{"data":{"query":...}}` يفشل برسالة `query should not be empty`).
- معاملات تشغيل اختيارية على المستوى الأعلى: `maxTokens`، `maxIterations`، `outputFormat` (`text`|`markdown`|`json`).
- التعدد الحواري: إما أن تحذف `sessionId` في الاستدعاء الأول وتعيد إرسال `data.session_id` في الاستدعاءات اللاحقة، **أو** ترسل مصفوفة `history` من أدوار `{"role","content"}`.
- توجد الإجابة في `data.output`. استقصِ ما دامت `status == "IN_PROGRESS"`؛ وتوقّف عند `SUCCESS`/`FAILED`.

حلقة استقصاء بلغة Python (requests):

```python
import requests, time
H = {"x-api-key": API_KEY, "Content-Type": "application/json"}
start = requests.post(f"https://platform-api.aixplain.com/v2/agents/{AGENT_ID}/run",
                      headers=H, json={"query": "Summarize this ticket."}, timeout=30).json()
poll_url = start["data"]
while True:
    res = requests.get(poll_url, headers=H, timeout=30).json()
    if res.get("completed"):
        print(res["data"]["output"]); break
    time.sleep(2)
```

## REST API — تشغيل نموذج مباشرة

نقطة نهاية تنفيذ واحدة لجميع الوسائط. القاعدة `https://models.aixplain.com`.

```bash
curl -X POST 'https://models.aixplain.com/api/v2/execute/<MODEL_ID>' \
  -H 'x-api-key: YOUR_API_KEY' -H 'Content-Type: application/json' \
  -d '{"text": "What is 2 + 2?"}'
```

إذا كانت الاستجابة تحوي `"completed": true`، فإن النتيجة في `data`. وإذا كانت `data` عنوان URL، فاستقصِ ذلك العنوان نفسه بالضبط (قد يتغيّر المضيف/الإصدار حسب الخدمة) حتى الاكتمال. مُدخلات أخرى: معاملات توليد النموذج اللغوي (`max_tokens`، `temperature`)؛ نص المحادثة `text` كمصفوفة `[{role,content}]`؛ الرؤية عبر مصفوفة `content` مع أجزاء `image_url.url` (عنوان URL عام أو `data:` بترميز base64)؛ نص تحويل النص إلى كلام `text`؛ التعرف على الكلام `language` + عنوان URL لـ `source_audio`؛ بث SSE عبر `"stream": true` (ينتهي بـ `data: [DONE]`)؛ البيانات الخام من المزوّد عبر `"options": {"includeRawData": true}`.

اكتشاف معاملات النموذج: `GET https://platform-api.aixplain.com/sdk/models/<MODEL_ID>` (يُرجع مصفوفة `params` تحتوي name/required/dataType/defaultValues).

## JavaScript / TypeScript

```javascript
const res = await fetch(`https://platform-api.aixplain.com/v2/agents/${AGENT_ID}/run`, {
  method: "POST",
  headers: { "x-api-key": API_KEY, "Content-Type": "application/json" },
  body: JSON.stringify({ query: "What is the weather today?", sessionId: "user_123" }),
});
const { data: pollUrl } = await res.json();              // data = polling URL
// then GET pollUrl with the same x-api-key header until { completed: true }
```

## واجهة API المتوافقة مع OpenAI

استخدم وكيل aiXplain أو نموذجًا منها كبديل مباشر لعميل OpenAI.

```python
from openai import OpenAI
client = OpenAI(api_key="YOUR_AIXPLAIN_API_KEY", base_url="https://api.aixplain.com/v1")
r = client.chat.completions.create(
    model="<AGENT_OR_MODEL_ASSET_ID>",
    messages=[{"role": "user", "content": "How do I create an agent?"}],
)
print(r.choices[0].message.content)
```

> تُظهر الوثائق عنوان القاعدة `https://api.aixplain.com/v1` مع مُعرّف أصل مجرّد كقيمة لـ `model`. وتشير مواد أخرى إلى `https://models.aixplain.com/api/v1/` وإلى صيغة نموذج `agent-<id>`. إذا أعطت إحدى الصيغتين خطأ 404، فجرّب الأخرى وتأكّد من ذلك مقابل وحدة تحكم Studio لدى المستخدم.

## رفع ملف محلي (REST)

تأخذ نقاط نهاية التنفيذ عناوين URL، لا بايتات الملفات. ارفع الملف أولًا (ملاحظة: تستخدم نقاط نهاية رفع الملفات الترويسة `Authorization: token YOUR_API_KEY`، **وليس** `x-api-key`):

1. `POST https://platform-api.aixplain.com/sdk/file/upload/temp-url` مع `{contentType, originalName}` ← `{key, uploadUrl, downloadUrl}`
2. نفّذ `PUT` لبايتات الملف إلى `uploadUrl`
3. مرّر `downloadUrl` إلى النموذج/الوكيل.

من Python يغلّف الـ SDK هذا: `FileUploader(api_key=...).upload(file_path, is_temp=True, return_download_link=True)` (استخدم `return_download_link=True` للحصول على عنوان URL قابل للنقر في المتصفح، لا مسار `s3://` خام). حدود الحجم: الصوت 50 MB، الصور/المستندات 25 MB، الفيديو/قواعد البيانات 300 MB.

## الوصول عبر خادم MCP

يمكن الوصول إلى كل نموذج/أداة في السوق عبر MCP على العنوان `https://models-mcp.aixplain.com/mcp/<ASSET_ID_OR_ENCODED_PATH>` (رمّز `/` بترميز URL على هيئة `%2F`). تختلف المصادقة هنا أيضًا: `Authorization: Bearer <KEY>` بالإضافة إلى `Accept: application/json, text/event-stream`. للإضافة إلى Claude Code: `claude mcp add --transport http <name> <url> --header "Authorization: Bearer <key>"`.

## مفاتيح API ومبدأ الحد الأدنى من الامتيازات

تأتي المفاتيح من Console ← Settings ← API Keys (`https://console.aixplain.com/settings/keys`)؛ يُعرض المفتاح الكامل مرة واحدة فقط. بحد أقصى 10 لكل مساحة عمل؛ والمفاتيح خاصة بمساحة العمل. حدّد نطاق مفتاح لأصول محددة وحدود معدل:

```python
from aixplain.v2 import APIKey, APIKeyLimits, TokenType

key = APIKey.get("your-api-key-id")
key.asset_limits = [APIKeyLimits(
    model="6646261c6eb563165658bbb1",          # asset ID (not path)
    token_per_minute=300_000, token_per_day=144_000_000,
    request_per_minute=60, request_per_day=28_800,
    token_type=TokenType.OUTPUT,
)]
key.save()
```

مراقبة الاستخدام: `aix.APIKey.get_usage_limits()` أو `get_usage_limits(model=MODEL_ID)` (استخدم المُعرّفات، لا المسارات). تظهر أخطاء تجاوز حد المعدل على هيئة HTTP **497** (حد aiXplain لكل دقيقة) أو **429**. أخطاء REST أخرى: 401 مفتاح غير صالح، 492 تعذّر جلب عنوان URL للمُدخل، 400 استعلام `query` مشوّه/فارغ.

## الأرصدة والفوترة

رصيد واحد = 1 دولار أمريكي. تُفوتر النماذج/الأدوات/التكاملات بأسعار المزوّد (هامش 0%). تضيف **الوكلاء** المنشورة هامشًا قدره 20% فوق مجموع استدعاءات النماذج + الأدوات (يغطي التنسيق، والوكلاء الدقيقة للمخطط/المنسّق/المفتش، والذاكرة، والتحقق). تتبّع الإنفاق عبر `response.used_credits`، أو Console ← Transactions، أو تبويب Validation في Studio.

## ما لا يغطيه الـ v2 SDK (الإصدار v1 القديم فقط)

عميل `aix.*` الموحّد (`from aixplain import Aixplain`) محوره الوكلاء/النماذج/الأدوات. **خطوط الأنابيب (Pipelines)، والضبط الدقيق (fine-tuning)، والقياس المرجعي (benchmarking)، ومجموعات البيانات/المتون (datasets/corpora) ليس لها واجهة v2 API.** وهي موجودة فقط في مصانع الإصدار v1 القديم:

```python
# Legacy v1 — only if the user explicitly needs these capabilities
from aixplain.factories import PipelineFactory, FinetuneFactory, BenchmarkFactory, DatasetFactory, CorpusFactory
pipeline = PipelineFactory.get("<pipeline_id>")
result = pipeline.run("input")
```

بالنسبة إلى **خطوط الأنابيب**، يُفضَّل بناؤها بصريًا في aiXplain Studio ثم تشغيلها عبر المُعرّف (Studio، أو نقاط نهاية خطوط الأنابيب في REST `https://platform-api.aixplain.com`، أو `PipelineFactory` في الإصدار v1). لا يحتوي الـ Python v2 SDK الحالي على بنّاء خطوط أنابيب. إذا طلب مستخدم "بناء خط أنابيب" في Python، فأخبره بهذا واعرض إما Studio أو ما يكافئه على هيئة **وكيل فريقي** (وهي الطريقة الأصلية في v2 لتركيب مهام سير عمل متعددة الخطوات).

## الهجرة من v1 إلى v2

استخدم `from aixplain import Aixplain; aix = Aixplain(api_key=...)` ثم `aix.Agent` / `aix.Model` / `aix.Tool`. تجنّب مصانع الإصدار v1 المهجورة `aixplain.factories.*` (`AgentFactory`, `ModelFactory`, …) لأي شيء يغطيه عميل v2. إذا رأيت شيفرة مصانع قديمة، فانقلها إلى مكافئاتها في `aix.*`.
