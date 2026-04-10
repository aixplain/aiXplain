from aixplain import Aixplain

prompt = """You are evaluating the correctness of the Assistant's response.You are given a task and a candidate response. Is this a correct and accurate response to the task?   
  
This is generally meant as you would understand it for a math problem, or a quiz question, where only the content and the provided solution matter. Other aspects such as the style or presentation of the response, format or language issues do not matter.  
  
**IMPORTANT**: The tool output ALWAYS takes priority over your own knowledge.  
  
The output should be a well-formatted JSON instance that conforms to the JSON schema below.  
  
As an example, for the schema {{"properties": {{"foo": {{"title": "Foo", "description": "a list of strings", "type": "array", "items": {{"type": "string"}}}}}}, "required": ["foo"]}}  
the object {{"foo": ["bar", "baz"]}} is a well-formatted instance of the schema. The object {{"properties": {{"foo": ["bar", "baz"]}}}} is not well-formatted.  
  
Here is the output JSON schema:  
```  
{{"properties": {{"reasoning": {{"description": "step by step reasoning to derive the final answer, using no more than 250 words", "title": "Reasoning", "type": "string"}}, "score": {{"description": "score should be one of `Perfectly Correct`, `Partially Correct` or `Incorrect`", "enum": ["Perfectly Correct", "Partially Correct", "Incorrect"], "title": "Score", "type": "string"}}}}, "required": ["reasoning", "score"]}}  
```  
  
Do not return any preamble or explanations, return only a pure JSON string surrounded by triple backticks (```)."""

aix = Aixplain(
    api_key="c43c6f6a107fcd44289e818e111d144111efe6e5c8be960c4327e42dbcd7672a",
    backend_url="https://dev-platform-api.aixplain.com",
    model_url="https://dev-models.aixplain.com/api/v2/execute"
)

my_metric = aix.MetricTool.get("aixplain-benchmarking/test-run-metric/aixplain")
my_metric.agent_response_data_fields = aix.MetricTool.AgentResponseDataFields(query=True, trace=True, output=True)
my_metric.additional_input_prompt = prompt

my_agent = aix.Agent.get("aixplain-benchmarking/web-serach-agent/aixplain") 
# agent_response = my_agent.run("Where did the inauguration programme take place for the Kolkata metro flag-off on August 22, 2025?")
# metric_result = my_metric.measure(agent_response.data)

query_list = ["Where did the inauguration programme take place for the Kolkata metro flag-off on August 22, 2025?"]*2
dataset = aix.AgentEvaluationExecutor.create_dataset_from_list(query_list)

evaluator = aix.AgentEvaluationExecutor()
agents = [my_agent]
metrics = [my_metric]
results = evaluator.evaluate(agents, dataset, metrics)
results.to_csv("results.csv", index=False)