# Biomedical Literature Retrieval Test

See [test instruction](./INSTRUCTIONS.md)

## Getting Started

1. Install dependencies:
   ```
   uv sync --locked
   ```

2. Run main script

   ```sh
   uv run main.py --help # to see the options
   ```

## Dev

1. Install pre-commit via ```pre-commit install```


## Decisions
Why [loguru](https://loguru.readthedocs.io/en/stable/overview.html#no-handler-no-formatter-no-filter-one-function-to-rule-them-all) ?
best logger in the market imo, super simple to use, add handlers, store logs into files, able to catch exceptions and by default show which file creates the log message.

```
2025-06-05 12:21:23.077 | SUCCESS  | src.eutils_retrieval.search:search_pmc:42 - Found 214 results in PMC.
2025-06-05 12:21:23.788 | SUCCESS  | __main__:main:37 - Found 214 results, took 6.526986598968506 seconds
```
