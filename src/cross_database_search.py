from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from src.eutils_retrieval.api import NCBIDatabase
from src.eutils_retrieval.extract import extract_all_db_article_ids
from src.eutils_retrieval.search import (
    ArticleIds,
    StorageInfos,
    fetch_all_stored_articles,
    search_and_store,
)
from utils import add_timer_and_logger, store_data_as_json

if TYPE_CHECKING:
    from collections.abc import Callable


def ncbi_search_and_fetch(
    queries: tuple[str, ...],
    db: tuple[NCBIDatabase, ...] | NCBIDatabase,
    folder: Path | None = None,
) -> list[ArticleIds]:
    """Search for all articles and fetch summary based on queries given.

    Will de-duplicate results to avoid redundancy across databases.

    Args:
        queries (list[str]): queries to find specific articles across databases.
        db (tuple[NCBIDatabase, ...] | NCBIDatabase): Databases source for article search.
        folder (Path, optional): can be given to store intermediate findings for each query.

    Returns:
        list[ArticleIds]: all article ids found based on queries.

    """
    search_method_by_db: Callable = {
        NCBIDatabase.PMC: pmc_search_and_fetch,
        NCBIDatabase.PUB_MED: pub_med_search_and_fetch,
    }.get(db, pubmed_pmc_cross_search)

    results = []
    db_label = db.value if isinstance(db, NCBIDatabase) else tuple(d.value for d in db)
    logger.info(
        f"Will run {len(queries)} queries on {db_label}",
    )
    for counter, query in enumerate(queries):
        prefix_log = f"({counter + 1}/{len(queries)}) "
        query_folder = folder / str(counter) if folder else None

        partial_results = search_method_by_db(query, query_folder, prefix_log=prefix_log)
        results.extend(partial_results)

    return merge_article_ids(results)


@add_timer_and_logger(task_description="PubMed and PMC databases cross-search")
def pubmed_pmc_cross_search(query: str, folder: Path | None = None) -> list[ArticleIds]:
    """Search for articles matching the query and optional date range.

    Args:
        query (str): Search query string
        folder (Path, optional): if given, store intermediate search from each db before merging

    Returns:
        list[ArticleIds]: List of dictionaries containing article information

    """
    pmc_article_ids = pmc_search_and_fetch(query, folder=folder)
    pub_med_article_ids = pub_med_search_and_fetch(query, folder=folder)

    return [*pmc_article_ids, *pub_med_article_ids]


