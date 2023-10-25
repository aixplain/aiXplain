import os

os.environ["BACKEND_URL"] = "https://dev-platform-api.aixplain.com"
os.environ["MODELS_RUN_URL"] = "https://dev-models.aixplain.com/api/v1/execute"
os.environ["PIPELINES_RUN_URL"] = "https://dev-platform-api.aixplain.com/assets/pipeline/execution/run"
os.environ["TEAM_API_KEY"] = "bf507a583959c6aa7e36c6e0136b6581fe3a5cb587b390ab7c99fea5428fd114"
# os.environ["TEAM_API_KEY"] = "298a708afd2083bdfa81f9e9cd27ceeadb79e9bd54cf8e555e3c853f7601721a"
from aixplain.factories import DatasetFactory, PipelineFactory, ModelFactory, FileFactory
from aixplain.enums import Function, Language, License


def main():
    r = FileFactory.create(local_path="en-pt.csv", is_temp=True)
    print(r)
    # models = ModelFactory.list(suppliers=Supplier.AWS)["results"]
    # models[0].supplier


if __name__ == "__main__":
    main()
