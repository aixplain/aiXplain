"""Unit tests for the pure helpers and small methods of ``aixplain.v2.rlm``.

Covers response parsing (code blocks, FINAL/FINAL_VAR), truncation, the
llm_query marker protocol, chunking, mode selection, prompt serialization,
context resolution, reprs, ``as_tool`` and the BUG-936 secret tripwire.
"""

import json
import pathlib

import pytest

from aixplain.v2 import rlm as rlm_mod
from aixplain.v2.exceptions import ResourceError
from aixplain.v2.rlm import RLM, RLMResult

from tests.unit.v2._rlm_fakes import API_KEY, FakeModel, make_context, make_rlm


@pytest.fixture(autouse=True)
def _no_env_keys(monkeypatch):
    monkeypatch.delenv("TEAM_API_KEY", raising=False)
    monkeypatch.delenv("AIXPLAIN_API_KEY", raising=False)


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------


class TestFindCodeBlocks:
    def test_extracts_every_repl_block_stripped(self):
        text = "plan\n```repl\nx = 1\n```\nmore\n```repl\n  print(x)  \n```\n"
        assert rlm_mod._find_code_blocks(text) == ["x = 1", "print(x)"]

    def test_ignores_non_repl_fences(self):
        assert rlm_mod._find_code_blocks("```python\nx = 1\n```") is None

    def test_none_when_no_blocks(self):
        assert rlm_mod._find_code_blocks("FINAL(done)") is None


class TestFindFinalAnswer:
    def test_final(self):
        assert rlm_mod._find_final_answer("thinking\nFINAL( the answer )") == ("FINAL", "the answer")

    def test_final_var(self):
        assert rlm_mod._find_final_answer("FINAL_VAR(result)") == ("FINAL_VAR", "result")

    def test_final_var_wins_over_final(self):
        assert rlm_mod._find_final_answer("FINAL(a)\nFINAL_VAR(b)") == ("FINAL_VAR", "b")

    def test_must_start_a_line(self):
        assert rlm_mod._find_final_answer("I will call FINAL(x) later") is None

    def test_multiline_content(self):
        assert rlm_mod._find_final_answer("FINAL(line one\nline two)") == ("FINAL", "line one\nline two")

    def test_none_without_declaration(self):
        assert rlm_mod._find_final_answer("still working") is None

    @pytest.mark.xfail(strict=True, reason="non-greedy FINAL\\((.*?)\\) stops at the first ')' in the answer")
    def test_answer_containing_parentheses_is_kept_whole(self):
        assert rlm_mod._find_final_answer("FINAL(Revenue grew (see Q3) by 5%)") == (
            "FINAL",
            "Revenue grew (see Q3) by 5%",
        )


class TestTruncate:
    def test_short_text_unchanged(self):
        assert rlm_mod._truncate("abc", max_chars=3) == "abc"

    def test_long_text_truncated_with_note(self):
        out = rlm_mod._truncate("abcdefghij", max_chars=4)
        assert out.startswith("abcd\n")
        assert "6 chars omitted" in out


class TestMessagesToPrompt:
    def test_roles_upper_cased_and_joined(self):
        msgs = [{"role": "system", "content": "S"}, {"role": "user", "content": "U"}]
        assert rlm_mod._messages_to_prompt(msgs) == "[SYSTEM]: S\n\n[USER]: U"

    def test_system_messages_embed_window(self):
        msgs = rlm_mod._build_system_messages("32K tokens")
        assert msgs[0]["role"] == "system"
        assert "32K tokens" in msgs[0]["content"]
        assert rlm_mod._LLM_PENDING_SENTINEL in msgs[0]["content"]

    def test_next_action_message_variants(self):
        first = rlm_mod._next_action_message("Q?", 0)
        later = rlm_mod._next_action_message("Q?", 3)
        forced = rlm_mod._next_action_message("Q?", 3, force_final=True)
        assert first["content"].startswith(rlm_mod._FIRST_ITER_PREFIX)
        assert later["content"].startswith(rlm_mod._CONTINUING_PREFIX)
        assert '"Q?"' in first["content"]
        assert forced == {"role": "user", "content": rlm_mod._FORCE_FINAL_PROMPT}


# ---------------------------------------------------------------------------
# llm_query marker protocol
# ---------------------------------------------------------------------------


