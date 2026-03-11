__author__ = "aiXplain"

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

Author: aiXplain Team
Description:
    RLM (Recursive Language Model) — orchestrates long-context analysis via
    an iterative REPL sandbox. The orchestrator model plans and writes Python
    code to chunk and explore a large context; a worker model handles per-chunk
    analysis via llm_query() calls injected into the sandbox session.
"""

import json
import logging
import os
import re
import tempfile
import time
import uuid
from typing import Dict, List, Optional, Text, Union

from aixplain.enums import Function, FunctionType, Supplier
from aixplain.enums.response_status import ResponseStatus
from aixplain.modules.model import Model
from aixplain.modules.model.response import ModelResponse
from aixplain.utils import config


# Sandbox 

# aiXplain managed Python sandbox tool ID.
_SANDBOX_TOOL_ID = "698cda188bbb345db14ac13b"

# Maximum characters of sandbox output fed back to the orchestrator per step.
_REPL_OUTPUT_MAX_CHARS = 100_000


# Prompt Templates 

_SYSTEM_PROMPT = """You are tasked with answering a query with associated context. You can access, transform, and analyze this context interactively in a REPL environment that can recursively query sub-LLMs, which you are strongly encouraged to use as much as possible. You will be queried iteratively until you provide a final answer.

The REPL environment is initialized with:
1. A `context` variable that contains extremely important information about your query. You should check the content of the `context` variable to understand what you are working with. Make sure you look through it sufficiently as you answer your query.
2. A `llm_query` function that allows you to query an LLM (that can handle around 500K chars) inside your REPL environment.
3. The ability to use `print()` statements to view the output of your REPL code and continue your reasoning.

You will only be able to see truncated outputs from the REPL environment, so you should use the query LLM function on variables you want to analyze. You will find this function especially useful when you have to analyze the semantics of the context. Use these variables as buffers to build up your final answer.
Make sure to explicitly look through the entire context in REPL before answering your query. An example strategy is to first look at the context and figure out a chunking strategy, then break up the context into smart chunks, and query an LLM per chunk with a particular question and save the answers to a buffer, then query an LLM with all the buffers to produce your final answer.

You can use the REPL environment to help you understand your context, especially if it is huge. Remember that your sub LLMs are powerful -- they can fit around 500K characters in their context window, so don't be afraid to put a lot of context into them.

When you want to execute Python code in the REPL environment, wrap it in triple backticks with the 'repl' language identifier:
```repl
# your Python code here
chunk = context[:10000]
answer = llm_query(f"What is the key finding in this text?\\n{chunk}")
print(answer)
```

IMPORTANT: When you are done with the iterative process, you MUST provide a final answer using one of these two forms (NOT inside a code block):
1. FINAL(your final answer here) — to provide the answer as literal text
2. FINAL_VAR(variable_name) — to return a variable you created in the REPL as your final answer

