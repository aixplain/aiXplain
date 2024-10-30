from aixplain.modules.agent import ModelTool, PipelineTool
from aixplain.factories import AgentFactory
from aixplain.factories import TeamAgentFactory

model_tool = ModelTool(
    model="66b2708c6eb5635d1c71f611"
)


agent = AgentFactory.create(
    name="agent delete test error 2",
    tools=[
        model_tool,
    ],
    description="desc",
    llm_id="66b2708c6eb5635d1c71f611",
)

team = TeamAgentFactory.create(
    name="agent team for delete 2test",
    description="desc",
    agents=[
        agent
    ],
    llm_id="66b2708c6eb5635d1c71f611"
)

print(agent.delete())