class TestExtractLlmRequests:
    M = rlm_mod._LLM_REQUEST_MARKER

    def test_no_marker_passthrough(self):
        assert rlm_mod._extract_llm_requests("hello\nworld") == ("hello\nworld", [])

    def test_marker_lines_removed_and_prompts_collected(self):
        stdout = f"before\n{self.M}{json.dumps(['p1', 'p2'])}\nafter\n{self.M}{json.dumps(['p3', 4])}"
        clean, prompts = rlm_mod._extract_llm_requests(stdout)
        assert clean == "before\nafter"
        assert prompts == ["p1", "p2", "p3", "4"]

    def test_text_before_marker_on_same_line_is_kept(self):
        clean, prompts = rlm_mod._extract_llm_requests(f"prefix {self.M}{json.dumps(['p'])}")
        assert clean == "prefix "
        assert prompts == ["p"]

    def test_malformed_payload_skipped(self):
        clean, prompts = rlm_mod._extract_llm_requests(f'{self.M}["trunc')
        assert clean == ""
        assert prompts == []

    def test_non_list_payload_and_non_scalar_items_ignored(self):
        stdout = f"{self.M}{json.dumps({'a': 1})}\n{self.M}{json.dumps(['ok', {'x': 1}, None])}"
        _, prompts = rlm_mod._extract_llm_requests(stdout)
        assert prompts == ["ok"]

    def test_marker_count_capped(self, monkeypatch):
        monkeypatch.setattr(rlm_mod, "_LLM_MAX_MARKERS_PER_BLOCK", 2)
        stdout = "\n".join(f"{self.M}{json.dumps([f'p{i}'])}" for i in range(5))
        _, prompts = rlm_mod._extract_llm_requests(stdout)
        assert prompts == ["p0", "p1"]

    def test_prompt_count_capped(self, monkeypatch):
        monkeypatch.setattr(rlm_mod, "_LLM_MAX_PROMPTS_PER_BATCH", 3)
        _, prompts = rlm_mod._extract_llm_requests(f"{self.M}{json.dumps([str(i) for i in range(10)])}")
        assert prompts == ["0", "1", "2"]

    def test_prompt_key_matches_prelude_hash(self):
        import hashlib

        assert rlm_mod._prompt_key("hi") == hashlib.sha256(b"hi").hexdigest()


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------


class TestChunkBudget:
    def test_budget_formula(self):
        # int(32000 * 0.8) - 800 - 4096 = 20704 tokens * 4 chars
        assert rlm_mod._compute_chunk_budget_chars(32_000) == 20_704 * 4

    def test_budget_floor(self):
        assert rlm_mod._compute_chunk_budget_chars(100) == 1000 * 4


class TestChunkText:
    def test_fits_in_one_chunk(self):
        assert rlm_mod._chunk_text("abc", 10) == ["abc"]

    def test_overlapping_chunks_cover_the_text(self):
        text = "".join(chr(ord("a") + i % 26) for i in range(100))
        chunks = rlm_mod._chunk_text(text, 40, overlap=10)
        assert all(len(c) <= 40 for c in chunks)
        assert [len(c) for c in chunks] == [40, 40, 40]
        # Each chunk starts `budget - overlap` chars after the previous one.
        assert chunks[1] == text[30:70]
        assert chunks[0][-10:] == chunks[1][:10]
        assert chunks[-1] == text[60:]

    def test_overlap_larger_than_budget_still_progresses(self):
        chunks = rlm_mod._chunk_text("abcdef", 2, overlap=5)
        assert chunks == ["ab", "bc", "cd", "de", "ef"]


class TestChunkContext:
    def test_list_of_strings_grouped_with_blank_line(self):
        chunks = rlm_mod._chunk_context(["aaaa", "bbbb", "cccc"], budget_chars=12)
        assert chunks == ["aaaa\n\nbbbb", "cccc"]

    def test_list_of_objects_serialized_as_json(self):
        items = [{"id": 1}, {"id": 2}]
        chunks = rlm_mod._chunk_context(items, budget_chars=1000)
        assert len(chunks) == 1
        assert json.loads(chunks[0]) == items

    def test_dict_split_by_items(self):
        d = {"a": "x" * 20, "b": "y" * 20, "c": "z" * 20}
        chunks = rlm_mod._chunk_context(d, budget_chars=60)
        merged = {}
        for c in chunks:
            merged.update(json.loads(c))
        assert merged == d
        assert len(chunks) == 2

    def test_string_context(self):
        assert rlm_mod._chunk_context("x" * 25, budget_chars=10) == rlm_mod._chunk_text("x" * 25, 10)

    def test_other_types_stringified(self):
        assert rlm_mod._chunk_context(12345, budget_chars=100) == ["12345"]

    def test_oversize_item_rechunked(self):
        chunks = rlm_mod._chunk_context(["q" * 5000], budget_chars=1000)
        assert len(chunks) > 1
        assert all(len(c) <= 1000 for c in chunks)