Think step by step carefully, plan, and execute this plan immediately — do not just say what you will do.
"""

_USER_PROMPT = (
    "Think step-by-step on what to do using the REPL environment (which contains the context) "
    "to answer the original query: \"{query}\".\n\n"
    "Continue using the REPL environment, which has the `context` variable, and querying sub-LLMs "
    "by writing to ```repl``` tags, and determine your answer. Your next action:"
)

_FIRST_ITER_PREFIX = (
    "You have not interacted with the REPL environment or seen your context yet. "
    "Your next action should be to look through the context first — do not provide a final answer yet.\n\n"
)

_CONTINUING_PREFIX = "The history above is your previous interactions with the REPL environment. "

_FORCE_FINAL_PROMPT = (
    "Based on all the information gathered so far, provide a final answer to the user's query. "
    "Use FINAL(your answer) or FINAL_VAR(variable_name)."
)

_DEFAULT_QUERY = (
    "Please read through the context and answer any queries or respond to "
    "any instructions contained within it."
)


# Prompt Helpers 

def _build_system_messages() -> List[Dict[str, str]]:
    return [{"role": "system", "content": _SYSTEM_PROMPT}]


def _next_action_message(query: str, iteration: int, force_final: bool = False) -> Dict[str, str]:
    if force_final:
        return {"role": "user", "content": _FORCE_FINAL_PROMPT}
    prefix = _FIRST_ITER_PREFIX if iteration == 0 else _CONTINUING_PREFIX
    return {"role": "user", "content": prefix + _USER_PROMPT.format(query=query)}


def _messages_to_prompt(messages: List[Dict[str, str]]) -> str:
    """Serialize a chat message list to a single prompt string for Model.run()."""
    return "\n\n".join(
        f"[{msg['role'].upper()}]: {msg['content']}"
        for msg in messages
    )


# Response Parsing 

def _find_code_blocks(text: str) -> Optional[List[str]]:
    """Extract all ```repl ... ``` code blocks from a model response."""
    results = [
        m.group(1).strip()
        for m in re.finditer(r"```repl\s*\n(.*?)\n```", text, re.DOTALL)
    ]
    return results if results else None


def _find_final_answer(text: str) -> Optional[tuple]:
    """Return (type, content) for FINAL_VAR or FINAL declarations, or None."""
    match = re.search(r"^\s*FINAL_VAR\((.*?)\)", text, re.MULTILINE | re.DOTALL)
    if match:
        return ("FINAL_VAR", match.group(1).strip())
    match = re.search(r"^\s*FINAL\((.*?)\)", text, re.MULTILINE | re.DOTALL)
    if match:
        return ("FINAL", match.group(1).strip())
    return None


def _truncate(text: str, max_chars: int = _REPL_OUTPUT_MAX_CHARS) -> str:
    if len(text) > max_chars:
        return text[:max_chars] + f"\n... [truncated — {len(text) - max_chars} chars omitted]"
    return text


# RLM Class 

class RLM(Model):
    """Recursive Language Model — long-context analysis via an iterative REPL sandbox.

    RLM wraps two aiXplain models:

    - An **orchestrator** (powerful, expensive): plans and writes Python code to
      explore the context iteratively in a managed sandbox environment.
    - A **worker** (fast, cheap): called via ``llm_query()`` inside the sandbox
      to perform focused analysis on individual context chunks.

    The sandbox is an aiXplain managed Python execution environment. Each
    ``run()`` call gets its own isolated session (UUID), so variables persist
    across REPL iterations within a single run but are cleaned up afterwards.

    Example usage::

        from aixplain.factories import ModelFactory

        rlm = ModelFactory.create_rlm(
            orchestrator_model_id="<orchestrator-model-id>",
            worker_model_id="<worker-model-id>",
        )
        response = rlm.run(data={
            "context": very_long_document,
            "query": "What are the key findings?",
        })
        print(response.data)
        print(f"Completed in {response['iterations_used']} iterations.")

    Attributes:
        orchestrator (Model): Root LLM that plans and writes REPL code.
        worker (Model): Sub-LLM used inside the sandbox via ``llm_query()``.
        max_iterations (int): Maximum orchestrator loop iterations before a
            forced final answer is requested.
    """

    # aiXplain managed Python sandbox tool ID.
    SANDBOX_TOOL_ID: str = _SANDBOX_TOOL_ID

    def __init__(
        self,
        id: Text,
        name: Text = "RLM",
        description: Text = "Recursive Language Model for long-context analysis.",
        orchestrator: Optional[Model] = None,
        worker: Optional[Model] = None,
        max_iterations: int = 10,
        api_key: Optional[Text] = None,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        **additional_info,
    ) -> None:
        """Initialize a new RLM instance.

        Args:
            id (Text): Identifier for this RLM instance.
            name (Text, optional): Display name. Defaults to "RLM".
            description (Text, optional): Description. Defaults to a generic string.
            orchestrator (Model, optional): Root LLM that drives the REPL loop.
                Must be set before calling ``run()``. Defaults to None.
            worker (Model, optional): Sub-LLM called inside the sandbox via
                ``llm_query()``. Must be set before calling ``run()``. Defaults to None.
            max_iterations (int, optional): Maximum orchestrator iterations.
                Defaults to 10.
            api_key (Text, optional): API key. Defaults to ``config.TEAM_API_KEY``.
            supplier (Union[Dict, Text, Supplier, int], optional): Supplier.
                Defaults to "aiXplain".
            **additional_info: Additional metadata stored on the instance.
        """
        super().__init__(
            id=id,
            name=name,
            description=description,
            api_key=api_key or config.TEAM_API_KEY,
            supplier=supplier,
            function=Function.TEXT_GENERATION,
            function_type=FunctionType.AI,
            **additional_info,
        )
        self.orchestrator = orchestrator
        self.worker = worker
        self.max_iterations = max_iterations

        # State reset on each run() call
        self._session_id: Optional[str] = None
        self._sandbox_tool: Optional[Model] = None
        self._messages: List[Dict[str, str]] = []

    # Sandbox Setup 

    def _setup_repl(self, context: Union[str, dict, list]) -> None:
        """Initialize a fresh sandbox session and load context + llm_query into it.

        Each call generates a new UUID session ID, ensuring complete isolation
        between runs. The context is serialized to a local temp file, uploaded
        to aiXplain storage, then downloaded and deserialized inside the sandbox
        as a variable named ``context``. This avoids the size limits of injecting
        large contexts as Python string literals.

        Supported context types and their serialization:
            - ``str``        → ``.txt`` file, loaded with ``open().read()``
            - ``dict``/``list`` → ``.json`` file, loaded with ``json.load()``
            - other          → converted to string, stored as ``.txt``

        Args:
            context: The large context to load into the sandbox.
        """
        # Lazy import avoids circular: model_factory → rlm → tool_factory → model_factory
        from aixplain.factories.tool_factory import ToolFactory
        from aixplain.factories.file_factory import FileFactory

        self._session_id = str(uuid.uuid4())
        self._sandbox_tool = ToolFactory.get(self.SANDBOX_TOOL_ID, api_key=self.api_key)
        logging.info(f"RLM: sandbox session started (id={self._session_id}).")

        # Serialize context to a local temp file 
        if isinstance(context, str):
            ext = ".txt"
            content_bytes = context.encode("utf-8")
            load_code = (
                "with open(_filename, 'r', encoding='utf-8') as _f:\n"
                "    context = _f.read()"
            )
        elif isinstance(context, (dict, list)):
            ext = ".json"
            content_bytes = json.dumps(context).encode("utf-8")
            load_code = (
                "import json as __json\n"
                "with open(_filename, 'r', encoding='utf-8') as _f:\n"
                "    context = __json.load(_f)"
            )
        else:
            # Fallback: stringify anything else
            ext = ".txt"
            content_bytes = str(context).encode("utf-8")
            load_code = (
                "with open(_filename, 'r', encoding='utf-8') as _f:\n"
                "    context = _f.read()"
            )

        # Write to a named temp file so the upload filename is predictable
        # (format will be: context.txt or context.json)
        tmp_dir = tempfile.mkdtemp()
        tmp_path = os.path.join(tmp_dir, f"context{ext}")
        try:
            with open(tmp_path, "wb") as f:
                f.write(content_bytes)

            # Upload to aiXplain storage 
            # FileFactory.create(is_temp=True) returns a temporary download URL.
            download_url = FileFactory.create(local_path=tmp_path, is_temp=True)
            logging.debug(f"RLM: context uploaded ({ext}, {len(content_bytes)} bytes).")
        finally:
            # Temp file is no longer needed once uploaded
            try:
                os.unlink(tmp_path)
                os.rmdir(tmp_dir)
            except OSError:
                pass

        # Extract sandbox filename from the download URL 
        # URL format: https://.../{prefix}-{filename}?{query_params}
        # e.g. https://storage.../abc123-context.txt?X-Amz-...
        sandbox_filename = download_url.split("?")[0].split("/")[-1].split("-")[1]

        # Inject sandbox download + load code 
        context_code = f"""import requests as __requests

