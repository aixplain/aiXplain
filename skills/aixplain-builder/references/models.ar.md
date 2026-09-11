# النماذج — الاستدلال المباشر

شغّل أيًّا من نماذج اللغة الكبيرة لدى aiXplain (أكثر من 170 نموذجًا) وأكثر من 900 أصل (الكلام، والرؤية، والترجمة، والتضمينات) مباشرةً ودون وكيل. تشترك جميع النماذج في واجهة واحدة، لذا يمكنك استبدال نموذج بآخر دون إعادة كتابة الشيفرة.

## الاستكشاف

```python
# Keyword search — returns a Page object (not a dict)
page = aix.Model.search("llama")
page.results        # list[Model]   (page["results"] also works — __getitem__ is just getattr)
page.total          # matches across all pages
page.page_total     # number of pages
page.skipped        # records the API returned that failed to deserialize
for m in page: ...  # the Page iterates over .results directly; there is no len(page)

# Filter by host / developer / vendor
openai_models    = aix.Model.search("", host="openai").results
meta_models      = aix.Model.search("", developer="meta").results
anthropic_models = aix.Model.search("", vendors="anthropic").results   # plural: `vendor=` is not a declared filter

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
print(r.details)   # provider-native payload (e.g. raw message objects, ASR segments)
print(r.run_time, r.used_credits)  # seconds, credits charged
print(r.asset)     # {"assetId": ..., "id": "openai/gpt-4o/openai"}
```

حقول `ModelResult` كاملةً: `status completed error_message url result supplier_error data _raw_data details run_time used_credits usage asset`. وإلى جانب مدخلات النموذج نفسه، تقبل الدوال `run`/`run_async`/`run_stream` الوسائط `timeout` و`wait_time` و`run_retries` و`run_retry_wait` و`api_key` و`resource_path` و`stream`، إضافةً إلى — الجديد في الإصدار 0.2.48 — `session_id` / `agent_name` في تشغيل نموذج عادي.

**أنواع المدخلات** (تعتمد الكلمة المفتاحية الصحيحة على النموذج — افحصها عبر `model.inputs.keys()`). الدالة `run()` تقبل الوسائط المسمّاة فقط؛ ولا يوجد وسيط موضعي:

| النوع | الاستدعاء |
|---|---|
| نص | `model.run(text="...")` أو `model.run(data="file.txt")` |
| صورة | `model.run(data="image.png")` |
| صوت | `model.run(data="audio.wav")` أو صيغة خاصة بالنموذج مثل `source_audio=URL` |
| فيديو | `model.run(data="video.mp4")` |
| منظَّم | `model.run(text="...", context="...")` |
| متعدد الوسائط | `model.run(data=[{"role": "user", "content": [...]}])` — انظر أدناه |

> مدخلات الصور والصوت والفيديو **غير** مدعومة في النشر المحلي (on-prem). وتختلف حدود الحجم والصيغة باختلاف المزوّد — راجع صفحة النموذج في Studio.

### البث التدفقي

```python
if model.supports_streaming:                       # check first — raises ValidationError if not
    with model.run_stream(text="Tell a short story.") as stream:
        for chunk in stream:
            print(chunk.data, end="", flush=True)
# equivalently: for chunk in model.run(text="...", stream=True): ...
```

حقول `StreamChunk`: `status data reasoning_content tool_calls usage finish_reason error_message` — إذ تُتاح آثار الاستدلال واستدعاءات الأدوات في كل جزء، لا دلتا النص وحدها.

وعبر REST يقابل ذلك `{"stream": true}` ← SSE، حيث يمثّل كل سطر `data:` جزءًا من نوع `chat.completion.chunk` بأسلوب OpenAI (اقرأ `choices[0].delta.content`؛ ويحمل آخر حدث غير `[DONE]` حقل `usage`). تفاصيل نقطة النهاية والترويسات في `references/deployment-access.md`.

### التشغيل غير المتزامن والدفعات

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

