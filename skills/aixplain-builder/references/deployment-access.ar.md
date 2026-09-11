# النشر والوصول (REST، JS، المتوافق مع OpenAI، مفاتيح API)

## نشر الوكلاء

إن `agent.save()` **هي** خطوة النشر — فلا وجود لدالة منفصلة اسمها `agent.deploy()`. الحفظ يرقّي الوكيل من `DRAFT` إلى `ONBOARDED`، فيمنحه نقطة نهاية دائمة بلا خوادم وذاتية التوسّع على السحابة المُدارة من aiXplain، يمكن الوصول إليها بالمعرّف عبر واجهة REST أدناه. أما الفرق فاستخدم معها `team.save(save_subcomponents=True)`.

بعد النشر، وجِّه المستخدم إلى التطبيق (انتقل كل شيء من `console.`/`studio.` إلى **`app.aixplain.com`**):
- لوحة المعلومات — الاستهلاك وزمن الاستجابة والتكلفة وآثار التشغيل: `https://app.aixplain.com/dashboard`
- السوق: `https://app.aixplain.com/marketplace`
- الباني المرئي: `https://app.aixplain.com/studio` · التحليلات: `https://app.aixplain.com/dashboard`
  (وحّدت aiXplain كل شيء على `app.aixplain.com`: فاعتبارًا من التوثيق `f5c016a` لم تبقَ **أي** إشارة إلى `studio.aixplain.com` / `console.aixplain.com`، ولا يوجد رابط عميق لكل وكيل موثّق من قبيل `/build/<ID>/schema`. سلِّم المستخدم **معرّف** الوكيل مع الرابط.)

### أنماط النشر الثلاثة

تعريف الوكيل وحوكمته متطابقان في الأنماط الثلاثة؛ والاختيار يقوم على احتياجات البيانات والبنية التحتية.

| النمط | موضع التشغيل | متى تختاره |
|---|---|---|
| **الويب (بلا خوادم)** | سحابة aiXplain المُدارة — وهو الافتراضي | أسرع طريق إلى الإنتاج، مع تولّي التوسّع التلقائي نيابةً عنك |
| **داخل المؤسسة (On-prem)** | بنيتك التحتية الخاصة، بما فيها المعزولة عن الشبكة | سيادة البيانات، والامتثال التنظيمي، وانعدام الاتصال الصادر |
| **سطح المكتب (Desktop)** | جهاز المستخدم نفسه، عبر aiXplain Desktop | نماذج/أدوات محلية أو سحابية مع إبقاء العمل على الجهاز |

لم يعد "Edge" نمطًا موثّقًا — فقد حلّ **Desktop** محلّه.

**Desktop** ليس له **أي سطح في الـ SDK إطلاقًا**: لا راية ولا صنف ولا أي شيء في `dir(Aixplain)`. وجِّه المستخدمين إلى الدليل على `https://app.aixplain.com/guide/desktop`؛ ولا تخترع له واجهة SDK.

**On-prem** يشغّل المنصّة بأكملها داخل شبكة العميل — فالتثبيت والتحديثات والتحقّق من الترخيص وزمن التشغيل كلها مكتفية ذاتيًا، ولا وصول لموظفي aiXplain إلى البيئة. ويُرتَّب له عبر aiXplain، **لا عبر راية في الـ SDK**، ولا يوجد إعداد SDK موثّق خاص بكل عملية نشر (مثل رابط خلفية مخصّص).

- خدمات مُحوَّاة على **Linux (Docker / Docker Compose)**، موسّعة أفقيًا خلف موازن أحمال؛ وعُقد الـ GPU لخدمة النماذج يوفّرها العميل.
- التثبيت المعزول عن الشبكة يُشحن على هيئة **حزم غير متصلة وموقّعة**؛ والتحديثات حزم تصحيح موقّعة يُتحقّق منها بمجاميع **SHA-256**؛ و**التراخيص الدائمة تُتحقَّق محليًا دون أي اتصال بالمصدر**.
- تبقى البيانات والنماذج والسجلات والقياسات داخل الشبكة. ويجري الاستدلال **في الذاكرة دون كتابة أي شيء على القرص افتراضيًا**، ولا تُستخدَم المطالبات والردود في التدريب أبدًا. والاستثناءان الوحيدان اللذان يُحفظان بموافقة صريحة هما **تضمينات RAG** و**ذاكرة الوكيل/الجلسة المُعدَّة**، وكلاهما محكوم بـ RBAC ومفاتيح محدّدة النطاق بالنموذج.
- يدعم أنظمة إقامة البيانات وحوكمة الوصول (مثل SDAIA وNCA وحماية البيانات في دول الخليج).
- **ليست كل الخدمات متاحة داخل المؤسسة** — حدِّد نطاق النشر مع aiXplain (`https://aixplain.com/enterprise-ai/`).

