from aixplain.factories import PipelineFactory


def test_fallback_to_v2():
    pipeline = PipelineFactory.get("6750535166d4db27e14f07b1")
    response = pipeline.run(
        "https://homepage.ntu.edu.tw/~karchung/miniconversations/mc1.mp3"
    )
    assert response["version"] == "3.0"
    assert response["status"] == "SUCCESS"

    pipeline = PipelineFactory.get("6750535166d4db27e14f07b1")
    response = pipeline.run("<<INVALID INPUT>>")
    assert response["version"] == "2.0"
    assert response["status"] == "ERROR"