@add_timer_and_logger(task_description="PMC database search and fetch")
def pmc_search_and_fetch(query: str, folder: Path | None = None) -> list[ArticleIds]:
    """Search PMC database for articles matching the given query.

    Args:
        query (str): Search query string
        folder (Path, optional): if given, store intermediate search from each db before merging

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

    pmc_article_ids = extract_all_db_article_ids(result_set, db=NCBIDatabase.PMC)

    logger.info(f"Found {len(pmc_article_ids)} articles in PMC")

    if folder:
        store_data_as_json(pmc_article_ids, folder / f"{NCBIDatabase.PMC.value}.json")

    return pmc_article_ids


@add_timer_and_logger(task_description="PubMed database search adn fetch")
def pub_med_search_and_fetch(query: str, folder: Path | None = None) -> list[ArticleIds]:
    """Search Pub Med database for articles matching the given query.

    Args:
        query (str): Search query string
        folder (Path, optional): if given, store intermediate search from each db before merging

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

    pub_med_article_ids = extract_all_db_article_ids(result_set, db=NCBIDatabase.PUB_MED)
    logger.info(f"Found {len(pub_med_article_ids)} articles in PubMed")

    if folder:
        store_data_as_json(pub_med_article_ids, folder / f"{NCBIDatabase.PUB_MED.value}.json")

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
        [
            {'id_1': 1, 'id_2': a},
            {'id_1': 3, 'id_2': Null},
            {'id_1': 2, 'id_2': b},
            {'id_1': Null, 'id_2': c}
        ]

    Returns:
        list (ArticleIds): unique couples of article identifiers in both databases

    """
    all_article_ids = []
    for article_ids_collection in article_ids_collections:
        all_article_ids.extend(article_ids_collection)

    original_nb_articles = len(all_article_ids)

    # using tuples to be able to hash when using set. unique hash is assured via
    # positioning and str type
    unique_article_ids: set = {
        (a["pmcid"], a["pmid"])
        for a in all_article_ids
        if (a["pmcid"] is not None or a["pmid"] is not None)
    }
    unique_article_ids = keep_tuple_with_most_infos(unique_article_ids)

    nb_unique_article_ids = len(unique_article_ids)
    if nb_unique_article_ids != original_nb_articles:
        logger.debug(
            f"Deduplication moved nb of articles from {original_nb_articles} "
            f"to {nb_unique_article_ids}",
        )
        return [ArticleIds(pmcid=t[0], pmid=t[1]) for t in unique_article_ids]

    logger.debug("No duplication detected.")
    return all_article_ids


def keep_tuple_with_most_infos(data: set[tuple[str | None, str | None]]) -> set[tuple[str, str]]:
    """Will deduplicate a collection of unique tuples with 2 elements.

     Keeping the one with no None value in it.

    Args:
        data (set[tuple]): data to deduplicate

    Returns:
        set[tuple]: data deduplicated

    Examples:
        >> data = {
            ("a", "b"), ("a", None),  # duplicated first key
            ("aa", "bb"), ("aa", None),  # duplicated first key
            ("1", None), #  not duplicated
            ("c", "d"), (None, "d"),  # duplicated second key
            ("cc", "dd"), (None, "dd"), # duplicated second key
            (None, "2"),  #  not duplicated
            ("zz", "zz"),  #  not duplicated
        }
        >> keep_tuple_with_most_infos(data)
        {("a", "b"), ("aa", "bb"), ("c", "d"), ("cc", "dd"), ("1", None), (None, "2"), ("zz", "zz")}

    """
    # identify all first keys that are duplicated
    duplicated_first_elements = [
        e for e, count in Counter(e[0] for e in data if e[0] is not None).items() if count > 1
    ]

    # identify all second keys that are duplicated
    duplicated_second_elements = [
        e for e, count in Counter(e[1] for e in data if e[1] is not None).items() if count > 1
    ]

    duplicated_element_by_first = {e: [] for e in duplicated_first_elements}
    duplicated_element_by_second = {e: [] for e in duplicated_second_elements}

    # Iterate only once to classify and identify whole tuple duplicates
    for element in data:
        if element[0] in duplicated_first_elements:
            duplicated_element_by_first[element[0]].append(element)
        if element[1] in duplicated_second_elements:
            duplicated_element_by_second[element[1]].append(element)

    # 1. Remove duplicates for 1st key
    max_duplicates_allowed = 2
    # since tuples are all unique, if the number of duplicates is greater than 2,
    # there are multiple ids for the same article in a db ?!
    for duplicated_first_element, duplicates in duplicated_element_by_first.items():
        # since tuples are all unique, there are multiple ids for the same article in a db ?!
        if len(duplicates) > max_duplicates_allowed:
            msg = f"Too many duplicates for 1st key={duplicated_first_element}\n{duplicates}"
            raise ValueError(msg)

        # will choose duplicates that has the most values i.e.
        # for [(value, None), (value, other_value)] we will choose (value, other_value)
        # if duplicated, has only 2 duplicates
        if duplicates[0][1] is None:
            data.remove(duplicates[0])
        else:
            data.remove(duplicates[1])

    # 1. Remove duplicates for 2st key
    for duplicated_second_element, duplicates in duplicated_element_by_second.items():
        if len(duplicates) > max_duplicates_allowed:
            msg = (f"Too many duplicates for 2nd key={duplicated_second_element}\n{duplicates}",)
            raise ValueError(msg)

        # will choose duplicates that has the most values i.e.
        # for [(None, other_value), (value, other_value)] we will choose (value, other_value)
        # if duplicated, has only 2 duplicates
        if duplicates[0][0] is None:
            data.remove(duplicates[0])
        else:
            data.remove(duplicates[1])

    return data
