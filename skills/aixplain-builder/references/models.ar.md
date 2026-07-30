# النماذج — الاستدلال المباشر

شغّل أيًّا من نماذج اللغة الكبيرة التي تتجاوز 170 نموذجًا في aiXplain، إضافةً إلى أكثر من 900 أصل (الكلام، الرؤية، الترجمة، التضمينات) مباشرةً، دون الحاجة إلى وكيل. تتشارك جميع النماذج واجهةً واحدة، لذا يمكنك استبدال أحدها بآخر دون إعادة كتابة الشيفرة.

## الاكتشاف

```python
# Keyword search (returns a dict — read the "results" key)
models = aix.Model.search("llama")["results"]

# Filter by host / developer / vendor
openai_models    = aix.Model.search("", host="openai")["results"]
meta_models      = aix.Model.search("", developer="meta")["results"]
anthropic_models = aix.Model.search("", vendor="anthropic")["results"]

for m in openai_models[:5]:
    print(m.name, m.id, m.host)

# Get a specific model by path or ID (both work)
model = aix.Model.get("openai/gpt-4o")
model = aix.Model.get("6646261c6eb563165658bbb1")
```

## التشغيل

```python
model = aix.Model.get("openai/gpt-4o")
r = model.run(text="Explain quantum computing simply")
print(r.data)      # normalized output
print(r.status)    # "SUCCESS"
print(r.usage.completion_tokens)   # token usage when available
```

**أنواع المدخلات** (تعتمد الكلمة المفتاحية الصحيحة على النموذج — افحصها باستخدام `model.inputs.keys()`):

| النوع | الاستدعاء |
|---|---|
| نص | `model.run(text="...")` or `model.run(data="file.txt")` |
| صورة | `model.run(data="image.png")` |
| صوت | `model.run(data="audio.wav")` or model-specific e.g. `source_audio=URL` |
| فيديو | `model.run(data="video.mp4")` |
| منظّم | `model.run({"text": "...", "context": "..."})` |

> مدخلات الصورة/الصوت/الفيديو **غير** مدعومة في النشر الداخلي (on-prem). تختلف حدود الحجم/الصيغة باختلاف المورّد — راجع صفحة النموذج في Studio.

### البث (Streaming)

```python
if model.supports_streaming:                       # check first — raises ValidationError if not
    with model.run_stream(text="Tell a short story.") as stream:
        for chunk in stream:
            print(chunk.data, end="", flush=True)   # chunk: .data .status .finish_reason .usage
# equivalently: for chunk in model.run(text="...", stream=True): ...
```

### غير المتزامن + الدفعات

```python
import time
start = model.run_async(text="Summarize the history of computing.")
while True:
    if not start.url:                # finished immediately
        print(start.data); break
    res = model.poll(start.url)
    if res.completed:
        print(res.data); break
    time.sleep(5)
```

الدفعات: أطلق جميع الطلبات باستخدام `run_async`، واجمع قيم `.url`، ثم استعلم عن كل منها حتى تتحقق `res.completed`. تحجب الدالة `sync_poll(url)` التنفيذ حتى الانتهاء وتعيد النتيجة النهائية في استدعاء واحد.

## ضبط المعاملات (`model.inputs`)

```python
model.inputs.temperature = 0.3            # dot notation
model.inputs['max_tokens'] = 1024         # dict notation
model.inputs.update(temperature=0.2, max_tokens=1200)   # bulk

model.inputs.keys()                       # all parameter names
model.inputs.get_required_parameters()    # e.g. ['text']
model.inputs.get_all_parameters()         # current values as dict
model.inputs.reset_parameter("temperature")
model.inputs.reset_all_parameters()
```

معاملات شائعة لنماذج اللغة الكبيرة: `temperature` (0–2)، `max_tokens`، `top_p` (0–1)، `frequency_penalty`/`presence_penalty` (−2–2). إرشادات: `0.9` للإبداع، `0.3` للدقة الواقعية، `0.0` للحتمية. لا تملك النماذج أي `.actions` — اضبطها عبر `model.inputs` فقط.

## المخرجات الخام من المورّد

تُعيد `options={"includeRawData": True}` استجابة المورّد الكاملة غير المعدّلة جنبًا إلى جنب مع الاستجابة المعيارية. تعمل مع أي نوع من النماذج (نموذج لغة كبير، كلام، رؤية).

```python
r = model.run(text="Summarize...", options={"includeRawData": True})
print(r.data)                    # normalized
print(r._raw_data["rawData"])    # provider's raw payload (shape varies by provider)
```

## التعرّف على الكلام (Whisper Large `66311fda6eb563279c574b71`)

```python
model = aix.Model.get("66311fda6eb563279c574b71")
r = model.run(
    source_audio="https://.../audio.mp3",   # public URL
    sourcelanguage="en",                     # REQUIRED field, but does NOT restrict detection
    options={"includeRawData": True},
)
print(r.data)                                       # full transcript
print(r._raw_data["rawData"]["language"])           # auto-detected language
segments = r._raw_data["rawData"]["segments"]        # per-segment start/end/text, avg_logprob, no_speech_prob
```

بالنسبة إلى ملف صوتي **محلي**، ارفعه أولًا (راجع `references/deployment-access.md § Upload a local file`)، ثم مرّر الرابط المُعاد بوصفه `source_audio`.

> إذا فشل رابط "عام" مع `err.invalid_input_data_or_input_url`، فقد يكون المضيف خلف حاجز تحدٍّ للبوتات/جدار حماية تطبيقات الويب (WAF) (مثلًا يعيد AWS WAF تحديًا بحالة HTTP 202 بدلًا من الملف)، وهو ما لا تستطيع خلفية aiXplain جلبه. الحل: نزّل الملف مرة واحدة عبر متصفح حقيقي، ثم أعد استضافته من خلال aiXplain باستخدام `FileUploader(...).upload(local_path, is_temp=True, return_download_link=True)` ومرّر ذلك الرابط.

## الترجمة

```python
t = aix.Model.get("google/cloud-translation")
print(t.run(text="Hello, how are you?", sourcelanguage="en", targetlanguage="es").data)
```

## استخدام نموذج داخل وكيل

```python
llm = aix.Model.get("openai/gpt-4o")
llm.inputs.temperature = 0.7
agent = aix.Agent(name="Assistant", description="...", llm=llm)   # as the reasoning LLM
# or attach as a callable tool:
agent = aix.Agent(name="Assistant", description="...", tools=[llm.as_tool()])
```

## استكشاف الأخطاء وإصلاحها

- **النموذج غير موجود** ← تحقّق من المسار/المعرّف باستخدام `aix.Model.search()`؛ وتأكّد من أن مفتاحك يملك صلاحية الوصول.
- **معاملات غير صالحة** ← لا تقبل جميع النماذج كل المعاملات؛ راجع صفحة النموذج في Studio أو `model.inputs.keys()`.
- **انتهاء مهلة التشغيل غير المتزامن** ← زِد فترة الاستعلام؛ وتحقّق من لوحة التحكم من أن المهمة ما زالت قيد التشغيل.
- **تحديد المعدّل (Rate limiting)** ← قلّل التزامن أو استخدم `run_async()` للدفعات (راجع HTTP 497/429 في `deployment-access.md`).
