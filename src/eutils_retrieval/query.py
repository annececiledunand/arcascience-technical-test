import itertools
from collections.abc import Generator, Iterable

from loguru import logger

# tested ok slightly above (less than 4186) but this seems like the nice spot to allow for a
# little of room error. Server does not seem to specify their max URI, not following HTTP 1.1.
PMC_API_MAX_URI_LENGTH = 4000


def create_e_queries(
    devices: Iterable[str],
    indicators: Iterable[str],
    year_bounds: tuple[int | None, int | None] = (None, None),
    query_max_length: int = PMC_API_MAX_URI_LENGTH,
) -> tuple[str, ...]:
    """Create all search queries combining hemostatic devices and urology indicators.

    Queries are sized based on endpoint URI length allowed.

    Args:
        devices (list): List of hemostatic devices and related terms
        indicators (list): List of urology indicators and related terms
        year_bounds (tuple[int, int]): Filters to apply to search query (start_date, end_date).
            Both are optionals.
        query_max_length (int): Max char size allowed for URL construction.
            Since query is used in URL construction, we need to limit the size.

    Returns:
        tuple[str]: All combination search queries

    """
    logger.info(
        "Determining the number of queries necessary to describe all devices and indicators",
    )

    year_bound_query = create_year_bound_query(*year_bounds)
    queries = create_complete_combinations_queries(
        devices,
        indicators,
        query_max_length=query_max_length,
    )

    if year_bound_query != "":
        return tuple(f"({q}) AND {year_bound_query}" for q in queries)
    return tuple(queries)


def create_one_combination_query(devices: Iterable[str], indicators: Iterable[str]) -> str:
    """Create a search query combining hemostatic devices and urology indicators.

    Args:
        devices (list): List of hemostatic devices and related terms
        indicators (list): List of urology indicators and related terms

    Returns:
        str: Combined search query

    """
    # note: join can directly use generators
    device_query = " OR ".join(f'"{device}"' for device in devices)
    indicator_query = " OR ".join(f'"{indicator}"' for indicator in indicators)

    # Combine with AND to find articles mentioning both
    return f"({device_query}) AND ({indicator_query})"


def create_year_bound_query(start_year: int | None = None, end_year: int | None = None) -> str:
    """Create a condition with year bounds, as range or exact matching, for query.

    If both years ar given, creates a range, if one is provided, will create an exact match.

    Args:
        start_year (int): The start year of publication
        end_year (int): the ned year of publication

    Returns:
        str: the date filter query

    """
    if start_year and end_year and start_year > end_year:
        msg = "`start_year` cannot be bigger than `end_year`"
        raise ValueError(msg)

    # Add date range if specified
    date_query = ""
    if start_year or end_year:
        if start_year:
            date_query += f"{start_year}[PDAT]"
        if start_year and end_year:
            date_query += ":"
        if end_year:
            date_query += f"{end_year}[PDAT]"

    return date_query


OR_QUERY = " OR "
AND_QUERY = " AND "


def create_complete_combinations_queries(
    devices: list[str],
    indicators: list[str],
    query_max_length: int,
) -> Generator[str, None, None]:
    """Create a list of queries reflecting all possible combination between devices and indicators.

    Args:
        devices (list): List of devices to combine
        indicators (list): List of indicators to combine
        query_max_length (int): forces one query to be smaller that a max length of chars allowed.

    Returns:
        Generator (str): all possible queries following the pattern
            (`device` OR ... `device`) AND (`indicator` OR ... `indicator`)

    Notes:
        We want to determine how many words from devices and indicators we can put together in a
        query pattern ANDxOR by resolving:

        nb_device_words_allowed * (biggest_device_word_length + nb_quotes_by_word(2))
        + (nb_device_words_allowed - 1) * length_of_or_query
        + length_of_and_query
        + nb_indicator_words_allowed * (biggest_indicator_word_length + nb_quotes_by_word(2))
        + (nb_indicator_words_allowed - 1) * length_of_or_query
        + nb_parenthesis_used(4)
        < query_max_length`

        with `nb_device_words_allowed` and `nb_indicator_words_allowed` the biggest possible values.
        To simplify we want `nb_indicator_words_allowed` == `nb_device_words_allowed` == x

    Examples:
        >> devices = ['a', 'b', 'c']
        >> indicators = ['1', '2', '3']

        If we did not limit the query size we would have :

        >> create_complete_combinations_queries(devices, indicators, query_max_length=1_000_000)
        (
            # only one query since 43 chars < query_max_length
            '("a" OR "b" OR "c") AND ("1" OR "2" OR "3")'
        )

        Now if we limit the size to force the query to not generate one

        >> create_complete_combinations_queries(devices, indicators, query_max_length=40)
        (
            '("a" OR "b") AND ("1" OR "2")',  # 31 chars
            '"c" AND ("1" OR "2")',
            '("a" OR "b") AND "3"',
            '"c" AND "3"',
        )

    """
    biggest_device_word_length = max(len(device) for device in devices)
    biggest_indicator_word_length = max(len(indicator) for indicator in indicators)

    smallest_necessary_query_length = (
        biggest_device_word_length + len(AND_QUERY) + biggest_indicator_word_length
    )
    if smallest_necessary_query_length > query_max_length:
        msg = (
            f"Cannot build query since the maximum length allowed ({query_max_length}) is not "
            f"sufficient to combine one by one the biggest words in either devices or indicators"
        )
        raise ValueError(
            msg,
        )

    nb_words_possible = biggest_nb_words_possible(
        biggest_device_word_length,
        biggest_indicator_word_length,
        query_max_length,
    )

    # Create as many group of words as allowed by the query length
    # cast generator directly to list because needs to be declared before using two generators
    # at once in return type (also a generator)
    devices_grouped = list(itertools.batched(devices, n=nb_words_possible))
    indicators_grouped = list(itertools.batched(indicators, n=nb_words_possible))

    return (
        create_one_combination_query(device_group, indicator_group)
        for device_group in devices_grouped
        for indicator_group in indicators_grouped
    )


def biggest_nb_words_possible(
    biggest_device_word_length: int,
    biggest_indicator_word_length: int,
    query_max_length: int,
) -> int:
    """Resolve `x` value as `int` in strict inequation.

    `x * (biggest_device_word_length + length_of_or_query + biggest_indicator_word_length + 4)
    - 2 * length_of_or_query
    + length_of_and_query
    + 4
    < query_max_length`

    Notes:
        `int` will round to the closest lesser integers
        see `create_complete_combinations_queries` docs for more context

    Returns:
        int: the smallest closer int that resolves this equation

    """
    solution = (query_max_length - 4 + 2 * len(OR_QUERY) - len(AND_QUERY)) / (
        biggest_device_word_length + biggest_indicator_word_length + 4 + 2 * len(OR_QUERY)
    )
    # we want to strictly resolve the inequation, thus f the result is exactly an int i.e.
    # resolving `=`, we decrement it
    return int(solution) if float(int(solution)) != solution else int(solution) - 1