الدفعات: أطلق جميع الطلبات عبر `run_async`، واجمع قيم `.url`، ثم استعلم عن كل منها حتى تتحقق `res.completed`. أما `sync_poll(url)` فتحجب التنفيذ حتى الانتهاء وتُعيد النتيجة النهائية في استدعاء واحد.

## ضبط المعاملات (`model.inputs`)

```python
model.inputs.temperature = 0.3            # dot notation (write)
model.inputs['max_tokens'] = 1024         # dict notation (write)
model.inputs.update(temperature=0.2, max_tokens=1200)   # bulk

model.inputs.keys()                       # all parameter names
model.inputs.required                     # PROPERTY, not a call -> ['text']
dict(model.inputs.items())                # current values as a plain {name: value} dict
model.inputs.reset("temperature")         # unset one
model.inputs.reset()                      # unset all
model.inputs.validate()                   # -> list of missing-required errors ([] means valid)
```

⚠️ **أُعيدت التسمية في الإصدار 0.2.48 — والدوال المساعدة الأربع القديمة أُزيلت.** الدوال `get_required_parameters()` و`get_all_parameters()` و`reset_parameter(k)` و`reset_all_parameters()` تمرّ الآن عبر `Inputs.__getattr__` (الذي لا يحلّ سوى أسماء المدخلات المصرّح بها) وتُطلق `AttributeError: Input '<name>' not found`. والبدائل هي ما ورد في الطرف الأيمن أعلاه.

ومَزلقان إضافيان:

- **القراءة تُعيد كائن `Input` لا القيمة.** فـ `model.inputs.temperature` ← `Input(name='temperature', required=False, type='number', value=0.3)`. وللحصول على القيمة الخام استخدم `.value`، أو `dict(model.inputs.items())["temperature"]`. أما الكتابة فما زالت تضبط القيمة، لذا تبقى `inputs.temperature = 0.3` كما هي.
- **المدخلات غير المصرّح بها تُرفَض ولا تُنشأ.** فـ `model.inputs.foo = 1` ← `AttributeError`؛ و`model.inputs['foo'] = 1` ← `KeyError`. والدالة `reset()` تُفرغ القيمة إلى `None` (إذ لا يحمل كائن `Input` قيمة افتراضية مخزَّنة، فمعنى "إعادة الضبط" هو "إلغاء التعيين")، كما أن إسناد السمة كاملةً `model.inputs = {"temperature": 0.2}` يُعترَض ويُنفَّذ بوصفه `update` لا استبدالًا.

وما زال صالحًا: `inputs.keys()` و`inputs.values()` و`len(inputs)` و`"text" in inputs` والتكرار على الأسماء.

المعاملات الشائعة لنماذج اللغة الكبيرة: `temperature` (من 0 إلى 2)، و`max_tokens`، و`top_p` (من 0 إلى 1)، و`frequency_penalty`/`presence_penalty` (من −2 إلى 2). إرشادات: `0.9` للإبداع، و`0.3` للدقة الواقعية، و`0.0` للنتائج الحتمية. والخاصية `Model.actions` **موجودة** فعلًا اعتبارًا من الإصدار 0.2.48 (وتُعيد إجراءً واحدًا هو `"run"`)، لكن لا خيار فيها — فالضبط يتم عبر `model.inputs`.

نماذج الاستدلال (عائلة GPT-5 وغيرها) تُتيح `reasoning_effort` (`minimal`/`low`/`medium`/`high`، والقيمة الافتراضية `medium`؛ أما `none` فلا توجد إلا في GPT-5.1). وقد تم التحقق من تمريرها إلى المزوّد بتاريخ 2026-07-23 (`minimal` ← صفر رمز استدلال). ⚠️ القيم **لا يجري التحقق منها** — فالخطأ الإملائي يعمل دون اعتراض ويرتد بصمت إلى قيمة افتراضية؛ كما أن `minimal` قد تضرّ بجودة الإجابة ضررًا ملحوظًا في المسائل متعددة الخطوات (و`low` هي نقطة التوازن الرخيصة والنظيفة).

## المخرجات الخام من المزوّد

