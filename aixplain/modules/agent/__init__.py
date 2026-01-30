"""Agent module for aiXplain SDK.

This module provides the Agent class and related functionality for creating and managing
AI agents that can execute tasks using various tools and models.

Copyright 2024 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Lucas Pavanelli and Thiago Castro Ferreira
Date: May 16th 2024
Description:
    Agentification Class
"""

__author__ = "aiXplain"
import inspect
import json
import logging
import re
import time
import traceback
from datetime import datetime

from aixplain.utils.file_utils import _request_with_retry
from aixplain.enums import Function, Supplier, AssetStatus, StorageType, ResponseStatus
from aixplain.enums.evolve_type import EvolveType
from aixplain.modules.model import Model
from aixplain.modules.agent.agent_task import WorkflowTask, AgentTask
from aixplain.modules.agent.output_format import OutputFormat
from aixplain.modules.agent.tool import Tool, DeployableTool
from aixplain.modules.agent.agent_response import AgentResponse
from aixplain.modules.agent.agent_response_data import AgentResponseData
from aixplain.modules.agent.utils import process_variables, validate_history
from pydantic import BaseModel
from typing import Dict, List, Text, Optional, Union, Any
from aixplain.modules.agent.evolve_param import EvolveParam, validate_evolve_param
from urllib.parse import urljoin
from aixplain.modules.model.llm_model import LLM
from aixplain.utils.convert_datatype_utils import normalize_expected_output

from aixplain.utils import config
from aixplain.modules.mixins import DeployableMixin
import warnings


