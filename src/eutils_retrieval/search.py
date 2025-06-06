from typing import NotRequired, TypedDict

from loguru import logger

from src.eutils_retrieval.api import NCBIDatabase, NCBIEndpoint, call_eutils

# Given by API endpoint when trying to retrieve more than 500 elements at once
MAX_ALLOWED_SUMMARY_RETRIEVAL = 500


class StorageInfos(TypedDict):
    """Minimal PMC search result needed to fetch stored articles."""

    db: NCBIDatabase
    total_results: int
    web_env: NotRequired[str]
    query_key: NotRequired[str]


class ArticleIds(TypedDict):
    """Article ids from both PMC and PubMed databases.

    Attributes:
        pmcid (str | None): id for PCM database
        pmid (str | None): id for PubMed database

    """

    pmcid: str | None
    pmid: str | None


def search_and_store(query: str, db: NCBIDatabase) -> StorageInfos | None:
    """Search `db` for articles based on query and ask to store them for later retrieval.

    Args:
        query (str): Search query string
        db (NCBIDatabase): database to search from

    Returns:
        StorageInfos: Information to retrieve requested data in storage

    Notes:
        See https://www.ncbi.nlm.nih.gov/books/NBK25500/#chapter1.Searching_a_Database
        -> Storing Search Results

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
    storage_infos: StorageInfos,
    max_allowed_elements: int = MAX_ALLOWED_SUMMARY_RETRIEVAL,
) -> dict | None:
    """Fetch all stored articles data requested in previous db query.

    Args:
        storage_infos (StorageInfos): Minimal infos needed to retrieve previously queried articles
        max_allowed_elements (int): Max number of elements allowed by the api endpoint to fetch data

    Returns:
        dict of all articles data, by uid + one key 'uids' that contains all uids used as key

    """
    all_articles: dict = {}

    total_elements = storage_infos["total_results"]
    limit = min(max_allowed_elements, total_elements)

    # Creates batches of fixed size `limit`, in order to reach `total_elements` by generating a
    # couple (offset, limit=MAX_ALLOWED_SUMMARY_RETRIEVAL) to the request
    for offset in range(0, total_elements, limit):
        logger.debug(
            f"Calling {storage_infos['db'].value} database for summary fetching "
            f"(from {offset} to {limit + offset}/{total_elements}).",
        )
        if stored_summaries := fetch_stored_articles_by_batch(
            storage_infos,
            offset=offset,
            limit=limit,
        ):
            all_articles = {
                **all_articles,
                **stored_summaries,
                "uids": [*all_articles.get("uids", []), *stored_summaries.get("uids", [])],
            }

    return all_articles


def fetch_stored_articles_by_batch(
    storage_infos: StorageInfos,
    offset: int = 0,
    limit: int = MAX_ALLOWED_SUMMARY_RETRIEVAL,
) -> dict | None:
    """Fetch stored articles data requested in previous db query, allowing for pagination.

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