يُعيد `options={"includeRawData": True}` استجابة المورّد الكاملة دون تعديل إلى جانب الاستجابة المُطبَّعة. ويعمل مع أي نوع من النماذج (اللغة الكبيرة، والكلام، والرؤية).

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

أما الملف الصوتي **المحلي** فارفعه أولًا (انظر `references/deployment-access.md § Upload a local file`)، ثم مرّر الرابط المُعاد بوصفه `source_audio`.

> إذا أخفق رابط "عام" مع الخطأ `err.invalid_input_data_or_input_url`، فقد يكون المضيف خلف تحدٍّ لمنع الروبوتات أو جدار حماية تطبيقات (مثل AWS WAF الذي يُعيد تحدي HTTP 202 بدل الملف)، وهو ما يتعذّر على الواجهة الخلفية لدى aiXplain جلبه. الحل: نزّل الملف مرة واحدة عبر متصفح حقيقي، ثم أعد استضافته من خلال aiXplain ومرّر ذلك الرابط:
>
> ```python
> from aixplain.v2.upload_utils import FileUploader, upload_file   # NOT aixplain.v2.file — that raises ImportError
> url = FileUploader(api_key=API_KEY).upload("audio.mp3", is_temp=True, return_download_link=True)
> url = upload_file("audio.mp3", is_temp=True, return_download_link=True)   # module-level one-shot, no class needed
> ```

## الترجمة

```python
t = aix.Model.get("google/cloud-translation")
print(t.run(text="Hello, how are you?", sourcelanguage="en", targetlanguage="es").data)
```

## سجل المحادثة ومدخلات الصور متعددة الوسائط

تقبل نماذج اللغة الكبيرة الحوارية مصفوفةً من رسائل `{"role", "content"}` بدلًا من سلسلة `text` بسيطة:

```python
model.run(text=[{"role": "user", "content": "Hello!"},
                {"role": "assistant", "content": "Hi! How can I help?"},
                {"role": "user", "content": "Tell me a fun fact."}])
```

> هذا موثَّق بوصفه شكل حمولة REST؛ وتمرّر حزمة SDK قيمة `text=` دون تغيير، غير أن `_validate_param_type` لا تسمح بمرور قائمة إلا إذا صرّح النموذج بأن `text` من النوع `json` (أو `text`/`json`). فإن رفضت المصفوفة، فأرسل الرسائل نفسها بوصفها `data=[...]`، أو استدعِ نقطة نهاية REST مباشرةً (`references/deployment-access.md`).

وفي نماذج اللغة الكبيرة القادرة على الرؤية، يصبح حقل `content` في كل رسالة مصفوفةً من أجزاء مصنَّفة — `{"type": "text", ...}` إضافةً إلى `{"type": "image_url", "image_url": {"url": ...}}`، حيث يكون الرابط إما رابطًا عامًّا أو معرّف موارد مضمَّنًا بصيغة `data:image/png;base64,...`:

```python
model.run(data=[{"role": "user", "content": [
    {"type": "text", "text": "What colour is the cat?"},
    {"type": "image_url", "image_url": {"url": "data:image/png;base64,iVBORw0KG..."}},
]}])
```

وعند وجود `data` تتخطى حزمة SDK عمدًا التحقق من المدخلات المطلوبة المفقودة في حقلي `text`/`prompt` المسطّحين، حتى لا يُرفض استدعاء الرؤية لافتقاره إلى `text`.

> رابط الصورة **المجرَّد** يجلبه المزوّد الأعلى، لذا يُعيد المضيف الذي يحجب الروبوتات `status: "FAILED"` مع `code: "invalid_image_url"`؛ أما معرّف الموارد المضمَّن بصيغة base64 فلا يعتمد قط على جلب خارجي. أشكال حمولات REST في: `references/deployment-access.md`.

## تحويل النص إلى كلام

أرسل النص فحسب. أصوات السحابة (AWS وGoogle وAzure) تعمل بصورة متزامنة وتُعيد في `data` رابطًا صوتيًّا **موقَّعًا ومحدود المدة** — فنزّله قبل انتهاء صلاحيته.