class TestSelectMode:
    @pytest.mark.parametrize("query", ["Compare across the chapters", "Find INCONSISTENCIES", "go step by step"])
    def test_recursive_hints(self, query):
        assert rlm_mod._select_mode(query) == "recursive"

    def test_default_parallel(self):
        assert rlm_mod._select_mode("Summarize the document") == "parallel"


# ---------------------------------------------------------------------------
# Reprs, as_tool, unsupported entry points
# ---------------------------------------------------------------------------


class TestReprAndTool:
    def test_rlm_result_repr_includes_rlm_fields(self):
        r = RLMResult(status="SUCCESS", completed=True, data="x")
        r.iterations_used = 3
        r.used_credits = 1.5
        text = repr(r)
        assert "iterations_used=3" in text
        assert "used_credits=1.5" in text
        assert text.endswith("\n)")

    def test_rlm_result_serialization_excludes_logs(self):
        r = RLMResult(status="SUCCESS", completed=True, data="x", used_credits=2.0, repl_logs=[{"a": 1}])
        dumped = r.to_dict()
        assert dumped["usedCredits"] == 2.0
        assert "repl_logs" not in dumped

    def test_rlm_repr(self):
        rlm = make_rlm(orchestrator_id="o1", worker_id="w1", max_iterations=4)
        rlm.id = "rid"
        assert repr(rlm) == "RLM(orchestrator_id='o1', worker_id='w1', max_iterations=4, id='rid')"

    def test_auto_uuid_id(self):
        assert make_rlm().id
        assert make_rlm().id != make_rlm().id

    def test_explicit_id_preserved(self):
        assert make_rlm(id="fixed").id == "fixed"

    def test_as_tool_defaults(self):
        rlm = make_rlm(id="rid")
        tool = rlm.as_tool()
        assert tool["id"] == tool["assetId"] == "rid"
        assert tool["name"] == "RLM"
        assert tool["type"] == "model"
        assert tool["function"] == "text-generation"
        assert "long-context" in tool["description"]

    def test_as_tool_uses_name_and_description(self):
        rlm = make_rlm(id="rid", name="Reader", description="reads")
        tool = rlm.as_tool()
        assert tool["name"] == "Reader"
        assert tool["description"] == "reads"

    def test_run_async_unsupported(self):
        with pytest.raises(NotImplementedError):
            make_rlm().run_async("x")

    def test_run_stream_unsupported(self):
        with pytest.raises(NotImplementedError):
            make_rlm().run_stream("x")


# ---------------------------------------------------------------------------
# Context resolution
# ---------------------------------------------------------------------------


