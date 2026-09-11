# Models — direct inference

Run any of aiXplain's 170+ LLMs and 900+ assets (speech, vision, translation, embeddings) directly, without an agent. All models share one interface, so you can swap one for another without rewriting code.

## Discover

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

## Run

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

Full `ModelResult`: `status completed error_message url result supplier_error data _raw_data details run_time used_credits usage asset`. Alongside the model's own inputs, `run`/`run_async`/`run_stream` accept `timeout`, `wait_time`, `run_retries`, `run_retry_wait`, `api_key`, `resource_path`, `stream`, and — new in 0.2.48 — `session_id` / `agent_name` on a plain model run.

**Input types** (the right keyword depends on the model — inspect with `model.inputs.keys()`). `run()` is keyword-only; there is no positional argument:

| Type | Call |
|---|---|
| Text | `model.run(text="...")` or `model.run(data="file.txt")` |
| Image | `model.run(data="image.png")` |
| Audio | `model.run(data="audio.wav")` or model-specific e.g. `source_audio=URL` |
| Video | `model.run(data="video.mp4")` |
| Structured | `model.run(text="...", context="...")` |
| Multimodal | `model.run(data=[{"role": "user", "content": [...]}])` — see below |

> Image/audio/video inputs are **not** supported on-prem. Size/format limits vary by vendor — check the model's Studio page.

### Streaming

```python
if model.supports_streaming:                       # check first — raises ValidationError if not
    with model.run_stream(text="Tell a short story.") as stream:
        for chunk in stream:
            print(chunk.data, end="", flush=True)
# equivalently: for chunk in model.run(text="...", stream=True): ...
```

`StreamChunk` fields: `status data reasoning_content tool_calls usage finish_reason error_message` — reasoning traces and tool calls are exposed per chunk, not just the text delta.

Over REST the same thing is `{"stream": true}` → SSE, each `data:` line an OpenAI-style `chat.completion.chunk` (read `choices[0].delta.content`; the last non-`[DONE]` event carries `usage`). Endpoint/header detail in `references/deployment-access.md`.

### Async + batch

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

Batch: fire all with `run_async`, collect the `.url`s, then poll each until `res.completed`. `sync_poll(url)` blocks until done and returns the final result in one call.

## Configure parameters (`model.inputs`)

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

⚠️ **Renamed in 0.2.48 — the four old helpers are gone.** `get_required_parameters()`, `get_all_parameters()`, `reset_parameter(k)` and `reset_all_parameters()` now fall through `Inputs.__getattr__` (which only resolves declared input names) and raise `AttributeError: Input '<name>' not found`. Replacements are the right-hand side above.

Two more traps:

- **Reading returns the `Input` object, not the value.** `model.inputs.temperature` → `Input(name='temperature', required=False, type='number', value=0.3)`. For the raw value use `.value`, or `dict(model.inputs.items())["temperature"]`. Writing still sets the value, so `inputs.temperature = 0.3` is unchanged.
- **Undeclared inputs are rejected, not created.** `model.inputs.foo = 1` → `AttributeError`; `model.inputs['foo'] = 1` → `KeyError`. `reset()` clears to `None` (an `Input` carries no stored default, so "reset" means "unset"), and whole-attribute assignment `model.inputs = {"temperature": 0.2}` is intercepted and does an `update`, not a replace.

Still fine: `inputs.keys()`, `inputs.values()`, `len(inputs)`, `"text" in inputs`, iteration over names.

Common LLM params: `temperature` (0–2), `max_tokens`, `top_p` (0–1), `frequency_penalty`/`presence_penalty` (−2–2). Guidance: `0.9` creative, `0.3` factual, `0.0` deterministic. `Model.actions` **does** exist as of 0.2.48 (it returns a single `"run"` action), but there is nothing to choose between — configure via `model.inputs`.

Reasoning models (GPT-5 family etc.) expose `reasoning_effort` (`minimal`/`low`/`medium`/`high`, default `medium`; `none` exists only on GPT-5.1). Verified forwarded to the provider as of 2026-07-23 (`minimal` → 0 reasoning tokens). ⚠️ Values are **not validated** — a typo runs fine and silently falls back to a default; and `minimal` can noticeably hurt answer quality on multi-step problems (`low` is the cheap-but-clean sweet spot).

## Provider raw output

`options={"includeRawData": True}` returns the supplier's full unmodified response alongside the normalized one. Works for any model type (LLM, speech, vision).

```python
r = model.run(text="Summarize...", options={"includeRawData": True})
print(r.data)                    # normalized
print(r._raw_data["rawData"])    # provider's raw payload (shape varies by provider)
```

## Speech recognition (Whisper Large `66311fda6eb563279c574b71`)

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

For a **local** audio file, upload it first (see `references/deployment-access.md § Upload a local file`), then pass the returned URL as `source_audio`.

> If a "public" URL fails with `err.invalid_input_data_or_input_url`, the host may be behind a bot-challenge/WAF (e.g. AWS WAF returns an HTTP 202 challenge instead of the file), which aiXplain's backend can't fetch. Fix: download the file once through a real browser, then re-host it through aiXplain and pass that URL:
>
> ```python
> from aixplain.v2.upload_utils import FileUploader, upload_file   # NOT aixplain.v2.file — that raises ImportError
> url = FileUploader(api_key=API_KEY).upload("audio.mp3", is_temp=True, return_download_link=True)
> url = upload_file("audio.mp3", is_temp=True, return_download_link=True)   # module-level one-shot, no class needed
> ```

