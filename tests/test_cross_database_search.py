import re

import pytest

from src.cross_database_search import (
    keep_tuple_with_most_infos,
    merge_article_ids,
    ncbi_search_and_fetch,
    pmc_search_and_fetch,
    pub_med_search_and_fetch,
    pubmed_pmc_cross_search,
)
from src.eutils_retrieval.api import NCBIDatabase, NCBIEndpoint

TEST_PUB_MED_ARTICLE_IDS = [
    {"idtype": "pubmed", "value": "36645057"},  # PubMed
    {"idtype": "doi", "value": "10.1080/0886022X.2022.2162419"},
    {"idtype": "pmc", "value": "PMC9848274"},  # PMC
    {"idtype": "pmcid", "idtypen": 5, "value": "pmc-id: PMC10189980;"},
]

TEST_PMC_ARTICLE_IDS = [
    {"idtype": "pmid", "value": "111111111"},  # PubMed
    {"idtype": "doi", "value": "10.1080/0886022X.2022.2162419"},
    {"idtype": "pmcid", "value": "PMC2222222222"},  # PMC
]


def test_ncbi_search_and_fetch_pmc_only(httpx_mock, search_and_store_response, tmp_path):
    # 1. Mock the search and store
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SEARCH.full_url() + "?.*"),
        method="GET",
        json=search_and_store_response,
    )
    # 2. Mock the fetch summary
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SUMMARY.full_url() + "?.*"),
        method="GET",
        json={"result": {"uids": ["bonjour"], "bonjour": {"articleids": TEST_PMC_ARTICLE_IDS}}},
    )

    result = ncbi_search_and_fetch(queries=["query"], db=NCBIDatabase.PMC, folder=tmp_path)
    assert result == [{"pmcid": "PMC2222222222", "pmid": "111111111"}]


def test_ncbi_search_and_fetch_pub_med_only(httpx_mock, search_and_store_response, tmp_path):
    # 1. Mock the search and store
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SEARCH.full_url() + "?.*"),
        method="GET",
        json=search_and_store_response,
    )
    # 2. Mock the fetch summary
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SUMMARY.full_url() + "?.*"),
        method="GET",
        json={"result": {"uids": ["bonjour"], "bonjour": {"articleids": TEST_PUB_MED_ARTICLE_IDS}}},
    )

    result = ncbi_search_and_fetch(queries=["query"], db=NCBIDatabase.PUB_MED, folder=tmp_path)
    assert result == [{"pmcid": "PMC9848274", "pmid": "36645057"}]


def test_pubmed_pmc_cross_search(httpx_mock, search_and_store_response, tmp_path):
    # 1. Mock the search and store
    for _ in range(2):
        httpx_mock.add_response(
            url=re.compile(NCBIEndpoint.SEARCH.full_url() + "?.*"),
            method="GET",
            json=search_and_store_response,
        )
    # 2. Mock the fetch summary (PMC is first)
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SUMMARY.full_url() + "?.*"),
        method="GET",
        json={"result": {"uids": ["bonjour"], "bonjour": {"articleids": TEST_PMC_ARTICLE_IDS}}},
    )
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SUMMARY.full_url() + "?.*"),
        method="GET",
        json={"result": {"uids": ["bonjour"], "bonjour": {"articleids": TEST_PUB_MED_ARTICLE_IDS}}},
    )

    result = pubmed_pmc_cross_search("query", folder=tmp_path)
    assert result == [
        {"pmcid": "PMC2222222222", "pmid": "111111111"},
        {"pmcid": "PMC9848274", "pmid": "36645057"},
    ]


def test_pub_med_search_and_fetch(httpx_mock, search_and_store_response, tmp_path):
    # 1. Mock the search and store
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SEARCH.full_url() + "?.*"),
        method="GET",
        json=search_and_store_response,
    )
    # 2. Mock the fetch summary
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SUMMARY.full_url() + "?.*"),
        method="GET",
        json={"result": {"uids": ["bonjour"], "bonjour": {"articleids": TEST_PUB_MED_ARTICLE_IDS}}},
    )

    result = pub_med_search_and_fetch(query="query", folder=tmp_path)
    assert result == [{"pmcid": "PMC9848274", "pmid": "36645057"}]


def test_pub_med_search_and_fetch_no_fetch_result(httpx_mock, search_and_store_response):
    # 1. Mock the search and store
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SEARCH.full_url() + "?.*"),
        method="GET",
        json=search_and_store_response,
    )
    # 2. Mock the fetch summary
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SUMMARY.full_url() + "?.*"),
        method="GET",
        json={"result": {}},
    )

    result = pub_med_search_and_fetch(query="query")
    assert result == []


