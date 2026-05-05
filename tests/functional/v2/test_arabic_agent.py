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

from aixplain.v2 import (
    EvaluatorConfig,
    EvaluatorType,
    Inspector,
    InspectorAction,
    InspectorActionConfig,
    InspectorSeverity,
    InspectorTarget,
)

ARABIC_CHAR_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")
ARABIC_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670]")
DIGIT_RE = re.compile(r"[\u0660-\u06690-9]")

MODELS = [
    pytest.param("gpt-4o", "6646261c6eb563165658bbb1", id="gpt-4o"),
    pytest.param("gpt-4.1-nano", "67fd9e2bef0365783d06e2f0", id="gpt-4.1-nano"),
    pytest.param("claude-opus-4.6", "698c87701239a117fd66b468", id="claude-opus-4.6"),
]

ARABIC_QUERIES = {
    "pure_arabic": "ما هي أهم القوانين التجارية في المملكة العربية السعودية؟",
    "arabic_punctuation": "أولاً: العقود التجارية؛ ثانياً: الشركات، ثالثاً: الإفلاس. ما رأيك؟",
    "mixed_ar_en": "اشرح لي مفهوم Due Diligence في القانون السعودي وما هي متطلبات الـ Compliance؟",
    "arabic_with_numbers": "المادة ١٢٣ من نظام الشركات لعام ٢٠٢٣م تنص على أن رأس المال لا يقل عن ٥٠٠,٠٠٠ ريال.",
    "arabic_special_chars": "عنوان المكتب: شارع الملك فهد، الرياض\nهاتف: +٩٦٦-١١-٢٣٤-٥٦٧٨\nبريد: info@lawfirm.sa",
    "arabic_long_diacritics": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ — هذا نَصٌّ مُشَكَّلٌ لاختبار المعالجة.",
    "arabic_legal_template": """
    بموجب هذا العقد المبرم بين:
    الطرف الأول: شركة «النور للاستشارات القانونية» (سجل تجاري رقم: ١٠١٠٥٤٣٢١٠)
    الطرف الثاني: مؤسسة «الأمانة للتجارة» (سجل تجاري رقم: ١٠١٠٦٧٨٩٠٠)
    يتفق الطرفان على البنود التالية:
    ١. مدة العقد: سنة هجرية كاملة.
    ٢. قيمة العقد: ٧٥٠,٠٠٠ ريال سعودي.
    ٣. التحكيم: يخضع لنظام التحكيم السعودي.
    """,
}

QUERY_EXPECTATIONS = {
    "pure_arabic": {"min_arabic_ratio": 0.35, "require_keywords": ["نظام"]},
    "arabic_punctuation": {"min_arabic_ratio": 0.30, "require_keywords": ["عقود", "شركات"]},
    "mixed_ar_en": {"min_arabic_ratio": 0.20, "require_keywords_any": ["Due Diligence", "Compliance"]},
    "arabic_with_numbers": {"min_arabic_ratio": 0.20, "require_any_number": True},
    "arabic_special_chars": {"min_arabic_ratio": 0.15, "require_any_number": True},
    "arabic_long_diacritics": {"min_arabic_ratio": 0.35, "require_diacritics": True},
    "arabic_legal_template": {"min_arabic_ratio": 0.30, "require_keywords_any": ["عقد", "التحكيم", "ريال"]},
}

SINGLE_AGENT_DEFS = [
    {
        "name": "SingleLegal",
        "description": "Arabic legal advisor - single agent, Arabic instructions + input",
        "instructions": (
            "ROLE: أنت مستشار قانوني سعودي متخصص في القانون التجاري.\n"
            "CONSTRAINTS: أجب باللغة العربية فقط. استخدم المصطلحات القانونية الصحيحة.\n"
            "OUTPUT RULES: رتّب إجابتك في نقاط مرقّمة. اذكر المراجع النظامية إن وُجدت."
        ),
        "queries": ["pure_arabic", "arabic_punctuation", "arabic_legal_template"],
    },
    {
        "name": "MixedLang",
        "description": "Mixed Arabic/English agent - tests bilingual serialization",
        "instructions": (
            "ROLE: You are a bilingual legal consultant fluent in Arabic and English.\n"
            "CONSTRAINTS: Respond in the same language the user writes in. "
            "If the query is mixed, respond in Arabic with English legal terms preserved.\n"
            "OUTPUT RULES: Structured bullet points. Cite Saudi regulations by article number."
        ),
        "queries": ["mixed_ar_en", "arabic_with_numbers", "arabic_special_chars"],
    },
    {
        "name": "Diacritics",
        "description": "Tests Arabic diacritics and special Unicode in instructions",
        "instructions": (
            "ROLE: أنت مُدقِّقٌ لُغَوِيٌّ متخصِّصٌ في النُّصوصِ العَرَبِيَّةِ المُشَكَّلَة.\n"
            "CONSTRAINTS: صحِّح أيَّ أخطاءٍ إملائيَّةٍ أو نحويَّةٍ. أضِف التَّشكيلَ الكاملَ للنَّصِّ.\n"
            "OUTPUT RULES: أعِد النَّصَّ المُصَحَّحَ مع التَّشكيلِ الكاملِ."
        ),
        "queries": ["arabic_long_diacritics", "pure_arabic"],
    },
]


def _contains_arabic(text: str) -> bool:
    return bool(ARABIC_CHAR_RE.search(text))


