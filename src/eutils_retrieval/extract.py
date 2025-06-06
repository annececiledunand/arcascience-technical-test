from loguru import logger

from src.eutils_retrieval.api import NCBIDatabase
from src.eutils_retrieval.search import ArticleIds


def extract_all_db_article_ids(articles: dict, db: NCBIDatabase) -> list[ArticleIds]:
    """Extract and format PubMed and PMC ids for a given article.

    Args:
        db (NCBIDatabase): Database giving its ids. Format and naming differs from db to db.
        articles (dict): all articles data in database. Has one key `uids` with
            list of uids (str) as value, other keys are `uid` with {article_data_dict} as value

    Returns:
        list of ArticleIds

    """
    uids = articles.pop("uids")  # uids key with list of all uids as key:value in dict
    if set(uids) != set(articles.keys()):
        logger.warning(  # pragma: no cover
            f"Difference between results and uids list given\n"
            f"Uids given in list: {len(set(uids))}\n"
            f"Uids as keys for result: {len(set(articles.keys()))}",
        )

    extract_article_ids_method = {
        NCBIDatabase.PUB_MED: extract_ids_from_pub_med_article,
        NCBIDatabase.PMC: extract_ids_from_pcm_article,
    }[db]

    results = [extract_article_ids_method(article_data) for article_data in articles.values()]
    return list(filter(None, results))


def extract_ids_from_pcm_article(article_data: dict) -> ArticleIds:
    """Extract and format PubMed and PMC ids for a given article in PCM database.

    Args:
        article_data (dict): all data in PMC database related to the article

    Returns:
        ArticleIds

    Notes:
        {...
        'articleids': [
            {'idtype': 'pmid', 'value': '36645057'},  # PubMed
            {'idtype': 'doi', 'value': '10.1080/0886022X.2022.2162419'},
            {'idtype': 'pmcid', 'value': 'PMC9848274'}
        ]
        ...}

    """
    # Extract PMID if available
    pmid, pmcid = None, None
    if "articleids" not in article_data:
        return {}

    for article_id in article_data["articleids"]:
        if article_id["idtype"] == "pmid" and article_id["value"] != "0":
            pmid = article_id["value"]
        if article_id["idtype"] == "pmcid" and article_id["value"] != "0":
            pmcid = article_id["value"]
            if not str(pmcid).startswith("PMC"):
                pmcid = f"PMC{pmcid}"

    if not pmcid and not pmid:
        return {}

    return ArticleIds(pmcid=pmcid, pmid=pmid)


def extract_ids_from_pub_med_article(article_data: dict) -> ArticleIds:
    """Extract and format PubMed and PMC ids for a given article in PCM database.

    Args:
        article_data (dict): all data in PMC database related to the article

    Returns:
        ArticleIds

    Notes:
        {...
        'articleids': [
            {'idtype': 'pubmed', 'value': '36645057'},  # PubMed
            {'idtype': 'doi', 'value': '10.1080/0886022X.2022.2162419'},
            {'idtype': 'pmc', 'value': 'PMC9848274'}  # PMC
            {'idtype': 'pmcid', 'idtypen': 5, 'value': 'pmc-id: PMC10189980;'}
        ]
        ...}

    """
    # Extract PMID if available
    pmid, pmcid = None, None
    if "articleids" not in article_data:
        return {}

    for article_id in article_data["articleids"]:
        if article_id["idtype"] == "pubmed" and article_id["value"] != "0":
            pmid = article_id["value"]
        if article_id["idtype"] == "pmc" and article_id["value"] != "0":
            pmcid = article_id["value"]
            if not str(pmcid).startswith("PMC"):
                pmcid = f"PMC{pmcid}"

    if not pmcid and not pmid:
        return {}

    return ArticleIds(pmcid=pmcid, pmid=pmid)