### قبل الإطلاق (بلا خوادم)

- تحقّق على مدخلات **تمثيلية وعدائية** معًا، مستعينًا بآثار التشغيل.
- أضف Inspectors لفحوص السلامة والجودة والامتثال.
- اضبط الوصول والحصص عبر مفاتيح API وحدود المعدّل (أدناه).
- أبقِ على إعادة المحاولات و**سلسلة احتياطية أساسية/ثانوية** لإخفاقات النماذج والأدوات، وضع **معايير إنهاء** واضحة كي لا تنفلت الحلقة.
- **التقط `requestId` في كل استدعاء** كي ترتبط عمليات المنصّة بسجلاتك الخاصة.

## واجهة REST — تشغيل وكيل منشور

**مخطّطا ترويسة مصادقة — وهنا تكمن العثرة المعتادة.** المفتاح نفسه، والترويسة مختلفة:

| نقاط النهاية | الترويسة |
|---|---|
| تنفيذ النماذج/الوكلاء والاستقصاء والاكتشاف (كل ما أدناه عدا الرفع) | `x-api-key: YOUR_API_KEY` |
| رفع الملفات فقط (`/sdk/file/upload/temp-url`, `/sdk/file/upload-url`) | `Authorization: token YOUR_API_KEY` |
| نقاط نهاية MCP (`models-mcp.aixplain.com`) | `Authorization: Bearer YOUR_API_KEY` |

الطلبات التي لها جسم تحتاج أيضًا إلى `Content-Type: application/json`. والمفتاح هو مفتاح **مساحة العمل (الفريق)** — أبقِه في جانب الخادم.

تشغيل الوكلاء غير متزامن دائمًا: فـ `POST` يُرجع رابط استقصاء، ثم تنفّذ عليه `GET` حتى يكتمل. وترويسة المصادقة هي `x-api-key`.

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

- يجب أن يكون `query` في **المستوى الأعلى** (فـ `{"data":{"query":...}}` يفشل بالخطأ `query should not be empty`).
- معاملات تشغيل اختيارية في المستوى الأعلى: `maxTokens`، `maxIterations`، `outputFormat` (`text`|`markdown`|`json`).
- للحوار متعدد الأدوار: إما أن تُغفل `sessionId` في الاستدعاء الأول وتعيد إرسال `data.session_id` في الاستدعاءات التالية، **أو** ترسل مصفوفة `history` من أدوار `{"role","content"}`.
- الإجابة في `data.output`. استقصِ ما دام `status == "IN_PROGRESS"`؛ وتوقّف عند `SUCCESS`/`FAILED`.

حلقة استقصاء بلغة Python (باستخدام requests):

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

وبالمثل، يمكنك بناء رابط الاستقصاء من `requestId` — فـ `f"https://platform-api.aixplain.com/sdk/agents/{start['requestId']}/result"` يفضي إلى المسار نفسه، وأنت تريد `requestId` في سجلاتك على أي حال. أما مع **النماذج** فداوم على استقصاء الرابط الدقيق المُرجَع في `data`: إذ يتباين مضيف الاستقصاء والإصدار (`/api/v1/data/` مقابل `/api/v2/data/`) بحسب الخدمة، كما أن استقصاء نموذج قيد التنفيذ يُرجع `{"completed": false}` مجرّدة بلا أي بيانات وصفية عن التقدّم.

## واجهة REST — تشغيل نموذج مباشرةً

نقطة نهاية تنفيذ واحدة لجميع الأنماط. القاعدة هي `https://models.aixplain.com`.

