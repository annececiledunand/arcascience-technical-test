import json
import time
from pathlib import Path

from loguru import logger

from src.eutils_retrieval.api import NCBIDatabase
from src.eutils_retrieval.cross_database_search import ncbi_search_and_fetch, merge_article_ids
from src.eutils_retrieval.query import create_e_queries
from src.eutils_retrieval.search import ArticleIds


def ncbi_article_retrieval(
    devices_indicators: tuple[list[str], list[str]],
    year_bounds: tuple[int | None, int | None],
    db: tuple[NCBIDatabase, ...] | NCBIDatabase,
    output_folder: Path,
    store_intermediate_results: bool = False,
):
    """
    Main method to retrieve article ids from NCBI Databases.

    Args:
        devices_indicators (tuple of list): List of hemostatic devices and related terms, urology indicators and related terms
        year_bounds (tuple[int, int]): Filters to apply to search query (start_date, end_date). Both are optionals.
        db (tuple[NCBIDatabase, ...] | NCBIDatabase): Databases source for article search and retrieval.
        output_folder (Path, optional): can be given to store intermediate findings for each query.
        store_intermediate_results (bool):store intermediate findings for each query and db into output folder sub folder.
    """
    start = time.time()
    # 1. determine all queries that corresponds to devices & indicators
    queries = create_e_queries(
        *devices_indicators,
        year_bounds=year_bounds,
    )

    # 2. Search all articles and fetch summary across databases
    intermediate_folder = None
    if store_intermediate_results:
        intermediate_folder = output_folder / "intermediate_results"
        intermediate_folder.mkdir(exist_ok=True)

    all_article_ids = ncbi_search_and_fetch(queries, db=db, folder=intermediate_folder)

    # 3. Deduplicates article records
    merged_results = merge_article_ids(all_article_ids)
    logger.success(f"Found {len(merged_results)} total results, took {time.time() - start} seconds")

    # 4. Store results into a json file
    _store_results(merged_results, output_folder)


def _store_results(results: list[ArticleIds], folder: Path):
    """Write all article ids into a JSON file inside `folder`"""
    result_file_path = folder / "retrieved_ids.json"

    logger.info(f"Writing results into {result_file_path}")
    with result_file_path.open("w") as json_writer:
        json.dump(results, json_writer, indent=4)
