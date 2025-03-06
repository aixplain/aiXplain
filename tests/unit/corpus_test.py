from aixplain.factories import CorpusFactory
import pytest
import requests_mock
from urllib.parse import urljoin
from aixplain.utils import config


def test_get_corpus_error_response():
    with requests_mock.Mocker() as mock:
        corpus_id = "invalid_corpus_id"
        url = urljoin(config.BACKEND_URL, f"sdk/corpora/{corpus_id}/overview")
        headers = {"Authorization": f"Token {config.AIXPLAIN_API_KEY}", "Content-Type": "application/json"}

        error_response = {"message": "Not Found"}
        mock.get(url, headers=headers, json=error_response, status_code=404)

        with pytest.raises(Exception) as excinfo:
            CorpusFactory.get(corpus_id=corpus_id)

        assert "Corpus GET Error: Status 404 - {'message': 'Not Found'}" in str(excinfo.value)


def test_list_corpus_error_response():
    with requests_mock.Mocker() as mock:
        url = urljoin(config.BACKEND_URL, "sdk/corpora/paginate")
        headers = {"Authorization": f"Token {config.AIXPLAIN_API_KEY}", "Content-Type": "application/json"}

        error_response = {"message": "Internal Server Error"}
        mock.post(url, headers=headers, json=error_response, status_code=500)

        with pytest.raises(Exception) as excinfo:
            CorpusFactory.list(query="test_query", page_number=0, page_size=20)

        assert "Corpus List Error: Status 500 - {'message': 'Internal Server Error'}" in str(excinfo.value)
