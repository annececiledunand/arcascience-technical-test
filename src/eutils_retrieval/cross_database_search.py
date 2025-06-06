import json
from pathlib import Path
from typing import Callable

from loguru import logger

from src.eutils_retrieval.api import NCBIDatabase
from src.eutils_retrieval.search import (
    ArticleIds,
    StorageInfos,
    search_and_store,
    fetch_all_stored_articles,
    extract_all_article_ids,
)
from utils import add_timer_and_logger


def ncbi_search_and_fetch(
    queries: tuple[str, ...],
    db: tuple[NCBIDatabase, ...] | NCBIDatabase,
    folder: Path = None,
) -> list[ArticleIds]:
    """
    Search for all articles and fetch summary based on queries given. Will de-duplicate results to avoid redundancy across databases

    Args:
        queries (list[str]): queries to find specific articles across databases.
        db (tuple[NCBIDatabase, ...] | NCBIDatabase): Databases source for article search and retrieval.
        folder (Path, optional): can be given to store intermediate findings for each query.

    Returns:
        list[ArticleIds]: all article ids found based on queries.
    """
    search_method_by_db: Callable = {
        NCBIDatabase.PMC: pmc_search_and_fetch,
        NCBIDatabase.PUB_MED: pub_med_search_and_fetch,
    }.get(db, pubmed_pmc_cross_search)

    results = []
    logger.info(
        f"Will run {len(queries)} queries on {db.value if isinstance(db, NCBIDatabase) else tuple(d.value for d in db)}"
    )
    for counter, query in enumerate(queries):
        prefix_log = f"({counter + 1}/{len(queries)}) "
        query_folder = folder / str(counter) if folder else None

        partial_results = search_method_by_db(query, query_folder, prefix_log=prefix_log)
        results.extend(partial_results)
    return results


@add_timer_and_logger(task_description="PubMed and PMC databases cross-search")
def pubmed_pmc_cross_search(query: str, folder: Path = None) -> list[ArticleIds]:
    """
    Search for articles matching the query and optional date range.

    Args:
        query (str): Search query string
        folder (Path, optional): if given, store intermediate search from each db before merging

    Returns:
        list[ArticleIds]: List of dictionaries containing article information
    """

    def _store_intermediate_results(article_ids: list[ArticleIds], name: str):
        if folder:
            folder.mkdir(exist_ok=True)
            (folder / f"{name}.json").write_text(json.dumps(article_ids, indent=4))

    pmc_article_ids = pmc_search_and_fetch(query)
    _store_intermediate_results(pmc_article_ids, "pmc")

    pub_med_article_ids = pub_med_search_and_fetch(query)
    _store_intermediate_results(pub_med_article_ids, "pub_med")

    return [*pmc_article_ids, *pub_med_article_ids]


@add_timer_and_logger(task_description="PMC database search and fetch")
def pmc_search_and_fetch(query: str, *args, **kwargs) -> list[ArticleIds]:
    """
    Search PMC database for articles matching the given query.

    Args:
        query (str): Search query string

    Returns:
        list: List of dictionaries containing 'pmcid' and 'pmid' (when available)
    """

    storage_infos: StorageInfos = search_and_store(query, db=NCBIDatabase.PMC)
    if storage_infos is None or storage_infos["total_results"] == 0:
        logger.info("Found no articles in PMC")
        return []

    result_set = fetch_all_stored_articles(storage_infos)

    if not result_set:
        logger.info("Found no articles in PMC")
        return []

    pmc_article_ids = extract_all_article_ids(result_set, db=NCBIDatabase.PMC)

    logger.info(f"Found {len(pmc_article_ids)} articles in PMC")
    return pmc_article_ids


@add_timer_and_logger(task_description="PubMed database search adn fetch")
def pub_med_search_and_fetch(query: str, *args, **kwargs) -> list[ArticleIds]:
    """
    Search Pub Med database for articles matching the given query.

    Args:
        query (str): Search query string

    Returns:
        list: List of dictionaries containing 'pmcid' and 'pmid' (when available)
    """

    storage_infos: StorageInfos = search_and_store(query, db=NCBIDatabase.PUB_MED)
    if storage_infos is None or storage_infos["total_results"] == 0:
        logger.info("Found no articles in PubMed")
        return []

    result_set = fetch_all_stored_articles(storage_infos)

    if not result_set:
        logger.info("Found no articles in PubMed")
        return []

    pub_med_article_ids = extract_all_article_ids(result_set, db=NCBIDatabase.PUB_MED)
    logger.info(f"Found {len(pub_med_article_ids)} articles in PubMed")

    return pub_med_article_ids


@add_timer_and_logger("Merging and de-duplicating article ids from multiple sources")
def merge_article_ids(*article_ids_collections: list[ArticleIds]) -> list[ArticleIds]:
    """Retrieve when possible, all unique couple ids that identifies an article in both databases.
    Will erase full and partial duplicates by preferring full info to partial.

    Examples:
        >> merge_article_ids(
            [{'id_1': 1, 'id_2': a}, {'id_1': 2, 'id_2': Null}, {'id_1': 3, 'id_2': Null}]
            [{'id_1': Null, 'id_2': a}, {'id_1': 2, 'id_2': b}, {'id_1': Null, 'id_2': c}]
        )
        [{'id_1': 1, 'id_2': a}, {'id_1': 2, 'id_2': Null}, {'id_1': 2, 'id_2': b}, {'id_1': Null, 'id_2': c}]

    Returns:
        list (ArticleIds): unique couples of article identifiers in both databases
    """
    all_article_ids = []
    for article_ids_collection in article_ids_collections:
        all_article_ids.extend(article_ids_collection)

    original_nb_articles = len(all_article_ids)

    # using tuples to be able to hash when using set. unique hash is assured via positioning and str type
    unique_article_ids = set((a["pmcid"], a["pmid"]) for a in all_article_ids)
    nb_unique_article_ids = len(unique_article_ids)

    if nb_unique_article_ids != original_nb_articles:
        logger.debug(
            f"Deduplication moved nb of articles from {original_nb_articles} to {nb_unique_article_ids}"
        )
        return list(ArticleIds(pmcid=t[0], pmid=t[1]) for t in unique_article_ids)

    logger.debug("No duplication detected.")
    return all_article_ids
