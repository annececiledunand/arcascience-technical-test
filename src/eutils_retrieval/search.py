from loguru import logger

from typing import TypedDict, NotRequired

from eutils_retrieval.api import call_eutils, NCBIEndpoint, NCBIDatabase

# Given by API endpoint when trying to retrieve more than 500 elements at once
MAX_ALLOWED_SUMMARY_RETRIEVAL = 500


class StorageInfos(TypedDict):
    """Minimal PMC search result needed to fetch stored articles"""

    db: NCBIDatabase
    total_results: int
    web_env: NotRequired[str]
    query_key: NotRequired[str]


class ArticleIds(TypedDict):
    """Article ids from both PMC and PubMed databases"""

    pmcid: str | None
    pmid: str | None


def search_and_store(query: str, db: NCBIDatabase) -> StorageInfos | None:
    """
    Search PMC database and ask to store them for later retrieval, for articles matching the given query.

    Args:
        query (str): Search query string
        db (NCBIDatabase): database to search from

    Returns:
        StorageInfos: Information to retrieve requested data in storage

    Notes:
        See https://www.ncbi.nlm.nih.gov/books/NBK25500/#chapter1.Searching_a_Database -> Storing Search Results
    """
    search_params = {
        "db": db.value,
        "term": query,
        "usehistory": "y",  # here ask to store data
        "retmode": "json",
    }

    logger.debug(f"Calling {db.value} database for search and store.")
    search_data = call_eutils(NCBIEndpoint.SEARCH, search_params)
    total_results = int(search_data["esearchresult"]["count"])

    if total_results == 0:
        logger.debug(f"No results found in {db.value}.")
        return StorageInfos(total_results=0, db=db)

    logger.debug(f"Found {total_results} results in {db.value}. Storing them for future querying")

    return StorageInfos(
        db=db,
        total_results=total_results,
        web_env=search_data["esearchresult"]["webenv"],
        query_key=search_data["esearchresult"]["querykey"],
    )


def fetch_all_stored_articles(
    storage_infos: StorageInfos, max_allowed_elements: int = MAX_ALLOWED_SUMMARY_RETRIEVAL
) -> dict | None:
    """Fetch all stored articles data requested in previous db query

    Args:
        storage_infos (StorageInfos): Minimal infos needed to retrieve previously queried articles
        max_allowed_elements (int): Max number of elements allowed by the api endpoint to fetch data

    Returns:
        dict of all articles data, by uid + one key 'uids' that contains all uids used as key
    """

    all_articles: dict = {}

    total_elements = storage_infos["total_results"]
    limit = total_elements if total_elements < max_allowed_elements else max_allowed_elements

    # Creates batches of fixed size `limit`, in order to reach `total_elements` by generating a couple
    # (offset, limit=MAX_ALLOWED_SUMMARY_RETRIEVAL) to the request
    for offset in range(0, total_elements, limit):
        logger.debug(
            f"Calling {storage_infos['db'].value} database for summary fetching (from {offset} to {limit + offset}/{total_elements})."
        )
        if stored_summaries := fetch_stored_articles_by_batch(
            storage_infos, offset=offset, limit=limit
        ):
            all_articles = {
                **all_articles,
                **stored_summaries,
                "uids": [*all_articles.get("uids", []), *stored_summaries.get("uids", [])],
            }

    return all_articles


def fetch_stored_articles_by_batch(
    storage_infos: StorageInfos, offset: int = 0, limit: int = MAX_ALLOWED_SUMMARY_RETRIEVAL
) -> dict | None:
    """Fetch stored articles data requested in previous db query, starting from a specific offset to a given limit.

    Args:
        storage_infos (StorageInfos): Minimal infos needed to retrieve previously queried articles
        offset (int): offset to start fetching the stored article infos
        limit (int): max number of article infos to fetch in one request.

    Returns:
        dict of all articles data, by uid + one key 'uids' that contains all uids used as key
    """

    summary_params = {
        "db": storage_infos["db"].value,
        "query_key": storage_infos["query_key"],
        "WebEnv": storage_infos["web_env"],
        "retstart": offset,
        "retmax": limit,
        "retmode": "json",
    }
    summary_data = call_eutils(NCBIEndpoint.SUMMARY, summary_params)

    if "result" not in summary_data:
        logger.error(f"Unexpected response format\n{summary_data}")
        return None

    return summary_data.get("result")


def extract_all_article_ids(articles: dict, db: NCBIDatabase) -> list[ArticleIds]:
    """Extract and format PubMed and PMC ids for a given article

    Args:
        db (NCBIDatabase): Database giving its ids. Format and naming differs from db to db.
        articles (dict): all articles data in database. Has one key `uids` with list of uids (str) as value, other keys are `uid` with {article_data_dict} as value

    Returns:
        list of ArticleIds
    """
    uids = articles.pop("uids")  # uids key with list of all uids as key:value in dict
    if set(uids) != set(articles.keys()):
        logger.warning(  # pragma: no cover
            f"Difference between results and uids list given\n"
            f"Uids given in list: {len(set(uids))}\n"
            f"Uids as keys for result: {len(set(articles.keys()))}"
        )

    extract_article_ids_method = {
        NCBIDatabase.PUB_MED: extract_ids_from_pub_med_article,
        NCBIDatabase.PMC: extract_ids_from_pcm_article,
    }[db]

    results = []
    for uid, article_data in articles.items():
        if article_result := extract_article_ids_method(article_data):
            results.append(article_result)

    return results


def extract_ids_from_pcm_article(article_data: dict) -> ArticleIds:
    """Extract and format PubMed and PMC ids for a given article in PCM database

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
    """Extract and format PubMed and PMC ids for a given article in PCM database

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
