from src.config import HEMOSTATIC_DEVICES_MINI_FLAT, UROLOGY_INDICATORS_MINI_FLAT
from src.eutils_retrieval.query import create_query
from src.eutils_retrieval.search import search_pubmed_pmc
import json
import os
import time
from loguru import logger


def main():
    start = time.time()
    # Create the query
    # Note: This is using the mini (reduced) datasets for testing
    #  For the final solution, you should use the full datasets:
    #  HEMOSTATIC_DEVICES_FLAT and UROLOGY_INDICATORS_FLAT
    query = create_query(HEMOSTATIC_DEVICES_MINI_FLAT, UROLOGY_INDICATORS_MINI_FLAT)

    # search for articles in the specified date range (only 2023 for now)
    results = search_pubmed_pmc(query, start_year=2023, end_year=2023)
    logger.success(f"Found {len(results)} results, took {time.time() - start} seconds")

    # Save the results to a JSON file
    os.makedirs("submission_results", exist_ok=True)
    with open(os.path.join("submission_results", "retrieved_ids.json"), "w") as f:
        json.dump(results, f, indent=4)


if __name__ == "__main__":
    main()