```bash
curl -X POST 'https://models.aixplain.com/api/v2/execute/<MODEL_ID>' \
  -H 'x-api-key: YOUR_API_KEY' -H 'Content-Type: application/json' \
  -d '{"text": "What is 2 + 2?"}'
```

إذا احتوت الاستجابة على `"completed": true`، فالنتيجة في `data`. وإذا كان `data` رابطًا، فاستقصِ ذلك الرابط بالضبط (فالمضيف/الإصدار قد يتباين بحسب الخدمة) حتى الاكتمال. مدخلات أخرى: معاملات توليد النماذج اللغوية (`max_tokens`، `temperature`)؛ ونصّ الدردشة `text` كمصفوفة `[{role,content}]`؛ والرؤية عبر مصفوفة `content` تضم أجزاء `image_url.url` (رابط عام أو base64 بصيغة `data:`)؛ وتحويل النص إلى كلام عبر `text`؛ والتعرّف على الكلام عبر `language` ورابط `source_audio`؛ والبثّ بـ SSE عبر `"stream": true` (وينتهي بـ `data: [DONE]`)؛ وبيانات المزوّد الخام عبر `"options": {"includeRawData": true}`.

لاكتشاف معاملات نموذج ما: `GET https://platform-api.aixplain.com/sdk/models/<MODEL_ID>` (يُرجع مصفوفة `params` تحمل name/required/dataType/availableOptions/defaultValues). وهذا هو مصدر الحقيقة لما يقبله النموذج — راجعه قبل أن تفترض وجود حقل ما.

### البثّ بـ SSE (النماذج اللغوية)

أضف `"stream": true` إلى جسم التنفيذ لتحصل على الرموز كأحداث Server-Sent Events بدل استجابة نهائية واحدة. وكل حدث سطر `data:` يحمل `chat.completion.chunk` بأسلوب OpenAI؛ اقرأ تدريجيًا من `choices[0].delta.content`. آخر حدث غير `[DONE]` يحمل إجماليات `usage`، وينتهي البثّ بـ `data: [DONE]`.

```
data: {"choices":[{"index":0,"delta":{"content":"1"},"finish_reason":null}]}
data: {"choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}
data: {"choices":[],"usage":{"prompt_tokens":12,"completion_tokens":8,"total_tokens":20}}
data: [DONE]
```

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

## الواجهة المتوافقة مع OpenAI

استخدم وكيل aiXplain أو نموذجها كبديل مباشر داخل عميل OpenAI.

```python
from openai import OpenAI
client = OpenAI(api_key="YOUR_AIXPLAIN_API_KEY", base_url="https://api.aixplain.com/v1")
r = client.chat.completions.create(
    model="<AGENT_OR_MODEL_ASSET_ID>",
    messages=[{"role": "user", "content": "How do I create an agent?"}],
)
print(r.choices[0].message.content)
```

> يعرض التوثيق الرابط الأساسي `https://api.aixplain.com/v1` مع معرّف أصل مجرّد في `model`. بينما تشير مواد أخرى إلى `https://models.aixplain.com/api/v1/` وإلى صيغة نموذج من الشكل `agent-<id>`. فإذا أعادت إحدى الصيغتين الخطأ 404، فجرّب الأخرى وتأكّد من بطاقة الأصل في `https://app.aixplain.com`.

## رفع ملف محلي (REST)

نقاط نهاية التنفيذ تأخذ روابط لا بايتات ملفات. فارفع أولًا (ملاحظة: نقاط نهاية رفع الملفات تستخدم `Authorization: token YOUR_API_KEY`، **لا** `x-api-key`):

1. `POST https://platform-api.aixplain.com/sdk/file/upload/temp-url` مع `{contentType, originalName}` ← `{key, uploadUrl, downloadUrl}`
2. نفّذ `PUT` لبايتات الملف إلى `uploadUrl`
3. مرِّر `downloadUrl` إلى النموذج/الوكيل.

ومن Python يغلّف الـ SDK هذا كله: `FileUploader(api_key=...).upload(file_path, is_temp=True, return_download_link=True)` (استخدم `return_download_link=True` للحصول على رابط قابل للنقر في المتصفح، لا مسار `s3://` خام). حدود الحجم: الصوت 50 ميغابايت، الصور/المستندات 25 ميغابايت، الفيديو/قواعد البيانات 300 ميغابايت.

