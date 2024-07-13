__author__ = "lucaspavanelli"

"""
Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import json
from dotenv import load_dotenv

load_dotenv()
from aixplain.factories import AgentFactory
from aixplain.modules.agent import ModelTool, PipelineTool
from aixplain.enums.supplier import Supplier

import pytest

RUN_FILE = "tests/functional/agent/data/agent_test_end2end.json"


def read_data(data_path):
    return json.load(open(data_path, "r"))


@pytest.fixture(scope="module", params=read_data(RUN_FILE))
def run_input_map(request):
    return request.param


def test_end2end(run_input_map):
    tools = []
    if "model_tools" in run_input_map:
        for tool in run_input_map["model_tools"]:
            for supplier in Supplier:
                if tool["supplier"] is not None and tool["supplier"].lower() in [
                    supplier.value["code"].lower(),
                    supplier.value["name"].lower(),
                ]:
                    tool["supplier"] = supplier
                    break
            tools.append(ModelTool(function=tool["function"], supplier=tool["supplier"]))
    if "pipeline_tools" in run_input_map:
        for tool in run_input_map["pipeline_tools"]:
            tools.append(PipelineTool(description=tool["description"], pipeline=tool["pipeline_id"]))
    print(f"Creating agent with tools: {tools}")
    agent = AgentFactory.create(name=run_input_map["agent_name"], llm_id=run_input_map["llm_id"], tools=tools)
    print(f"Agent created: {agent.__dict__}")
    print("Running agent")
    response = agent.run(query=run_input_map["query"])
    print(f"Agent response: {response}")
    assert response is not None
    assert response["completed"] is True
    assert response["status"].lower() == "success"
    assert "data" in response
    assert response["data"]["session_id"] is not None
    assert response["data"]["output"] is not None
    print("Deleting agent")
    agent.delete()


def test_list_agents():
    agents = AgentFactory.list()
    assert "results" in agents
    agents_result = agents["results"]
    assert type(agents_result) is list
