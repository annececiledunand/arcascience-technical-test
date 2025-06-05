from http import HTTPStatus

import httpx
from httpx_retries import RetryTransport, Retry
from loguru import logger

from typing import TypedDict, NotRequired


PMC_DATABASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
URL_SEARCH_TAIL = "esearch.fcgi"
URL_SUMMARY_TAIL = "esummary.fcgi"

MAX_ALLOWED_SUMMARY_RETRIEVAL = 500


class PMCStorageInfos(TypedDict):
    """Minimal PMC search result needed to fetch stored articles"""

    total_results: int
    web_env: NotRequired[str]
    query_key: NotRequired[str]


class ArticleIds(TypedDict):
    """Article ids from both PMC and PubMed databases"""

    pmcid: str
    pmid: str | None


TRANSPORT_SEARCH_ENDPOINT = RetryTransport(retry=Retry(total=2, backoff_factor=0.5))


def pmc_search_and_store(query: str) -> PMCStorageInfos | None:
    """
    Search PMC database and ask to store them for later retrieval, for articles matching the given query.

    Args:
        query (str): Search query string

    Returns:
        PMCStorageInfos: Information to retrieve requested data in storage

    Notes:
        See https://www.ncbi.nlm.nih.gov/books/NBK25500/#chapter1.Searching_a_Database -> Storing Search Results
    """
    search_params = {
        "db": "pmc",
        "term": query,
        "usehistory": "y",  # here ask to store data
        "retmode": "json",
    }

    url = f"{PMC_DATABASE_URL}{URL_SEARCH_TAIL}"

    with httpx.Client(transport=TRANSPORT_SEARCH_ENDPOINT) as client:
        search_response = client.get(url, params=search_params)

    if search_response.status_code == HTTPStatus.REQUEST_URI_TOO_LONG:
        logger.error(
            f"Error while searching and storing PMC db: {HTTPStatus.REQUEST_URI_TOO_LONG} ({len(str(search_response.request.url))} chars in URL)"
        )
        return None

    if search_response.status_code != HTTPStatus.OK:
        logger.error(
            f"Error searching PMC: ({search_response.status_code}){search_response.reason_phrase}"
        )
        return None  # todo: maybe raise exception here

    search_data = search_response.json()
    total_results = int(search_data["esearchresult"]["count"])

    if total_results == 0:
        logger.info("No results found in PMC.")
        return PMCStorageInfos(total_results=0)

    logger.success(f"Found {total_results} results in PMC. Storing them for future querying")

    return PMCStorageInfos(
        total_results=total_results,
        web_env=search_data["esearchresult"]["webenv"],
        query_key=search_data["esearchresult"]["querykey"],
    )


