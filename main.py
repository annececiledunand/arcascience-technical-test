from enum import Enum
from pathlib import Path
from typing import Annotated

import typer

from src.config import (
    HEMOSTATIC_DEVICES_FLAT,
    HEMOSTATIC_DEVICES_MINI_FLAT,
    UROLOGY_INDICATORS_FLAT,
    UROLOGY_INDICATORS_MINI_FLAT,
)
from src.eutils_retrieval.api import NCBIDatabase
from src.retrieval import ncbi_article_retrieval

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
    with_async: Annotated[
        bool,
        typer.Option(help="Use async method."),
    ] = False,
    db_name: Annotated[
        DbNameArg,
        typer.Option(help="Dbs to call for search. Default to all"),
    ] = DbNameArg.ALL,
) -> None:
    """Typer method to allow cli run for `ncbi_article_retrieval`."""
    db = DB_NAME_MAPPING[db_name]
    # Use mini to choose a small sample of the real data
    devices_indicators = (HEMOSTATIC_DEVICES_FLAT, UROLOGY_INDICATORS_FLAT)
    if mini:
        devices_indicators = (HEMOSTATIC_DEVICES_MINI_FLAT, UROLOGY_INDICATORS_MINI_FLAT)

    # Check that the folder exists, or creates it
    SUBMISSION_RESULTS_FOLDER.mkdir(exist_ok=True)
    ncbi_article_retrieval(
        devices_indicators=devices_indicators,
        year_bounds=(start_year, end_year),
        db=db,
        output_folder=SUBMISSION_RESULTS_FOLDER,
        store_intermediate_results=intermediate,
        with_async=with_async,
    )


if __name__ == "__main__":
    typer.run(main)
