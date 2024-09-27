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
Date: August 15th 2024
Description:
    TeamAgent Factory Class
"""

import json
import logging

from aixplain.enums.supplier import Supplier
from aixplain.factories.agent_factory import AgentFactory
from aixplain.factories.agent_factory.utils import validate_llm, validate_name
from aixplain.modules.agent import Agent
from aixplain.modules.team_agent import TeamAgent
from aixplain.utils import config
from aixplain.factories.team_agent_factory.utils import build_team_agent
from aixplain.utils.file_utils import _request_with_retry
from typing import Dict, List, Optional, Text, Union
from urllib.parse import urljoin


class TeamAgentFactory:
    @classmethod
    def create(
        cls,
        name: Text,
        agents: List[Union[Text, Agent]],
        llm_id: Text = "669a63646eb56306647e1091",
        description: Text = "",
        api_key: Text = config.TEAM_API_KEY,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        version: Optional[Text] = None,
        use_mentalist_and_inspector: bool = True,
    ) -> TeamAgent:
        """Create a new team agent in the platform."""
        validate_name(name)
        # validate LLM ID
        validate_llm(llm_id)
        assert len(agents) > 0, "TeamAgent Onboarding Error: At least one agent must be provided."
        for agent in agents:
            if isinstance(agent, Text) is True:
                try:
                    agent = AgentFactory.get(agent)
                except Exception:
                    raise Exception(f"TeamAgent Onboarding Error: Agent {agent} does not exist.")
            else:
                assert isinstance(agent, Agent), "TeamAgent Onboarding Error: Agents must be instances of Agent class"

        mentalist_and_inspector_llm_id = None
        if use_mentalist_and_inspector is True:
            mentalist_and_inspector_llm_id = llm_id
        try:
            team_agent = None
            url = urljoin(config.BACKEND_URL, "sdk/agent-communities")
            headers = {"x-api-key": api_key}

            if isinstance(supplier, dict):
                supplier = supplier["code"]
            elif isinstance(supplier, Supplier):
                supplier = supplier.value["code"]

            agent_list = []
            for idx, agent in enumerate(agents):
                agent_list.append({"assetId": agent.id, "number": idx, "type": "AGENT", "label": "AGENT"})

            payload = {
                "name": name,
                "agents": agent_list,
                "links": [],
                "description": description,
                "llmId": llm_id,
                "supervisorId": llm_id,
                "plannerId": mentalist_and_inspector_llm_id,
                "supplier": supplier,
                "version": version,
            }

            logging.info(f"Start service for POST Create TeamAgent  - {url} - {headers} - {json.dumps(payload)}")
            r = _request_with_retry("post", url, headers=headers, json=payload)
            if 200 <= r.status_code < 300:
                response = r.json()
                team_agent = build_team_agent(payload=response, api_key=api_key)
            else:
                error = r.json()
                error_msg = "TeamAgent Onboarding Error: Please contact the administrators."
                if "message" in error:
                    msg = error["message"]
                    if error["message"] == "err.name_already_exists":
                        msg = "TeamAgent name already exists."
                    elif error["message"] == "err.asset_is_not_available":
                        msg = "Some tools are not available."
                    error_msg = f"TeamAgent Onboarding Error (HTTP {r.status_code}): {msg}"
                logging.exception(error_msg)
                raise Exception(error_msg)
        except Exception as e:
            raise Exception(e)
        return team_agent

    @classmethod
    def list(cls) -> Dict:
        """List all agents available in the platform."""
        url = urljoin(config.BACKEND_URL, "sdk/agent-communities")
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
                    agents.append(build_team_agent(agent))
                return {"results": agents, "page_total": page_total, "page_number": 0, "total": total}
            else:
                error_msg = "Agent Listing Error: Please contact the administrators."
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
        url = urljoin(config.BACKEND_URL, f"sdk/agent-communities/{agent_id}")
        if config.AIXPLAIN_API_KEY != "":
            headers = {"x-aixplain-key": f"{config.AIXPLAIN_API_KEY}", "Content-Type": "application/json"}
        else:
            api_key = api_key if api_key is not None else config.TEAM_API_KEY
            headers = {"x-api-key": api_key, "Content-Type": "application/json"}
        logging.info(f"Start service for GET Agent  - {url} - {headers}")
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()
        if 200 <= r.status_code < 300:
            return build_team_agent(resp)
        else:
            msg = "Please contact the administrators."
            if "message" in resp:
                msg = resp["message"]
            error_msg = f"Agent Get Error (HTTP {r.status_code}): {msg}"
            raise Exception(error_msg)