def fetch_all_stored_articles(
    storage_infos: PMCStorageInfos, max_allowed_elements: int = MAX_ALLOWED_SUMMARY_RETRIEVAL
) -> dict | None:
    """Fetch all stored articles data requested in previous db query

    Args:
        storage_infos (PMCStorageInfos): Minimal infos needed to retrieve previously queried articles
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
        if stored_summaries := fetch_stored_articles_by_batch(
            storage_infos, offset=offset, limit=limit
        ):
            all_articles = {
                **all_articles,
                **stored_summaries,
                "uids": [*all_articles.get("uids", []), *stored_summaries.get("uids", [])],
            }

    return all_articles


TRANSPORT_SUMMARY_ENDPOINT = RetryTransport(retry=Retry(total=3, backoff_factor=0.5))


def fetch_stored_articles_by_batch(
    storage_infos: PMCStorageInfos, offset: int = 0, limit: int = MAX_ALLOWED_SUMMARY_RETRIEVAL
) -> dict | None:
    """Fetch stored articles data requested in previous db query, starting from a specific offset to a given limit.

    Args:
        storage_infos (PMCStorageInfos): Minimal infos needed to retrieve previously queried articles
        offset (int): offset to start fetching the stored article infos
        limit (int): max number of article infos to fetch in one request.

    Returns:
        dict of all articles data, by uid + one key 'uids' that contains all uids used as key
    """

    summary_params = {
        "db": "pmc",
        "query_key": storage_infos["query_key"],
        "WebEnv": storage_infos["web_env"],
        "retstart": offset,
        "retmax": limit,
        "retmode": "json",
    }

    with httpx.Client(transport=TRANSPORT_SUMMARY_ENDPOINT) as client:
        summary_response = client.get(
            f"{PMC_DATABASE_URL}{URL_SUMMARY_TAIL}", params=summary_params
        )

    if summary_response.status_code != HTTPStatus.OK:
        logger.error(f"Error retrieving PMC results: {summary_response.status_code}")
        return None

    summary_data = summary_response.json()
    if "result" not in summary_data:
        logger.error(f"Unexpected response format\n{summary_response.text}")
        return None

    return summary_data.get("result")


def search_pmc(query: str) -> list[ArticleIds]:
    """
    Search PMC database for articles matching the given query.

    Args:
        query (str): Search query string

    Returns:
        list: List of dictionaries containing 'pmcid' and 'pmid' (when available)
    """

    try:
        # Search for IDs matching the query
        storage_infos: PMCStorageInfos = pmc_search_and_store(query)
        if storage_infos is None or storage_infos["total_results"] == 0:
            return []

        result_set = fetch_all_stored_articles(storage_infos)

        if not result_set:
            return []
        return extract_all_article_ids(result_set)

    # TODO catch exception less broadly
    except Exception:
        # logger.exception in loguru is a ERROR level message and capture exception in message
        logger.exception("Error processing PMC search")
        return []


def extract_all_article_ids(articles: dict) -> list[ArticleIds]:
    """Extract and format PubMed and PMC ids for a given article

    Args:
        articles (dict): all articles data in PMC database. Has one key `uids` with list of uids (str) as value, other keys are `uid` with {article_data_dict} as value

    Returns:
        list of ArticleIds
    """
    uids = articles.pop("uids")  # uids key with list of all uids as key:value in dict
    if set(uids) != set(articles.keys()):
        logger.warning(
            f"Difference between results and uids list given\n"
            f"Uids given in list: {len(set(uids))}\n"
            f"Uids as keys for result: {len(set(articles.keys()))}"
        )

    results = []
    for uid, article_data in articles.items():
        if article_result := extract_one_article_ids(uid, article_data):
            results.append(article_result)

    return results


def extract_one_article_ids(uid: str, article_data: dict) -> ArticleIds:
    """Extract and format PubMed and PMC ids for a given article

    Args:
        uid (str): PMC uid of the current article
        article_data (dict): all data in PMC database re lated to the article

    Returns:
        ArticleIds
    """
    # Extract PMID if available
    pmid = None
    if "articleids" not in article_data:
        return {}

    for article_id in article_data["articleids"]:
        if article_id["idtype"] == "pmid" and article_id["value"] != "0":
            pmid = article_id["value"]

    # Format PMCID
    formatted_pmcid = uid
    if not str(formatted_pmcid).startswith("PMC"):
        formatted_pmcid = f"PMC{uid}"

    return ArticleIds(pmcid=formatted_pmcid, pmid=pmid)


def search_pubmed_pmc(
    query: str, start_year: int | None = None, end_year: int | None = None
) -> list[dict]:
    """
    Search for articles matching the query and optional date range.

    Args:
        query (str): Search query string
        start_year (int, optional): Start year for filtering
        end_year (int, optional): End year for filtering

    Returns:
        list: List of dictionaries containing article information
    """
    # Add date range if specified
    if start_year or end_year:
        date_query = ""
        if start_year:
            date_query += f"{start_year}[PDAT]"
        if start_year and end_year:
            date_query += ":"
        if end_year:
            date_query += f"{end_year}[PDAT]"

        query = f"({query}) AND {date_query}"

    # Currently only searches PMC - PubMed support needed (not implemented)
    results = search_pmc(query)

    # Filter out entries with no identifiers
    filtered_results = [
        info for info in results if info["pmcid"] is not None or info["pmid"] is not None
    ]

    return filtered_results
