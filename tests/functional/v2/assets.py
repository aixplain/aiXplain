"""Centralised, pinned asset ids for v2 functional tests.

Functional tests otherwise hardcode model/tool ids inline and drift when a
platform asset is replaced. Keeping them here means a single place to update,
and lets several test files share the same pinned vision / image / streaming
models instead of each inventing its own.

The ids are deliberately real platform assets (not fixtures): these tests are
the only coverage for several public run-time features, so they must exercise
the live backend rather than a mock.
"""

import base64

#: Gemini vision model that accepts image attachments on an agent run.
VISION_LLM_ID = "6a2846019a0a2598b61e12b8"

#: Seedream image-generation model. Attached to an agent as a *tool* it emits an
#: ``image`` artifact with a presigned URL.
IMAGE_MODEL_ID = "69f347e7de823633d9604dfd"

#: GPT-5.4 — exposes a ``reasoning_effort`` input parameter.
REASONING_MODEL_ID = "69b7e5f1b2fe44704ab0e7d0"

#: GPT-5.2 — supports streaming and emits OpenAI-style tool-call deltas.
STREAMING_MODEL_ID = "69727676c60248082d79932f"

#: Tavily web-search tool used to force multi-step tool-using runs (budget tests).
TAVILY_TOOL_ID = "6931bdf462eb386b7158def3"

#: Minimal 1x1 red PNG, used as a deterministic attachment payload.
RED_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
