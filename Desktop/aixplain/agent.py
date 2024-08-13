from aixplain.factories import AgentFactory, ModelFactory
from aixplain.modules.agent import ModelTool, PipelineTool
from aixplain.enums import Function, Supplier

# Define the tools
# ssmodel = ModelFactory.get("618ba6e5e2e1a9153ca2a3a5")
# print("functions",ssmodel.function)
speech_synthesis_tool = ModelTool(function=Function.SPEECH_SYNTHESIS)

ner_tool = ModelTool(
    function=Function.NAMED_ENTITY_RECOGNITION,
    supplier=Supplier.MICROSOFT
)


#Make a pipeline to use here, this one isn't public, public pipelines aren't avaible on aixplain
text_analysis_pipeline_tool = PipelineTool(
    description="Analyses text. It provides outputs for Topic Classification, Sentiment Analysis and Entity Linking.",
    pipeline="666198a06f1b3d64bd8f8dcc"
)

# Create the agent
agent = AgentFactory.create(
    name="Text Analysis Agent",
    tools=[
        speech_synthesis_tool,
        ner_tool,
        text_analysis_pipeline_tool,
    ],
    description="A multilingual agent that analyses text.",
    llm_id="6646261c6eb563165658bbb1" # GPT-4o
)


print(agent.__dict__)