## الوصول عبر خادم MCP

أي **نموذج أو أداة** في السوق متاح كخادم MCP مستضاف — ومفتاح PAYG واحد يغطي كل أصل يستطيع المفتاح بلوغه. **الوكلاء لا يكشفون خادم MCP**؛ بل النماذج والأدوات هي التي تفعل.

**نقطة النهاية:** `https://models-mcp.aixplain.com/mcp/<ASSET_ID_OR_ENCODED_PATH>`

| الصيغة | مثال |
|---|---|
| معرّف الأصل | `.../mcp/6646261c6eb563165658bbb1` |
| مسار مُرمَّز للروابط (القياسي) | `.../mcp/openai%2Fgpt-4o-mini%2Fopenai` |
| مسار بشرطات مائلة خام (يعمل أيضًا) | `.../mcp/openai/gpt-4o-mini/openai` |

أما المسارات المستبدَل فيها الشرطات السفلية (`openai_gpt-4o-mini_openai`) فهي **لا** تعمل. والمصادقة مطلوبة في كل طلب: `Authorization: Bearer <KEY>` إضافةً إلى `Accept: application/json, text/event-stream`.

**HTTP المباشر (Streamable HTTP)** — لـ Claude Code وVS Code وإصدارات Cursor الأحدث. مدخل واحد لكل أصل:

```json
{"mcpServers": {"gpt4o_mini": {
  "url": "https://models-mcp.aixplain.com/mcp/openai%2Fgpt-4o-mini%2Fopenai",
  "headers": {"Authorization": "Bearer <AIXPLAIN_APIKEY>",
              "Accept": "application/json, text/event-stream"}}}}
```

أمر مختصر في Claude Code: `claude mcp add --transport http <name> <url> --header "Authorization: Bearer <key>"`.

**جسر stdio (`mcp-remote`)** — يقرأ Claude Desktop وإصدارات Cursor الأقدم ملف `claude_desktop_config.json`، وهو لا يقبل سوى خوادم من نوع `command`، فيحتاجان إلى وسيط محلي. ويتطلّب Node 18+:

```json
{"mcpServers": {"gpt4o_mini": {
  "command": "npx",
  "args": ["-y", "mcp-remote",
           "https://models-mcp.aixplain.com/mcp/openai%2Fgpt-4o-mini%2Fopenai",
           "--header", "Authorization:${AUTH_HEADER}"],
  "env": {"AUTH_HEADER": "Bearer <AIXPLAIN_APIKEY>",
          "PATH": "/opt/homebrew/bin:/usr/bin:/bin"}}}}
```

> وجود مسافة حرفية داخل أحد عناصر `args` (مثل `"Authorization: Bearer ..."`) يُعطّل `mcp-remote` — ولهذا تقيم القيمة في `env.AUTH_HEADER`. وأبقِ مجلد `npx` ضمن `PATH` (وهو عادةً `/opt/homebrew/bin` على معالجات Apple Silicon).

قاعدة عملية: إن كان إعداد العميل يأخذ `url` فاستخدم HTTP المباشر؛ وإن كان يأخذ `command`/`args` فاستخدم الجسر.

وإن كنت تبني عميلك الخاص: تُرجع نقطة النهاية استجابات JSON-RPC **بتنسيق SSE**، فحلّل سطر `data:`. واستدعِ `tools/list` أولًا دائمًا — فاسم الأداة ديناميكي (مثل `GPT-4o Mini (669a63646eb56306647e1091)` لنموذج، و`search` لـ Tavily) ومخطّطات المدخلات تتباين بحسب الأصل. وقائمة `tools/list` فارغة تعني أن الأصل لا يكشف أي إجراءات عبر MCP؛ و`404` يعني أن المسار/المعرّف غير مفعَّل لـ MCP (جرّب معرّف الأصل)؛ و`401` يعني أن ترويسة `Authorization: Bearer` مفقودة أو أن المفتاح خاطئ.