def _contains_diacritics(text: str) -> bool:
    return bool(ARABIC_DIACRITICS_RE.search(text))


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


def _assert_success_response(response) -> tuple[str, list]:
    assert response is not None
    assert getattr(response, "completed", None) is True
    assert getattr(response, "status", "").upper() == "SUCCESS"
    output = _extract_output(response)
    assert output.strip(), "Expected a non-empty response output"
    return output, _extract_steps(response)


def _assert_query_expectations(query_key: str, output: str) -> None:
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

    if expectations.get("require_any_number"):
        assert DIGIT_RE.search(output), f"Expected numeric content in {query_key} response"

    if expectations.get("require_diacritics"):
        assert _contains_diacritics(output), f"Expected Arabic diacritics in {query_key} response"


def _build_name(prefix: str, model_name: str) -> str:
    return f"{prefix}-{model_name}-{int(time.time())}-{uuid.uuid4().hex[:6]}"


def _is_inspector_step(step: dict) -> bool:
    agent_info = step.get("agent") or {}
    return (agent_info.get("id") or "").lower().startswith("inspector")


def _is_inspector_abort_message(output: str) -> bool:
    normalized = output.lower()
    return "inspector detected issues" in normalized or "check your input query and inspector configuration" in normalized


@pytest.fixture
def resource_tracker():
    """Track created resources for reliable cleanup."""
    resources = []
    yield resources
    for resource in reversed(resources):
        try:
            resource.delete()
        except Exception:
            pass


def _make_single_agent(client, llm_id: str, model_name: str, agent_def: dict):
    agent = client.Agent(
        name=_build_name(agent_def["name"], model_name),
        description=agent_def["description"],
        instructions=agent_def["instructions"],
        llm=llm_id,
        max_tokens=900,
        max_iterations=4,
    )
    agent.save()
    return agent


def _make_team_agent(client, llm_id: str, model_name: str, inspectors=None):
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
    drafter.save()

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
        max_tokens=900,
        max_iterations=4,
    )
    team_agent.save()
    return [researcher, drafter, team_agent]


def _make_output_inspector(llm_id: str, model_name: str):
    return Inspector(
        name=f"ArabicContentValidator-{model_name}",
        severity=InspectorSeverity.HIGH,
        targets=[InspectorTarget.OUTPUT],
        action=InspectorActionConfig(type=InspectorAction.ABORT),
        evaluator=EvaluatorConfig(
            type=EvaluatorType.ASSET,
            asset_id=llm_id,
            prompt=(
                "تحقق من أن الرد مكتوب بالعربية الفصحى وأنه يتعلق بالقانون التجاري السعودي فقط. "
                "إذا كان الرد بلغة أخرى أو خارج النطاق، ارفضه."
            ),
        ),
    )


@pytest.mark.parametrize(("model_name", "llm_id"), MODELS)
def test_arabic_single_agent_variants_across_llms(client, resource_tracker, model_name, llm_id):
    """Keep broad LLM coverage, but run only one representative query per agent variant."""
    representative_queries = {
        "SingleLegal": "pure_arabic",
        "MixedLang": "mixed_ar_en",
        "Diacritics": "arabic_long_diacritics",
    }

    for agent_config in SINGLE_AGENT_DEFS:
        query_key = representative_queries[agent_config["name"]]
        agent = _make_single_agent(client, llm_id, model_name, agent_config)
        resource_tracker.append(agent)

        response = agent.run(ARABIC_QUERIES[query_key])
        output, _ = _assert_success_response(response)
        _assert_query_expectations(query_key, output)


@pytest.mark.parametrize(("model_name", "llm_id"), MODELS)
def test_arabic_team_agent_across_llms(client, resource_tracker, model_name, llm_id):
    """Use one contract-heavy query to cover the team-agent serialization path."""
    resources = _make_team_agent(client, llm_id, model_name)
    resource_tracker.extend(resources)
    team_agent = resources[-1]

    response = team_agent.run(ARABIC_QUERIES["arabic_legal_template"])
    output, steps = _assert_success_response(response)
    _assert_query_expectations("arabic_legal_template", output)
    assert steps, "Expected team-agent execution steps for Arabic team flow"


@pytest.mark.parametrize(("model_name", "llm_id"), MODELS)
def test_arabic_inspector_agent_across_llms(client, resource_tracker, model_name, llm_id):
    """Verify the inspector actually executes on the Arabic runtime path."""
    inspector = _make_output_inspector(llm_id, model_name)
    resources = _make_team_agent(client, llm_id, model_name, inspectors=[inspector])
    resource_tracker.extend(resources)
    team_agent = resources[-1]

    response = team_agent.run(ARABIC_QUERIES["pure_arabic"])
    output, steps = _assert_success_response(response)
    response_generator_steps = [
        step for step in steps if ((step.get("agent") or {}).get("id") or "").lower() == "response_generator"
    ]
    assert len(response_generator_steps) == 1, "Expected exactly one response_generator step"

    response_generator_index = steps.index(response_generator_steps[0])
    inspector_steps = [step for step in steps[response_generator_index + 1 :] if _is_inspector_step(step)]
    assert inspector_steps, "Expected inspector step(s) after response_generator"

    if _is_inspector_abort_message(output):
        return

    _assert_query_expectations("pure_arabic", output)
