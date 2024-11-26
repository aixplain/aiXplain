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

from aixplain.enums.function import Function
from aixplain.enums.supplier import Supplier
from aixplain.modules.agent import Agent, Tool
from aixplain.modules.agent.tool.model_tool import ModelTool
from aixplain.modules.agent.tool.pipeline_tool import PipelineTool
from aixplain.modules.model import Model
from aixplain.modules.pipeline import Pipeline
from aixplain.utils import config
from typing import Dict, List, Optional, Text, Union

from aixplain.utils.file_utils import _request_with_retry
from urllib.parse import urljoin


class AgentFactory:
    @classmethod
    def create(
        cls,
        name: Text,
        description: Text,
        llm_id: Text = "669a63646eb56306647e1091",
        tools: List[Tool] = [],
        api_key: Text = config.TEAM_API_KEY,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        version: Optional[Text] = None,
    ) -> Agent:
        """Create a new agent in the platform.

        Args:
            name (Text): name of the agent
            description (Text): description of the agent role.
            llm_id (Text, optional): aiXplain ID of the large language model to be used as agent. Defaults to "669a63646eb56306647e1091" (GPT-4o mini).
            tools (List[Tool], optional): list of tool for the agent. Defaults to [].
            api_key (Text, optional): team/user API key. Defaults to config.TEAM_API_KEY.
            supplier (Union[Dict, Text, Supplier, int], optional): owner of the agent. Defaults to "aiXplain".
            version (Optional[Text], optional): version of the agent. Defaults to None.

        Returns:
            Agent: created Agent
        """
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
            "assets": [tool.to_dict() for tool in tools],
            "description": description,
            "supplier": supplier,
            "version": version,
            "llmId": llm_id,
            "status": "draft",
        }
        agent = build_agent(payload=payload, api_key=api_key)
        agent.validate()
        response = "Unspecified error"
        try:
            logging.debug(f"Start service for POST Create Agent  - {url} - {headers} - {json.dumps(payload)}")
            r = _request_with_retry("post", url, headers=headers, json=payload)
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
    def create_model_tool(
        cls,
        model: Optional[Union[Model, Text]] = None,
        function: Optional[Union[Function, Text]] = None,
        supplier: Optional[Union[Supplier, Text]] = None,
        description: Text = "",
    ) -> ModelTool:
        """Create a new model tool."""
        if function is not None and isinstance(function, str):
            function = Function(function)

        if supplier is not None:
            if isinstance(supplier, str):
                for supplier_ in Supplier:
                    if supplier.lower() in [supplier.value["code"].lower(), supplier.value["name"].lower()]:
                        supplier = supplier_
                        break
                if isinstance(supplier, str):
                    supplier = None
        return ModelTool(function=function, supplier=supplier, model=model, description=description)

    @classmethod
    def create_pipeline_tool(cls, description: Text, pipeline: Union[Pipeline, Text]) -> PipelineTool:
        """Create a new pipeline tool."""
        return PipelineTool(description=description, pipeline=pipeline)

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
