import re
from http import HTTPStatus
from http.client import HTTPException

import httpx
import pytest
from httpx import URL
from pytest_httpx import HTTPXMock

from eutils_retrieval.api import NCBIEndpoint
from src.eutils_retrieval.search import (
    pmc_search_and_store,
    extract_one_article_ids,
    ArticleIds,
    extract_all_article_ids,
    PMCStorageInfos,
    fetch_all_stored_articles,
    fetch_stored_articles_by_batch,
)


def test_pmc_search_and_store_ok(httpx_mock: HTTPXMock, search_and_store_response):
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SEARCH.full_url() + "?.*"),
        method="GET",
        json=search_and_store_response,
    )

    result = pmc_search_and_store("my query")
    assert result == {
        "total_results": 1,
        "query_key": "my_query_key",
        "web_env": "MCID_FAKE_UUID",
    }


def test_pmc_search_and_store_no_result(httpx_mock: HTTPXMock, search_and_store_response_none):
    """Handle no document found"""
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SEARCH.full_url() + "?.*"),
        method="GET",
        json=search_and_store_response_none,
    )

    result = pmc_search_and_store("my query")
    assert result == {
        "total_results": 0,
    }


def test_pmc_search_and_store_error(httpx_mock: HTTPXMock):
    """Should not break when any other code than 200 is given back"""
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SEARCH.full_url() + "?.*"),
        method="GET",
        status_code=HTTPStatus.IM_A_TEAPOT,
    )

    with pytest.raises(HTTPException):
        pmc_search_and_store("my query")


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


def test_fetch_all_stored_articles(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SUMMARY.full_url() + "?.*"),
        method="GET",
        json={"result": {"uids": ["bonjour"], "bonjour": 2}},
    )

    storage_infos = PMCStorageInfos(query_key="query_key", web_env="web_env", total_results=10)

    result = fetch_all_stored_articles(storage_infos)
    assert result == {"uids": ["bonjour"], "bonjour": 2}
    assert httpx_mock.get_request().url == URL(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pmc&query_key=query_key&WebEnv=web_env&retstart=0&retmax=10&retmode=json"
    )


def test_fetch_stored_articles_by_batch(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SUMMARY.full_url() + "?.*"),
        method="GET",
        json={"result": {"uids": ["bonjour"], "bonjour": 2}},
    )

    storage_infos = PMCStorageInfos(query_key="query_key", web_env="web_env", total_results=10)

    result = fetch_stored_articles_by_batch(storage_infos, offset=7, limit=11)
    assert result == {"uids": ["bonjour"], "bonjour": 2}
    assert httpx_mock.get_request().url == URL(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pmc&query_key=query_key&WebEnv=web_env&retstart=7&retmax=11&retmode=json"
    )


def test_fetch_stored_articles_by_batch_retry_ok(httpx_mock: HTTPXMock):
    # Tests that endpoint was retried after timeout and still got correct result since only 2 timeout instead of MAX_RETRY=3
    httpx_mock.add_exception(
        exception=httpx.ReadTimeout("Unable to read within timeout"),
        url=re.compile(NCBIEndpoint.SUMMARY.full_url() + "?.*"),
        method="GET",
    )
    httpx_mock.add_exception(
        exception=httpx.ReadTimeout("Unable to read within timeout"),
        url=re.compile(NCBIEndpoint.SUMMARY.full_url() + "?.*"),
        method="GET",
    )
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SUMMARY.full_url() + "?.*"),
        method="GET",
        json={"result": {"uids": ["bonjour"], "bonjour": 2}},
    )

    storage_infos = PMCStorageInfos(query_key="query_key", web_env="web_env", total_results=10)

    result = fetch_stored_articles_by_batch(storage_infos, offset=7, limit=11)
    assert result == {"uids": ["bonjour"], "bonjour": 2}

    # check called 3 times (2 retry) the correct url
    requests_made = httpx_mock.get_requests()
    assert len(requests_made) == 3
    assert all(
        r.url
        == URL(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pmc&query_key=query_key&WebEnv=web_env&retstart=7&retmax=11&retmode=json"
        )
        for r in requests_made
    )


def test_fetch_stored_articles_by_batch_retry_fail(httpx_mock: HTTPXMock):
    # Tests that endpoint was too many times retried after timeout
    for _ in range(4):
        httpx_mock.add_exception(
            exception=httpx.ReadTimeout("Unable to read within timeout"),
            url=re.compile(NCBIEndpoint.SUMMARY.full_url() + "?.*"),
            method="GET",
        )

    storage_infos = PMCStorageInfos(query_key="query_key", web_env="web_env", total_results=10)
    with pytest.raises(httpx.TimeoutException):
        result = fetch_stored_articles_by_batch(storage_infos, offset=7, limit=11)
        assert result is None

    # check called 4 times (3 retry) the correct url
    requests_made = httpx_mock.get_requests()
    assert len(requests_made) == 4
    assert all(
        r.url
        == URL(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pmc&query_key=query_key&WebEnv=web_env&retstart=7&retmax=11&retmode=json"
        )
        for r in requests_made
    )


def test_fetch_all_stored_articles_with_batch(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SUMMARY.full_url() + "?.*"),
        method="GET",
        json={"result": {"uids": ["bonjour"], "bonjour": 1}},
    )
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SUMMARY.full_url() + "?.*"),
        method="GET",
        json={"result": {"uids": ["hello"], "hello": 2}},
    )

    storage_infos = PMCStorageInfos(query_key="query_key", web_env="web_env", total_results=2)

    result = fetch_all_stored_articles(storage_infos, max_allowed_elements=1)
    # check that the batching method is called two times
    assert result == {"uids": ["bonjour", "hello"], "bonjour": 1, "hello": 2}


def test_fetch_all_stored_articles_no_result(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SUMMARY.full_url() + "?.*"),
        method="GET",
        json="bonjour",
    )

    storage_infos = PMCStorageInfos(query_key="query_key", web_env="web_env", total_results=10)

    result = fetch_all_stored_articles(storage_infos)
    assert result == {}


def test_fetch_all_stored_articles_error(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SUMMARY.full_url() + "?.*"),
        method="GET",
        status_code=HTTPStatus.IM_A_TEAPOT,
    )

    storage_infos = PMCStorageInfos(query_key="query_key", web_env="web_env", total_results=10)
    with pytest.raises(HTTPException):
        fetch_all_stored_articles(storage_infos)
