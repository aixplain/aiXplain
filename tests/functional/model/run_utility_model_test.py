from aixplain.factories import ModelFactory
from aixplain.modules.model.utility_model import UtilityModelInput
from aixplain.enums import DataType


def test_run_utility_model():
    inputs = [
        UtilityModelInput(name="inputA", description="input A is the only input", type=DataType.TEXT),
    ]

    output_description = "An example is 'test'"

    utility_model = ModelFactory.create_utility_model(
        name="test_script",
        description="This is a test script",
        inputs=inputs,
        code="def main(inputA: str):\n\treturn inputA",
        output_examples=output_description,
    )

    assert utility_model.id is not None
    assert utility_model.inputs == inputs
    assert utility_model.output_examples == output_description

    response = utility_model.run(data={"inputA": "test"})
    assert response.status == "SUCCESS"
    assert response.data == "test"

    utility_model.code = "def main(inputA: str):\n\treturn 5"
    utility_model.update()
    response = utility_model.run(data={"inputA": "test"})
    assert response.status == "SUCCESS"
    assert str(response.data) == "5"

    utility_model.delete()
