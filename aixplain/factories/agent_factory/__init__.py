__author__ = "lucaspavanelli"

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

Author: Thiago Castro Ferreira and Lucas Pavanelli
Date: May 16th 2024
Description:
    Agent Factory Class
"""

import json
import logging
import warnings

from aixplain.enums.function import Function
from aixplain.enums.supplier import Supplier
from aixplain.modules.agent import Agent, AgentTask, Tool, MonitoringTools
from aixplain.modules.agent.tool.model_tool import ModelTool
from aixplain.modules.agent.tool.pipeline_tool import PipelineTool
from aixplain.modules.agent.tool.python_interpreter_tool import PythonInterpreterTool
from aixplain.modules.agent.tool.custom_python_code_tool import CustomPythonCodeTool
from aixplain.modules.model import Model
from aixplain.modules.pipeline import Pipeline
from aixplain.utils import config
from typing import Callable, Dict, List, Optional, Text, Union

from aixplain.utils.file_utils import _request_with_retry
from urllib.parse import urljoin


class AgentFactory:
    @classmethod
    def create(
        cls,
        name: Text,
        description: Text,
        role: Optional[Text] = None,
        llm_id: Text = "669a63646eb56306647e1091",
        tools: List[Union[Tool, Model]] = [],
        api_key: Text = config.TEAM_API_KEY,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        version: Optional[Text] = None,
        tasks: List[AgentTask] = [],
        monitoring_tools: MonitoringTools = None,
    ) -> Agent:
        """Create a new agent in the platform.

        Warning:
            The 'role' parameter was recently added and serves the same purpose as 'description' did previously: set the role of the agent as a system prompt.
            The 'description' parameter is still required and should be used to set a short summary of the agent's purpose.
            For the next releases, the 'role' parameter will be required.

        Args:
            name (Text): name of the agent
            description (Text): description of the agent role.
            role (Text): role of the agent.
            llm_id (Text, optional): aiXplain ID of the large language model to be used as agent. Defaults to "669a63646eb56306647e1091" (GPT-4o mini).
            tools (List[Union[Tool, Model]], optional): list of tool for the agent. Defaults to [].
            api_key (Text, optional): team/user API key. Defaults to config.TEAM_API_KEY.
            supplier (Union[Dict, Text, Supplier, int], optional): owner of the agent. Defaults to "aiXplain".
            version (Optional[Text], optional): version of the agent. Defaults to None.
            tasks (List[AgentTask], optional): list of tasks for the agent. Defaults to [].
            monitoring_tools (MonitoringTools, optional): list of monitoring tools for the agent. Defaults to None.
        Returns:
            Agent: created Agent
        """
        warnings.warn(
            "The 'role' parameter was recently added and serves the same purpose as 'description' did previously: set the role of the agent as a system prompt. "
            "The 'description' parameter is still required and should be used to set a short summary of the agent's purpose. "
            "For the next releases, the 'role' parameter will be required.",
            UserWarning,
        )
        from aixplain.factories.agent_factory.utils import build_agent

        agent = None
        url = urljoin(config.BACKEND_URL, "sdk/agents")
        headers = {"x-api-key": api_key}

        if isinstance(supplier, dict):
            supplier = supplier["code"]
        elif isinstance(supplier, Supplier):
            supplier = supplier.value["code"]

        payload = {
            "name": name,
            "assets": [
                tool.to_dict()
                if isinstance(tool, Tool)
                else {
                    "id": tool.id,
                    "name": tool.name,
                    "description": tool.description,
                    "supplier": tool.supplier.value["code"] if isinstance(tool.supplier, Supplier) else tool.supplier,
                    "parameters": tool.get_parameters().to_list()
                    if hasattr(tool, "get_parameters") and tool.get_parameters() is not None
                    else None,
                    "function": tool.function if hasattr(tool, "function") and tool.function is not None else None,
                    "type": "model",
                    "version": tool.version if hasattr(tool, "version") else None,
                    "assetId": tool.id,
                }
                for tool in tools
            ],
            "description": description,
            "role": role or description,
            "supplier": supplier,
            "version": version,
            "llmId": llm_id,
            "status": "draft",
            "tasks": [task.to_dict() for task in tasks],
            "tools": monitoring_tools.to_list() if monitoring_tools is not None else None,
        }
        agent = build_agent(payload=payload, api_key=api_key)
        agent.validate()
        response = "Unspecified error"
        try:
            logging.info(f"Start service for POST Create Agent  - {url} - {headers} - {json.dumps(agent.to_dict())}")
            r = _request_with_retry("post", url, headers=headers, json=agent.to_dict())
            response = r.json()
        except Exception:
            raise Exception("Agent Onboarding Error: Please contact the administrators.")
        if 200 <= r.status_code < 300:
            agent = build_agent(payload=response, api_key=api_key)
        else:
            error_msg = f"Agent Onboarding Error: {response}"
            if "message" in response:
                msg = response["message"]
                if response["message"] == "err.name_already_exists":
                    msg = "Agent name already exists."
                elif response["message"] == "err.asset_is_not_available":
                    msg = "Some tools are not available."
                error_msg = f"Agent Onboarding Error (HTTP {r.status_code}): {msg}"
            logging.exception(error_msg)
            raise Exception(error_msg)
        return agent

    @classmethod
    def create_task(
        cls, name: Text, description: Text, expected_output: Text, dependencies: Optional[List[Text]] = None
    ) -> AgentTask:
        return AgentTask(name=name, description=description, expected_output=expected_output, dependencies=dependencies)

    @classmethod
    def create_model_tool(
        cls,
        model: Optional[Union[Model, Text]] = None,
        function: Optional[Union[Function, Text]] = None,
        supplier: Optional[Union[Supplier, Text]] = None,
        description: Text = "",
        parameters: Optional[Dict] = None,
    ) -> ModelTool:
        """Create a new model tool."""
        if function is not None and isinstance(function, str):
            function = Function(function)

        if supplier is not None:
            if isinstance(supplier, str):
                for supplier_ in Supplier:
                    if supplier.lower() in [supplier_.value["code"].lower(), supplier_.value["name"].lower()]:
                        supplier = supplier_
                        break
            assert isinstance(supplier, Supplier), f"Supplier {supplier} is not a valid supplier"
        return ModelTool(function=function, supplier=supplier, model=model, description=description, parameters=parameters)

    @classmethod
    def create_pipeline_tool(cls, description: Text, pipeline: Union[Pipeline, Text]) -> PipelineTool:
        """Create a new pipeline tool."""
        return PipelineTool(description=description, pipeline=pipeline)

    @classmethod
    def create_python_interpreter_tool(cls) -> PythonInterpreterTool:
        """Create a new python interpreter tool."""
        return PythonInterpreterTool()

    @classmethod
    def create_custom_python_code_tool(cls, code: Union[Text, Callable], description: Text = "") -> CustomPythonCodeTool:
        """Create a new custom python code tool."""
        return CustomPythonCodeTool(description=description, code=code)

    @classmethod
    def list(cls) -> Dict:
        """List all agents available in the platform."""
        from aixplain.factories.agent_factory.utils import build_agent

        url = urljoin(config.BACKEND_URL, "sdk/agents")
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}

        resp = {}
        payload = {}
        logging.info(f"Start service for GET List Agents - {url} - {headers} - {json.dumps(payload)}")
        try:
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
        except Exception:
            raise Exception("Agent Listing Error: Please contact the administrators.")

        if 200 <= r.status_code < 300:
            agents, page_total, total = [], 0, 0
            results = resp
            page_total = len(results)
            total = len(results)
            logging.info(f"Response for GET List Agents - Page Total: {page_total} / Total: {total}")
            for agent in results:
                agents.append(build_agent(agent))
            return {"results": agents, "page_total": page_total, "page_number": 0, "total": total}
        else:
            error_msg = "Agent Listing Error: Please contact the administrators."
            if isinstance(resp, dict) and "message" in resp:
                msg = resp["message"]
                error_msg = f"Agent Listing Error (HTTP {r.status_code}): {msg}"
            logging.exception(error_msg)
            raise Exception(error_msg)

    @classmethod
    def get(cls, agent_id: Text, api_key: Optional[Text] = None) -> Agent:
        """Get agent by id."""
        from aixplain.factories.agent_factory.utils import build_agent

        url = urljoin(config.BACKEND_URL, f"sdk/agents/{agent_id}")

        api_key = api_key if api_key is not None else config.TEAM_API_KEY
        headers = {"x-api-key": api_key, "Content-Type": "application/json"}
        logging.info(f"Start service for GET Agent  - {url} - {headers}")
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()
        if 200 <= r.status_code < 300:
            return build_agent(resp)
        else:
            msg = "Please contact the administrators."
            if "message" in resp:
                msg = resp["message"]
            error_msg = f"Agent Get Error (HTTP {r.status_code}): {msg}"
            raise Exception(error_msg)
