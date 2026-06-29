# Models — direct inference

Run any of aiXplain's 170+ LLMs and 900+ assets (speech, vision, translation, embeddings) directly, without an agent. All models share one interface, so you can swap one for another without rewriting code.

## Discover

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

## Run

```python
model = aix.Model.get("openai/gpt-4o")
r = model.run(text="Explain quantum computing simply")
print(r.data)      # normalized output
print(r.status)    # "SUCCESS"
print(r.usage.completion_tokens)   # token usage when available
```

**Input types** (the right keyword depends on the model — inspect with `model.inputs.keys()`):

| Type | Call |
|---|---|
| Text | `model.run(text="...")` or `model.run(data="file.txt")` |
| Image | `model.run(data="image.png")` |
| Audio | `model.run(data="audio.wav")` or model-specific e.g. `source_audio=URL` |
| Video | `model.run(data="video.mp4")` |
| Structured | `model.run({"text": "...", "context": "..."})` |

> Image/audio/video inputs are **not** supported on-prem. Size/format limits vary by vendor — check the model's Studio page.

### Streaming

```python
if model.supports_streaming:                       # check first — raises ValidationError if not
    with model.run_stream(text="Tell a short story.") as stream:
        for chunk in stream:
            print(chunk.data, end="", flush=True)   # chunk: .data .status .finish_reason .usage
# equivalently: for chunk in model.run(text="...", stream=True): ...
```

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
model.inputs.temperature = 0.3            # dot notation
model.inputs['max_tokens'] = 1024         # dict notation
model.inputs.update(temperature=0.2, max_tokens=1200)   # bulk

model.inputs.keys()                       # all parameter names
model.inputs.get_required_parameters()    # e.g. ['text']
model.inputs.get_all_parameters()         # current values as dict
model.inputs.reset_parameter("temperature")
model.inputs.reset_all_parameters()
```

Common LLM params: `temperature` (0–2), `max_tokens`, `top_p` (0–1), `frequency_penalty`/`presence_penalty` (−2–2). Guidance: `0.9` creative, `0.3` factual, `0.0` deterministic. Models have **no** `.actions` — configure via `model.inputs` only.

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

> If a "public" URL fails with `err.invalid_input_data_or_input_url`, the host may be behind a bot-challenge/WAF (e.g. AWS WAF returns an HTTP 202 challenge instead of the file), which aiXplain's backend can't fetch. Fix: download the file once through a real browser, then re-host it through aiXplain with `FileUploader(...).upload(local_path, is_temp=True, return_download_link=True)` and pass that URL.

## Translation

```python
t = aix.Model.get("google/cloud-translation")
print(t.run(text="Hello, how are you?", sourcelanguage="en", targetlanguage="es").data)
```

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
- **Async timing out** → increase the poll interval; check the dashboard that the task is still running.
- **Rate limiting** → reduce concurrency or use `run_async()` for batches (see HTTP 497/429 in `deployment-access.md`).
