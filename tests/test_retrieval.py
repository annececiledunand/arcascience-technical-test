import json
import re

from src.eutils_retrieval.api import NCBIDatabase, NCBIEndpoint
from src.retrieval import STORE_RESULTS_FILE_NAME, ncbi_article_retrieval

TEST_PUB_MED_ARTICLE_IDS = [
    {"idtype": "pubmed", "value": "36645057"},  # PubMed
    {"idtype": "pmc", "value": "PMC9848274"},  # PMC
]
TEST_PUB_MED_ARTICLE_IDS_WITH_DUPLICATES = [
    {"idtype": "pubmed", "value": "666"},  # PubMed
    {"idtype": "pmc", "value": "0"},  # PMC here no PMC but has a PMC id in PubMed db
]

TEST_PMC_ARTICLE_IDS = [
    {"idtype": "pmid", "value": "111111111"},  # PubMed
    {"idtype": "pmcid", "value": "PMC2222222222"},  # PMC
]
TEST_PMC_ARTICLE_IDS_WITH_DUPLICATES = [
    {"idtype": "pmid", "value": "666"},  # PubMed
    {"idtype": "pmcid", "value": "PMC123"},  # PMC
]


def test_retrieval(httpx_mock, search_and_store_response, tmp_path):
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
        json={
            "result": {
                "uids": ["bonjour"],
                "pmc_only": {"articleids": TEST_PMC_ARTICLE_IDS},
                "duplicates": {"articleids": TEST_PMC_ARTICLE_IDS_WITH_DUPLICATES},
            },
        },
    )
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SUMMARY.full_url() + "?.*"),
        method="GET",
        json={
            "result": {
                "uids": ["bonjour"],
                "pub_med_only": {"articleids": TEST_PUB_MED_ARTICLE_IDS},
                "duplicates": {"articleids": TEST_PUB_MED_ARTICLE_IDS_WITH_DUPLICATES},
            },
        },
    )

    assert not (tmp_path / STORE_RESULTS_FILE_NAME).exists()
    ncbi_article_retrieval(
        [["device_1", "device_2"], ["indicator_1", "indicator_2"]],
        (2023, 2024),
        db=(NCBIDatabase.PMC, NCBIDatabase.PUB_MED),
        output_folder=tmp_path,
        store_intermediate_results=True,
    )

    with (tmp_path / STORE_RESULTS_FILE_NAME).open() as reader:
        result = json.load(reader)

    expected = [
        {"pmcid": "PMC2222222222", "pmid": "111111111"},
        {"pmcid": "PMC9848274", "pmid": "36645057"},
        {"pmcid": "PMC123", "pmid": "666"},
    ]
    assert len(result) == len(expected)
    assert all(r in expected for r in result)
