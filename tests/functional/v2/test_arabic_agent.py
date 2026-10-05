__author__ = "OpenAI"

"""
Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import re
import time
import uuid

import pytest

from aixplain.v2 import Inspector

ARABIC_CHAR_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")

#: (display name, asset name in `tests/functional/_assets.py`). Parametrising
#: on the asset *name* keeps collection backend-independent: the id is resolved
#: from the `assets` fixture at setup, so the same parameter ids run against
#: dev, test and prod. gpt-5.4 is the registry's ``DEFAULT_LLM``.
MODELS = [
    pytest.param("gpt-5.4", "DEFAULT_LLM", id="gpt-5.4"),
    pytest.param("claude-opus-4.6", "CLAUDE_LLM", id="claude-opus-4.6"),
]

ARABIC_QUERIES = {
    "pure_arabic": "ما هي أهم القوانين التجارية في المملكة العربية السعودية؟",
    "mixed_ar_en": "اشرح لي مفهوم Due Diligence في القانون السعودي وما هي متطلبات الـ Compliance؟",
}

QUERY_EXPECTATIONS = {
    "pure_arabic": {"min_arabic_ratio": 0.35, "require_keywords": ["نظام"]},
    "mixed_ar_en": {"min_arabic_ratio": 0.20, "require_keywords_any": ["Due Diligence", "Compliance"]},
}

#: Arabic with full diacritics, so saving and running the agent exercises that Unicode.
SINGLE_AGENT_DESCRIPTION = "مستشار قانونيّ ثنائيّ اللُّغة"
SINGLE_AGENT_INSTRUCTIONS = (
    "ROLE: أنت مُستشارٌ قانونيٌّ سعوديٌّ مُتخصِّصٌ في القانونِ التِّجاريِّ.\n"
    "CONSTRAINTS: أجب بالعربيّة، واحتفظ بالمصطلحات الإنجليزيّة كما وردت في السُّؤال.\n"
    "OUTPUT RULES: رتّب إجابتك في نقاطٍ مُرقَّمةٍ، واذكر المراجع النِّظاميّة إن وُجدت."
)


def _contains_arabic(text: str) -> bool:
    return bool(ARABIC_CHAR_RE.search(text))


def _arabic_ratio(text: str) -> float:
    visible_chars = [char for char in text if not char.isspace()]
    if not visible_chars:
        return 0.0
    arabic_chars = len(ARABIC_CHAR_RE.findall(text))
    return arabic_chars / len(visible_chars)


def _extract_output(response) -> str:
    data = getattr(response, "data", None)
    if data is None:
        return ""
    if hasattr(data, "output") and data.output is not None:
        return str(data.output)
    if isinstance(data, dict):
        return str(data.get("output", ""))
    return str(data)


def _extract_steps(response) -> list:
    data = getattr(response, "data", None)
    if data is None:
        return []
    steps = getattr(data, "steps", None) or []
    if isinstance(data, dict):
        steps = data.get("steps", []) or []
    return steps


#: How many times a run is retried before an empty output is called a failure,
#: and how long to wait between attempts. An empty body from a momentarily
#: degraded model is transient, so it is worth retrying; an empty body on every
#: attempt is a result this suite must report, not absorb.
_OUTPUT_ATTEMPTS = 3
_OUTPUT_RETRY_DELAY_SECONDS = 10

#: Start of the `_run_until_output` exhaustion failure. The `flaky` markers below
#: pass it as `rerun_except`, so pytest-rerunfailures does not rerun a test whose
#: model already came back empty on every attempt: `_run_until_output` is the one
#: retry layer for empty output, and the marker is only for timeouts and other
#: transient failures. Stacking the two multiplied the billed runs per item.
_NO_OUTPUT_FAILURE = "returned no usable content"


def _has_usable_output(output: str) -> bool:
    """True if the model produced content these tests can assert against.

    A degraded model returns an empty body, or — when it drives an inspector's
    evaluator — a ``content=None`` response that the inspector surfaces as an
    unparseable verdict. Both shapes are checked here.
    """
    if not output.strip():
        return False
    return not ("inspector_verdict_unparseable" in output and "content=None" in output)


def _assert_success_response(response) -> tuple[str, list]:
    assert response is not None
    assert getattr(response, "completed", None) is True
    assert getattr(response, "status", "").upper() == "SUCCESS"
    return _extract_output(response), _extract_steps(response)


def _run_until_output(run, description: str) -> tuple[str, list]:
    """Call *run* until it yields usable content; fail if it never does.

    This replaces a skip on empty output (ENG-3684). That skip was added so a
    backend model outage would not turn CI red, but it made an outage and a
    genuine regression in the Arabic runtime path indistinguishable:
    three tests across two LLMs could all go quiet and the leg still reported
    success. Retrying absorbs the transient case that motivated the skip; a run
    that comes back empty every time is reported as the failure it is.

    Args:
        run: Zero-argument callable that performs the agent run and returns the
            response. Called again, from scratch, on each retry.
        description: What is being run, for the failure message.
    """
    output = ""
    for attempt in range(1, _OUTPUT_ATTEMPTS + 1):
        output, steps = _assert_success_response(run())
        if _has_usable_output(output):
            return output, steps
        if attempt < _OUTPUT_ATTEMPTS:
            time.sleep(_OUTPUT_RETRY_DELAY_SECONDS)

    pytest.fail(
        f"{description} {_NO_OUTPUT_FAILURE} in {_OUTPUT_ATTEMPTS} consecutive runs, "
        f"{_OUTPUT_RETRY_DELAY_SECONDS}s apart (last output: {output!r}). This failure is not "
        "rerun. If the model is genuinely unavailable on this backend, drop it from MODELS "
        "rather than letting the leg pass without it."
    )


def _assert_arabic_output(query_key: str, output: str) -> None:
    expectations = QUERY_EXPECTATIONS[query_key]
    assert _contains_arabic(output), f"Expected Arabic content for {query_key}"
    assert "serial" not in output.lower()
    assert "json parse" not in output.lower()
    assert _arabic_ratio(output) >= expectations["min_arabic_ratio"], (
        f"Arabic ratio too low for {query_key}: {_arabic_ratio(output):.2f}"
    )

    for keyword in expectations.get("require_keywords", []):
        assert keyword.lower() in output.lower(), f"Expected keyword '{keyword}' in {query_key} response"

    if expectations.get("require_keywords_any"):
        assert any(keyword.lower() in output.lower() for keyword in expectations["require_keywords_any"]), (
            f"Expected one of {expectations['require_keywords_any']} in {query_key} response"
        )


def _build_name(prefix: str, model_name: str) -> str:
    return f"{prefix}-{model_name}-{int(time.time())}-{uuid.uuid4().hex[:6]}"


def _is_inspector_step(step: dict, inspector_name: str = "") -> bool:
    # The backend reports the inspector's own name as the step agent id
    # (e.g. 'ArabicContentValidator-gpt-5.4'), not an 'inspector|...' prefix.
    agent_info = step.get("agent") or {}
    step_id = (agent_info.get("id") or "").lower()
    return "inspector" in step_id or (bool(inspector_name) and step_id == inspector_name.lower())


def _is_inspector_abort_message(output: str) -> bool:
    normalized = output.lower()
    return (
        "inspector detected issues" in normalized
        or "check your input query and inspector configuration" in normalized
        or "blocked by an inspector" in normalized
    )


def _make_single_agent(client, tracker, llm_id: str, model_name: str):
    agent = client.Agent(
        name=_build_name("ArabicSingleLegal", model_name),
        description=SINGLE_AGENT_DESCRIPTION,
        instructions=SINGLE_AGENT_INSTRUCTIONS,
        llm=llm_id,
        max_tokens=2048,
        max_iterations=4,
    )
    agent.save()
    tracker.append(agent)
    return agent


def _make_team_agent(client, tracker, llm_id: str, model_name: str, inspectors=None):
    """Build a researcher + drafter team, registering each agent with ``tracker`` as it is saved."""
    researcher = client.Agent(
        name=_build_name("ArabicResearcher", model_name),
        description="باحث قانوني",
        instructions=(
            "ROLE: أنت باحث قانوني. ابحث في الأنظمة السعودية.\n"
            "CONSTRAINTS: أجب بالعربية. اذكر أرقام المواد.\n"
            "OUTPUT RULES: قدّم ملخصاً في ٣ نقاط."
        ),
        llm=llm_id,
    )
    drafter = client.Agent(
        name=_build_name("ArabicDrafter", model_name),
        description="صائغ عقود",
        instructions=(
            "ROLE: أنت متخصص في صياغة العقود التجارية.\n"
            "CONSTRAINTS: استخدم الصيغ القانونية الرسمية بالعربية.\n"
            "OUTPUT RULES: صِغ الرد كمسوَّدة قانونية."
        ),
        llm=llm_id,
    )
    researcher.save()
    tracker.append(researcher)
    drafter.save()
    tracker.append(drafter)

    team_agent = client.Agent(
        name=_build_name("ArabicTeamPipeline", model_name),
        description="Multi-agent pipeline with Arabic",
        instructions=(
            "ROLE: أنت مدير مكتب محاماة. وزّع المهام على فريقك.\n"
            "CONSTRAINTS: تحدث بالعربية. وجّه كل سؤال للمتخصص المناسب.\n"
            "OUTPUT RULES: اجمع ردود الفريق في تقرير واحد مُنسَّق."
        ),
        llm=llm_id,
        agents=[researcher, drafter],
        inspectors=inspectors or [],
        max_tokens=2048,
        max_iterations=4,
    )
    team_agent.save()
    tracker.append(team_agent)
    return team_agent


def _make_output_inspector(llm_id: str, model_name: str):
    return Inspector(
        name=f"ArabicContentValidator-{model_name}",
        severity="high",
        targets=["output"],
        action="abort",
        metric={
            "asset_id": llm_id,
            "prompt": (
                "تحقق من أن الرد مكتوب بالعربية الفصحى وأنه يتعلق بالقانون التجاري السعودي فقط. "
                "إذا كان الرد بلغة أخرى أو خارج النطاق، ارفضه."
            ),
        },
    )


@pytest.mark.flaky(reruns=1, reruns_delay=5, rerun_except=_NO_OUTPUT_FAILURE)
@pytest.mark.parametrize(("model_name", "llm_asset"), MODELS)
def test_arabic_single_agent(client, assets, resource_tracker, model_name, llm_asset):
    """An agent with diacritic Arabic instructions answers a mixed Arabic/English query in Arabic."""
    agent = _make_single_agent(client, resource_tracker, getattr(assets, llm_asset), model_name)

    output, _ = _run_until_output(
        lambda: agent.run(ARABIC_QUERIES["mixed_ar_en"]),
        f"Arabic single agent on {model_name}",
    )
    _assert_arabic_output("mixed_ar_en", output)


@pytest.mark.flaky(reruns=1, reruns_delay=5, rerun_except=_NO_OUTPUT_FAILURE)
@pytest.mark.parametrize(("model_name", "llm_asset"), MODELS)
def test_arabic_team_agent_with_inspector(client, assets, resource_tracker, model_name, llm_asset):
    """One team run covers Arabic team serialization, delegation, and an Arabic-prompted inspector."""
    llm_id = getattr(assets, llm_asset)
    inspector = _make_output_inspector(llm_id, model_name)
    team_agent = _make_team_agent(client, resource_tracker, llm_id, model_name, inspectors=[inspector])

    output, steps = _run_until_output(
        lambda: team_agent.run(ARABIC_QUERIES["pure_arabic"]),
        f"Arabic team agent with inspector on {model_name}",
    )
    assert steps, "Expected team-agent execution steps for the Arabic team flow"
    inspector_steps = [step for step in steps if _is_inspector_step(step, inspector.name)]
    assert inspector_steps, "Expected inspector step(s) in the run"

    if _is_inspector_abort_message(output):
        return

    _assert_arabic_output("pure_arabic", output)
