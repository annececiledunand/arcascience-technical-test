from pathlib import Path

from src.config import HEMOSTATIC_DEVICES_MINI_FLAT, UROLOGY_INDICATORS_MINI_FLAT
from src.eutils_retrieval.query import create_one_combination_query
from src.eutils_retrieval.search import search_pubmed_pmc
import json
import time
from loguru import logger


SUBMISSION_RESULTS_FOLDER = Path(__file__).parent / "submission_results"


def main():
    start = time.time()
    # Create the query
    # Note: This is using the mini (reduced) datasets for testing
    #  For the final solution, you should use the full datasets:
    #  HEMOSTATIC_DEVICES_FLAT and UROLOGY_INDICATORS_FLAT
    query = create_one_combination_query(HEMOSTATIC_DEVICES_MINI_FLAT, UROLOGY_INDICATORS_MINI_FLAT)

    # search for articles in the specified date range (only 2023 for now)
    results = search_pubmed_pmc(query, start_year=2023, end_year=2023)
    logger.success(f"Found {len(results)} results, took {time.time() - start} seconds")

    # Save the results to a JSON file
    SUBMISSION_RESULTS_FOLDER.mkdir(exist_ok=True)
    with (SUBMISSION_RESULTS_FOLDER / "retrieved_ids.json").open("w") as json_writer:
        json.dump(results, json_writer, indent=4)


if __name__ == "__main__":
    main()