وأداة **Marketplace Search** الخاصة بـ aiXplain (`6960f934f316da19e5f22494`) مكشوفة هي نفسها عبر MCP، فيستطيع العميل اكتشاف الأصول حواريًا ثم توصيل ما يجده.

## مفاتيح API ومبدأ الامتياز الأدنى

تأتي المفاتيح من إعدادات الفريق ← API keys (`https://app.aixplain.com/team/settings?tab=api-keys`)؛ ويُعرض المفتاح الكامل مرة واحدة فقط. الحد الأقصى 10 مفاتيح لكل مساحة عمل؛ والمفاتيح خاصة بمساحة العمل ولا يمكن نقلها بين مساحات العمل.

> **المقتطف أدناه يحتاج بصمت إلى مفتاح *admin*.** فالمالكون/المشرفون وحدهم يستطيعون إنشاء مفاتيح المشرفين، ومفتاح المشرف وحده يستطيع ضبط الحدود على المفاتيح الأخرى أو فحصها — فمفتاح العضو الذي يستدعي `APIKey.search()` يرفع `Forbidden`. والمقايضة هي: **مفاتيح المشرفين لا تستطيع تشغيل الاستدلال**، فتحتاج إلى عميلين (`aix` = مفتاح عضو للتشغيل، و`aix_admin` = مفتاح مشرف للحوكمة). ولا يزال بوسع الأعضاء استدعاء `get_usage_limits()` على مفاتيحهم الخاصة.

```python
from datetime import datetime
from aixplain.v2 import APIKey, APIKeyLimits, TokenType   # also: from aixplain.v2.api_key import ...

# Admin key: create a member key with per-asset + global limits, a budget and an expiry
new_key = aix_admin.APIKey(
    name="member-key-prod",
    asset_limits=[APIKeyLimits(
        model="6646261c6eb563165658bbb1",          # asset ID or path
        token_per_minute=300_000, token_per_day=144_000_000,
        request_per_minute=60, request_per_day=28_800,
        token_type=TokenType.OUTPUT,               # INPUT | OUTPUT | TOTAL; omit = input+output
    )],
    global_limits=APIKeyLimits(token_per_minute=100, token_per_day=1000,
                               request_per_minute=100, request_per_day=1000),
    budget=1000,                                   # total credits; raise the value to top up
    expires_at=datetime(2030, 1, 1),               # omit for a non-expiring key
).save()

# Edit an existing key — by ID, or by the key string itself
key = APIKey.get("your-api-key-id")
key = aix_admin.APIKey.get_by_access_key("TARGET_MEMBER_API_KEY")   # when you hold the secret, not the ID
print(key.id, key.name, key.is_admin, key.global_limits, key.asset_limits)
key.asset_limits = [APIKeyLimits(model="669a63646eb56306647e1091", request_per_minute=2)]
key.save()

aix_admin.APIKey.search()          # list every key in the workspace — admin only
```

الحدود العامة وحدود كل أصل تُنفَّذ **كلتاهما** — والأشد منهما هو الذي يفرض نفسه أولًا؛ والحد العام لا يبطل الحد الخاص بكل نموذج. والإنفاذ يقيم في **طبقة الوصول داخل AgenticOS** ويغطي كل مسارات الاستدعاء (REST، والـ SDK، والنموذج اللغوي الأساسي للوكيل بما في ذلك وكلاء الفرق، وخطوط الأنابيب متعددة الوكلاء)، فتحديد نموذج ما يحدّه على مستوى مساحة العمل كلها. والطلبات المتجاوزة للحد **تُرفض فورًا ولا تُوضع في طابور**، أما تغييرات الحدود فتسري عند **بداية الإطار الزمني التالي** (الدقيقة التالية / اليوم التالي).

لمراقبة الاستهلاك: `aix.APIKey.get_usage_limits()` أو `get_usage_limits(model=MODEL_ID)` (استخدم المعرّفات لا المسارات) ← صفوف `APIKeyUsageLimit` تحمل `daily_request_count/limit` و`daily_token_count/limit` و`model`. والصف الذي فيه `model=None` هو **النطاق العام**؛ وكون العدادات كلها `None` يعني فقط أنه لا حد عام مُعدّ — فتجاهله ما لم تكن قد ضبطت واحدًا.

