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
from typing import Dict, List, Text, Optional, Union
from urllib.parse import urljoin

from aixplain.enums import ResponseStatus
from aixplain.enums.function import Function
from aixplain.enums.supplier import Supplier
from aixplain.enums.asset_status import AssetStatus
from aixplain.enums.storage_type import StorageType
from aixplain.modules.model import Model
from aixplain.modules.agent import Agent, OutputFormat
from aixplain.modules.agent.agent_response import AgentResponse
from aixplain.modules.agent.agent_response_data import AgentResponseData
from aixplain.modules.agent.utils import process_variables
from aixplain.modules.team_agent.evolver_response_data import EvolverResponseData
from aixplain.modules.team_agent.evolver_response import EvolverResponse
from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry


class InspectorTarget(str, Enum):
    # TODO: INPUT
    STEPS = "steps"
    OUTPUT = "output"

    def __str__(self):
        return self._value_


class TeamAgent(Model):
    """Advanced AI system capable of using multiple agents to perform a variety of tasks.

    Attributes:
        id (Text): ID of the Team Agent
        name (Text): Name of the Team Agent
        agents (List[Agent]): List of Agents that the Team Agent uses.
        description (Text, optional): description of the Team Agent. Defaults to "".
        llm_id (Text, optional): large language model. Defaults to GPT-4o (6646261c6eb563165658bbb1).
        supplier (Text): Supplier of the Team Agent.
        version (Text): Version of the Team Agent.
        backend_url (str): URL of the backend.
        api_key (str): The TEAM API key used for authentication.
        cost (Dict, optional): model price. Defaults to None.
        use_mentalist_and_inspector (bool): Use Mentalist and Inspector tools. Defaults to True.
    """

    is_valid: bool

    def __init__(
        self,
        id: Text,
        name: Text,
        agents: List[Agent] = [],
        description: Text = "",
        llm_id: Text = "6646261c6eb563165658bbb1",
        api_key: Optional[Text] = config.TEAM_API_KEY,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        version: Optional[Text] = None,
        cost: Optional[Dict] = None,
        use_mentalist: bool = True,
        use_inspector: bool = True,
        max_inspectors: int = 1,
        inspector_targets: List[InspectorTarget] = [InspectorTarget.STEPS],
        status: AssetStatus = AssetStatus.DRAFT,
        **additional_info,
    ) -> None:
        """Create a FineTune with the necessary information.

        Args:
            id (Text): ID of the Team Agent
            name (Text): Name of the Team Agent
            agents (List[Agent]): List of agents that the Team Agent uses.
            description (Text, optional): description of the Team Agent. Defaults to "".
            llm_id (Text, optional): large language model. Defaults to GPT-4o (6646261c6eb563165658bbb1).
            supplier (Text): Supplier of the Team Agent.
            version (Text): Version of the Team Agent.
            backend_url (str): URL of the backend.
            api_key (str): The TEAM API key used for authentication.
            cost (Dict, optional): model price. Defaults to None.
            use_mentalist_and_inspector (bool): Use Mentalist and Inspector tools. Defaults to True.
        """
        super().__init__(id, name, description, api_key, supplier, version, cost=cost)
        self.additional_info = additional_info
        self.agents = agents
        self.llm_id = llm_id
        self.api_key = api_key 
        self.use_mentalist = use_mentalist
        self.use_inspector = use_inspector
        self.max_inspectors = max_inspectors
        self.inspector_targets = inspector_targets

        if isinstance(status, str):
            try:
                status = AssetStatus(status)
            except Exception:
                status = AssetStatus.DRAFT
        self.status = status
        self.is_valid = True

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
        output_format: OutputFormat = OutputFormat.TEXT,
        evolve: bool = False,
    ) -> Dict:
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
            output_format (ResponseFormat, optional): response format. Defaults to TEXT.
            evolve (bool, optional): evolve the team agent. Defaults to False.
        Returns:
            Dict: parsed output from model
        """
        start = time.time()
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
                evolve=evolve,
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
        output_format: OutputFormat = OutputFormat.TEXT,
        evolve: bool = False,
    ) -> Dict:
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
            output_format (ResponseFormat, optional): response format. Defaults to TEXT.
            evolve (bool, optional): evolve the team agent. Defaults to False.
        Returns:
            dict: polling URL in response
        """
        from aixplain.factories.file_factory import FileFactory

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
        input_data = process_variables(query, data, parameters, self.description)

        payload = {
            "id": self.id,
            "query": input_data,
            "sessionId": session_id,
            "history": history,
            "executionParams": {
                "maxTokens": (parameters["max_tokens"] if "max_tokens" in parameters else max_tokens),
                "maxIterations": (parameters["max_iterations"] if "max_iterations" in parameters else max_iterations),
                "outputFormat": output_format.value,
            },
            "evolve": evolve,
        }
        payload.update(parameters)
        payload = json.dumps(payload)

        r = _request_with_retry("post", self.url, headers=headers, data=payload)
        logging.info(f"Team Agent Run Async: Start service for {name} - {self.url} - {payload} - {headers}")

        resp = None
        try:
            resp = r.json()
            logging.info(f"Result of request for {name} - {r.status_code} - {resp}")

            poll_url = resp["data"]
            response = AgentResponse(
                status=ResponseStatus.IN_PROGRESS,
                url=poll_url,
                data=AgentResponseData(input=input_data),
                run_time=0.0,
                used_credits=0.0,
            )
            if evolve:
                response =  EvolverResponse(
                                        status=ResponseStatus.IN_PROGRESS,
                                        url=poll_url,
                                        data=EvolverResponseData(
                                                    evolved_agent="",
                                                    current_code="",
                                                    evaluation_report="",
                                                    comparison_report="",
                                                    criteria="",
                                                    archive="",),
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
                if evolve:
                        response = EvolverResponse(
                                            status=ResponseStatus.FAILED,
                                            error=msg,
                                        )
        return response
    

    def poll(self, poll_url: Text, name: Text = "model_process", evolve: bool = False) -> EvolverResponse:
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        r = _request_with_retry("get", poll_url, headers=headers)
        try:
            resp = r.json()
            evolver_data = None
            resp_data = resp.get("data", {})
            if resp["completed"] is True:
                status = ResponseStatus.SUCCESS
                if "error_message" in resp or "supplierError" in resp:
                    status = ResponseStatus.FAILED
            else:
                status = ResponseStatus.IN_PROGRESS
                response = f"EvolverResponse(status={status}, completed={resp['completed']})"
            logging.debug(f"Single Poll for Model: Status of polling for {name}: {resp}")

            if evolve:
                if status == ResponseStatus.SUCCESS:
                    evolver_data = EvolverResponseData.from_dict(resp_data, llm_id=self.llm_id, api_key=self.api_key)

                response = EvolverResponse(
                    status=status,
                    data=evolver_data or EvolverResponseData(
                                            evolved_agent="",
                                            current_code="",
                                            evaluation_report="",
                                            comparison_report="",
                                            criteria="",
                                            archive="",),
                    details=resp.get("details", {}),
                    completed=resp.get("completed", False),
                    error_message=resp.get("error_message", ""),
                    used_credits=resp.get("usedCredits", 0),
                    run_time=resp.get("runTime", 0),
                    usage=resp.get("usage", None),
                )
            response = AgentResponse(
                                status=status,
                                data=resp.get("data", {}),
                                details=resp.get("details", {}),
                                completed=resp.get("completed", False),
                                error_message=resp.get("error_message", ""),
                                used_credits=resp.get("usedCredits", 0),
                                run_time=resp.get("runTime", 0),
                                usage=resp.get("usage", None),
                            )

        except Exception as e:
            logging.error(f"Single Poll for Model: Error of polling for {name}: {e}")
            if evolve:
                response = f"EvolverResponse(status={ResponseStatus.FAILED}, error_message={str(e)}, completed=False)"

            response = f"AgentResponse(status={ResponseStatus.FAILED}, error_message={str(e)}, completed=False)"
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

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "agents": [
                {"assetId": agent.id, "number": idx, "type": "AGENT", "label": "AGENT"} for idx, agent in enumerate(self.agents)
            ],
            "links": [],
            "description": self.description,
            "llmId": self.llm_id,
            "supervisorId": self.llm_id,
            "plannerId": self.llm_id if self.use_mentalist else None,
            "inspectorId": self.llm_id if self.use_inspector else None,
            "maxInspectors": self.max_inspectors,
            "inspectorTargets": [target.value for target in self.inspector_targets],
            "supplier": self.supplier.value["code"] if isinstance(self.supplier, Supplier) else self.supplier,
            "version": self.version,
            "status": self.status.value,
        }

    def _validate(self) -> None:
        """Validate the Team."""
        from aixplain.factories.model_factory import ModelFactory

        # validate name
        assert (
            re.match(r"^[a-zA-Z0-9 \-\(\)]*$", self.name) is not None
        ), "Team Agent Creation Error: Team name contains invalid characters. Only alphanumeric characters, spaces, hyphens, and brackets are allowed."

        try:
            llm = ModelFactory.get(self.llm_id)
            assert llm.function == Function.TEXT_GENERATION, "Large Language Model must be a text generation model."
        except Exception:
            raise Exception(f"Large Language Model with ID '{self.llm_id}' not found.")

        for agent in self.agents:
            agent.validate(raise_exception=True)

    def validate(self, raise_exception: bool = False) -> bool:
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
        """Update the Team Agent."""
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
        """Save the Team Agent."""
        self.update()

    def deploy(self) -> None:
        """Deploy the Team Agent."""
        assert self.status == AssetStatus.DRAFT, "Team Agent Deployment Error: Team Agent must be in draft status."
        assert self.status != AssetStatus.ONBOARDED, "Team Agent Deployment Error: Team Agent must be onboarded."
        self.status = AssetStatus.ONBOARDED
        self.update()

    def evolve(self, query: Text) -> None:
        """Evolve the Team Agent."""
        return self.run_async(query=query, evolve=True)