class Agent(Model, DeployableMixin[Union[Tool, DeployableTool]]):
    """An advanced AI system that performs tasks using specialized tools from the aiXplain marketplace.

    This class represents an AI agent that can understand natural language instructions,
    use various tools and models, and execute complex tasks. It combines a large language
    model (LLM) with specialized tools to provide comprehensive task-solving capabilities.

    Attributes:
        id (Text): ID of the Agent.
        name (Text): Name of the Agent.
        tools (List[Union[Tool, Model]]): Collection of tools and models the Agent can use.
        description (Text, optional): Detailed description of the Agent's capabilities.
            Defaults to "".
        instructions (Text): System instructions/prompt defining the Agent's behavior.
        llm_id (Text): ID of the large language model. Defaults to GPT-4o
            (6646261c6eb563165658bbb1).
        llm (Optional[LLM]): The LLM instance used by the Agent.
        supplier (Text): The provider/creator of the Agent.
        version (Text): Version identifier of the Agent.
        status (AssetStatus): Current status of the Agent (DRAFT or ONBOARDED).
        tasks (List[AgentTask]): List of tasks the Agent can perform.
        backend_url (str): URL endpoint for the backend API.
        api_key (str): Authentication key for API access.
        cost (Dict, optional): Pricing information for using the Agent. Defaults to None.
        is_valid (bool): Whether the Agent's configuration is valid.
        cost (Dict, optional): model price. Defaults to None.
        output_format (OutputFormat): default output format for agent responses.
        expected_output (Union[BaseModel, Text, dict], optional): expected output. Defaults to None.
    """

    is_valid: bool

    def __init__(
        self,
        id: Text,
        name: Text,
        description: Text,
        instructions: Optional[Text] = None,
        tools: List[Union[Tool, Model]] = [],
        llm_id: Text = "6646261c6eb563165658bbb1",
        llm: Optional[LLM] = None,
        api_key: Optional[Text] = config.TEAM_API_KEY,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        version: Optional[Text] = None,
        cost: Optional[Dict] = None,
        status: AssetStatus = AssetStatus.DRAFT,
        tasks: List[AgentTask] = [],
        workflow_tasks: List[WorkflowTask] = [],
        output_format: OutputFormat = OutputFormat.TEXT,
        expected_output: Optional[Union[BaseModel, Text, dict]] = None,
        **additional_info,
    ) -> None:
        """Initialize a new Agent instance.

        Args:
            id (Text): ID of the Agent.
            name (Text): Name of the Agent.
            description (Text): Detailed description of the Agent's capabilities.
            instructions (Optional[Text], optional): System instructions/prompt defining
                the Agent's behavior. Defaults to None.
            tools (List[Union[Tool, Model]], optional): Collection of tools and models
                the Agent can use. Defaults to empty list.
            llm_id (Text, optional): ID of the large language model. Defaults to GPT-4o
                (6646261c6eb563165658bbb1).
            llm (Optional[LLM], optional): The LLM instance to use. If provided, takes
                precedence over llm_id. Defaults to None.
            api_key (Optional[Text], optional): Authentication key for API access.
                Defaults to config.TEAM_API_KEY.
            supplier (Union[Dict, Text, Supplier, int], optional): The provider/creator
                of the Agent. Defaults to "aiXplain".
            version (Optional[Text], optional): Version identifier. Defaults to None.
            cost (Optional[Dict], optional): Pricing information. Defaults to None.
            status (AssetStatus, optional): Current status of the Agent.
                Defaults to AssetStatus.DRAFT.
            tasks (List[AgentTask], optional): List of tasks the Agent can perform.
                Defaults to empty list.
            workflow_tasks (List[WorkflowTask], optional): List of workflow tasks
                the Agent can execute. Defaults to empty list.
            output_format (OutputFormat, optional): default output format for agent responses. Defaults to OutputFormat.TEXT.
            expected_output (Union[BaseModel, Text, dict], optional): expected output. Defaults to None.
            **additional_info: Additional configuration parameters.
        """
        super().__init__(id, name, description, api_key, supplier, version, cost=cost)
        self.instructions = instructions
        self.additional_info = additional_info
        self.tools = tools
        for i, _ in enumerate(tools):
            self.tools[i].api_key = api_key
        self.llm_id = llm_id
        self.llm = llm
        if isinstance(status, str):
            try:
                status = AssetStatus(status)
            except Exception:
                status = AssetStatus.DRAFT
        self.status = status
        if tasks:
            warnings.warn(
                "The 'tasks' parameter is deprecated and will be removed in a future version. "
                "Use 'workflow_tasks' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            self.workflow_tasks = tasks
        else:
            self.workflow_tasks = workflow_tasks
        self.tasks = self.workflow_tasks
        self.output_format = output_format
        self.expected_output = expected_output
        self.is_valid = True

    def _validate(self) -> None:
        """Perform internal validation of the Agent's configuration.

        This method checks:
        1. Name contains only valid characters
        2. LLM is a text generation model
        3. Tool names are unique
        4. No nested Agents are used

        Raises:
            AssertionError: If any validation check fails.
        """
        from aixplain.utils.llm_utils import get_llm_instance

        # validate name
        assert (
            re.match(r"^[a-zA-Z0-9 \-\(\)]*$", self.name) is not None
        ), "Agent Creation Error: Agent name contains invalid characters. Only alphanumeric characters, spaces, hyphens, and brackets are allowed."

        llm = get_llm_instance(self.llm_id, api_key=self.api_key, use_cache=True)

        assert (
            llm.function == Function.TEXT_GENERATION
        ), "Large Language Model must be a text generation model."

        tool_names = []
        for tool in self.tools:
            tool_name = None
            if isinstance(tool, Tool):
                tool_name = tool.name
            elif isinstance(tool, Model):
                assert not isinstance(
                    tool, Agent
                ), "Agent cannot contain another Agent."
                tool_name = tool.name
            tool_names.append(tool_name)

        if len(tool_names) != len(set(tool_names)):
            duplicates = set(
                [name for name in tool_names if tool_names.count(name) > 1]
            )
            raise Exception(
                f"Agent Creation Error - Duplicate tool names found: {', '.join(duplicates)}. Make sure all tool names are unique."
            )

            tool_name = tool.name
            tool_names.append(tool_name)

        if len(tool_names) != len(set(tool_names)):
            duplicates = set(
                [name for name in tool_names if tool_names.count(name) > 1]
            )
            raise Exception(
                f"Agent Creation Error - Duplicate tool names found: {', '.join(duplicates)}. Make sure all tool names are unique."
            )

    def validate(self, raise_exception: bool = False) -> bool:
        """Validate the Agent's configuration and mark its validity status.

        This method runs all validation checks and updates the is_valid flag.
        If validation fails, it can either raise an exception or log warnings.

        Args:
            raise_exception (bool, optional): Whether to raise exceptions on validation
                failures. If False, failures are logged as warnings. Defaults to False.

        Returns:
            bool: True if validation passed, False otherwise.

        Raises:
            Exception: If validation fails and raise_exception is True.
        """
        try:
            self._validate()
            self.is_valid = True
        except Exception as e:
            self.is_valid = False
            if raise_exception:
                raise e
            else:
                logging.warning(f"Agent Validation Error: {e}")
                logging.warning(
                    "You won't be able to run the Agent until the issues are handled manually."
                )
        return self.is_valid

    def generate_session_id(self, history: list = None) -> str:
        """Generate a unique session ID for agent conversations.

        Args:
            history (list, optional): Previous conversation history. Defaults to None.

        Returns:
            str: A unique session identifier based on timestamp and random components.
        """
        if history:
            validate_history(history)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        session_id = f"{self.id}_{timestamp}"

        if not history:
            return session_id

        try:
            validate_history(history)
            headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}

            payload = {
                "id": self.id,
                "query": "/",
                "sessionId": session_id,
                "history": history,
                "executionParams": {
                    "maxTokens": 2048,
                    "maxIterations": 10,
                    "outputFormat": OutputFormat.TEXT.value,
                    "expectedOutput": None,
                },
                "allowHistoryAndSessionId": True,
            }

            r = _request_with_retry(
                "post", self.url, headers=headers, data=json.dumps(payload)
            )
            resp = r.json()
            poll_url = resp.get("data")

            result = self.sync_poll(
                poll_url, name="model_process", timeout=300, wait_time=0.5
            )

            if result.get("status") == ResponseStatus.SUCCESS:
                return session_id
            else:
                logging.error(f"Session {session_id} initialization failed: {result}")
                return session_id

        except Exception as e:
            logging.error(f"Failed to initialize session {session_id}: {e}")
            return session_id

    def _normalize_progress_data(self, progress: Dict) -> Dict:
        """Normalize progress data from camelCase to snake_case.

        Args:
            progress (Dict): Progress data from backend (may use camelCase)

        Returns:
            Dict: Normalized progress data with snake_case keys
        """
        if not progress:
            return progress

        # Map camelCase to snake_case for known fields
        normalized = {}
        key_mapping = {
            "toolInput": "tool_input",
            "toolOutput": "tool_output",
            "currentStep": "current_step",
            "totalSteps": "total_steps",
        }

        for key, value in progress.items():
            # Use mapped key if available, otherwise keep original
            normalized_key = key_mapping.get(key, key)
            normalized[normalized_key] = value

        return normalized

    def poll(self, poll_url: Text, name: Text = "model_process") -> "AgentResponse":
        """Override poll to normalize progress data from camelCase to snake_case.

        Args:
            poll_url (Text): URL to poll for operation status.
            name (Text, optional): Identifier for the operation. Defaults to "model_process".

        Returns:
            AgentResponse: Response with normalized progress data.
        """
        # Call parent poll method
        response = super().poll(poll_url, name)

        # Normalize progress data if present (stored in additional_fields)
        if hasattr(response, "additional_fields") and isinstance(response.additional_fields, dict):
            if "progress" in response.additional_fields and response.additional_fields["progress"]:
                response.additional_fields["progress"] = self._normalize_progress_data(
                    response.additional_fields["progress"]
                )

        return response

    def _format_agent_progress(
        self,
        progress: Dict,
        verbosity: Optional[str] = "full",
    ) -> Optional[str]:
        """Format agent progress message based on verbosity level.

        Args:
            progress (Dict): Progress data from polling response
            verbosity (Optional[str]): "full", "compact", or None (disables output)

        Returns:
            Optional[str]: Formatted message or None
        """
        if verbosity is None:
            return None

        stage = progress.get("stage", "working")
        tool = progress.get("tool")
        runtime = progress.get("runtime")
        success = progress.get("success")
        reason = progress.get("reason", "")
        tool_input = progress.get("tool_input", "")
        tool_output = progress.get("tool_output", "")

        # Determine status icon
        if success is True:
            status_icon = "✓"
        elif success is False:
            status_icon = "✗"
        else:
            status_icon = "⏳"

        agent_name = self.name

        if verbosity == "compact":
            # Compact mode: minimal info
            if tool:
                msg = f"⚙️  {agent_name} | {tool} | {status_icon}"
                if success is True and tool_output:
                    output_str = str(tool_output)[:200]
                    msg += f" {output_str}"
                    msg += "..." if len(str(tool_output)) > 200 else ""
            else:
                stage_name = stage.replace("_", " ").title()
                msg = f"🤖  {agent_name} | {status_icon} {stage_name}"
        else:
            # Full verbosity: detailed info
            if tool:
                msg = f"⚙️  {agent_name} | {tool} | {status_icon}"

                if tool_input:
                    msg += f" | Input: {tool_input}"

                if tool_output:
                    msg += f" | Output: {tool_output}"

                if reason:
                    msg += f" | Reason: {reason}"
            else:
                stage_name = stage.replace("_", " ").title()
                msg = f"🤖  {agent_name} | {status_icon} {stage_name}"
                if reason:
                    msg += f" | {reason}"

        return msg

    def _format_completion_message(
        self,
        elapsed_time: float,
        response_body: "AgentResponse",
        timed_out: bool = False,
        timeout: float = 300,
        verbosity: Optional[str] = "full",
    ) -> str:
        """Format completion message with metrics.

        Args:
            elapsed_time (float): Total elapsed time in seconds
            response_body (AgentResponse): Final response
            timed_out (bool): Whether the operation timed out
            timeout (float): Timeout value if timed out
            verbosity (Optional[str]): "full" or "compact"

        Returns:
            str: Formatted completion message
        """
        if timed_out:
            return f"✅ Done | ✗ Timeout - No response after {timeout}s"

        # Collect metrics from execution_stats if available
        total_api_calls = 0
        total_credits = 0.0
        runtime = elapsed_time

        # Extract data dict (handle tuple or direct object)
        data_dict = None
        if hasattr(response_body, "data") and response_body.data:
            if isinstance(response_body.data, tuple) and len(response_body.data) > 0:
                # Data is a tuple, get first element
                data_dict = response_body.data[0] if isinstance(response_body.data[0], dict) else None
            elif isinstance(response_body.data, dict):
                # Data is already a dict
                data_dict = response_body.data
            elif hasattr(response_body.data, "executionStats") or hasattr(response_body.data, "execution_stats"):
                # Data is an object with attributes
                exec_stats = getattr(response_body.data, "executionStats", None) or getattr(
                    response_body.data, "execution_stats", None
                )
                if exec_stats and isinstance(exec_stats, dict):
                    total_api_calls = exec_stats.get("api_calls", 0)
                    total_credits = exec_stats.get("credits", 0.0)
                    runtime = exec_stats.get("runtime", elapsed_time)

        # Try to get metrics from data dict (camelCase fields from backend)
        if data_dict and isinstance(data_dict, dict):
            # Check executionStats first
            exec_stats = data_dict.get("executionStats")
            if exec_stats and isinstance(exec_stats, dict):
                total_api_calls = exec_stats.get("api_calls", 0)
                total_credits = exec_stats.get("credits", 0.0)
                runtime = exec_stats.get("runtime", elapsed_time)

            # Fallback: check top-level fields (usedCredits, runTime)
            if total_credits == 0.0:
                total_credits = data_dict.get("usedCredits", 0.0)
            if runtime == elapsed_time:
                runtime = data_dict.get("runTime", elapsed_time)

        # Build single-line completion message with metrics
        if verbosity == "compact":
            msg = f"✅ Done | ({runtime:.1f} s total"
        else:
            msg = f"✅ Done | Completed successfully ({runtime:.1f} s total"

        # Always show API calls and credits
        if total_api_calls > 0:
            msg += f" | {total_api_calls} API calls"
        msg += f" | ${total_credits}"
        msg += ")"

        return msg

    def sync_poll(
        self,
        poll_url: Text,
        name: Text = "model_process",
        wait_time: float = 0.5,
        timeout: float = 300,
        progress_verbosity: Optional[str] = "compact",
    ) -> "AgentResponse":
        """Poll the platform until agent execution completes or times out.

        Args:
            poll_url (Text): URL to poll for operation status.
            name (Text, optional): Identifier for the operation. Defaults to "model_process".
            wait_time (float, optional): Initial wait time in seconds between polls. Defaults to 0.5.
            timeout (float, optional): Maximum total time to poll in seconds. Defaults to 300.
            progress_verbosity (Optional[str], optional): Progress display mode - "full" (detailed), "compact" (brief), or None (no progress). Defaults to "compact".

        Returns:
            AgentResponse: The final response from the agent execution.
        """
        logging.info(f"Polling for Agent: Start polling for {name}")
        start, end = time.time(), time.time()
        wait_time = max(wait_time, 0.2)
        completed = False
        response_body = AgentResponse(status=ResponseStatus.FAILED, completed=False)
        last_message = None  # Track last message to avoid duplicates

        while not completed and (end - start) < timeout:
            try:
                response_body = self.poll(poll_url, name=name)
                completed = response_body["completed"]

                # Display progress inline if enabled
                if progress_verbosity and not completed:
                    progress = response_body.get("progress")
                    if progress:
                        msg = self._format_agent_progress(progress, progress_verbosity)
                        if msg and msg != last_message:
                            print(msg, flush=True)
                            last_message = msg

                end = time.time()
                if completed is False:
                    time.sleep(wait_time)
                    if wait_time < 60:
                        wait_time *= 1.1
            except Exception as e:
                response_body = AgentResponse(
                    status=ResponseStatus.FAILED,
                    completed=False,
                    error_message="No response from the service.",
                )
                logging.error(f"Polling for Agent: polling for {name}: {e}")
                return response_body
                break

        # Display completion message
        if progress_verbosity:
            elapsed_time = end - start
            timed_out = response_body["completed"] is not True
            completion_msg = self._format_completion_message(
                elapsed_time, response_body, timed_out, timeout, progress_verbosity
            )
            print(completion_msg, flush=True)

        if response_body["completed"] is True:
            logging.debug(f"Polling for Agent: Final status of polling for {name}: {response_body}")
        else:
            response_body = AgentResponse(
                status=ResponseStatus.FAILED,
                completed=False,
                error_message="No response from the service.",
            )
            logging.error(f"Polling for Agent: Final status of polling for {name}: No response in {timeout} seconds")

        return response_body

    def run(
        self,
        data: Optional[Union[Dict, Text]] = None,
        query: Optional[Text] = None,
        session_id: Optional[Text] = None,
        history: Optional[List[Dict]] = None,
        name: Text = "model_process",
        timeout: float = 300,
        parameters: Dict = {},
        wait_time: float = 0.5,
        content: Optional[Union[Dict[Text, Text], List[Text]]] = None,
        max_tokens: int = 4096,
        max_iterations: int = 5,
        trace_request: bool = False,
        progress_verbosity: Optional[str] = "compact",
        run_response_generation: bool = True,
        **kwargs,
    ) -> AgentResponse:
        """Runs an agent call.

        Args:
            data (Optional[Union[Dict, Text]], optional): data to be processed by the agent. Defaults to None.
            query (Optional[Text], optional): query to be processed by the agent. Defaults to None.
            session_id (Optional[Text], optional): conversation Session ID. Defaults to None.
            history (Optional[List[Dict]], optional): chat history (in case session ID is None). Defaults to None.
            name (Text, optional): ID given to a call. Defaults to "model_process".
            timeout (float, optional): total polling time. Defaults to 300.
            parameters (Dict, optional): optional parameters to the model. Defaults to "{}".
            wait_time (float, optional): wait time in seconds between polling calls. Defaults to 0.5.
            content (Union[Dict[Text, Text], List[Text]], optional): Content inputs to be processed according to the query. Defaults to None.
            max_tokens (int, optional): maximum number of tokens which can be generated by the agent. Defaults to 2048.
            max_iterations (int, optional): maximum number of iterations between the agent and the tools. Defaults to 10.
            trace_request (bool, optional): return the request id for tracing the request. Defaults to False.
            progress_verbosity (Optional[str], optional): Progress display mode - "full" (detailed), "compact" (brief), or None (no progress). Defaults to "compact".
            run_response_generation (bool, optional): Whether to run response generation. Defaults to True.
            **kwargs: Additional keyword arguments.

        Returns:
            Dict: parsed output from model
        """
        start = time.time()
        
        # Define supported kwargs
        supported_kwargs = {"output_format", "expected_output"}
        
        # Validate kwargs - raise error if unsupported kwargs are provided
        unsupported_kwargs = set(kwargs.keys()) - supported_kwargs
        if unsupported_kwargs:
            raise ValueError(
                f"Unsupported keyword argument(s): {', '.join(sorted(unsupported_kwargs))}. "
                f"Supported kwargs are: {', '.join(sorted(supported_kwargs))}."
            )
        
        # Extract deprecated parameters from kwargs
        output_format = kwargs.get("output_format", None)
        expected_output = kwargs.get("expected_output", None)

        if output_format is not None:
            warnings.warn(
                "The 'output_format' parameter is deprecated and will be removed in a future version. "
                "Set the output format during agent initialization instead.",
                DeprecationWarning,
                stacklevel=2,
            )

        if expected_output is not None:
            warnings.warn(
                "The 'expected_output' parameter is deprecated and will be removed in a future version. "
                "Set the expected output during agent initialization instead.",
                DeprecationWarning,
                stacklevel=2,
            )


        if session_id is not None and history is not None:
            raise ValueError("Provide either `session_id` or `history`, not both.")

        if session_id is not None:
            if not session_id.startswith(f"{self.id}_"):
                raise ValueError(
                    f"Session ID '{session_id}' does not belong to this Agent."
                )
        if history:
            validate_history(history)
        result_data = {}
        if len(self.tasks) > 0:
            max_iterations = 30
        try:
            response = self.run_async(
                data=data,
                query=query,
                session_id=session_id,
                history=history,
                name=name,
                parameters=parameters,
                content=content,
                max_tokens=max_tokens,
                max_iterations=max_iterations,
                output_format=output_format,
                expected_output=expected_output,
                trace_request=trace_request,
                run_response_generation=run_response_generation,
            )
            if response["status"] == ResponseStatus.FAILED:
                end = time.time()
                response["elapsed_time"] = end - start
                return response
            poll_url = response["url"]
            end = time.time()
            result = self.sync_poll(
                poll_url, name=name, timeout=timeout, wait_time=wait_time, progress_verbosity=progress_verbosity
            )
            result_data = result.get("data") or {}
            if result.status == ResponseStatus.FAILED:
                return AgentResponse(
                    status=ResponseStatus.FAILED,
                    completed=False,
                    data=AgentResponseData(
                        input=result_data.get("input"),
                        output=result_data.get("output"),
                        session_id=result_data.get("session_id"),
                        intermediate_steps=result_data.get("intermediate_steps"),
                        steps=result_data.get("steps"),
                        execution_stats=result_data.get("executionStats"),
                    ),
                    used_credits=result_data.get("usedCredits", 0.0),
                    run_time=result_data.get("runTime", end - start),
                )

            return AgentResponse(
                status=ResponseStatus.SUCCESS,
                completed=True,
                data=AgentResponseData(
                    input=result_data.get("input"),
                    output=result_data.get("output"),
                    session_id=result_data.get("session_id"),
                    intermediate_steps=result_data.get("intermediate_steps"),
                    steps=result_data.get("steps"),
                    execution_stats=result_data.get("executionStats"),
                ),
                used_credits=result_data.get("usedCredits", 0.0),
                run_time=result_data.get("runTime", end - start),
            )
        except Exception as e:
            msg = f"Error in request for {name} - {traceback.format_exc()}"
            logging.error(f"Agent Run: Error in running for {name}: {e}")
            end = time.time()
            return AgentResponse(
                status=ResponseStatus.FAILED,
                data=AgentResponseData(
                    input="",
                    output=None,
                    session_id=session_id,
                    intermediate_steps=None,
                    steps=None,
                    execution_stats=None,
                ),
                error=msg,
            )

    def run_async(
        self,
        data: Optional[Union[Dict, Text]] = None,
        query: Optional[Text] = None,
        session_id: Optional[Text] = None,
        history: Optional[List[Dict]] = None,
        name: Text = "model_process",
        parameters: Dict = {},
        content: Optional[Union[Dict[Text, Text], List[Text]]] = None,
        max_tokens: int = 2048,
        max_iterations: int = 5,
        output_format: Optional[OutputFormat] = None,
        expected_output: Optional[Union[BaseModel, Text, dict]] = None,
        evolve: Union[Dict[str, Any], EvolveParam, None] = None,
        trace_request: bool = False,
        run_response_generation: bool = True,
    ) -> AgentResponse:
        """Runs asynchronously an agent call.

        Args:
            data (Optional[Union[Dict, Text]], optional): data to be processed by the agent. Defaults to None.
            query (Optional[Text], optional): query to be processed by the agent. Defaults to None.
            session_id (Optional[Text], optional): conversation Session ID. Defaults to None.
            history (Optional[List[Dict]], optional): chat history (in case session ID is None). Defaults to None.
            name (Text, optional): ID given to a call. Defaults to "model_process".
            parameters (Dict, optional): optional parameters to the model. Defaults to "{}".
            content (Union[Dict[Text, Text], List[Text]], optional): Content inputs to be processed according to the query. Defaults to None.
            max_tokens (int, optional): maximum number of tokens which can be generated by the agent. Defaults to 2048.
            max_iterations (int, optional): maximum number of iterations between the agent and the tools. Defaults to 10.
            output_format (OutputFormat, optional): response format. If not provided, uses the format set during initialization.
            expected_output (Union[BaseModel, Text, dict], optional): expected output. Defaults to None.
            output_format (ResponseFormat, optional): response format. Defaults to TEXT.
            evolve (Union[Dict[str, Any], EvolveParam, None], optional): evolve the agent configuration. Can be a dictionary, EvolveParam instance, or None.
            trace_request (bool, optional): return the request id for tracing the request. Defaults to False.
            run_response_generation (bool, optional): Whether to run response generation. Defaults to True.

        Returns:
            dict: polling URL in response
        """
        if session_id is not None and history is not None:
            raise ValueError("Provide either `session_id` or `history`, not both.")

        if session_id is not None:
            if not session_id.startswith(f"{self.id}_"):
                raise ValueError(
                    f"Session ID '{session_id}' does not belong to this Agent."
                )

        if history:
            validate_history(history)

        from aixplain.factories.file_factory import FileFactory

        # Validate and normalize evolve parameters using the base model
        evolve_param = validate_evolve_param(evolve)
        evolve_dict = evolve_param.to_dict()

        if output_format == OutputFormat.JSON:
            assert expected_output is not None and (
                issubclass(expected_output, BaseModel)
                or isinstance(expected_output, dict)
            ), "Expected output must be a Pydantic BaseModel or a JSON object when output format is JSON."

        assert (
            data is not None or query is not None
        ), "Either 'data' or 'query' must be provided."
        if data is not None:
            if isinstance(data, dict):
                assert (
                    "query" in data and data["query"] is not None
                ), "When providing a dictionary, 'query' must be provided."
                query = data.get("query")
                if session_id is None:
                    session_id = data.get("session_id")
                if history is None:
                    history = data.get("history")
                if content is None:
                    content = data.get("content")
            else:
                query = data

        # process content inputs
        if content is not None:
            assert (
                FileFactory.check_storage_type(query) == StorageType.TEXT
            ), "When providing 'content', query must be text."

            if isinstance(content, list):
                assert len(content) <= 3, "The maximum number of content inputs is 3."
                for input_link in content:
                    input_link = FileFactory.to_link(input_link)
                    query += f"\n{input_link}"
            elif isinstance(content, dict):
                for key, value in content.items():
                    assert (
                        "{{" + key + "}}" in query
                    ), f"Key '{key}' not found in query."
                    value = FileFactory.to_link(value)
                    query = query.replace("{{" + key + "}}", f"'{value}'")

        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}

        # build query
        input_data = process_variables(query, data, parameters, self.instructions)
        if expected_output is None:
            expected_output = self.expected_output
        if expected_output is not None and isinstance(expected_output, type) and issubclass(expected_output, BaseModel):
            expected_output = expected_output.model_json_schema()
        expected_output = normalize_expected_output(expected_output)
        # Use instance output_format if none provided
        if output_format is None:
            output_format = self.output_format

        if isinstance(output_format, OutputFormat):
            output_format = output_format.value


        payload = {
            "id": self.id,
            "query": input_data,
            "sessionId": session_id,
            "history": history,
            "executionParams": {
                "maxTokens": (
                    parameters["max_tokens"]
                    if "max_tokens" in parameters
                    else max_tokens
                ),
                "maxIterations": (
                    parameters["max_iterations"]
                    if "max_iterations" in parameters
                    else max_iterations
                ),
                "outputFormat": output_format,
                "expectedOutput": expected_output,
            },
            "evolve": json.dumps(evolve_dict),
            "runResponseGeneration": run_response_generation,
        }
        payload.update(parameters)
        payload = json.dumps(payload)

        try:
            r = _request_with_retry("post", self.url, headers=headers, data=payload)
            resp = r.json()
            if trace_request:
                logging.info(f"Agent Run Async: Trace request id: {resp.get('requestId')}")
            poll_url = resp.get("data")
            return AgentResponse(
                status=ResponseStatus.IN_PROGRESS,
                url=poll_url,
                data=AgentResponseData(input=input_data),
                run_time=0.0,
                used_credits=0.0,
            )
        except Exception as e:
            msg = f"Error in request for {name} - {traceback.format_exc()}"
            logging.error(f"Agent Run Async: Error in running for {name}: {e}")
            return AgentResponse(
                status=ResponseStatus.FAILED,
                error=msg,
            )

    def to_dict(self) -> Dict:
        """Convert the Agent instance to a dictionary representation.

        Returns:
            Dict: Dictionary containing the agent's configuration and metadata.
        """
        from aixplain.factories.agent_factory.utils import build_tool_payload

        return {
            "id": self.id,
            "name": self.name,
            "assets": [build_tool_payload(tool) for tool in self.tools],
            "description": self.description,
            "instructions": self.instructions or self.description,
            "supplier": (
                self.supplier.value["code"]
                if isinstance(self.supplier, Supplier)
                else self.supplier
            ),
            "version": self.version,
            "llmId": self.llm_id if self.llm is None else self.llm.id,
            "status": self.status.value,
            "tasks": [task.to_dict() for task in self.workflow_tasks],
            "tools": (
                [
                    {
                        "type": "llm",
                        "description": "main",
                        "parameters": (
                            self.llm.get_parameters().to_list()
                            if self.llm.get_parameters()
                            else None
                        ),
                    }
                ]
                if self.llm is not None
                else []
            ),
            "cost": self.cost,
            "api_key": self.api_key,
            "outputFormat": self.output_format.value,
            "expectedOutput": self.expected_output,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Agent":
        """Create an Agent instance from a dictionary representation.

        Args:
            data: Dictionary containing Agent parameters

        Returns:
            Agent instance
        """
        from aixplain.factories.agent_factory.utils import build_tool
        from aixplain.enums import AssetStatus
        from aixplain.modules.agent import WorkflowTask

        # Extract tools from assets using proper tool building
        tools = []
        if "assets" in data:
            for asset_data in data["assets"]:
                try:
                    tool = build_tool(asset_data)
                    tools.append(tool)
                except Exception as e:
                    # Log warning but continue processing other tools
                    import logging

                    logging.warning(f"Failed to build tool from asset data: {e}")

        # Extract tasks using from_dict method
        workflow_tasks = []
        if "tasks" in data:
            for task_data in data["tasks"]:
                workflow_tasks.append(WorkflowTask.from_dict(task_data))

        # Extract LLM from tools section (main LLM info)
        llm = None
        if "tools" in data and data["tools"]:
            llm_tool = next(
                (tool for tool in data["tools"] if tool.get("type") == "llm"), None
            )
            if llm_tool and llm_tool.get("parameters"):
                # Reconstruct LLM from parameters if available
                from aixplain.factories.model_factory import ModelFactory

                try:
                    llm = ModelFactory.get(
                        data.get("llmId", "6646261c6eb563165658bbb1")
                    )
                    if llm_tool.get("parameters"):
                        # Apply stored parameters to LLM
                        llm.set_parameters(llm_tool["parameters"])
                except Exception:
                    # If LLM loading fails, llm remains None and llm_id will be used
                    pass

        # Extract status
        status = AssetStatus.DRAFT
        if "status" in data:
            if isinstance(data["status"], str):
                status = AssetStatus(data["status"])
            else:
                status = data["status"]

        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            instructions=data.get("instructions"),
            tools=tools,
            llm_id=data.get("llmId", "6646261c6eb563165658bbb1"),
            llm=llm,
            api_key=data.get("api_key"),
            supplier=data.get("supplier", "aiXplain"),
            version=data.get("version"),
            cost=data.get("cost"),
            status=status,
            workflow_tasks=workflow_tasks,
            output_format=OutputFormat(data.get("outputFormat", OutputFormat.TEXT)),
            expected_output=data.get("expectedOutput"),
        )

    def delete(self) -> None:
        """Delete this Agent from the aiXplain platform.

        This method attempts to delete the Agent. The operation will fail if the
        Agent is being used by any team agents.

        Raises:
            Exception: If deletion fails, with detailed error messages for different
                failure scenarios:
                - Agent is in use by accessible team agents (lists team agent IDs)
                - Agent is in use by inaccessible team agents
                - Other deletion errors (with HTTP status code)
        """
        try:
            url = urljoin(config.BACKEND_URL, f"sdk/agents/{self.id}")
            headers = {
                "x-api-key": config.TEAM_API_KEY,
                "Content-Type": "application/json",
            }
            logging.debug(f"Start service for DELETE Agent  - {url} - {headers}")
            r = _request_with_retry("delete", url, headers=headers)
            logging.debug(f"Result of request for DELETE Agent - {r.status_code}")
            if r.status_code != 200:
                raise Exception()
        except Exception:
            try:
                response_json = r.json()
                error_message = response_json.get("message", "").strip("{{}}")

                if r.status_code == 403 and error_message == "err.agent_is_in_use":
                    # Get team agents that use this agent
                    from aixplain.factories.team_agent_factory import TeamAgentFactory

                    team_agents = TeamAgentFactory.list()["results"]
                    using_team_agents = [
                        ta
                        for ta in team_agents
                        if any(agent.id == self.id for agent in ta.agents)
                    ]

                    if using_team_agents:
                        # Scenario 1: User has access to team agents
                        team_agent_ids = [ta.id for ta in using_team_agents]
                        message = (
                            "Error: Agent cannot be deleted.\n"
                            "Reason: This agent is currently used by one or more "
                            "team agents.\n\n"
                            f"team_agent_id: {', '.join(team_agent_ids)}. "
                            "To proceed, remove the agent from all team agents "
                            "before deletion."
                        )
                    else:
                        # Scenario 2: User doesn't have access to team agents
                        message = (
                            "Error: Agent cannot be deleted.\n"
                            "Reason: This agent is currently used by one or more "
                            "team agents.\n\n"
                            "One or more inaccessible team agents are "
                            "referencing it."
                        )
                else:
                    message = (
                        f"Agent Deletion Error (HTTP {r.status_code}): {error_message}."
                    )
            except ValueError:
                message = f"Agent Deletion Error (HTTP {r.status_code}): There was an error in deleting the agent."
            logging.error(message)
            raise Exception(message)

    def update(self) -> None:
        """Update the Agent's configuration on the aiXplain platform.

        This method validates and updates the Agent's configuration. It is deprecated
        in favor of the save() method.

        Raises:
            Exception: If validation fails or if there are errors during the update.
            DeprecationWarning: This method is deprecated, use save() instead.

        Note:
            This method is deprecated and will be removed in a future version.
            Please use save() instead.
        """
        import warnings
        import inspect

        # Get the current call stack
        stack = inspect.stack()
        if len(stack) > 2 and stack[1].function != "save":
            warnings.warn(
                "update() is deprecated and will be removed in a future version. Please use save() instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        from aixplain.factories.agent_factory.utils import build_agent

        self.validate(raise_exception=True)
        url = urljoin(config.BACKEND_URL, f"sdk/agents/{self.id}")
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}

        payload = self.to_dict()

        logging.debug(
            f"Start service for PUT Update Agent  - {url} - {headers} - {json.dumps(payload)}"
        )
        resp = "No specified error."
        try:
            r = _request_with_retry("put", url, headers=headers, json=payload)
            resp = r.json()
        except Exception:
            raise Exception("Agent Update Error: Please contact the administrators.")

        if 200 <= r.status_code < 300:
            return build_agent(resp)
        else:
            error_msg = f"Agent Update Error (HTTP {r.status_code}): {resp}"
            raise Exception(error_msg)

    def save(self) -> None:
        """Save the Agent's current configuration to the aiXplain platform.

        This method validates and saves any changes made to the Agent's configuration.
        It is the preferred method for updating an Agent's settings.

        Raises:
            Exception: If validation fails or if there are errors during the save operation.
        """
        self.update()

    def __repr__(self) -> str:
        """Return a string representation of the Agent.

        Returns:
            str: A string in the format "Agent: <name> (id=<id>)".
        """
        return f"Agent: {self.name} (id={self.id})"

    def evolve_async(
        self,
        evolve_type: Union[EvolveType, str] = EvolveType.TEAM_TUNING,
        max_successful_generations: int = 3,
        max_failed_generation_retries: int = 3,
        max_iterations: int = 50,
        max_non_improving_generations: Optional[int] = 2,
        llm: Optional[Union[Text, LLM]] = None,
    ) -> AgentResponse:
        """Asynchronously evolve the Agent and return a polling URL in the AgentResponse.

        Args:
            evolve_type (Union[EvolveType, str]): Type of evolution (TEAM_TUNING or INSTRUCTION_TUNING). Defaults to TEAM_TUNING.
            max_successful_generations (int): Maximum number of successful generations to evolve. Defaults to 3.
            max_failed_generation_retries (int): Maximum retry attempts for failed generations. Defaults to 3.
            max_iterations (int): Maximum number of iterations. Defaults to 50.
            max_non_improving_generations (Optional[int]): Stop condition parameter for non-improving generations. Defaults to 2, can be None.
            llm (Optional[Union[Text, LLM]]): LLM to use for evolution. Can be an LLM ID string or LLM object. Defaults to None.

        Returns:
            AgentResponse: Response containing polling URL and status.
        """
        from aixplain.utils.evolve_utils import create_llm_dict

        query = "<placeholder query>"

        # Create EvolveParam from individual parameters
        evolve_parameters = EvolveParam(
            to_evolve=True,
            evolve_type=evolve_type,
            max_successful_generations=max_successful_generations,
            max_failed_generation_retries=max_failed_generation_retries,
            max_iterations=max_iterations,
            max_non_improving_generations=max_non_improving_generations,
            llm=create_llm_dict(llm),
        )

        return self.run_async(query=query, evolve=evolve_parameters)

    def evolve(
        self,
        evolve_type: Union[EvolveType, str] = EvolveType.TEAM_TUNING,
        max_successful_generations: int = 3,
        max_failed_generation_retries: int = 3,
        max_iterations: int = 50,
        max_non_improving_generations: Optional[int] = 2,
        llm: Optional[Union[Text, LLM]] = None,
    ) -> AgentResponse:
        """Synchronously evolve the Agent and poll for the result.

        Args:
            evolve_type (Union[EvolveType, str]): Type of evolution (TEAM_TUNING or INSTRUCTION_TUNING). Defaults to TEAM_TUNING.
            max_successful_generations (int): Maximum number of successful generations to evolve. Defaults to 3.
            max_failed_generation_retries (int): Maximum retry attempts for failed generations. Defaults to 3.
            max_iterations (int): Maximum number of iterations. Defaults to 50.
            max_non_improving_generations (Optional[int]): Stop condition parameter for non-improving generations. Defaults to 2, can be None.
            llm (Optional[Union[Text, LLM]]): LLM to use for evolution. Can be an LLM ID string or LLM object. Defaults to None.

        Returns:
            AgentResponse: Final response from the evolution process.
        """
        from aixplain.utils.evolve_utils import create_llm_dict
        from aixplain.factories.team_agent_factory.utils import (
            build_team_agent_from_yaml,
        )

        # Create EvolveParam from individual parameters
        evolve_parameters = EvolveParam(
            to_evolve=True,
            evolve_type=evolve_type,
            max_successful_generations=max_successful_generations,
            max_failed_generation_retries=max_failed_generation_retries,
            max_iterations=max_iterations,
            max_non_improving_generations=max_non_improving_generations,
            llm=create_llm_dict(llm),
        )

        start = time.time()
        try:
            logging.info(f"Evolve started with parameters: {evolve_parameters}")
            logging.info("It might take a while...")
            response = self.evolve_async(
                evolve_type=evolve_type,
                max_successful_generations=max_successful_generations,
                max_failed_generation_retries=max_failed_generation_retries,
                max_iterations=max_iterations,
                max_non_improving_generations=max_non_improving_generations,
                llm=llm,
            )
            if response["status"] == ResponseStatus.FAILED:
                end = time.time()
                response["elapsed_time"] = end - start
                return response
            poll_url = response["url"]
            end = time.time()
            result = self.sync_poll(poll_url, name="evolve_process", timeout=600)
            result_data = result.data

            if (
                "current_code" in result_data
                and result_data["current_code"] is not None
            ):
                if evolve_parameters.evolve_type == EvolveType.TEAM_TUNING:
                    result_data["evolved_agent"] = build_team_agent_from_yaml(
                        result_data["current_code"],
                        self.llm_id,
                        self.api_key,
                        self.id,
                    )
                elif evolve_parameters.evolve_type == EvolveType.INSTRUCTION_TUNING:
                    self.instructions = result_data["current_code"]
                    self.update()
                    result_data["evolved_agent"] = self
                else:
                    raise ValueError(
                        "evolve_parameters.evolve_type must be one of the following: TEAM_TUNING, INSTRUCTION_TUNING"
                    )
            return AgentResponse(
                status=ResponseStatus.SUCCESS,
                completed=True,
                data=result_data,
                used_credits=getattr(result, "used_credits", 0.0),
                run_time=getattr(result, "run_time", end - start),
            )
        except Exception as e:
            logging.error(f"Agent Evolve: Error in evolving: {e}")
            end = time.time()
            return AgentResponse(
                status=ResponseStatus.FAILED,
                completed=False,
                error_message="No response from the service.",
            )