def test_pub_med_search_and_fetch_no_search_result(httpx_mock, search_and_store_response_none):
    # 1. Mock the search and store
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SEARCH.full_url() + "?.*"),
        method="GET",
        json=search_and_store_response_none,
    )

    result = pub_med_search_and_fetch(query="query")
    assert result == []


def test_pmc_search_and_fetch(httpx_mock, search_and_store_response, tmp_path):
    # 1. Mock the search and store
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SEARCH.full_url() + "?.*"),
        method="GET",
        json=search_and_store_response,
    )
    # 2. Mock the fetch summary
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SUMMARY.full_url() + "?.*"),
        method="GET",
        json={"result": {"uids": ["bonjour"], "bonjour": {"articleids": TEST_PMC_ARTICLE_IDS}}},
    )

    result = pmc_search_and_fetch(query="query", folder=tmp_path)
    assert result == [{"pmcid": "PMC2222222222", "pmid": "111111111"}]


def test_pmc_search_and_fetch_no_search_result(httpx_mock, search_and_store_response_none):
    # 1. Mock the search and store
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SEARCH.full_url() + "?.*"),
        method="GET",
        json=search_and_store_response_none,
    )

    result = pmc_search_and_fetch(query="query")
    assert result == []


def test_pmc_search_and_fetch_no_fetch_result(httpx_mock, search_and_store_response):
    # 1. Mock the search and store
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SEARCH.full_url() + "?.*"),
        method="GET",
        json=search_and_store_response,
    )
    # 2. Mock the fetch summary
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SUMMARY.full_url() + "?.*"),
        method="GET",
        json={"result": {}},
    )

    result = pmc_search_and_fetch(query="query")
    assert result == []


def test_merge_article_ids():
    collection1 = [
        {"pmcid": 1, "pmid": "a"},
        {"pmcid": 2, "pmid": None},
        {"pmcid": 3, "pmid": None},
    ]
    collection2 = [
        {"pmcid": 1, "pmid": "a"},
        {"pmcid": None, "pmid": "a"},
        {"pmcid": 2, "pmid": "b"},
        {"pmcid": None, "pmid": "c"},
    ]
    expected = [
        {"pmcid": 3, "pmid": None},
        {"pmcid": None, "pmid": "c"},
        {"pmcid": 1, "pmid": "a"},
        {"pmcid": 2, "pmid": "b"},
    ]

    result = merge_article_ids(collection1, collection2)
    # list of dict is not sortable easily ...
    assert len(result) == len(expected)
    assert all(r in expected for r in result)


def test_merge_article_ids_no_duplication():
    collection1 = [{"pmcid": 1, "pmid": "a"}, {"pmcid": 3, "pmid": None}]
    collection2 = [{"pmcid": 2, "pmid": "b"}, {"pmcid": None, "pmid": "c"}]
    expected = [
        {"pmcid": 3, "pmid": None},
        {"pmcid": None, "pmid": "c"},
        {"pmcid": 1, "pmid": "a"},
        {"pmcid": 2, "pmid": "b"},
    ]

    result = merge_article_ids(collection1, collection2)
    # list of dict is not sortable easily ...
    assert len(result) == len(expected)
    assert all(r in expected for r in result)


def test_keep_tuple_with_most_infos():
    result = keep_tuple_with_most_infos(
        {
            ("a", "b"),
            ("a", None),  # duplicated first key
            ("aa", None),  # duplicated first key
            ("aa", "bb"),
            ("1", None),  #  not duplicated
            ("c", "d"),
            (None, "d"),  # duplicated second key
            (None, "dd"),  # duplicated second key
            ("cc", "dd"),
            (None, "2"),  #  not duplicated
            ("zz", "zz"),  #  not duplicated
        },
    )
    assert result == {
        ("a", "b"),
        ("aa", "bb"),
        ("c", "d"),
        ("cc", "dd"),
        ("1", None),
        (None, "2"),
        ("zz", "zz"),
    }


def test_keep_tuple_with_most_infos_error_duplicates():
    with pytest.raises(ValueError, match="Too many duplicates for 1st key=a"):
        keep_tuple_with_most_infos({("a", "b"), ("a", None), ("a", "c")})

    with pytest.raises(ValueError, match="Too many duplicates for 2nd key=b"):
        keep_tuple_with_most_infos({("a", "b"), ("aa", "b"), (None, "b")})
