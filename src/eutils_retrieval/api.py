from enum import Enum
from http import HTTPStatus
from http.client import HTTPException
from typing import TypedDict, Literal

import httpx
from httpx_retries import RetryTransport, Retry

NCBI_EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
"""NCBI E-utilities api url"""


class NCBIDatabase(str, Enum):
    """Databases supported by NCBI API"""

    PMC = "pmc"
    PUB_MED = "pubmed"


class NCBIEndpoint(str, Enum):
    """List endpoints of NCBI E-utilities API supported"""

    SEARCH = "esearch.fcgi"
    SUMMARY = "esummary.fcgi"

    def full_url(self) -> str:
        """Build full URL as : base_url + endpoint"""
        return NCBI_EUTILS_BASE_URL + self.value

    def validated_params(self, params: dict) -> dict:
        return PARAMS_BY_ENDPOINT[self](params)


class SummaryEndpointParams(TypedDict):
    """
    Expected params when calling Summary endpoint

    Notes:
        See https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.EFetch for all attributes documentations

    Attributes:
        db: Database from which to retrieve records
    """

    db: NCBIDatabase
    query_key: str
    WebEnv: str
    retstart: int
    retmax: int
    retmode: Literal["json"]


class SearchEndpointParams(TypedDict):
    """
    Expected params when calling search endpoint

    Notes:
        See https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.EFetch for all attributes documentations

    Attributes:
        db: Database from which to retrieve records
        usehistory ("y" | "n"): store search result to be queried later
        term (str): Entrez text query
    """

    db: NCBIDatabase
    term: str
    usehistory: Literal["y", "n"]
    retmode: Literal["json"]


PARAMS_BY_ENDPOINT = {
    NCBIEndpoint.SEARCH: SearchEndpointParams,
    NCBIEndpoint.SUMMARY: SummaryEndpointParams,
}


DEFAULT_RETRY = 3
"""Nb of allowed retry for each call"""


def call_eutils(
    endpoint: NCBIEndpoint,
    params: dict,
    retry: int = DEFAULT_RETRY,
):
    """Make HTTP call to NCBI E-utilities endpoints, handles error and retry"""
    retry_transport = RetryTransport(retry=Retry(total=retry, backoff_factor=0.5))
    with httpx.Client(transport=retry_transport) as client:
        response = client.get(endpoint.full_url(), params=endpoint.validated_params(params))

    if response.status_code == HTTPStatus.REQUEST_URI_TOO_LONG:
        raise HTTPException(
            f"Error while calling {endpoint}: {HTTPStatus.REQUEST_URI_TOO_LONG} ({len(str(response.request.url))} chars in URL)"
        )

    if response.status_code != HTTPStatus.OK:
        raise HTTPException(
            f"Error while calling {endpoint}: ({response.status_code}){response.reason_phrase}"
        )

    return response.json()
