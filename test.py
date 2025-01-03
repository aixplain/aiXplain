import os
os.environ["TEAM_API_KEY"] = "f8dcf228a8a0d2b85a800eabe8f73b9af89f571c668b7524ffe82fca83a95096"


Name = "agent test" 
Task = "Answer the questions" 


Tool = "640b517694bf816d35a59125" 

from aixplain.factories import AgentFactory
from aixplain.modules.agent import ModelTool

agent = AgentFactory.create(
	name=Name,
	description=Task,
	tools=[
		ModelTool(model=Tool),
	],
    llm_id="66b2708c6eb5635d1c71f611"
)
print("agent defined")




Query = "Hello"

agent_response = agent.run(Query)
print(vars(agent_response))