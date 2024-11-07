import os
os.environ["BACKEND_URL"] = "https://dev-platform-api.aixplain.com"
os.environ["BENCHMARKS_BACKEND_URL"] = "https://dev-platform-api.aixplain.com"
os.environ["MODELS_RUN_URL"] = "https://dev-models.aixplain.com/api/v1/execute"
os.environ["TEAM_API_KEY"] = "65a701f4ddcc6be76a68996bd29255b85d1e335faa8eb0cdd5ebf7d857214e90"



from aixplain.factories import PipelineFactory
pipeline = PipelineFactory.get("66e40c5d8ee4eeb80a3aa819")
result = pipeline.run("poem prompt")
print("RESULT")
print(result)