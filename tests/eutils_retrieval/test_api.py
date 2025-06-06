import re

import httpx
import pytest
from httpx import HTTPStatusError
from pytest_httpx import HTTPXMock

from eutils_retrieval.api import NCBIEndpoint, call_eutils, SearchEndpointParams, NCBIDatabase


def test_call_eutils(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SEARCH.full_url() + "?.*"),
        method="GET",
        json={"call": "response"},
    )

    result = call_eutils(
        NCBIEndpoint.SEARCH,
        params=SearchEndpointParams(
            db=NCBIDatabase.PMC, term="my_query", usehistory="n", retmode="json"
        ),
        retry=0,
    )
    assert result == {"call": "response"}


def test_call_eutils_no_retry_error(httpx_mock: HTTPXMock):
    httpx_mock.add_exception(
        exception=httpx.ReadTimeout("Unable to read within timeout"),
        url=re.compile(NCBIEndpoint.SEARCH.full_url() + "?.*"),
        method="GET",
    )
    with pytest.raises(httpx.TimeoutException):
        call_eutils(
            NCBIEndpoint.SEARCH,
            params=SearchEndpointParams(
                db=NCBIDatabase.PMC, term="my_query", usehistory="n", retmode="json"
            ),
            retry=0,
        )


def test_call_eutils_error_uri_too_long(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SEARCH.full_url() + "?.*"),
        method="GET",
        status_code=414,
    )

    with pytest.raises(HTTPStatusError, match="Client error '414 Request-URI Too Long' for url"):
        call_eutils(
            NCBIEndpoint.SEARCH,
            params=SearchEndpointParams(
                db=NCBIDatabase.PMC, term="my_query", usehistory="n", retmode="json"
            ),
            retry=0,
        )


def test_call_eutils_retry(httpx_mock: HTTPXMock):
    httpx_mock.add_exception(
        exception=httpx.ReadTimeout("Unable to read within timeout"),
        url=re.compile(NCBIEndpoint.SEARCH.full_url() + "?.*"),
        method="GET",
    )
    httpx_mock.add_response(
        url=re.compile(NCBIEndpoint.SEARCH.full_url() + "?.*"),
        method="GET",
        json={"call": "response"},
    )

    result = call_eutils(
        NCBIEndpoint.SEARCH,
        params=SearchEndpointParams(
            db=NCBIDatabase.PMC, term="my_query", usehistory="n", retmode="json"
        ),
        retry=2,
    )
    assert result == {"call": "response"}
