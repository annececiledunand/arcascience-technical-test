from pathlib import Path
from typing import Annotated

import typer

from src.config import (
    UROLOGY_INDICATORS_FLAT,
    HEMOSTATIC_DEVICES_FLAT,
    PMC_API_MAX_URI_LENGTH,
    HEMOSTATIC_DEVICES_MINI_FLAT,
    UROLOGY_INDICATORS_MINI_FLAT,
)
from src.eutils_retrieval.query import create_complete_combinations_queries
from src.eutils_retrieval.search import search_pubmed_pmc
import json
import time
from loguru import logger


SUBMISSION_RESULTS_FOLDER = Path(__file__).parent / "submission_results"


def main(
    mini: Annotated[
        bool,
        typer.Option(help="Use a small sample of data to build the request query instead of all."),
    ] = False,
    start_year: Annotated[int, typer.Option(help="Filter articles that only starts after")] = 2023,
    end_year: Annotated[int, typer.Option(help="Filter articles that only end before")] = 2023,
):
    if start_year > end_year:
        raise Exception("`start_year` cannot be bigger than `end_year`")

    # Use mini to choose a small sample of the real data
    devices_indicators = (HEMOSTATIC_DEVICES_FLAT, UROLOGY_INDICATORS_FLAT)
    if mini:
        devices_indicators = (HEMOSTATIC_DEVICES_MINI_FLAT, UROLOGY_INDICATORS_MINI_FLAT)

    logger.info("Determining the number of queries necessary to call PMC API")
    queries = create_complete_combinations_queries(
        *devices_indicators,
        query_max_length=PMC_API_MAX_URI_LENGTH,
    )

    results = []
    queries = tuple(queries)
    for counter, query in enumerate(queries):
        start = time.time()

        logger.info(f"({counter + 1}/{len(queries)}) Searching PMC")
        partial_results = search_pubmed_pmc(query, start_year=start_year, end_year=end_year)

        results.extend(partial_results)
        logger.info(
            f"({counter + 1}/{len(queries)}) Found {len(results)} results, took {time.time() - start} seconds"
        )

    logger.success(f"Found {len(results)} total results, took {time.time() - start} seconds")

    # Save the results to a JSON file
    SUBMISSION_RESULTS_FOLDER.mkdir(exist_ok=True)
    result_file_path = SUBMISSION_RESULTS_FOLDER / "retrieved_ids.json"

    logger.info(f"Writing results into {result_file_path}")
    with result_file_path.open("w") as json_writer:
        json.dump(results, json_writer, indent=4)


if __name__ == "__main__":
    typer.run(main)
