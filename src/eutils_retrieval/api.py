import asyncio
from collections.abc import Awaitable, Callable, Iterable
from enum import Enum
from http import HTTPStatus
from typing import Literal, TypedDict

import httpx
from httpx_retries import Retry, RetryTransport
from loguru import logger

NCBI_EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
"""NCBI E-utilities api url"""


class NCBIDatabase(str, Enum):
    """Databases supported by NCBI API."""

    PMC = "pmc"
    PUB_MED = "pubmed"


class NCBIEndpoint(str, Enum):
    """List endpoints of NCBI E-utilities API supported."""

    SEARCH = "esearch.fcgi"
    SUMMARY = "esummary.fcgi"

    def full_url(self) -> str:
        """Build full URL as : base_url + endpoint."""
        return NCBI_EUTILS_BASE_URL + self.value

    def validated_params(self, params: dict) -> dict:
        """Check parameters compatibility with endpoint."""
        return PARAMS_BY_ENDPOINT[self](params)


class SummaryEndpointParams(TypedDict):
    """Expected params when calling Summary endpoint.

    Notes:
        See https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.EFetch for
        all attributes documentations

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
    """Expected params when calling search endpoint.

    Notes:
        See https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.EFetch for all
        attributes documentations

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
) -> dict | list:
    """Make HTTP call to NCBI E-utilities endpoints, handles error and retry."""
    retry_transport = RetryTransport(retry=Retry(total=retry, backoff_factor=0.5))
    with httpx.Client(transport=retry_transport) as client:
        response = client.get(endpoint.full_url(), params=endpoint.validated_params(params))

    if response.status_code == HTTPStatus.REQUEST_URI_TOO_LONG:
        logger.error(
            f"Error while calling {endpoint}: {HTTPStatus.REQUEST_URI_TOO_LONG} "
            f"({len(str(response.request.url))} chars in URL)",
        )
        response.raise_for_status()

    if response.status_code != HTTPStatus.OK:
        logger.error(
            f"Error while calling {endpoint}: ({response.status_code}){response.reason_phrase}",
        )
        response.raise_for_status()

    return response.json()


async def call_eutils_async(
    endpoint: NCBIEndpoint,
    params: dict,
    retry: int = DEFAULT_RETRY,
) -> dict | list:
    """Make HTTP call to NCBI E-utilities endpoints, handles error and retry."""
    retry_transport = RetryTransport(retry=Retry(total=retry, backoff_factor=0.5))
    timeout = httpx.Timeout(10.0, read=None)
    async with httpx.AsyncClient(transport=retry_transport, timeout=timeout) as client:
        response = await client.get(endpoint.full_url(), params=endpoint.validated_params(params))

    if response.status_code == HTTPStatus.REQUEST_URI_TOO_LONG:
        logger.error(
            f"Error while calling {endpoint}: {HTTPStatus.REQUEST_URI_TOO_LONG} "
            f"({len(str(response.request.url))} chars in URL)",
        )
        response.raise_for_status()

    if response.status_code != HTTPStatus.OK:
        logger.error(
            f"Error while calling {endpoint}: ({response.status_code}){response.reason_phrase}",
        )
        response.raise_for_status()

    return response.json()


def execute_parallel_limited(
    async_method: Callable,
    iterable_args_and_kwargs: list[tuple[list, dict]],
    nb_concurrent_runs: int,
) -> list:
    """Call `async_method` in a sync way, with all arguments of `iterable_args_and_kwargs`, limited by `nb_concurrent_run`.

    Args:
        async_method (callable)
        iterable_args_and_kwargs (list (args, kwargs)): args and kwargs needed for each call to `async_method`.
            Must be equivalent to method signature.
        nb_concurrent_runs (int): nb of concurrent runs to allow.

    Returns:
        list of results of `async_method` called with each `iterable_args_and_kwargs`

    """

    async def _async_get_all_requests_with_concurrency_limit():
        return await _gather_with_concurrency(
            nb_concurrent_runs,
            *[async_method(*args, **kwargs) for (args, kwargs) in iterable_args_and_kwargs],
        )

    return asyncio.run(_async_get_all_requests_with_concurrency_limit())


async def _gather_with_concurrency(nb_concurrent_runs: int, *coroutines: Iterable[Awaitable]):
    """Using semaphore to limit the number of concurrent calls."""
    semaphore = asyncio.Semaphore(nb_concurrent_runs)

    async def sem_coro(coro: Awaitable):
        async with semaphore:
            return await coro

    return await asyncio.gather(*(sem_coro(c) for c in coroutines))
