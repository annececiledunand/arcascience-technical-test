import pytest


@pytest.fixture
def search_and_store_response() -> dict:
    return {
        "header": {"type": "esearch", "version": "0.3"},
        "esearchresult": {
            "count": "1",
            "retmax": "1",
            "retstart": "0",
            "querykey": "my_query_key",
            "webenv": "MCID_FAKE_UUID",
            "idlist": ["11111111"],
            "translationset": [],
            "translationstack": [
                {
                    "term": '"Hemoblast"[All Fields]',
                    "field": "All Fields",
                    "count": "40",
                    "explode": "N",
                },
                {
                    "term": '"Biom\'up"[All Fields]',
                    "field": "All Fields",
                    "count": "115",
                    "explode": "N",
                },
                "OR",
                "GROUP",
                {
                    "term": '"urological surgery"[All Fields]',
                    "field": "All Fields",
                    "count": "5509",
                    "explode": "N",
                },
                {
                    "term": '"vascular surgery"[All Fields]',
                    "field": "All Fields",
                    "count": "57080",
                    "explode": "N",
                },
                "OR",
                {
                    "term": '"renal transplant"[All Fields]',
                    "field": "All Fields",
                    "count": "49752",
                    "explode": "N",
                },
                "OR",
                {
                    "term": '"kidney transplant"[All Fields]',
                    "field": "All Fields",
                    "count": "56721",
                    "explode": "N",
                },
                "OR",
                {
                    "term": '"prostatectomy"[All Fields]',
                    "field": "All Fields",
                    "count": "53418",
                    "explode": "N",
                },
                "OR",
                {
                    "term": '"nephrectomy"[All Fields]',
                    "field": "All Fields",
                    "count": "54413",
                    "explode": "N",
                },
                "OR",
                {
                    "term": '"nephrolithotomy"[All Fields]',
                    "field": "All Fields",
                    "count": "5975",
                    "explode": "N",
                },
                "OR",
                {
                    "term": '"pyeloplasty"[All Fields]',
                    "field": "All Fields",
                    "count": "2641",
                    "explode": "N",
                },
                "OR",
                {
                    "term": '"ureterectomy"[All Fields]',
                    "field": "All Fields",
                    "count": "1525",
                    "explode": "N",
                },
                "OR",
                {
                    "term": '"cystectomy"[All Fields]',
                    "field": "All Fields",
                    "count": "26326",
                    "explode": "N",
                },
                "OR",
                "GROUP",
                "AND",
                "GROUP",
                {"term": "2023[PubDate]", "field": "PubDate", "count": "0", "explode": "N"},
                {"term": "2023[PubDate]", "field": "PubDate", "count": "0", "explode": "N"},
                "RANGE",
                "AND",
            ],
            "querytranslation": '(("Hemoblast"[All Fields] OR "Biom\'up"[All Fields]) AND ("urological surgery"[All Fields] OR "vascular surgery"[All Fields] OR "renal transplant"[All Fields] OR "kidney transplant"[All Fields] OR "prostatectomy"[All Fields] OR "nephrectomy"[All Fields] OR "nephrolithotomy"[All Fields] OR "pyeloplasty"[All Fields] OR "ureterectomy"[All Fields] OR "cystectomy"[All Fields])) AND 2023[PubDate] : 2023[PubDate]',
        },
    }


@pytest.fixture
def search_and_store_response_none() -> dict:
    return {
        "header": {"type": "esearch", "version": "0.3"},
        "esearchresult": {
            "count": "0",
            "retmax": "0",
            "retstart": "0",
            "querykey": "my_query_key",
            "webenv": "MCID_NOPE",
            "idlist": [],
            "translationset": [],
            "translationstack": [
                {
                    "term": '"Hemoblast"[All Fields]',
                    "field": "All Fields",
                    "count": "40",
                    "explode": "N",
                },
                {
                    "term": '"Biom\'up"[All Fields]',
                    "field": "All Fields",
                    "count": "115",
                    "explode": "N",
                },
                "OR",
                "GROUP",
                {
                    "term": '"urological surgery"[All Fields]',
                    "field": "All Fields",
                    "count": "5509",
                    "explode": "N",
                },
                "AND",
                "GROUP",
                {"term": "2023[PubDate]", "field": "PubDate", "count": "0", "explode": "N"},
                {"term": "2023[PubDate]", "field": "PubDate", "count": "0", "explode": "N"},
                "RANGE",
                "AND",
            ],
            "querytranslation": '(("Hemoblast"[All Fields] OR "Biom\'up"[All Fields]) AND "urological surgery"[All Fields]) AND 2023[PubDate] : 2023[PubDate]',
        },
    }
