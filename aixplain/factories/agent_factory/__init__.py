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

from aixplain.enums.supplier import Supplier
from aixplain.modules.agent import Agent, Tool
from aixplain.modules.agent.tool.model_tool import ModelTool
from aixplain.modules.agent.tool.pipeline_tool import PipelineTool
from aixplain.utils import config
from typing import Dict, List, Optional, Text, Union

from aixplain.factories.agent_factory.utils import build_agent
from aixplain.utils.file_utils import _request_with_retry
from urllib.parse import urljoin


class AgentFactory:
    @classmethod
    def create(
        cls,
        name: Text,
        llm_id: Text,
        tools: List[Tool] = [],
        description: Text = "",
        api_key: Text = config.TEAM_API_KEY,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        version: Optional[Text] = None,
    ) -> Agent:
        """Create a new agent in the platform."""
        try:
            agent = None
            url = urljoin(config.BACKEND_URL, "sdk/agents")
            headers = {"x-api-key": api_key}

            if isinstance(supplier, dict):
                supplier = supplier["code"]
            elif isinstance(supplier, Supplier):
                supplier = supplier.value["code"]

            tool_payload = []
            for tool in tools:
                if isinstance(tool, ModelTool):
                    tool_payload.append(
                        {
                            "function": tool.function.value,
                            "type": "model",
                            "description": tool.description,
                            "supplier": tool.supplier.value["code"] if tool.supplier else None,
                            "version": tool.version if tool.version else None,
                        }
                    )
                elif isinstance(tool, PipelineTool):
                    tool_payload.append(
                        {
                            "assetId": tool.pipeline,
                            "description": tool.description,
                            "type": "pipeline",
                        }
                    )
                else:
                    raise Exception("Agent Creation Error: Tool type not supported.")

            payload = {
                "name": name,
                "assets": tool_payload,
                "description": description,
                "supplier": supplier,
                "version": version,
            }
            if llm_id is not None:
                payload["llmId"] = llm_id

            logging.info(f"Start service for POST Create Agent  - {url} - {headers} - {json.dumps(payload)}")
            r = _request_with_retry("post", url, headers=headers, json=payload)
            if 200 <= r.status_code < 300:
                response = r.json()
                agent = build_agent(payload=response, api_key=api_key)
            else:
                error = r.json()
                error_msg = "Agent Onboarding Error: Please contant the administrators."
                if "message" in error:
                    msg = error["message"]
                    if error["message"] == "err.name_already_exists":
                        msg = "Agent name already exists."
                    elif error["message"] == "err.asset_is_not_available":
                        msg = "Some the tools are not available."
                    error_msg = f"Agent Onboarding Error (HTTP {r.status_code}): {msg}"
                logging.exception(error_msg)
                raise Exception(error_msg)
        except Exception as e:
            raise Exception(e)
        return agent

    @classmethod
    def list(cls) -> Dict:
        """List all agents available in the platform."""
        url = urljoin(config.BACKEND_URL, "sdk/agents")
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}

        payload = {}
        logging.info(f"Start service for GET List Agents - {url} - {headers} - {json.dumps(payload)}")
        try:
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()

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
                error_msg = "Agent Listing Error: Please contant the administrators."
                if "message" in resp:
                    msg = resp["message"]
                    error_msg = f"Agent Listing Error (HTTP {r.status_code}): {msg}"
                logging.exception(error_msg)
                raise Exception(error_msg)
        except Exception as e:
            raise Exception(e)

    @classmethod
    def get(cls, agent_id: Text, api_key: Optional[Text] = None) -> Agent:
        """Get agent by id."""
        url = urljoin(config.BACKEND_URL, f"sdk/agents/{agent_id}")
        if config.AIXPLAIN_API_KEY != "":
            headers = {"x-aixplain-key": f"{config.AIXPLAIN_API_KEY}", "Content-Type": "application/json"}
        else:
            api_key = api_key if api_key is not None else config.TEAM_API_KEY
            headers = {"x-api-key": api_key, "Content-Type": "application/json"}
        logging.info(f"Start service for GET Agent  - {url} - {headers}")
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()
        if 200 <= r.status_code < 300:
            return build_agent(resp)
        else:
            msg = "Please contant the administrators."
            if "message" in resp:
                msg = resp["message"]
            error_msg = f"Agent Get Error (HTTP {r.status_code}): {msg}"
            raise Exception(error_msg)
