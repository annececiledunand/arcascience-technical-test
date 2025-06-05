import requests
from loguru import logger

from typing import TypedDict, NotRequired


PMC_DATABASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"


class PMCStorageInfos(TypedDict):
    """Explicits the return type of search and store method to always expect the correct arguments and types"""

    total_results: int
    web_env: NotRequired[str]
    query_key: NotRequired[str]


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

    logger.debug(f"Search and store params:\n{search_params}")

    session = requests.Session()
    url = f"{PMC_DATABASE_URL}esearch.fcgi"

    search_response = session.get(url, params=search_params)
    if search_response.status_code != 200:
        logger.error(
            f"Error searching PMC: ({search_response.status_code}){search_response.reason}"
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


def search_pmc(query: str) -> list[dict]:
    """
    Search PMC database for articles matching the given query.

    Args:
        query (str): Search query string

    Returns:
        list: List of dictionaries containing 'pmcid' and 'pmid' (when available)
    """
    session = requests.Session()

    try:
        # Search for IDs matching the query
        storage_infos: PMCStorageInfos = pmc_search_and_store(query)
        if storage_infos is None or storage_infos["total_results"] == 0:
            return []

        # Inefficient retrieval approach - doesn't use batching properly
        # This will work for small result sets but fail/be slow for large ones
        summary_params = {
            "db": "pmc",
            "query_key": storage_infos["query_key"],
            "WebEnv": storage_infos["web_env"],
            "retstart": 0,
            "retmax": storage_infos[
                "total_results"
            ],  # Tries to get all results at once - will often fail
            "retmode": "json",
        }

        summary_response = session.get(f"{PMC_DATABASE_URL}esummary.fcgi", params=summary_params)
        if summary_response.status_code != 200:
            logger.error(f"Error retrieving PMC results: {summary_response.status_code}")
            return []

        summary_data = summary_response.json()
        if "result" not in summary_data:
            logger.error("Unexpected response format")
            return []

        result_set = summary_data["result"]
        uids = result_set.get("uids", [])

        results = []
        for uid in uids:
            if uid not in result_set:
                continue
            article_data = result_set[uid]

            # Extract PMID if available
            pmid = None
            if "articleids" not in article_data:
                continue
            for article_id in article_data["articleids"]:
                if article_id["idtype"] == "pmid" and article_id["value"] != "0":
                    pmid = article_id["value"]

            # Format PMCID
            formatted_pmcid = uid
            if not str(formatted_pmcid).startswith("PMC"):
                formatted_pmcid = f"PMC{uid}"

            article_result = {"pmcid": formatted_pmcid, "pmid": pmid}
            results.append(article_result)

        return results

    # TODO catch exception less broadly
    except Exception:
        # logger.exception in loguru is a ERROR level message and capture exception in message
        logger.exception("Error processing PMC search")
        return []


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
