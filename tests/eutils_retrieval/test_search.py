import re
from http import HTTPStatus

import httpx
import pytest
from pytest_httpx import HTTPXMock

from src.eutils_retrieval.search import (
    PMC_DATABASE_URL,
    URL_SEARCH_TAIL,
    pmc_search_and_store,
    extract_one_article_ids,
    ArticleIds,
    extract_all_article_ids,
)


def test_pmc_search_and_store_ok(httpx_mock: HTTPXMock, search_and_store_response):
    httpx_mock.add_response(
        url=re.compile(PMC_DATABASE_URL + URL_SEARCH_TAIL + "?.*"),
        method="GET",
        json=search_and_store_response,
    )

    with httpx.Client():
        result = pmc_search_and_store("my query")
        assert result == {
            "total_results": 1,
            "query_key": "my_query_key",
            "web_env": "MCID_FAKE_UUID",
        }


def test_pmc_search_and_store_no_result(httpx_mock: HTTPXMock, search_and_store_response_none):
    """Handle no document found"""
    httpx_mock.add_response(
        url=re.compile(PMC_DATABASE_URL + URL_SEARCH_TAIL + "?.*"),
        method="GET",
        json=search_and_store_response_none,
    )

    with httpx.Client():
        result = pmc_search_and_store("my query")
        assert result == {
            "total_results": 0,
        }


def test_pmc_search_and_store_error(httpx_mock: HTTPXMock):
    """Should not break when any other code than 200 is given back"""
    httpx_mock.add_response(
        url=re.compile(PMC_DATABASE_URL + URL_SEARCH_TAIL + "?.*"),
        method="GET",
        status_code=HTTPStatus.IM_A_TEAPOT,
    )

    with httpx.Client():
        result = pmc_search_and_store("my query")
        assert result is None


@pytest.mark.parametrize(
    "uid, article_data, expected",
    (
        ("1", {"not the right key": 1}, {}),
        (
            "1",
            {"articleids": [{"idtype": "pmid", "value": "1"}]},
            ArticleIds(pmcid="PMC1", pmid="1"),
        ),
        (
            "PMC_OTHER_1",
            {"articleids": [{"idtype": "pmid", "value": "0"}]},
            ArticleIds(pmcid="PMC_OTHER_1", pmid=None),
        ),
    ),
)
def test_extract_one_article_ids(uid, article_data, expected):
    result = extract_one_article_ids(uid, article_data)
    assert result == expected


def test_extract_all_article_ids():
    articles = {
        "uids": ["0", "1", "2", "PMC_OTHER_1"],
        "0": {"not the right key": 1},
        "1": {"articleids": [{"idtype": "pmid", "value": "1"}]},
        "PMC_OTHER_1": {"articleids": [{"idtype": "pmid", "value": "0"}]},
    }
    expected = [ArticleIds(pmcid="PMC1", pmid="1"), ArticleIds(pmcid="PMC_OTHER_1", pmid=None)]

    result = extract_all_article_ids(articles)
    assert result == expected