```python
tts = aix.Model.get("618ba6e4e2e1a9153ca2a3a2")     # AWS speech-synthesis, English (Amy)
print(tts.run(text="The quick brown fox.").data)     # -> https://...mp3?...signed...
```

وتتطلب الأصوات من فئة ElevenLabs إضافةً إلى ذلك `voice_id` (وإغفاله يُعيد `FAILED`)؛ راجع `model.params` بحثًا عن الحقول المطلوبة مثل `voice_id` أو `language`.

## الملفات بوصفها أصولًا من الدرجة الأولى (`aix.File`)

جديد في الإصدار 0.2.48: أصل مسجَّل في الواجهة الخلفية (`sdk/file-asset`)، متمايز عن رابط `FileUploader` العابر.

```python
f = aix.File(source="/path/audio.mp3", name="audio")   # source may be a local path, a local DIR, or an http(s) URL
f.save()                                               # uploads, registers, populates f.id / f.url
print(f.url, f.id, f.size, f.extension, f.status)

aix.File.create_from_file("/path/audio.mp3")           # classmethod alias for the constructor
aix.File.get("<id-or-encoded-path>", recursive=True)
aix.File.search(query=None, page_number=0, page_size=20)   # -> Page[File]
f.download("/local/dest")                              # folders come down as a single ZIP
```

حقول أخرى: `description path source file_type is_temp children parent_id relative_path tags privacy whitelist created_at updated_at`؛ والخصائص `file_path` (اسم بديل لـ `source`) و`is_dir` و`encoded_id` و`is_deleted` و`is_modified`. والنوع `FileType` هو `FILE | FOLDER`؛ وقيمة `privacy` الافتراضية خاصة.

> ⚠️ استخدام `File(..., is_temp=True)` **لا** يُبقي الأصل مؤقتًا: فالدالة `save()` ترفع دائمًا عبر نقطة نهاية الروابط المؤقتة، ثم تسجّل سجل `file-asset` دائمًا، ثم تفرض `is_temp = False`. وللحصول على رابط عابر فعلًا استخدم `FileUploader.upload(..., is_temp=True, return_download_link=True)`. أما مصدر `http(s)` فيُعاد استضافته عبر جلب محمي من هجمات SSRF (يُعاد التحقق من كل وجهة إعادة توجيه، مع طلب `PUT` موقَّع مسبقًا وإعادة التوجيه معطَّلة) — وهي طريقة مدعومة لإعادة استضافة ملف بعيد.

## استخدام نموذج داخل وكيل

```python
llm = aix.Model.get("openai/gpt-4o")
llm.inputs.temperature = 0.7
agent = aix.Agent(name="Assistant", description="...", llm=llm)   # as the reasoning LLM
# or attach as a callable tool:
agent = aix.Agent(name="Assistant", description="...", tools=[llm.as_tool()])
```

## استكشاف الأخطاء وإصلاحها

- **النموذج غير موجود** ← تحقق من المسار أو المعرّف عبر `aix.Model.search()`؛ وتأكد من أن مفتاحك يملك صلاحية الوصول.
- **معاملات غير صالحة** ← ليست كل النماذج تقبل كل المعاملات؛ راجع صفحة النموذج في Studio أو `model.inputs.keys()`.
- **`AttributeError: Input 'get_all_parameters' not found`** (أو `get_required_parameters` / `reset_parameter` / `reset_all_parameters`) ← شيفرة سابقة للإصدار 0.2.48؛ انظر إعادة التسمية في قسم *ضبط المعاملات*.
- **`ImportError: cannot import name 'FileUploader' from 'aixplain.v2.file'`** ← استورده من `aixplain.v2.upload_utils` (أو `aixplain.v2`)؛ إذ صار `aixplain.v2.file` يحتوي على المورد `File`.
- **انتهاء مهلة العملية غير المتزامنة** ← زِد فترة الاستعلام؛ وتحقق من لوحة التحكم من أن المهمة ما زالت قيد التشغيل.
- **تحديد المعدل** ← قلّل التزامن أو استخدم `run_async()` للدفعات (انظر HTTP 497/429 في `deployment-access.md`).
