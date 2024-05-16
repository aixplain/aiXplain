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
from aixplain.utils import config
from typing import Dict, List, Optional, Text, Union

from aixplain.factories.agent_factory.utils import build_agent
from aixplain.utils.file_utils import _request_with_retry


class AgentFactory:
    @classmethod
    def create(
        cls,
        name: Text,
        tools: List[Tool] = [],
        description: Text = "",
        api_key: Optional[Text] = config.TEAM_API_KEY,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        version: Optional[Text] = None,
        cost: Optional[Dict] = None,
    ) -> Agent:
        """Create a new agent in the platform."""
        try:
            agent = None
            url = "http://54.86.247.242:8000/execute"
            headers = {"Authorization": "token " + api_key}

            if isinstance(Supplier, dict):
                supplier = supplier["code"]
            elif isinstance(supplier, Supplier):
                supplier = supplier.value

            payload = {
                "name": name,
                "tools": [tool.function.value for tool in tools],
                "description": description,
                "supplier": supplier,
                "version": version,
                "cost": cost,
            }
            logging.info(f"Start service for POST Create Agent  - {url} - {headers}")
            r = _request_with_retry("post", url, headers=headers, json=payload)
            if 200 <= r.status_code < 300:
                response = r.json()

                asset_id = response["id"]
                agent = Agent(
                    id=asset_id, name=name, tools=tools, description=description, supplier=supplier, version=version, cost=cost
                )
            else:
                error_msg = "Agent Onboarding Error: Please contant the administrators."
                logging.exception(error_msg)
                raise Exception(error_msg)
        except Exception as e:
            raise Exception(e)
        return agent

    @classmethod
    def list(cls) -> Dict:
        """List all agents available in the platform."""
        url = "http://54.86.247.242:8000/list"
        if config.AIXPLAIN_API_KEY != "":
            headers = {"x-aixplain-key": f"{config.AIXPLAIN_API_KEY}", "Content-Type": "application/json"}
        else:
            headers = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}

        payload = {}
        logging.info(f"Start service for POST List Agents - {url} - {headers} - {json.dumps(payload)}")
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()

        agents, page_total, total = [], 0, 0
        results = resp
        page_total = len(results)
        total = len(results)
        logging.info(f"Response for POST List Dataset - Page Total: {page_total} / Total: {total}")
        for agent in results:
            agents.append(build_agent(agent))
        return {"results": agents, "page_total": page_total, "page_number": 0, "total": total}

    @classmethod
    def get(cls, agent_id: Text) -> Agent:
        """Get agent by id."""
        url = f"http://54.86.247.242:8000/get?id={agent_id}"
        if config.AIXPLAIN_API_KEY != "":
            headers = {"x-aixplain-key": f"{config.AIXPLAIN_API_KEY}", "Content-Type": "application/json"}
        else:
            headers = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}
        logging.info(f"Start service for GET Agent  - {url} - {headers}")
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()
        return build_agent(resp)
