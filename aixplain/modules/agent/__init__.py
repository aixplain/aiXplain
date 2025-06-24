__author__ = "aiXplain"

"""
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
import json
import logging
import re
import time
import traceback

from aixplain.utils.file_utils import _request_with_retry
from aixplain.enums import Function, Supplier, AssetStatus, StorageType, ResponseStatus
from aixplain.modules.model import Model
from aixplain.modules.agent.agent_task import AgentTask
from aixplain.modules.agent.output_format import OutputFormat
from aixplain.modules.agent.tool import Tool
from aixplain.modules.agent.agent_response import AgentResponse
from aixplain.modules.agent.agent_response_data import AgentResponseData
from aixplain.modules.agent.utils import process_variables
from pydantic import BaseModel
from typing import Dict, List, Text, Optional, Union
from urllib.parse import urljoin
from aixplain.modules.model.llm_model import LLM

from aixplain.utils import config
from aixplain.modules.mixins import DeployableMixin


class Agent(Model, DeployableMixin[Tool]):
    """Advanced AI system capable of performing tasks by leveraging specialized software tools and resources from aiXplain marketplace.

    Attributes:
        id (Text): ID of the Agent
        name (Text): Name of the Agent
        tools (List[Union[Tool, Model]]): List of tools that the Agent uses.
        description (Text, optional): description of the Agent. Defaults to "".
        instructions (Text): instructions of the Agent.
        llm_id (Text): large language model. Defaults to GPT-4o (6646261c6eb563165658bbb1).
        supplier (Text): Supplier of the Agent.
        version (Text): Version of the Agent.
        backend_url (str): URL of the backend.
        api_key (str): The TEAM API key used for authentication.
        cost (Dict, optional): model price. Defaults to None.
    """

    is_valid: bool

    def __init__(
        self,
        id: Text,
        name: Text,
        description: Text,
        instructions: Text,
        tools: List[Union[Tool, Model]] = [],
        llm_id: Text = "6646261c6eb563165658bbb1",
        llm: Optional[LLM] = None,
        api_key: Optional[Text] = config.TEAM_API_KEY,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        version: Optional[Text] = None,
        cost: Optional[Dict] = None,
        status: AssetStatus = AssetStatus.DRAFT,
        tasks: List[AgentTask] = [],
        **additional_info,
    ) -> None:
        """Create an Agent with the necessary information.

        Args:
            id (Text): ID of the Agent
            name (Text): Name of the Agent
            description (Text): description of the Agent.
            instructions (Text): role of the Agent.
            tools (List[Union[Tool, Model]]): List of tools that the Agent uses.
            llm_id (Text, optional): large language model ID. Defaults to GPT-4o (6646261c6eb563165658bbb1).
            llm (LLM, optional): large language model object. Defaults to None.
            supplier (Text): Supplier of the Agent.
            version (Text): Version of the Agent.
            backend_url (str): URL of the backend.
            api_key (str): The TEAM API key used for authentication.
            cost (Dict, optional): model price. Defaults to None.
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
        self.tasks = tasks
        self.is_valid = True

    def _validate(self) -> None:
        """Validate the Agent."""
        from aixplain.utils.llm_utils import get_llm_instance

        # validate name
        assert (
            re.match(r"^[a-zA-Z0-9 \-\(\)]*$", self.name) is not None
        ), "Agent Creation Error: Agent name contains invalid characters. Only alphanumeric characters, spaces, hyphens, and brackets are allowed."

        llm = get_llm_instance(self.llm_id, api_key=self.api_key)

        assert llm.function == Function.TEXT_GENERATION, "Large Language Model must be a text generation model."

        tool_names = []
        for tool in self.tools:
            tool_name = None
            if isinstance(tool, Tool):
                tool_name = tool.name
            elif isinstance(tool, Model):
                assert not isinstance(tool, Agent), "Agent cannot contain another Agent."
                tool_name = tool.name
            tool_names.append(tool_name)

        if len(tool_names) != len(set(tool_names)):
            duplicates = set([name for name in tool_names if tool_names.count(name) > 1])
            raise Exception(
                f"Agent Creation Error - Duplicate tool names found: {', '.join(duplicates)}. Make sure all tool names are unique."
            )

            tool_name = tool.name
            tool_names.append(tool_name)

        if len(tool_names) != len(set(tool_names)):
            duplicates = set([name for name in tool_names if tool_names.count(name) > 1])
            raise Exception(
                f"Agent Creation Error - Duplicate tool names found: {', '.join(duplicates)}. Make sure all tool names are unique."
            )

    def validate(self, raise_exception: bool = False) -> bool:
        """Validate the Agent."""
        try:
            self._validate()
            self.is_valid = True
        except Exception as e:
            self.is_valid = False
            if raise_exception:
                raise e
            else:
                logging.warning(f"Agent Validation Error: {e}")
                logging.warning("You won't be able to run the Agent until the issues are handled manually.")
        return self.is_valid

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
        max_iterations: int = 10,
        output_format: OutputFormat = OutputFormat.TEXT,
        expected_output: Optional[Union[BaseModel, Text, dict]] = None,
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
            output_format (OutputFormat, optional): response format. Defaults to TEXT.
            expected_output (Union[BaseModel, Text, dict], optional): expected output. Defaults to None.
        Returns:
            Dict: parsed output from model
        """
        start = time.time()
        result_data = {}
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
            )
            if response["status"] == ResponseStatus.FAILED:
                end = time.time()
                response["elapsed_time"] = end - start
                return response
            poll_url = response["url"]
            end = time.time()
            result = self.sync_poll(poll_url, name=name, timeout=timeout, wait_time=wait_time)
            # if result.status == ResponseStatus.FAILED:
            #    raise Exception("Model failed to run with error: " + result.error_message)
            result_data = result.get("data") or {}
            return AgentResponse(
                status=ResponseStatus.SUCCESS,
                completed=True,
                data=AgentResponseData(
                    input=result_data.get("input"),
                    output=result_data.get("output"),
                    session_id=result_data.get("session_id"),
                    intermediate_steps=result_data.get("intermediate_steps"),
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
        max_iterations: int = 10,
        output_format: OutputFormat = OutputFormat.TEXT,
        expected_output: Optional[Union[BaseModel, Text, dict]] = None,
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
            output_format (OutputFormat, optional): response format. Defaults to TEXT.
            expected_output (Union[BaseModel, Text, dict], optional): expected output. Defaults to None.
        Returns:
            dict: polling URL in response
        """
        from aixplain.factories.file_factory import FileFactory

        if not self.is_valid:
            raise Exception("Agent is not valid. Please validate the agent before running.")

        if output_format == OutputFormat.JSON:
            assert expected_output is not None and (
                issubclass(expected_output, BaseModel) or isinstance(expected_output, dict)
            ), "Expected output must be a Pydantic BaseModel or a JSON object when output format is JSON."

        assert data is not None or query is not None, "Either 'data' or 'query' must be provided."
        if data is not None:
            if isinstance(data, dict):
                assert "query" in data and data["query"] is not None, "When providing a dictionary, 'query' must be provided."
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
            assert FileFactory.check_storage_type(query) == StorageType.TEXT, "When providing 'content', query must be text."

            if isinstance(content, list):
                assert len(content) <= 3, "The maximum number of content inputs is 3."
                for input_link in content:
                    input_link = FileFactory.to_link(input_link)
                    query += f"\n{input_link}"
            elif isinstance(content, dict):
                for key, value in content.items():
                    assert "{{" + key + "}}" in query, f"Key '{key}' not found in query."
                    value = FileFactory.to_link(value)
                    query = query.replace("{{" + key + "}}", f"'{value}'")

        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}

        # build query
        input_data = process_variables(query, data, parameters, self.instructions)

        if expected_output is not None and issubclass(expected_output, BaseModel):
            expected_output = expected_output.model_json_schema()
        if isinstance(output_format, OutputFormat):
            output_format = output_format.value

        payload = {
            "id": self.id,
            "query": input_data,
            "sessionId": session_id,
            "history": history,
            "executionParams": {
                "maxTokens": (parameters["max_tokens"] if "max_tokens" in parameters else max_tokens),
                "maxIterations": (parameters["max_iterations"] if "max_iterations" in parameters else max_iterations),
                "outputFormat": output_format,
                "expectedOutput": expected_output,
            },
        }

        payload.update(parameters)
        payload = json.dumps(payload)

        try:
            r = _request_with_retry("post", self.url, headers=headers, data=payload)
            resp = r.json()
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
        from aixplain.factories.agent_factory.utils import build_tool_payload

        return {
            "id": self.id,
            "name": self.name,
            "assets": [build_tool_payload(tool) for tool in self.tools],
            "description": self.description,
            "role": self.instructions,
            "supplier": (self.supplier.value["code"] if isinstance(self.supplier, Supplier) else self.supplier),
            "version": self.version,
            "llmId": self.llm_id if self.llm is None else self.llm.id,
            "status": self.status.value,
            "tasks": [task.to_dict() for task in self.tasks],
            "tools": [
                {
                    "type": "llm",
                    "description": "main",
                    "parameters": self.llm.get_parameters().to_list() if self.llm.get_parameters() else None,
                }
            ]
            if self.llm is not None
            else [],
        }

    def delete(self) -> None:
        """Delete Agent service"""
        try:
            url = urljoin(config.BACKEND_URL, f"sdk/agents/{self.id}")
            headers = {
                "x-api-key": config.TEAM_API_KEY,
                "Content-Type": "application/json",
            }
            logging.debug(
                f"Start service for DELETE Agent  - {url} - {headers}"
            )
            r = _request_with_retry("delete", url, headers=headers)
            logging.debug(
                f"Result of request for DELETE Agent - {r.status_code}"
            )
            if r.status_code != 200:
                raise Exception()
        except Exception:
            try:
                response_json = r.json()
                error_message = response_json.get('message', '').strip('{{}}')

                if r.status_code == 403 and error_message == "err.agent_is_in_use":
                    # Get team agents that use this agent
                    from aixplain.factories.team_agent_factory import (
                        TeamAgentFactory
                    )
                    team_agents = TeamAgentFactory.list()["results"]
                    using_team_agents = [
                        ta for ta in team_agents
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
                        f"Agent Deletion Error (HTTP {r.status_code}): "
                        f"{error_message}."
                    )
            except ValueError:
                message = (
                    f"Agent Deletion Error (HTTP {r.status_code}): "
                    "There was an error in deleting the agent."
                )
            logging.error(message)
            raise Exception(message)

    def update(self) -> None:
        """Update agent."""
        import warnings
        import inspect

        # Get the current call stack
        stack = inspect.stack()
        if len(stack) > 2 and stack[1].function != "save":
            warnings.warn(
                "update() is deprecated and will be removed in a future version. " "Please use save() instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        from aixplain.factories.agent_factory.utils import build_agent

        self.validate(raise_exception=True)
        url = urljoin(config.BACKEND_URL, f"sdk/agents/{self.id}")
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}

        payload = self.to_dict()

        logging.debug(f"Start service for PUT Update Agent  - {url} - {headers} - {json.dumps(payload)}")
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
        """Save the Agent."""
        self.update()

    def __repr__(self):
        return f"Agent: {self.name} (id={self.id})"
