from enum import Enum
from pathlib import Path
from typing import Annotated

import typer

from eutils_retrieval.api import NCBIDatabase
from eutils_retrieval.search import ArticleIds
from src.config import (
    UROLOGY_INDICATORS_FLAT,
    HEMOSTATIC_DEVICES_FLAT,
    HEMOSTATIC_DEVICES_MINI_FLAT,
    UROLOGY_INDICATORS_MINI_FLAT,
)
from src.eutils_retrieval.query import create_e_queries
from eutils_retrieval.cross_database_search import merge_article_ids, ncbi_search_and_fetch
import json
import time
from loguru import logger


SUBMISSION_RESULTS_FOLDER = Path(__file__).parent / "submission_results"


class DbNameArg(Enum):
    """CLi db name to use requests. typer does not support literals yet."""

    ALL = "all"
    PUB_MED = "pub_med"
    PMC = "pmc"


DB_NAME_MAPPING = {
    DbNameArg.ALL: (
        NCBIDatabase.PUB_MED,
        NCBIDatabase.PMC,
    ),
    DbNameArg.PUB_MED: NCBIDatabase.PUB_MED,
    DbNameArg.PMC: NCBIDatabase.PMC,
}


def main(
    mini: Annotated[
        bool,
        typer.Option(help="Use a small sample of data to build the request query instead of all."),
    ] = False,
    start_year: Annotated[int, typer.Option(help="Filter articles that only starts after")] = 2023,
    end_year: Annotated[int, typer.Option(help="Filter articles that only end before")] = 2023,
    intermediate: Annotated[
        bool,
        typer.Option(help="Store intermediate found article ids from databases for each query."),
    ] = False,
    db_name: Annotated[
        DbNameArg, typer.Option(help="Dbs to call for search. Default to all")
    ] = DbNameArg.ALL,
):
    db = DB_NAME_MAPPING[db_name]
    # Use mini to choose a small sample of the real data
    devices_indicators = (HEMOSTATIC_DEVICES_FLAT, UROLOGY_INDICATORS_FLAT)
    if mini:
        devices_indicators = (HEMOSTATIC_DEVICES_MINI_FLAT, UROLOGY_INDICATORS_MINI_FLAT)

    # Check that the folder exists, or creates it
    SUBMISSION_RESULTS_FOLDER.mkdir(exist_ok=True)

    start = time.time()
    # 1. determine all queries that corresponds to devices & indicators
    queries = create_e_queries(
        *devices_indicators,
        year_bounds=(start_year, end_year),
    )

    # 2. Search all articles and fetch summary across databases
    all_article_ids = ncbi_search_and_fetch(
        queries, db=db, folder=SUBMISSION_RESULTS_FOLDER if intermediate else None
    )

    # 3. Deduplicates article records
    merged_results = merge_article_ids(all_article_ids)
    logger.success(f"Found {len(merged_results)} total results, took {time.time() - start} seconds")

    # 4. Store results into a json file
    _store_results(merged_results, SUBMISSION_RESULTS_FOLDER)


def _store_results(results: list[ArticleIds], folder: Path):
    """Write all article ids into a JSON file inside `folder`"""
    result_file_path = folder / "retrieved_ids.json"

    logger.info(f"Writing results into {result_file_path}")
    with result_file_path.open("w") as json_writer:
        json.dump(results, json_writer, indent=4)


if __name__ == "__main__":
    typer.run(main)