_url = {repr(download_url)}
_filename = {repr(sandbox_filename)}

with __requests.get(_url, stream=True) as _r:
    _r.raise_for_status()
    with open(_filename, "wb") as _f:
        for _chunk in _r.iter_content(chunk_size=8192):
            if _chunk:
                _f.write(_chunk)

{load_code}
"""

        self._run_sandbox(context_code)
        logging.debug(f"RLM: context loaded into sandbox from uploaded file ({sandbox_filename}).")

        # Inject llm_query 
        # The function is defined directly in the sandbox session so that it
        # persists for all subsequent code blocks in this run. It calls the
        # worker model's run endpoint using requests, with async polling.
        worker_url = (
            f"{self.worker.url}/{self.worker.id}"
            .replace("api/v1/execute", "api/v2/execute")
        )

        llm_query_code = f"""import requests as __requests
import time as __time
import json as __json

def llm_query(prompt):
    _headers = {{"x-api-key": "{self.api_key}", "Content-Type": "application/json"}}
    _payload = __json.dumps({{"data": prompt}})
    try:
        _resp = __requests.post("{worker_url}", headers=_headers, data=_payload, timeout=60)
        _result = _resp.json()
        if _result.get("status") == "IN_PROGRESS":
            _poll_url = _result.get("url")
            _wait = 0.5
            _start = __time.time()
            while not _result.get("completed") and (__time.time() - _start) < 300:
                __time.sleep(_wait)
                _r = __requests.get(_poll_url, headers=_headers, timeout=30)
                _result = _r.json()
                _wait = min(_wait * 1.1, 60)
        return str(_result.get("data", "Error: no data in worker response"))
    except Exception as _e:
        return f"Error: llm_query failed — {{_e}}"
