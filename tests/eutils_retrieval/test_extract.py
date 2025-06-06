import pytest

from eutils_retrieval.api import NCBIDatabase
from eutils_retrieval.extract import (
    extract_all_db_article_ids,
    extract_ids_from_pcm_article,
    extract_ids_from_pub_med_article,
)
from eutils_retrieval.search import ArticleIds


@pytest.mark.parametrize(
    ("article_data", "expected"),
    [
        ({"not the right key": 1}, {}),
        ({"articleids": [{"idtype": "pmcid", "value": "0"}]}, {}),
        (
            {"articleids": [{"idtype": "pmcid", "value": "PMC1"}]},
            ArticleIds(pmcid="PMC1", pmid=None),
        ),
        ({"articleids": [{"idtype": "pmid", "value": "1"}]}, ArticleIds(pmcid=None, pmid="1")),
        (
            {
                "articleids": [
                    {"idtype": "pmid", "value": "0"},
                    {"idtype": "pmcid", "value": "_OTHER_1"},
                ],
            },
            ArticleIds(pmcid="PMC_OTHER_1", pmid=None),
        ),
    ],
)
def test_extract_ids_from_pcm_article(article_data, expected):
    result = extract_ids_from_pcm_article(article_data)
    assert result == expected


@pytest.mark.parametrize(
    ("article_data", "expected"),
    [
        ({"not the right key": 1}, {}),
        ({"articleids": [{"idtype": "pubmed", "value": "0"}]}, {}),
        (
            {"articleids": [{"idtype": "pmc", "value": "PMC1"}]},
            ArticleIds(pmcid="PMC1", pmid=None),
        ),
        (
            {"articleids": [{"idtype": "pubmed", "value": "1"}]},
            ArticleIds(pmcid=None, pmid="1"),
        ),
        (
            {
                "articleids": [
                    {"idtype": "pubmed", "value": "0"},
                    {"idtype": "pmcid", "value": "_OTHER_1"},
                    {"idtype": "pmc", "value": "1"},
                ],
            },
            ArticleIds(pmcid="PMC1", pmid=None),
        ),
    ],
)
def test_extract_ids_from_pub_med_article(article_data, expected):
    result = extract_ids_from_pub_med_article(article_data)
    assert result == expected


def test_extract_all_article_ids():
    articles = {
        "uids": ["0", "1", "2", "PMC_OTHER_1"],
        "0": {"not the right key": 1},
        "1": {"articleids": [{"idtype": "pmid", "value": "1"}, {"idtype": "pmcid", "value": "1"}]},
        "PMC_OTHER_1": {"articleids": [{"idtype": "pmid", "value": "0"}]},
    }
    expected = [ArticleIds(pmcid="PMC1", pmid="1")]

    result = extract_all_db_article_ids(articles, db=NCBIDatabase.PMC)
    assert result == expected
