from src.config import HEMOSTATIC_DEVICES_MINI_FLAT, UROLOGY_INDICATORS_MINI_FLAT
from src.eutils_retrieval.search import search_pubmed_pmc
import json
import os
import time
from loguru import logger


def create_query(devices, indicators):
    """
    Create a search query combining hemostatic devices and urology indicators.

    Args:
        devices (list): List of hemostatic devices and related terms
        indicators (list): List of urology indicators and related terms

    Returns:
        str: Combined search query
    """
    device_query = " OR ".join([f'"{device}"' for device in devices])
    indicator_query = " OR ".join([f'"{indicator}"' for indicator in indicators])

    # Combine with AND to find articles mentioning both
    return f"({device_query}) AND ({indicator_query})"


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
