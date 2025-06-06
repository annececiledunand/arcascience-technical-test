# Biomedical Literature Retrieval Test

See [test instruction](./INSTRUCTIONS.md)

## Getting Started

1. Install project dependencies:
   ```
   uv sync --locked
   ```

2. Run tests

   ```sh
   uv run pytest
   ```

3. Run main script

   ```sh
   uv run main.py --help # to see the options
   ```
   
## Repository structure

- [pyproject.toml](./pyproject.toml) : defines the entire project configuration
- [main.py](./main.py) : the CLI entrypoint, runs the entire project
- [src/](./src)
  - [retrieval.py](src/retrieval.py) : the main method to call endpoints and fetch article results
  - [cross_database_search.py](src/cross_database_search.py) : methods linked to handling call to both `PMC` and `PubMed` databases, as well as de-duplication of article ids
  - [config.py](src/config.py) : same DEVICES & INDICATORS as original
  - [utils.py](src/utils.py)
  - [eutils_retrieval/](src/eutils_retrieval)
    - [api.py](src/eutils_retrieval/api.py) : all objects needed to call NCBI endpoints
    - [query.py](src/eutils_retrieval/query.py) : query builders from DEVICES & INDICATORS for text search
    - [extract.py](src/eutils_retrieval/extract.py) : methods used to extract article ids from summary fetch responses, since there is a difference with PMC and PubMed ids label
    - [search.py](src/eutils_retrieval/search.py) : all methods to call search and summary api endpoint for both databases
- [tests/](./tests) : contains all tests following the same nomenclature as `src` folder

## Features & libs

- usage of [`uv`](https://docs.astral.sh/uv/) as a package and project manager
- linter `ruff` with the maximum rules implemented
- usage of [`typer`](https://typer.tiangolo.com/) for simple CLI creation, allowing [`main.py`](./main.py) to have options
- usage of a pre-commit for dev purposes (runs `ruff`)
- typing for all methods
- tests via `pytest`
- coverage (99%) for the test suite
- lib [`loguru`](https://loguru.readthedocs.io/en/stable/overview.html) for logging, super simple to use, add handlers, store logs into files, able to catch exceptions and traceback to pretty-print it in console, and by default show which file creates the log message.
- simple github action that runs both a linter (ruff) and the test suite, as well as the coverage, and fails under 99%

## Tasks report

### 1. Handling URI too long issue

Dynamically split the big query `(device ... OR device) AND (indicator ... OR indicator)` into multiple shorter ones, 
that could not be bigger than 4000 char (empirically on API endpoint). Simple solution implemented (can complexify decision).

The method tries to find the nb of `devices` and `indicators` maximum as to not create a query bigger than 4000 char,
counting the spaces, `OR`, `AND`, parenthesis, etc. 

See [src/eutils_retrieval/query.py](./src/eutils_retrieval/query.py) and method `create_complete_combinations_queries` docstring as well as the related tests.


### 2.1 & 2.2 Handle the batching for `summary` endpoint

Added batching support by allowing pagination (offset, limit) to be sent to endpoint, and iterate over it.
See [src/eutils_retrieval/search.py](./src/eutils_retrieval/search.py) and method `fetch_all_stored_articles` docstring as well as the related tests.


### 2.3 Multiprocessing

Used lib multiprocess to split and parallelize the maximum of api calls, and using the `backoff` parameter of api call retries to wait more each failed call. 
In documentation, we are told the server can only allow 3 requests by the second (if no APIKey is possessed by the project, which is the case here) [here](https://www.ncbi.nlm.nih.gov/books/NBK25497/#chapter2.Usage_Guidelines_and_Requiremen)


### 2.4 Retry logic for HTTP calls

Created a generic method with a retry implementation using the lib [`httpx`](https://www.python-httpx.org/) for all HTTP calls.

See [src/eutils_retrieval/api.py](./src/eutils_retrieval/api.py) and method `call_eutils` docstring as well as the related tests.

### 3.1 Add call to PubMed db

Allowed customisation of payload argument `db` via a fixed enum to avoid literals.
(See [src/eutils_retrieval/api.py](./src/eutils_retrieval/api.py) and method `call_eutils` docstring as well as the related tests.)


### 3.2 Deduplication

Created a `merge_article_ids` methods that identifies and remove any duplicates from both db.
See [cross_database_search.py](src/cross_database_search.py) and method `merge_article_ids` docstring as well as the related tests.


### 3.3 Logging

Used lib `loguru` extensively and allowed for user to store intermediate results for debugging purposes if needed.
Logs and tqdm progress bars are difficult to merge, `rich` lib can be more appropriate since loguru is build with 
`rich` compatibility in mind, but too long to develop as a side feature.

### 4. New Features/Improvements
- Allowed to select via CLI the year bounds wanted (or none)
- Allowed to store intermediate results for debugging purposes if needed
- Allowed to choose from which db `pub_med` or `pmc` or both to fetch the article ids
- Added flag `--mini` to run the script with the starting sample selection for testing purposes (deactivated by default)


## Notes

For error handling, I removed all of the `try, except` with a too broad clause. In general, I prefer the code to break as early and cleanly as possible,
and that allows for debugging in a much safer and faster way. I raised exceptions each time the code could not continue 
**with those simple features** and would have needed proper error-handling days of implementations. 