"""

        self._run_sandbox(llm_query_code)
        logging.debug("RLM: llm_query injected into sandbox.")

    def _run_sandbox(self, code: str) -> None:
        """Execute code in the sandbox, ignoring the output (used for setup steps)."""
        self._sandbox_tool.run(
            inputs={"code": code, "sessionId": self._session_id},
            action="run",
        )

    # Code Execution 

    def _execute_code(self, code: str) -> str:
        """Execute a Python code block in the sandbox and return formatted output.

        Runs the code in the current session (preserving all previously defined
        variables), captures stdout and stderr, and returns them as a string
        truncated to ``_REPL_OUTPUT_MAX_CHARS`` characters.

        Args:
            code: Python source code to execute.

        Returns:
            Formatted string combining stdout and stderr. Returns "No output"
            if both are empty.
        """
        result = self._sandbox_tool.run(
            inputs={"code": code, "sessionId": self._session_id},
            action="run",
        )
        stdout = result.data.get("stdout", "") if isinstance(result.data, dict) else ""
        stderr = result.data.get("stderr", "") if isinstance(result.data, dict) else ""

        parts = []
        if stdout:
            parts.append(stdout)
        if stderr:
            parts.append(f"[stderr]: {stderr}")

        raw_output = "\n".join(parts) if parts else "No output"
        return _truncate(raw_output)

    def _get_repl_variable(self, variable_name: str) -> Optional[str]:
        """Retrieve a named variable's string value from the current sandbox session.

        Called when the orchestrator declares ``FINAL_VAR(variable_name)``.
        Runs ``print(str(variable_name))`` in the sandbox and returns stdout.

        Args:
            variable_name: Name of the variable to retrieve (quotes are stripped).

        Returns:
            String representation of the variable, or None if not found or on error.
        """
        var = variable_name.strip().strip("\"'")
        result = self._sandbox_tool.run(
            inputs={"code": f"print(str({var}))", "sessionId": self._session_id},
            action="run",
        )
        stdout = result.data.get("stdout", "") if isinstance(result.data, dict) else ""
        stderr = result.data.get("stderr", "") if isinstance(result.data, dict) else ""

        if stderr and not stdout:
            logging.warning(f"RLM: FINAL_VAR('{var}') error: {stderr.strip()}")
            return None
        return stdout.strip() if stdout else None

    # Orchestrator 

    def _orchestrator_completion(self, messages: List[Dict[str, str]]) -> str:
        """Query the orchestrator model with the full conversation history.

        Serializes the message list to a formatted prompt string and calls
        ``orchestrator.run()``.

        Args:
            messages: Full conversation history as role/content dicts.

        Returns:
            The orchestrator's text response.

        Raises:
            RuntimeError: If the orchestrator model call fails.
        """
        # TODO: If orchestrator supports a native chat/messages API, pass
        #       messages directly instead of serializing to a flat string, e.g.:
        #   if isinstance(self.orchestrator, LLM):
        #       response = self.orchestrator.run(data={"messages": messages})
        prompt = _messages_to_prompt(messages)
        response = self.orchestrator.run(data=prompt, max_tokens = 10000)
        if response.get("completed") or response["status"] == ResponseStatus.SUCCESS:
            return str(response["data"])
        raise RuntimeError(
            f"Orchestrator model failed: {response.get('error_message', 'Unknown error')}"
        )

    # Core Orchestration Loop 

    def run(
        self,
        data: Union[Text, Dict],
        name: Text = "rlm_process",
        timeout: float = 600,
        parameters: Optional[Dict] = None,
        wait_time: float = 0.5,
        stream: bool = False,
    ) -> ModelResponse:
        """Run the RLM orchestration loop over a (potentially large) context.

        A fresh sandbox session is created for each call. The orchestrator is
        called iteratively; each iteration it may execute code blocks in the
        sandbox (with outputs fed back into the conversation) and eventually
        declare a final answer via ``FINAL(...)`` or ``FINAL_VAR(...)``.

        Args:
            data (Union[Text, Dict]): Input data. Two accepted formats:

                - ``str``: Treated as the context; a default query is used.
                - ``dict``: Must contain ``"context"`` (required) and optionally
                  ``"query"`` (defaults to a generic analysis prompt).

            name (Text, optional): Identifier used in log messages.
                Defaults to ``"rlm_process"``.
            timeout (float, optional): Maximum total wall-clock time in seconds.
                Defaults to 600.
            parameters (Optional[Dict], optional): Reserved for future use.
            wait_time (float, optional): Kept for API compatibility. Unused.
            stream (bool, optional): Unsupported. Must be False.

        Returns:
            ModelResponse: Standard response with:

                - ``data``: The final answer string.
                - ``completed``: True on success.
                - ``run_time``: Total elapsed seconds.
                - ``iterations_used``: Number of orchestrator iterations (via
                  ``response["iterations_used"]``).

        Raises:
            AssertionError: If ``orchestrator`` or ``worker`` models are not set,
                or if ``stream=True``.
            ValueError: If ``data`` is a dict missing the ``"context"`` key,
                or an unsupported type.
        """
        assert self.orchestrator is not None, (
            "RLM requires an orchestrator model. "
            "Set rlm.orchestrator or pass orchestrator= to ModelFactory.create_rlm()."
        )
        assert self.worker is not None, (
            "RLM requires a worker model. "
            "Set rlm.worker or pass worker= to ModelFactory.create_rlm()."
        )
        assert not stream, "RLM does not support streaming responses."

        # Parse data argument 
        if isinstance(data, str):
            context = data
            query = _DEFAULT_QUERY
        elif isinstance(data, dict):
            if "context" not in data:
                raise ValueError(
                    "When passing data as a dict, it must contain a 'context' key. "
                    "Optionally include a 'query' key."
                )
            context = data["context"]
            query = data.get("query", _DEFAULT_QUERY)
        else:
            raise ValueError(
                f"Unsupported data type: {type(data)}. Expected str or dict with 'context' key."
            )

        logging.info(f"RLM '{name}': starting. Query: {query[:120]!r}")
        start_time = time.time()
        iterations_used = 0
        final_answer = None
        repl_logs: List[Dict] = []

        # Initialize sandbox and conversation 
        self._setup_repl(context)
        self._messages = _build_system_messages()

        try:
            for iteration in range(self.max_iterations):
                iterations_used = iteration + 1

                if (time.time() - start_time) > timeout:
                    logging.warning(
                        f"RLM '{name}': timeout after {iteration} iterations — forcing final answer."
                    )
                    break

                # Ask orchestrator for its next action
                response_text = self._orchestrator_completion(
                    self._messages + [_next_action_message(query, iteration)]
                )
                logging.debug(f"RLM '{name}' iter {iteration}: orchestrator responded.")

                # Execute repl code blocks if present
                code_blocks = _find_code_blocks(response_text)
                if code_blocks:
                    self._messages.append({"role": "assistant", "content": response_text})
                    for code in code_blocks:
                        output = self._execute_code(code)
                        repl_logs.append({"iteration": iteration, "code": code, "output": output})
                        logging.debug(
                            f"RLM '{name}' iter {iteration}: "
                            f"executed {len(code)} chars → {len(output)} chars output."
                        )
                        self._messages.append({
                            "role": "user",
                            "content": (
                                f"Code executed:\n```python\n{code}\n```\n\n"
                                f"REPL output:\n{output}"
                            ),
                        })
                else:
                    self._messages.append({"role": "assistant", "content": response_text})

                # Check for final answer declaration
                final_result = _find_final_answer(response_text)
                if final_result is not None:
                    answer_type, content = final_result
                    if answer_type == "FINAL":
                        final_answer = content
                        break
                    elif answer_type == "FINAL_VAR":
                        retrieved = self._get_repl_variable(content)
                        if retrieved is not None:
                            final_answer = retrieved
                            break
                        logging.warning(
                            f"RLM '{name}': FINAL_VAR('{content}') not found in sandbox — continuing."
                        )

            # Force a final answer if loop exhausted or timed out without one
            if final_answer is None:
                logging.info(
                    f"RLM '{name}': requesting forced final answer after {iterations_used} iterations."
                )
                self._messages.append(_next_action_message(query, iterations_used, force_final=True))
                final_answer = self._orchestrator_completion(self._messages)

        except Exception as e:
            error_msg = f"RLM run error: {str(e)}"
            logging.error(error_msg)
            return ModelResponse(
                status=ResponseStatus.FAILED,
                completed=True,
                error_message=error_msg,
                run_time=time.time() - start_time,
                iterations_used=iterations_used,
            )

        run_time = time.time() - start_time
        logging.info(f"RLM '{name}': done in {iterations_used} iterations, {run_time:.1f}s.")

        return ModelResponse(
            status=ResponseStatus.SUCCESS,
            data=final_answer or "",
            completed=True,
            run_time=run_time,
            iterations_used=iterations_used,
        )

    def run_async(
        self,
        data: Union[Text, Dict],
        name: Text = "rlm_process",
        parameters: Optional[Dict] = None,
    ) -> ModelResponse:
        """Not supported for RLM.

        Raises:
            NotImplementedError: Always. Use ``run()`` instead.
        """
        raise NotImplementedError("RLM does not support async execution. Use run() instead.")

    def run_stream(self, data: Union[Text, Dict], parameters: Optional[Dict] = None):
        """Not supported for RLM.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("RLM does not support streaming responses.")

    def __repr__(self) -> str:
        """Return a string representation of this RLM instance."""
        orchestrator_name = self.orchestrator.name if self.orchestrator else "None"
        worker_name = self.worker.name if self.worker else "None"
        return (
            f"RLM("
            f"id={self.id!r}, "
            f"orchestrator={orchestrator_name!r}, "
            f"worker={worker_name!r}, "
            f"max_iterations={self.max_iterations}"
            f")"
        )