class TestResolveContext:
    def test_raw_text_passthrough(self):
        assert RLM._resolve_context("just some text") == "just some text"

    def test_url_passthrough(self):
        assert RLM._resolve_context("https://example.com/doc.txt") == "https://example.com/doc.txt"

    def test_dict_and_list_passthrough(self):
        d = {"a": 1}
        lst = [1, 2]
        assert RLM._resolve_context(d) is d
        assert RLM._resolve_context(lst) is lst

    def test_other_types_stringified(self):
        assert RLM._resolve_context(42) == "42"

    def test_text_file_path_str(self, tmp_path):
        f = tmp_path / "doc.txt"
        f.write_text("file body", encoding="utf-8")
        assert RLM._resolve_context(str(f)) == "file body"

    def test_pathlib_path(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text("# title", encoding="utf-8")
        assert RLM._resolve_context(pathlib.Path(f)) == "# title"

    def test_json_file_parsed(self, tmp_path):
        f = tmp_path / "doc.JSON"
        f.write_text(json.dumps({"k": [1, 2]}), encoding="utf-8")
        assert RLM._resolve_context(f) == {"k": [1, 2]}

    def test_invalid_json_file_raises_value_error(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("{not json", encoding="utf-8")
        with pytest.raises(ValueError, match="failed to read context file"):
            RLM._resolve_context(f)

    def test_url_context_non_url_passthrough(self):
        assert RLM._resolve_url_context("plain") == "plain"
        assert RLM._resolve_url_context({"a": 1}) == {"a": 1}

    @pytest.mark.parametrize(
        "url,content_type,body,expected",
        [
            ("https://e.com/data", "application/json; charset=utf-8", '{"a": 1}', {"a": 1}),
            ("https://e.com/data.JSON?sig=1", "text/plain", "[1, 2]", [1, 2]),
            ("https://e.com/data.json", "application/json", "not json", "not json"),
            ("https://e.com/doc.txt", "text/plain", "hello", "hello"),
        ],
    )
    def test_url_context_fetched_via_safe_get(self, monkeypatch, url, content_type, body, expected):
        import aixplain.utils.url_safety as url_safety

        class _Resp:
            headers = {"Content-Type": content_type}
            text = body

            def raise_for_status(self):
                pass

            def json(self):
                return json.loads(body)

        calls = []
        monkeypatch.setattr(url_safety, "safe_get", lambda u, timeout: calls.append((u, timeout)) or _Resp())
        assert RLM._resolve_url_context(url) == expected
        assert calls == [(url, 60)]


# ---------------------------------------------------------------------------
# Worker metadata
# ---------------------------------------------------------------------------


class TestWorkerWindow:
    @pytest.mark.parametrize(
        "raw,label,tokens",
        [
            (2_000_000, "2.0M tokens", 2_000_000),
            ("128000", "128K tokens", 128_000),
            (512, "512 tokens", 512),
            ("lots", "lots", rlm_mod._DEFAULT_WORKER_WINDOW_TOKENS),
            (None, "a large context window", rlm_mod._DEFAULT_WORKER_WINDOW_TOKENS),
        ],
    )
    def test_window_label_and_tokens(self, raw, label, tokens):
        worker = FakeModel(max_context_length=raw)
        rlm = make_rlm(make_context(models={"worker": worker}))
        assert rlm._get_worker_context_window() == label
        assert rlm._get_worker_context_tokens() == tokens

    def test_models_resolved_once_and_cached(self):
        ctx = make_context(models={"worker": FakeModel(), "orch": FakeModel()})
        rlm = make_rlm(ctx)
        assert rlm._get_worker() is rlm._get_worker()
        assert rlm._get_orchestrator() is rlm._get_orchestrator()
        rlm._get_sandbox()
        rlm._get_sandbox()
        assert ctx.Model.get.call_count == 2
        ctx.Tool.get.assert_called_once_with(rlm_mod._SANDBOX_TOOL_ID)


# ---------------------------------------------------------------------------
# Secret tripwire + redaction (BUG-936)
# ---------------------------------------------------------------------------


class TestSecrets:
    def test_secret_values_from_context_and_env(self, monkeypatch):
        monkeypatch.setenv("TEAM_API_KEY", "env-team-key-123")
        monkeypatch.setenv("AIXPLAIN_API_KEY", "short")  # below _MIN_SECRET_LEN -> ignored
        rlm = make_rlm()
        assert set(rlm._secret_values()) == {API_KEY, "env-team-key-123"}

    def test_contains_secret(self):
        rlm = make_rlm()
        assert rlm._contains_secret(f"key={API_KEY}")
        assert not rlm._contains_secret("nothing here")
        assert not rlm._contains_secret("")
        assert not rlm._contains_secret(None)

    def test_assert_no_secrets_raises(self):
        rlm = make_rlm()
        rlm._assert_no_secrets("print('safe')")
        with pytest.raises(ResourceError, match="BUG-936"):
            rlm._assert_no_secrets(f"KEY = '{API_KEY}'")

    def test_redact(self):
        rlm = make_rlm()
        assert rlm._redact(f"a {API_KEY} b {API_KEY}") == "a ***REDACTED*** b ***REDACTED***"
        assert rlm._redact("") == ""
        assert rlm._redact(None) is None

    def test_short_context_key_is_not_treated_as_secret(self):
        ctx = make_context()
        ctx.api_key = "abc"
        rlm = make_rlm(ctx)
        assert rlm._secret_values() == ()
        assert rlm._redact("abc") == "abc"
