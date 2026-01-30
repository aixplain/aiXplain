"""Team Agent module for aiXplain SDK.

This module provides the TeamAgent class and related functionality for creating and managing
multi-agent teams that can collaborate on complex tasks.

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
Date: August 15th 2024
Description:
    Team Agent Class
"""

__author__ = "aiXplain"

import json
import logging
import time
import traceback
import re
import warnings
from enum import Enum
from typing import Dict, List, Text, Optional, Union, Any
from urllib.parse import urljoin
from datetime import datetime

from aixplain.enums import ResponseStatus
from aixplain.enums.function import Function
from aixplain.enums.supplier import Supplier
from aixplain.enums.asset_status import AssetStatus
from aixplain.enums.storage_type import StorageType
from aixplain.enums.evolve_type import EvolveType
from aixplain.modules.model import Model
from aixplain.modules.agent import Agent, OutputFormat
from aixplain.modules.agent.agent_response import AgentResponse
from aixplain.modules.agent.agent_response_data import AgentResponseData
from aixplain.modules.agent.evolve_param import EvolveParam, validate_evolve_param
from aixplain.modules.agent.utils import process_variables, validate_history
from aixplain.modules.team_agent.evolver_response_data import EvolverResponseData
from aixplain.utils.convert_datatype_utils import normalize_expected_output
from aixplain.utils import config
from aixplain.utils.request_utils import _request_with_retry
from aixplain.modules.model.llm_model import LLM
from aixplain.modules.mixins import DeployableMixin
from pydantic import BaseModel


class InspectorTarget(str, Enum):
    """Target stages for inspector validation in the team agent pipeline.

    This enumeration defines the stages where inspectors can be applied to
    validate and ensure quality of the team agent's operation.

    Attributes:
        INPUT: Validates the input data before processing.
        STEPS: Validates intermediate steps during processing.
        OUTPUT: Validates the final output before returning.
    """

    INPUT = "input"
    STEPS = "steps"
    OUTPUT = "output"

    def __str__(self):
        """Return the string value of the enum member.

        Returns:
            str: The string value associated with the enum member.
        """
        return self._value_