## Translation

```python
t = aix.Model.get("google/cloud-translation")
print(t.run(text="Hello, how are you?", sourcelanguage="en", targetlanguage="es").data)
```

## Chat history & multimodal image input

Conversational LLMs take an array of `{"role", "content"}` messages in place of a plain `text` string:

```python
model.run(text=[{"role": "user", "content": "Hello!"},
                {"role": "assistant", "content": "Hi! How can I help?"},
                {"role": "user", "content": "Tell me a fun fact."}])
```

> Documented as a REST payload shape; the SDK forwards `text=` unchanged, but `_validate_param_type` only lets a list through when the model declares `text` as `json` (or `text`/`json`). If it rejects the array, send the same messages as `data=[...]`, or call the REST endpoint directly (`references/deployment-access.md`).

For vision-capable LLMs each message's `content` becomes an array of typed parts — `{"type": "text", ...}` plus `{"type": "image_url", "image_url": {"url": ...}}`, where the URL is either a public URL or an inline `data:image/png;base64,...` URI:

```python
model.run(data=[{"role": "user", "content": [
    {"type": "text", "text": "What colour is the cat?"},
    {"type": "image_url", "image_url": {"url": "data:image/png;base64,iVBORw0KG..."}},
]}])
```

When `data` is present the SDK deliberately skips missing-required checks for the flat `text`/`prompt` inputs, so a vision call isn't rejected for lacking `text`.

> A plain image **URL** is fetched by the upstream provider, so a bot-blocking host returns `status: "FAILED"` with `code: "invalid_image_url"`; a base64 data URI never depends on an external fetch. REST payload shapes: `references/deployment-access.md`.

## Text-to-speech

Send just the text. Cloud voices (AWS, Google, Azure) run synchronously and return a **signed, time-limited** audio URL in `data` — download it before it expires.

```python
tts = aix.Model.get("618ba6e4e2e1a9153ca2a3a2")     # AWS speech-synthesis, English (Amy)
print(tts.run(text="The quick brown fox.").data)     # -> https://...mp3?...signed...
```

ElevenLabs-class voices additionally require `voice_id` (omitting it returns `FAILED`); check `model.params` for required fields like `voice_id` or `language`.

## Files as first-class assets (`aix.File`)

New in 0.2.48: a registered backend asset (`sdk/file-asset`), distinct from the throwaway `FileUploader` URL.

```python
f = aix.File(source="/path/audio.mp3", name="audio")   # source may be a local path, a local DIR, or an http(s) URL
f.save()                                               # uploads, registers, populates f.id / f.url
print(f.url, f.id, f.size, f.extension, f.status)

aix.File.create_from_file("/path/audio.mp3")           # classmethod alias for the constructor
aix.File.get("<id-or-encoded-path>", recursive=True)
aix.File.search(query=None, page_number=0, page_size=20)   # -> Page[File]
f.download("/local/dest")                              # folders come down as a single ZIP
```

Other fields: `description path source file_type is_temp children parent_id relative_path tags privacy whitelist created_at updated_at`; properties `file_path` (alias of `source`), `is_dir`, `encoded_id`, `is_deleted`, `is_modified`. `FileType` is `FILE | FOLDER`; `privacy` defaults to private.

> ⚠️ `File(..., is_temp=True)` does **not** keep the asset temporary: `save()` always uploads through the temp-url endpoint, registers a permanent `file-asset` record, then forces `is_temp = False`. For a genuinely throwaway URL use `FileUploader.upload(..., is_temp=True, return_download_link=True)`. An `http(s)` `source` is re-hosted through an SSRF-guarded fetch (every redirect target re-validated, presigned `PUT` with redirects disabled) — a supported way to re-host a remote file.

## Use a model inside an agent

```python
llm = aix.Model.get("openai/gpt-4o")
llm.inputs.temperature = 0.7
agent = aix.Agent(name="Assistant", description="...", llm=llm)   # as the reasoning LLM
# or attach as a callable tool:
agent = aix.Agent(name="Assistant", description="...", tools=[llm.as_tool()])
```

## Troubleshooting

- **Model not found** → verify path/ID with `aix.Model.search()`; confirm your key has access.
- **Invalid parameters** → not all models accept all params; check the model's Studio page or `model.inputs.keys()`.
- **`AttributeError: Input 'get_all_parameters' not found`** (or `get_required_parameters` / `reset_parameter` / `reset_all_parameters`) → pre-0.2.48 code; see the renames under *Configure parameters*.
- **`ImportError: cannot import name 'FileUploader' from 'aixplain.v2.file'`** → import from `aixplain.v2.upload_utils` (or `aixplain.v2`); `aixplain.v2.file` now holds the `File` resource.
- **Async timing out** → increase the poll interval; check the dashboard that the task is still running.
- **Rate limiting** → reduce concurrency or use `run_async()` for batches (see HTTP 497/429 in `deployment-access.md`).
