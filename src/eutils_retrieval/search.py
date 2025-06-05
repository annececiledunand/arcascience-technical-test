import requests
from loguru import logger


def search_pmc(query):
    """
    Search PMC database for articles matching the given query.

    Args:
        query (str): Search query string

    Returns:
        list: List of dictionaries containing 'pmcid' and 'pmid' (when available)
    """
    session = requests.Session()
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    # Search for IDs matching the query
    search_params = {
        "db": "pmc",
        "term": query,
        "usehistory": "y",
        "retmode": "json",
    }

    try:
        search_response = session.get(f"{base_url}esearch.fcgi", params=search_params)
        if search_response.status_code != 200:
            logger.error(f"Error searching PMC: {search_response.status_code}")
            return []

        search_data = search_response.json()
        total_results = int(search_data["esearchresult"]["count"])

        if total_results == 0:
            logger.info("No results found in PMC.")
            return []

        web_env = search_data["esearchresult"]["webenv"]
        query_key = search_data["esearchresult"]["querykey"]

        logger.success(f"Found {total_results} results in PMC.")

        # Inefficient retrieval approach - doesn't use batching properly
        # This will work for small result sets but fail/be slow for large ones
        summary_params = {
            "db": "pmc",
            "query_key": query_key,
            "WebEnv": web_env,
            "retstart": 0,
            "retmax": total_results,  # Tries to get all results at once - will often fail
            "retmode": "json",
        }

        summary_response = session.get(f"{base_url}esummary.fcgi", params=summary_params)
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


def search_pubmed_pmc(query, start_year=None, end_year=None):
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