class TeamAgent(Model, DeployableMixin[Agent]):
    """Advanced AI system capable of using multiple agents to perform a variety of tasks.

    Attributes:
        id (Text): ID of the Team Agent
        name (Text): Name of the Team Agent
        agents (List[Agent]): List of agents that the Team Agent uses.
        description (Text, optional): description of the Team Agent. Defaults to "".
        llm (Optional[LLM]): Main LLM instance for the team agent.
        supervisor_llm (Optional[LLM]): Supervisor LLM instance for the team agent.
        api_key (str): The TEAM API key used for authentication.
        supplier (Text): Supplier of the Team Agent.
        version (Text): Version of the Team Agent.
        cost (Dict, optional): model price. Defaults to None.
        status (AssetStatus): Status of the Team Agent. Defaults to DRAFT.
        instructions (Optional[Text]): Instructions to guide the team agent.
        output_format (OutputFormat): Response format. Defaults to TEXT.
        expected_output (Optional[Union[BaseModel, Text, dict]]): Expected output format.

    Deprecated Attributes:
        llm_id (Text): DEPRECATED. Use 'llm' parameter instead. Large language model ID.
        mentalist_llm (Optional[LLM]): DEPRECATED. LLM for planning.
        use_mentalist (bool): DEPRECATED. Whether to use Mentalist agent for pre-planning.
    """

    is_valid: bool

    def __init__(
        self,
        id: Text,
        name: Text,
        agents: List[Agent] = [],
        description: Text = "",
        llm: Optional[LLM] = None,
        supervisor_llm: Optional[LLM] = None,
        api_key: Optional[Text] = config.TEAM_API_KEY,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        version: Optional[Text] = None,
        cost: Optional[Dict] = None,
        status: AssetStatus = AssetStatus.DRAFT,
        instructions: Optional[Text] = None,
        output_format: OutputFormat = OutputFormat.TEXT,
        expected_output: Optional[Union[BaseModel, Text, dict]] = None,
        **additional_info,
    ) -> None:
        """Initialize a TeamAgent instance.

        Args:
            id (Text): Unique identifier for the team agent.
            name (Text): Name of the team agent.
            agents (List[Agent], optional): List of agents in the team. Defaults to [].
            description (Text, optional): Description of the team agent. Defaults to "".
            llm (Optional[LLM], optional): LLM instance. Defaults to None.
            supervisor_llm (Optional[LLM], optional): Supervisor LLM instance. Defaults to None.
            api_key (Optional[Text], optional): API key. Defaults to config.TEAM_API_KEY.
            supplier (Union[Dict, Text, Supplier, int], optional): Supplier. Defaults to "aiXplain".
            version (Optional[Text], optional): Version. Defaults to None.
            cost (Optional[Dict], optional): Cost information. Defaults to None.
            status (AssetStatus, optional): Status of the team agent. Defaults to AssetStatus.DRAFT.
            instructions (Optional[Text], optional): Instructions for the team agent. Defaults to None.
            output_format (OutputFormat, optional): Output format. Defaults to OutputFormat.TEXT.
            expected_output (Optional[Union[BaseModel, Text, dict]], optional): Expected output format. Defaults to None.
            **additional_info: Additional keyword arguments.

        Deprecated Args:
            llm_id (Text, optional): DEPRECATED. Use 'llm' parameter instead. ID of the language model. Defaults to "6646261c6eb563165658bbb1".
            mentalist_llm (Optional[LLM], optional): DEPRECATED. Mentalist/Planner LLM instance. Defaults to None.
            use_mentalist (bool, optional): DEPRECATED. Whether to use mentalist/planner. Defaults to True.
        """
        # Define supported kwargs
        supported_kwargs = {"llm_id", "mentalist_llm", "use_mentalist"}

        # Validate kwargs - raise error if unsupported kwargs are provided
        unsupported_kwargs = set(additional_info.keys()) - supported_kwargs
        if unsupported_kwargs:
            raise ValueError(
                f"Unsupported keyword argument(s): {', '.join(sorted(unsupported_kwargs))}. "
                f"Supported kwargs are: {', '.join(sorted(supported_kwargs))}."
            )
        # Handle deprecated parameters from kwargs
        if "llm_id" in additional_info:
            llm_id = additional_info.pop("llm_id")
            warnings.warn(
                "Parameter 'llm_id' is deprecated and will be removed in a future version. "
                "Please use 'llm' parameter instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        else:
            llm_id = "6646261c6eb563165658bbb1"

        if "mentalist_llm" in additional_info:
            mentalist_llm = additional_info.pop("mentalist_llm")
            warnings.warn(
                "Parameter 'mentalist_llm' is deprecated and will be removed in a future version.",
                DeprecationWarning,
                stacklevel=2,
            )
        else:
            mentalist_llm = None

        if "use_mentalist" in additional_info:
            use_mentalist = additional_info.pop("use_mentalist")
            warnings.warn(
                "Parameter 'use_mentalist' is deprecated and will be removed in a future version.",
                DeprecationWarning,
                stacklevel=2,
            )
        else:
            use_mentalist = True

        """Initialize a TeamAgent instance.

        Args:
            id (Text): Unique identifier for the team agent.
            name (Text): Name of the team agent.
            agents (List[Agent], optional): List of agents in the team. Defaults to [].
            description (Text, optional): Description of the team agent. Defaults to "".
            llm (Optional[LLM], optional): LLM instance. Defaults to None.
            supervisor_llm (Optional[LLM], optional): Supervisor LLM instance. Defaults to None.
            api_key (Optional[Text], optional): API key. Defaults to config.TEAM_API_KEY.
            supplier (Union[Dict, Text, Supplier, int], optional): Supplier. Defaults to "aiXplain".
            version (Optional[Text], optional): Version. Defaults to None.
            cost (Optional[Dict], optional): Cost information. Defaults to None.
            status (AssetStatus, optional): Status of the team agent. Defaults to AssetStatus.DRAFT.
            instructions (Optional[Text], optional): Instructions for the team agent. Defaults to None.
            output_format (OutputFormat, optional): Output format. Defaults to OutputFormat.TEXT.
            expected_output (Optional[Union[BaseModel, Text, dict]], optional): Expected output format. Defaults to None.
            **additional_info: Additional keyword arguments.

        Deprecated Args:
            llm_id (Text, optional): DEPRECATED. Use 'llm' parameter instead. ID of the language model. Defaults to "6646261c6eb563165658bbb1".
            mentalist_llm (Optional[LLM], optional): DEPRECATED. Mentalist/Planner LLM instance. Defaults to None.
            use_mentalist (bool, optional): DEPRECATED. Whether to use mentalist/planner. Defaults to True.
        """
        super().__init__(id, name, description, api_key, supplier, version, cost=cost)
        self.additional_info = additional_info
        self.agents = agents
        self.llm_id = llm_id
        self.llm = llm
        self.api_key = api_key
        self.use_mentalist = use_mentalist
        self.use_inspector = False
        self.supervisor_llm = supervisor_llm
        self.mentalist_llm = mentalist_llm
        self.instructions = instructions
        if isinstance(status, str):
            try:
                status = AssetStatus(status)
            except Exception:
                status = AssetStatus.DRAFT
        self.status = status
        self.is_valid = True
        self.output_format = output_format
        self.expected_output = expected_output

    def generate_session_id(self, history: list = None) -> str:
        """Generate a new session ID for the team agent.

        Args:
            history (list, optional): Chat history to initialize the session with. Defaults to None.

        Returns:
            str: The generated session ID in format "{team_agent_id}_{timestamp}".
        """
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
                    "maxIterations": 30,
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
                logging.error(f"Team session init failed for {session_id}: {result}")
                return session_id
        except Exception as e:
            logging.error(f"Failed to initialize team session {session_id}: {e}")
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

    def _format_team_progress(
        self,
        progress: Dict,
        verbosity: Optional[str] = "full",
    ) -> Optional[str]:
        """Format team agent progress message based on verbosity level.

        Args:
            progress (Dict): Progress data from polling response
            verbosity (Optional[str]): "full", "compact", or None (disables output)

        Returns:
            Optional[str]: Formatted message or None
        """
        if verbosity is None:
            return None

        stage = progress.get("stage", "working")
        agent_name = progress.get("agent")
        tool = progress.get("tool")
        message = progress.get("message", "")
        runtime = progress.get("runtime")
        success = progress.get("success")
        current_step = progress.get("current_step", 0)
        total_steps = progress.get("total_steps", 0)
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

        # Capitalize system agent names for better display
        if agent_name:
            system_agents = {
                "orchestrator": "Orchestrator",
                "mentalist": "Mentalist",
                "response_generator": "Response Generator",
            }
            display_agent_name = system_agents.get(agent_name.lower(), agent_name)
        else:
            display_agent_name = None

        # Determine emoji and context
        if stage in ["planning", "mentalist"]:
            emoji = "🤖"
            context = "Mentalist"
        elif display_agent_name and tool:
            emoji = "⚙️"
            context = f"{display_agent_name} | {tool}"
        elif display_agent_name:
            emoji = "🤖"
            context = display_agent_name
        else:
            emoji = "🤖"
            context = self.name

        if verbosity == "compact":
            # Compact mode: minimal info
            msg = f"{emoji}  {context} | {status_icon}"

            if current_step and total_steps:
                msg += f" [{current_step}/{total_steps}]"

            # Show message if available (common for planning/orchestration stages)
            if message and not tool_output:
                msg += f" {message[:100]}"
            elif success is True and tool_output:
                output_str = str(tool_output)[:200]
                msg += f" {output_str}"
                msg += "..." if len(output_str) > 200 else ""
        else:
            # Full verbosity: detailed info
            msg = f"{emoji}  {context} | {status_icon}"

            if current_step and total_steps:
                msg += f" | Step {current_step}/{total_steps}"

            if tool_input:
                msg += f" | Input: {tool_input}"

            if tool_output:
                msg += f" | Output: {tool_output}"

            if reason:
                msg += f" | Reason: {reason}"
            elif message:
                # Show message if reason is not available (common for planning/orchestration)
                msg += f" | {message}"

        return msg

    def _format_completion_message(
        self,
        elapsed_time: float,
        response_body: AgentResponse,
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
                data_dict = (
                    response_body.data[0]
                    if isinstance(response_body.data[0], dict)
                    else None
                )
            elif isinstance(response_body.data, dict):
                # Data is already a dict
                data_dict = response_body.data
            elif hasattr(response_body.data, "executionStats") or hasattr(
                response_body.data, "execution_stats"
            ):
                # Data is an object with attributes
                exec_stats = getattr(
                    response_body.data, "executionStats", None
                ) or getattr(response_body.data, "execution_stats", None)
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
    ) -> AgentResponse:
        """Poll the platform until team agent execution completes or times out.

        Args:
            poll_url (Text): URL to poll for operation status.
            name (Text, optional): Identifier for the operation. Defaults to "model_process".
            wait_time (float, optional): Initial wait time in seconds between polls. Defaults to 0.5.
            timeout (float, optional): Maximum total time to poll in seconds. Defaults to 300.
            progress_verbosity (Optional[str], optional): Progress display mode - "full" (detailed), "compact" (brief), or None (no progress). Defaults to "compact".

        Returns:
            AgentResponse: The final response from the team agent execution.
        """
        logging.info(f"Polling for Team Agent: Start polling for {name}")
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
                        msg = self._format_team_progress(progress, progress_verbosity)
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
                logging.error(f"Polling for Team Agent: polling for {name}: {e}")
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
            logging.debug(
                f"Polling for Team Agent: Final status of polling for {name}: {response_body}"
            )
        else:
            response_body = AgentResponse(
                status=ResponseStatus.FAILED,
                completed=False,
                error_message="No response from the service.",
            )
            logging.error(
                f"Polling for Team Agent: Final status of polling for {name}: No response in {timeout} seconds"
            )

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
        max_tokens: int = 2048,
        max_iterations: int = 30,
        trace_request: bool = False,
        progress_verbosity: Optional[str] = "compact",
        **kwargs,
    ) -> AgentResponse:
        """Runs a team agent call.

        Args:
            data (Optional[Union[Dict, Text]], optional): data to be processed by the team agent. Defaults to None.
            query (Optional[Text], optional): query to be processed by the team agent. Defaults to None.
            session_id (Optional[Text], optional): conversation Session ID. Defaults to None.
            history (Optional[List[Dict]], optional): chat history (in case session ID is None). Defaults to None.
            name (Text, optional): ID given to a call. Defaults to "model_process".
            timeout (float, optional): total polling time. Defaults to 300.
            parameters (Dict, optional): optional parameters to the model. Defaults to "{}".
            wait_time (float, optional): wait time in seconds between polling calls. Defaults to 0.5.
            content (Union[Dict[Text, Text], List[Text]], optional): Content inputs to be processed according to the query. Defaults to None.
            max_tokens (int, optional): maximum number of tokens which can be generated by the agents. Defaults to 2048.
            max_iterations (int, optional): maximum number of iterations between the agents. Defaults to 30.
            trace_request (bool, optional): return the request id for tracing the request. Defaults to False.
            progress_verbosity (Optional[str], optional): Progress display mode - "full" (detailed), "compact" (brief), or None (no progress). Defaults to "compact".
            **kwargs: Additional deprecated keyword arguments (output_format, expected_output).

        Returns:
            AgentResponse: parsed output from model
        """
        # Handle deprecated parameters from kwargs
        output_format = kwargs.pop("output_format", None)
        if output_format is not None:
            warnings.warn(
                "Parameter 'output_format' in run() is deprecated and will be removed in a future version. "
                "Please set 'output_format' during TeamAgent initialization instead.",
                DeprecationWarning,
                stacklevel=2,
            )

        expected_output = kwargs.pop("expected_output", None)
        if expected_output is not None:
            warnings.warn(
                "Parameter 'expected_output' in run() is deprecated and will be removed in a future version. "
                "Please set 'expected_output' during TeamAgent initialization instead.",
                DeprecationWarning,
                stacklevel=2,
            )

        start = time.time()
        result_data = {}
        if session_id is not None and history is not None:
            raise ValueError("Provide either `session_id` or `history`, not both.")

        if session_id is not None:
            if not session_id.startswith(f"{self.id}_"):
                raise ValueError(
                    f"Session ID '{session_id}' does not belong to this Agent."
                )
        if history:
            validate_history(history)
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
            )
            if response["status"] == ResponseStatus.FAILED:
                end = time.time()
                response["elapsed_time"] = end - start
                return response
            poll_url = response["url"]
            end = time.time()
            result = self.sync_poll(poll_url, name=name, timeout=timeout, wait_time=wait_time)
            result_data = result.data or {}
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
                        critiques=result_data.get("critiques", ""),
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
                    critiques=result_data.get("critiques", ""),
                ),
                used_credits=result_data.get("usedCredits", 0.0),
                run_time=result_data.get("runTime", end - start),
            )
        except Exception as e:
            logging.error(f"Team Agent Run: Error in running for {name}: {e}")
            end = time.time()
            return AgentResponse(
                status=ResponseStatus.FAILED,
                completed=False,
                error_message="No response from the service.",
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
        max_iterations: int = 30,
        output_format: Optional[OutputFormat] = None,
        expected_output: Optional[Union[BaseModel, Text, dict]] = None,
        evolve: Union[Dict[str, Any], EvolveParam, None] = None,
        trace_request: bool = False,
    ) -> AgentResponse:
        """Runs asynchronously a Team Agent call.

        Args:
            data (Optional[Union[Dict, Text]], optional): data to be processed by the Team Agent. Defaults to None.
            query (Optional[Text], optional): query to be processed by the Team Agent. Defaults to None.
            session_id (Optional[Text], optional): conversation Session ID. Defaults to None.
            history (Optional[List[Dict]], optional): chat history (in case session ID is None). Defaults to None.
            name (Text, optional): ID given to a call. Defaults to "model_process".
            parameters (Dict, optional): optional parameters to the model. Defaults to "{}".
            content (Union[Dict[Text, Text], List[Text]], optional): Content inputs to be processed according to the query. Defaults to None.
            max_tokens (int, optional): maximum number of tokens which can be generated by the agents. Defaults to 2048.
            max_iterations (int, optional): maximum number of iterations between the agents. Defaults to 30.
            output_format (OutputFormat, optional): response format. If not provided, uses the format set during initialization.
            expected_output (Union[BaseModel, Text, dict], optional): expected output. Defaults to None.
            evolve (Union[Dict[str, Any], EvolveParam, None], optional): evolve the team agent configuration. Can be a dictionary, EvolveParam instance, or None.
            trace_request (bool, optional): return the request id for tracing the request. Defaults to False.

        Returns:
            AgentResponse: polling URL in response
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

        if not self.is_valid:
            raise Exception(
                "Team Agent is not valid. Please validate the team agent before running."
            )

        assert (
            data is not None or query is not None
        ), "Either 'data' or 'query' must be provided."
        if data is not None:
            if isinstance(data, dict):
                assert (
                    "query" in data and data["query"] is not None
                ), "When providing a dictionary, 'query' must be provided."
                if session_id is None:
                    session_id = data.pop("session_id", None)
                if history is None:
                    history = data.pop("history", None)
                if content is None:
                    content = data.pop("content", None)
                query = data.get("query", data)
            else:
                query = data

        # process content inputs
        if content is not None:
            assert (
                isinstance(query, str)
                and FileFactory.check_storage_type(query) == StorageType.TEXT
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
        if expected_output is None:
            expected_output = self.expected_output
        input_data = process_variables(query, data, parameters, self.description)
        expected_output = normalize_expected_output(expected_output)
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
        }
        payload.update(parameters)
        payload = json.dumps(payload)

        r = _request_with_retry("post", self.url, headers=headers, data=payload)
        logging.info(
            f"Team Agent Run Async: Start service for {name} - {self.url} - {payload} - {headers}"
        )

        resp = None
        try:
            resp = r.json()
            logging.info(f"Result of request for {name} - {r.status_code} - {resp}")
            if trace_request:
                logging.info(
                    f"Team Agent Run Async: Trace request id: {resp.get('requestId')}"
                )
            poll_url = resp["data"]
            response = AgentResponse(
                status=ResponseStatus.IN_PROGRESS,
                url=poll_url,
                data=AgentResponseData(input=input_data),
                run_time=0.0,
                used_credits=0.0,
            )
        except Exception:
            msg = f"Error in request for {name} - {traceback.format_exc()}"
            logging.error(f"Team Agent Run Async: Error in running for {name}: {resp}")
            if resp is not None:
                response = AgentResponse(
                    status=ResponseStatus.FAILED,
                    error=msg,
                )
        return response

    def poll(self, poll_url: Text, name: Text = "model_process") -> AgentResponse:
        """Poll once for team agent execution status.

        Args:
            poll_url (Text): URL to poll for status.
            name (Text, optional): Identifier for the operation. Defaults to "model_process".

        Returns:
            AgentResponse: Response containing status, data, and progress information.
        """
        used_credits, run_time = 0.0, 0.0
        resp, error_message, status = None, None, ResponseStatus.SUCCESS
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        r = _request_with_retry("get", poll_url, headers=headers)
        try:
            resp = r.json()
            if resp["completed"] is True:
                status = ResponseStatus(resp.get("status", "FAILED"))
                if "error_message" in resp or "supplierError" in resp:
                    status = ResponseStatus.FAILED
                    error_message = resp.get("error_message")
            else:
                status = ResponseStatus.IN_PROGRESS
            logging.debug(
                f"Single Poll for Team Agent: Status of polling for {name}: {resp}"
            )

            resp_data = resp.get("data") or {}
            used_credits = resp_data.get("usedCredits", 0.0)
            run_time = resp_data.get("runTime", 0.0)
            evolve_type = resp_data.get("evolve_type", EvolveType.TEAM_TUNING.value)
            if "evolved_agent" in resp_data and status == ResponseStatus.SUCCESS:
                if evolve_type == EvolveType.INSTRUCTION_TUNING.value:
                    # return this class as it is but replace its description and instructions
                    evolved_agent = self
                    current_code = resp_data.get("current_code", "")
                    evolved_agent.description = current_code
                    evolved_agent.update()
                    resp_data["evolved_agent"] = evolved_agent
                else:
                    resp_data = EvolverResponseData.from_dict(
                        resp_data, llm_id=self.llm_id, api_key=self.api_key
                    )
            else:
                resp_data = AgentResponseData(
                    input=resp_data.get("input"),
                    output=resp_data.get("output"),
                    session_id=resp_data.get("session_id"),
                    intermediate_steps=resp_data.get("intermediate_steps"),
                    steps=resp_data.get("steps"),
                    execution_stats=resp_data.get("executionStats"),
                )
        except Exception as e:
            import traceback

            logging.error(
                f"Single Poll for Team Agent: Error of polling for {name}: {e}, traceback: {traceback.format_exc()}"
            )
            status = ResponseStatus.FAILED
            error_message = str(e)
        finally:
            # Normalize progress data from camelCase to snake_case
            progress_data = resp.get("progress") if resp else None
            if progress_data:
                progress_data = self._normalize_progress_data(progress_data)

            response = AgentResponse(
                status=status,
                data=resp_data,
                details=resp.get("details", {}),
                completed=resp.get("completed", False),
                used_credits=used_credits,
                run_time=run_time,
                usage=resp.get("usage", None),
                error_message=error_message,
                progress=progress_data,
            )
        return response

    def delete(self) -> None:
        """Deletes Team Agent."""
        try:
            url = urljoin(config.BACKEND_URL, f"sdk/agent-communities/{self.id}")
            headers = {
                "x-api-key": config.TEAM_API_KEY,
                "Content-Type": "application/json",
            }
            logging.debug(f"Start service for DELETE Team Agent  - {url} - {headers}")
            r = _request_with_retry("delete", url, headers=headers)
            if r.status_code != 200:
                raise Exception()
        except Exception:
            message = f"Team Agent Deletion Error (HTTP {r.status_code}): Make sure the Team Agent exists and you are the owner."
            logging.error(message)
            raise Exception(f"{message}")

    def _serialize_agent(self, agent, idx: int) -> Dict:
        """Serialize an agent for the to_dict method.

        This internal method converts an agent object into a dictionary format
        suitable for serialization, including its base properties and any
        additional data from the agent's own to_dict method.

        Args:
            agent: The agent object to serialize.
            idx (int): The index position of the agent in the team.

        Returns:
            Dict: A dictionary containing the serialized agent data with:
                - assetId: The agent's ID
                - number: The agent's index position
                - type: Always "AGENT"
                - label: Always "AGENT"
                - Additional fields from agent.to_dict() if available
        """
        base_dict = {
            "assetId": agent.id,
            "number": idx,
            "type": "AGENT",
            "label": "AGENT",
        }

        # Try to get additional data from agent's to_dict method
        try:
            if hasattr(agent, "to_dict") and callable(getattr(agent, "to_dict")):
                agent_dict = agent.to_dict()
                # Ensure it's actually a dictionary and not a Mock or other object
                if isinstance(agent_dict, dict) and hasattr(agent_dict, "items"):
                    try:
                        # Add all fields except 'id' to avoid duplication with 'assetId'
                        additional_data = {
                            k: v for k, v in agent_dict.items() if k not in ["id"]
                        }
                        base_dict.update(additional_data)
                    except (TypeError, AttributeError):
                        # If items() doesn't work or iteration fails, skip the additional data
                        pass
        except Exception:
            # If anything goes wrong, just use the base dictionary
            pass

        return base_dict

    def to_dict(self) -> Dict:
        """Convert the TeamAgent instance to a dictionary representation.

        This method serializes the TeamAgent and all its components (agents, LLMs, etc.) into a dictionary format suitable for storage
        or transmission.

        Returns:
            Dict: A dictionary containing:
                - id (str): The team agent's ID
                - name (str): The team agent's name
                - agents (List[Dict]): Serialized list of agents
                - links (List): Empty list (reserved for future use)
                - description (str): The team agent's description
                - llmId (str): ID of the main language model
                - supervisorId (str): ID of the supervisor language model
                - plannerId (str): ID of the planner model (if use_mentalist)
                - supplier (str): The supplier code
                - version (str): The version number
                - status (str): The current status
                - instructions (str): The team agent's instructions
        """
        if self.use_mentalist:
            planner_id = self.mentalist_llm.id if self.mentalist_llm else self.llm_id
        else:
            planner_id = None
        return {
            "id": self.id,
            "name": self.name,
            "agents": [
                self._serialize_agent(agent, idx)
                for idx, agent in enumerate(self.agents)
            ],
            "links": [],
            "description": self.description,
            "llmId": self.llm.id if self.llm else self.llm_id,
            "supervisorId": (
                self.supervisor_llm.id if self.supervisor_llm else self.llm_id
            ),
            "plannerId": planner_id,
            "supplier": (
                self.supplier.value["code"]
                if isinstance(self.supplier, Supplier)
                else self.supplier
            ),
            "version": self.version,
            "status": self.status.value,
            "instructions": self.instructions,
            "outputFormat": self.output_format.value,
            "expectedOutput": self.expected_output,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "TeamAgent":
        """Create a TeamAgent instance from a dictionary representation.

        Args:
            data: Dictionary containing TeamAgent parameters

        Returns:
            TeamAgent instance
        """
        from aixplain.factories.model_factory import ModelFactory
        from aixplain.enums import AssetStatus
        from aixplain.modules.agent import Agent

        # Extract agents from agents list using proper agent loading
        agents = []
        if "agents" in data:
            for agent_data in data["agents"]:
                if "assetId" in agent_data:
                    try:
                        # Load agent using AgentFactory
                        agent = Agent.from_dict(agent_data)
                        agents.append(agent)
                    except Exception as e:
                        # Log warning but continue processing other agents
                        import logging

                        logging.warning(
                            f"Failed to load agent {agent_data['assetId']}: {e}"
                        )
                else:
                    agents.append(Agent.from_dict(agent_data))
        # Extract status
        status = AssetStatus.DRAFT
        if "status" in data:
            if isinstance(data["status"], str):
                status = AssetStatus(data["status"])
            else:
                status = data["status"]

        # Extract LLM instances using proper model loading
        llm = None
        supervisor_llm = None
        mentalist_llm = None

        try:
            if "llmId" in data:
                llm = ModelFactory.get(data["llmId"])
        except Exception:
            pass  # llm remains None, will use llm_id

        try:
            if "supervisorId" in data and data["supervisorId"] != data.get("llmId"):
                supervisor_llm = ModelFactory.get(data["supervisorId"])
        except Exception:
            pass  # supervisor_llm remains None

        try:
            if "plannerId" in data and data["plannerId"]:
                mentalist_llm = ModelFactory.get(data["plannerId"])
        except Exception:
            pass  # mentalist_llm remains None

        # Determine if mentalist is used
        use_mentalist = data.get("plannerId") is not None

        return cls(
            id=data["id"],
            name=data["name"],
            agents=agents,
            description=data.get("description", ""),
            llm=llm,
            supervisor_llm=supervisor_llm,
            supplier=data.get("supplier", "aiXplain"),
            version=data.get("version"),
            status=status,
            instructions=data.get("instructions"),
            output_format=OutputFormat(data.get("outputFormat", OutputFormat.TEXT)),
            expected_output=data.get("expectedOutput"),
            # Pass deprecated params via kwargs
            llm_id=data.get("llmId", "6646261c6eb563165658bbb1"),
            mentalist_llm=mentalist_llm,
            use_mentalist=use_mentalist,
        )

    def _validate(self) -> None:
        from aixplain.utils.llm_utils import get_llm_instance

        """Validate the Team."""

        # validate name
        assert (
            re.match(r"^[a-zA-Z0-9 \-\(\)]*$", self.name) is not None
        ), "Team Agent Creation Error: Team name contains invalid characters. Only alphanumeric characters, spaces, hyphens, and brackets are allowed."

        try:
            llm = get_llm_instance(self.llm_id, use_cache=True)
            assert (
                llm.function == Function.TEXT_GENERATION
            ), "Large Language Model must be a text generation model."
        except Exception:
            raise Exception(f"Large Language Model with ID '{self.llm_id}' not found.")

        for agent in self.agents:
            agent.validate(raise_exception=True)

    def validate(self, raise_exception: bool = False) -> bool:
        """Validate the TeamAgent configuration.

        This method checks the validity of the TeamAgent's configuration,
        including name format, LLM compatibility, and agent validity.

        Args:
            raise_exception (bool, optional): If True, raises exceptions for
                validation failures. If False, logs warnings. Defaults to False.

        Returns:
            bool: True if validation succeeds, False otherwise.

        Raises:
            Exception: If raise_exception is True and validation fails, with
                details about the specific validation error.

        Note:
            - The team agent cannot be run until all validation issues are fixed
            - Name must contain only alphanumeric chars, spaces, hyphens, brackets
            - LLM must be a text generation model
            - All agents must pass their own validation
        """
        try:
            self._validate()
            self.is_valid = True
        except Exception as e:
            self.is_valid = False
            if raise_exception:
                raise e
            else:
                logging.warning(f"Team Agent Validation Error: {e}")
                logging.warning(
                    "You won't be able to run the Team Agent until the issues are handled manually."
                )

        return self.is_valid

    def update(self) -> None:
        """Update the TeamAgent in the backend.

        This method validates and updates the TeamAgent's configuration in the
        backend system. It is deprecated in favor of the save() method.

        Raises:
            Exception: If validation fails or if the update request fails.
                Specific error messages will indicate:
                - Validation failures with details
                - HTTP errors with status codes
                - General update errors requiring admin attention

        Note:
            - This method is deprecated, use save() instead
            - Performs validation before attempting update
            - Requires valid team API key for authentication
            - Returns a new TeamAgent instance if successful
        """
        import warnings
        import inspect

        # Get the current call stack
        stack = inspect.stack()
        if len(stack) > 2 and stack[1].function != "save":
            warnings.warn(
                "update() is deprecated and will be removed in a future version. "
                "Please use save() instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        from aixplain.factories.team_agent_factory.utils import build_team_agent

        self.validate(raise_exception=True)
        url = urljoin(config.BACKEND_URL, f"sdk/agent-communities/{self.id}")
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}

        payload = self.to_dict()

        logging.debug(
            f"Start service for PUT Update Team Agent - {url} - {headers} - {json.dumps(payload)}"
        )
        resp = "No specified error."
        try:
            r = _request_with_retry("put", url, headers=headers, json=payload)
            resp = r.json()
        except Exception:
            raise Exception(
                "Team Agent Update Error: Please contact the administrators."
            )

        if 200 <= r.status_code < 300:
            return build_team_agent(resp)
        else:
            error_msg = f"Team Agent Update Error (HTTP {r.status_code}): {resp}"
            raise Exception(error_msg)

    def save(self) -> None:
        """Save the Agent."""
        self.update()

    def __repr__(self):
        """Return a string representation of the TeamAgent.

        Returns:
            str: A string in the format "TeamAgent: <name> (id=<id>)".
        """
        return f"TeamAgent: {self.name} (id={self.id})"

    def evolve_async(
        self,
        evolve_type: Union[EvolveType, str] = EvolveType.TEAM_TUNING,
        max_successful_generations: int = 3,
        max_failed_generation_retries: int = 3,
        max_iterations: int = 50,
        max_non_improving_generations: Optional[int] = 2,
        llm: Optional[Union[Text, LLM]] = None,
    ) -> AgentResponse:
        """Asynchronously evolve the Team Agent and return a polling URL in the AgentResponse.

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

        response = self.run_async(query=query, evolve=evolve_parameters)
        return response

    def evolve(
        self,
        evolve_type: Union[EvolveType, str] = EvolveType.TEAM_TUNING,
        max_successful_generations: int = 3,
        max_failed_generation_retries: int = 3,
        max_iterations: int = 50,
        max_non_improving_generations: Optional[int] = 2,
        llm: Optional[Union[Text, LLM]] = None,
    ) -> AgentResponse:
        """Synchronously evolve the Team Agent and poll for the result.

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
        from aixplain.enums import EvolveType
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
            current_code = (
                result_data.get("current_code")
                if isinstance(result_data, dict)
                else result_data.current_code
            )
            if current_code is not None:
                if evolve_parameters.evolve_type == EvolveType.TEAM_TUNING:
                    result_data["evolved_agent"] = build_team_agent_from_yaml(
                        result_data["current_code"],
                        self.llm_id,
                        self.api_key,
                        self.id,
                    )
                elif evolve_parameters.evolve_type == EvolveType.INSTRUCTION_TUNING:
                    self.instructions = result_data["current_code"]
                    self.description = result_data["current_code"]
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
            logging.error(f"Team Agent Evolve: Error in evolving: {e}")
            end = time.time()
            return AgentResponse(
                status=ResponseStatus.FAILED,
                completed=False,
                error_message="No response from the service.",
            )
