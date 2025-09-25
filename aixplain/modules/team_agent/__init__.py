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
Date: August 15th 2024
Description:
    Team Agent Class
"""

import json
import logging
import time
import traceback
import re
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
from aixplain.modules.team_agent.inspector import Inspector
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
        llm_id (Text, optional): large language model. Defaults to GPT-4o (6646261c6eb563165658bbb1).
        api_key (str): The TEAM API key used for authentication.
        supplier (Text): Supplier of the Team Agent.
        version (Text): Version of the Team Agent.
        cost (Dict, optional): model price. Defaults to None.
        use_mentalist (bool): Use Mentalist agent for pre-planning. Defaults to True.
        inspectors (List[Inspector]): List of inspectors that the team agent uses.
        inspector_targets (List[InspectorTarget]): List of targets where the inspectors are applied. Defaults to [InspectorTarget.STEPS].
    """

    is_valid: bool

    def __init__(
        self,
        id: Text,
        name: Text,
        agents: List[Agent] = [],
        description: Text = "",
        llm_id: Text = "6646261c6eb563165658bbb1",
        llm: Optional[LLM] = None,
        supervisor_llm: Optional[LLM] = None,
        mentalist_llm: Optional[LLM] = None,
        api_key: Optional[Text] = config.TEAM_API_KEY,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        version: Optional[Text] = None,
        cost: Optional[Dict] = None,
        use_mentalist: bool = True,
        inspectors: List[Inspector] = [],
        inspector_targets: List[InspectorTarget] = [InspectorTarget.STEPS],
        status: AssetStatus = AssetStatus.DRAFT,
        instructions: Optional[Text] = None,
        output_format: OutputFormat = OutputFormat.TEXT,
        expected_output: Optional[Union[BaseModel, Text, dict]] = None,
        **additional_info,
    ) -> None:

        super().__init__(id, name, description, api_key, supplier, version, cost=cost)
        self.additional_info = additional_info
        self.agents = agents
        self.llm_id = llm_id
        self.llm = llm
        self.api_key = api_key
        self.use_mentalist = use_mentalist
        self.inspectors = inspectors
        self.inspector_targets = inspector_targets
        self.use_inspector = True if inspectors else False
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

            r = _request_with_retry("post", self.url, headers=headers, data=json.dumps(payload))
            resp = r.json()
            poll_url = resp.get("data")

            result = self.sync_poll(poll_url, name="model_process", timeout=300, wait_time=0.5)

            if result.get("status") == ResponseStatus.SUCCESS:
                return session_id
            else:
                logging.error(f"Team session init failed for {session_id}: {result}")
                return session_id
        except Exception as e:
            logging.error(f"Failed to initialize team session {session_id}: {e}")
            return session_id

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
        output_format: Optional[OutputFormat] = None,
        expected_output: Optional[Union[BaseModel, Text, dict]] = None,
        trace_request: bool = False,
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
            output_format (OutputFormat, optional): response format. If not provided, uses the format set during initialization.
            expected_output (Union[BaseModel, Text, dict], optional): expected output. Defaults to None.
            trace_request (bool, optional): return the request id for tracing the request. Defaults to False.
        Returns:
            AgentResponse: parsed output from model
        """
        start = time.time()
        result_data = {}
        if session_id is not None and history is not None:
            raise ValueError("Provide either `session_id` or `history`, not both.")

        if session_id is not None:
            if not session_id.startswith(f"{self.id}_"):
                raise ValueError(f"Session ID '{session_id}' does not belong to this Agent.")
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
            result_data = result.data
            return AgentResponse(
                status=ResponseStatus.SUCCESS,
                completed=True,
                data=AgentResponseData(
                    input=result_data.get("input"),
                    output=result_data.get("output"),
                    session_id=result_data.get("session_id"),
                    intermediate_steps=result_data.get("intermediate_steps"),
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
                raise ValueError(f"Session ID '{session_id}' does not belong to this Agent.")

        if history:
            validate_history(history)

        from aixplain.factories.file_factory import FileFactory

        # Validate and normalize evolve parameters using the base model
        evolve_param = validate_evolve_param(evolve)
        evolve_dict = evolve_param.to_dict()

        if not self.is_valid:
            raise Exception("Team Agent is not valid. Please validate the team agent before running.")

        assert data is not None or query is not None, "Either 'data' or 'query' must be provided."
        if data is not None:
            if isinstance(data, dict):
                assert "query" in data and data["query"] is not None, "When providing a dictionary, 'query' must be provided."
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
                isinstance(query, str) and FileFactory.check_storage_type(query) == StorageType.TEXT
            ), "When providing 'content', query must be text."

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
                "maxTokens": (parameters["max_tokens"] if "max_tokens" in parameters else max_tokens),
                "maxIterations": (parameters["max_iterations"] if "max_iterations" in parameters else max_iterations),
                "outputFormat": output_format,
                "expectedOutput": expected_output,
            },
            "evolve": json.dumps(evolve_dict),
        }
        payload.update(parameters)
        payload = json.dumps(payload)

        r = _request_with_retry("post", self.url, headers=headers, data=payload)
        logging.info(f"Team Agent Run Async: Start service for {name} - {self.url} - {payload} - {headers}")

        resp = None
        try:
            resp = r.json()
            logging.info(f"Result of request for {name} - {r.status_code} - {resp}")
            if trace_request:
                logging.info(f"Team Agent Run Async: Trace request id: {resp.get('requestId')}")
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
            logging.debug(f"Single Poll for Team Agent: Status of polling for {name}: {resp}")

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
                    resp_data = EvolverResponseData.from_dict(resp_data, llm_id=self.llm_id, api_key=self.api_key)
            else:
                resp_data = AgentResponseData(
                    input=resp_data.get("input"),
                    output=resp_data.get("output"),
                    session_id=resp_data.get("session_id"),
                    intermediate_steps=resp_data.get("intermediate_steps"),
                    execution_stats=resp_data.get("executionStats"),
                )
        except Exception as e:
            import traceback

            logging.error(f"Single Poll for Team Agent: Error of polling for {name}: {e}, traceback: {traceback.format_exc()}")
            status = ResponseStatus.FAILED
            error_message = str(e)
        finally:
            response = AgentResponse(
                status=status,
                data=resp_data,
                details=resp.get("details", {}),
                completed=resp.get("completed", False),
                used_credits=used_credits,
                run_time=run_time,
                usage=resp.get("usage", None),
                error_message=error_message,
            )
        return response

    def delete(self) -> None:
        """Delete Corpus service"""
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
            message = (
                f"Team Agent Deletion Error (HTTP {r.status_code}): Make sure the Team Agent exists and you are the owner."
            )
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
        base_dict = {"assetId": agent.id, "number": idx, "type": "AGENT", "label": "AGENT"}

        # Try to get additional data from agent's to_dict method
        try:
            if hasattr(agent, "to_dict") and callable(getattr(agent, "to_dict")):
                agent_dict = agent.to_dict()
                # Ensure it's actually a dictionary and not a Mock or other object
                if isinstance(agent_dict, dict) and hasattr(agent_dict, "items"):
                    try:
                        # Add all fields except 'id' to avoid duplication with 'assetId'
                        additional_data = {k: v for k, v in agent_dict.items() if k not in ["id"]}
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

        This method serializes the TeamAgent and all its components (agents,
        inspectors, LLMs, etc.) into a dictionary format suitable for storage
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
                - inspectors (List[Dict]): Serialized list of inspectors
                - inspectorTargets (List[str]): List of inspector target stages
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
            "agents": [self._serialize_agent(agent, idx) for idx, agent in enumerate(self.agents)],
            "links": [],
            "description": self.description,
            "llmId": self.llm.id if self.llm else self.llm_id,
            "supervisorId": (self.supervisor_llm.id if self.supervisor_llm else self.llm_id),
            "plannerId": planner_id,
            "inspectors": [inspector.model_dump(by_alias=True) for inspector in self.inspectors],
            "inspectorTargets": [target.value for target in self.inspector_targets],
            "supplier": (self.supplier.value["code"] if isinstance(self.supplier, Supplier) else self.supplier),
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
        from aixplain.modules.team_agent import Inspector, InspectorTarget
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

                        logging.warning(f"Failed to load agent {agent_data['assetId']}: {e}")
                else:
                    agents.append(Agent.from_dict(agent_data))
        # Extract inspectors using proper model validation
        inspectors = []
        if "inspectors" in data:
            for inspector_data in data["inspectors"]:
                try:
                    if isinstance(inspector_data, Inspector):
                        inspectors.append(inspector_data)
                    elif hasattr(Inspector, "model_validate"):
                        inspectors.append(Inspector.model_validate(inspector_data))
                    else:
                        inspectors.append(Inspector(**inspector_data))
                except Exception as e:
                    import logging

                    logging.warning(f"Failed to create inspector from data: {e}")
                    continue

        # Extract inspector targets
        inspector_targets = [InspectorTarget.STEPS]  # default
        if "inspectorTargets" in data:
            inspector_targets = [InspectorTarget(target) for target in data["inspectorTargets"]]

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
            llm_id=data.get("llmId", "6646261c6eb563165658bbb1"),
            llm=llm,
            supervisor_llm=supervisor_llm,
            mentalist_llm=mentalist_llm,
            supplier=data.get("supplier", "aiXplain"),
            version=data.get("version"),
            use_mentalist=use_mentalist,
            status=status,
            instructions=data.get("instructions"),
            inspectors=inspectors,
            inspector_targets=inspector_targets,
            output_format=OutputFormat(data.get("outputFormat", OutputFormat.TEXT)),
            expected_output=data.get("expectedOutput"),
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
            assert llm.function == Function.TEXT_GENERATION, "Large Language Model must be a text generation model."
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
                logging.warning("You won't be able to run the Team Agent until the issues are handled manually.")

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
                "update() is deprecated and will be removed in a future version. " "Please use save() instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        from aixplain.factories.team_agent_factory.utils import build_team_agent

        self.validate(raise_exception=True)
        url = urljoin(config.BACKEND_URL, f"sdk/agent-communities/{self.id}")
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}

        payload = self.to_dict()

        logging.debug(f"Start service for PUT Update Team Agent - {url} - {headers} - {json.dumps(payload)}")
        resp = "No specified error."
        try:
            r = _request_with_retry("put", url, headers=headers, json=payload)
            resp = r.json()
        except Exception:
            raise Exception("Team Agent Update Error: Please contact the administrators.")

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
        from aixplain.factories.team_agent_factory.utils import build_team_agent_from_yaml

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
            current_code = result_data.get("current_code") if isinstance(result_data, dict) else result_data.current_code
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