تظهر أخطاء تجاوز حد المعدّل على هيئة HTTP **497** (حد aiXplain لكل دقيقة) أو **429**. وأخطاء REST الأخرى: 401 مفتاح خاطئ، و492 رابط مدخل يتعذّر جلبه، و400 `query` مشوّه أو فارغ. وفرز الأخطاء بحسب نصّها: `Invalid API key` = محذوف/منتهٍ/مكتوب خطأً أو من مساحة عمل خاطئة؛ و`Rate limit exceeded` = حدود مفتاح المشرف أو تزامن مفرط (تراجَع تدريجيًا)؛ و`Insufficient credits` = اشحن رصيد مساحة العمل.

## الأرصدة والفوترة

الرصيد الواحد يساوي دولارًا أمريكيًا واحدًا. وتُفوتَر النماذج/الأدوات/التكاملات بأسعار المورّدين (بهامش 0%). أما **الوكلاء** المنشورون فيضيفون هامشًا قدره 20% فوق مجموع استدعاءات النماذج والأدوات (ويغطي التنسيق، والوكلاء المصغّرة للتخطيط/التنسيق/الفحص، والذاكرة، والتحقّق). وتتبّع الإنفاق عبر `response.used_credits` أو سجل المعاملات على `https://app.aixplain.com/team/settings?tab=usage`.

## ما لا تغطيه النسخة v2 من الـ SDK (الإصدار v1 القديم فقط)

العميل الموحّد `aix.*` (`from aixplain import Aixplain`) متمحور حول الوكلاء والنماذج والأدوات. أما **خطوط الأنابيب (Pipelines)، والضبط الدقيق (fine-tuning)، وقياس الأداء (benchmarking)، ومجموعات البيانات/المدوّنات فليس لها واجهة في v2.** فهي موجودة فقط في مصانع v1 القديمة — التي صار لها الآن **تاريخ إزالة صارم هو 2027-02-01** (`aixplain._compat.V1_REMOVAL_DATE`، مُتحقَّق منه في الحزمة المثبَّتة). واستيراد شيفرة v1 يُصدر `AixplainV1DeprecationWarning` مرةً واحدة لكل عملية؛ ويمكن إسكاته بـ `AIXPLAIN_SUPPRESS_V1_DEPRECATION=1`. وخريطة النقل هي **MIGRATION.md** (`https://github.com/aixplain/aiXplain/blob/main/MIGRATION.md`) — وهي غير مشحونة داخل الـ wheel، فالنسخة المثبّتة لا تحوي ملفًا محليًا منها. وتاريخ الإزالة مشروط بسدّ الفجوات الثماني في المصانع التي يعدّدها MIGRATION.md، لكن خطّط على أساس وقوعه لا على خلافه.

```python
# Legacy v1 — only if the user explicitly needs these capabilities
from aixplain.factories import PipelineFactory, FinetuneFactory, BenchmarkFactory, DatasetFactory, CorpusFactory
pipeline = PipelineFactory.get("<pipeline_id>")
result = pipeline.run("input")
```

أما **خطوط الأنابيب** فالأفضل بناؤها مرئيًا في aiXplain Studio ثم تشغيلها بالمعرّف (من Studio، أو عبر نقاط نهاية خطوط الأنابيب في REST على `https://platform-api.aixplain.com`، أو عبر `PipelineFactory` في v1). فالنسخة v2 الحالية من SDK بايثون لا تتضمّن بانيًا لخطوط الأنابيب. وإذا طلب مستخدم "بناء خط أنابيب" بلغة Python، فأخبره بذلك واعرض عليه إما Studio أو المكافئ في صورة **وكيل فريق** (وهو الأسلوب الأصيل في v2 لتركيب سير عمل متعدد الخطوات).

## الترحيل من v1 إلى v2

استخدم `from aixplain import Aixplain; aix = Aixplain(api_key=...)` ثم `aix.Agent` / `aix.Model` / `aix.Tool`. وتجنّب مصانع v1 المهمَلة `aixplain.factories.*` (`AgentFactory`، `ModelFactory`، …) في كل ما يغطيه عميل v2. وإذا صادفت شيفرة مصانع قديمة، فانقلها إلى مكافئاتها في `aix.*`.
