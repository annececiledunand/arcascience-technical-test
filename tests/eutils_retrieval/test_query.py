import pytest

from src.eutils_retrieval.query import (
    create_one_combination_query,
    create_complete_combinations_queries,
    biggest_nb_words_possible,
    create_year_bound_query,
    create_e_queries,
)

TEST_DEVICES = [
    "Hemoblast",
    "Biom'up",
    "Gelfoam",
    "Gelatin sponge",
]
TEST_INDICATORS = ["Urology Indicators", "urological surgery", "vascular surgery"]


def test_create_e_queries():
    result = create_e_queries(["a", "b", "c"], ["1", "2", "3"], (2023, 2024), 39)
    assert list(result) == [
        '(("a" OR "b") AND ("1" OR "2")) AND 2023[PDAT]:2024[PDAT]',
        '(("a" OR "b") AND ("3")) AND 2023[PDAT]:2024[PDAT]',
        '(("c") AND ("1" OR "2")) AND 2023[PDAT]:2024[PDAT]',
        '(("c") AND ("3")) AND 2023[PDAT]:2024[PDAT]',
    ]


def test_create_e_queries_no_bound():
    result = create_e_queries(["a", "b", "c"], ["1", "2", "3"], (None, None), 39)
    assert list(result) == [
        '("a" OR "b") AND ("1" OR "2")',
        '("a" OR "b") AND ("3")',
        '("c") AND ("1" OR "2")',
        '("c") AND ("3")',
    ]


@pytest.mark.parametrize(
    "bounds, expected",
    (
        ((None, None), ""),
        ((2023, None), "2023[PDAT]"),
        ((None, 2023), "2023[PDAT]"),
        ((2023, 2024), "2023[PDAT]:2024[PDAT]"),
    ),
)
def test_create_year_bound_query(bounds: tuple[int | None, int | None], expected: str):
    result = create_year_bound_query(*bounds)
    assert result == expected


def test_create_year_bound_query_error():
    with pytest.raises(ValueError, match="`start_year` cannot be bigger than `end_year`"):
        create_year_bound_query(2023, 2022)


def test_create_one_combination_query():
    expected_query = (
        '("Hemoblast" OR "Biom\'up" OR "Gelfoam" OR "Gelatin sponge")'
        " AND "
        '("Urology Indicators" OR "urological surgery" OR "vascular surgery")'
    )
    result = create_one_combination_query(TEST_DEVICES, TEST_INDICATORS)
    assert result == expected_query


def test_biggest_nb_words_possible():
    result = biggest_nb_words_possible(1, 1, 30)
    assert result == 2  # ('a' OR 'b') AND ('c' OR 'd') is 29 chars


def test_biggest_nb_words_possible_smaller():
    result = biggest_nb_words_possible(1, 1, 28)
    assert result == 1  # ('a' OR 'b') AND ('c' OR 'd') is 29 chars


def test_create_complete_combinations_queries_impossible():
    with pytest.raises(
        Exception,
        match="Cannot build query since the maximum length allowed \(2\) is not sufficient to combine one by one the biggest words in either devices or indicators",
    ):
        create_complete_combinations_queries(["a", "b"], ["1", "2"], 2)


def test_create_complete_combinations_queries_no_split():
    result = create_complete_combinations_queries(["a", "b"], ["1", "2"], 1_000_000)
    assert list(result) == ['("a" OR "b") AND ("1" OR "2")']


def test_create_complete_combinations_queries_split_once():
    result = create_complete_combinations_queries(["a", "b"], ["1", "2"], 28)
    assert list(result) == [
        '("a") AND ("1")',
        '("a") AND ("2")',
        '("b") AND ("1")',
        '("b") AND ("2")',
    ]


def test_create_complete_combinations_queries_split_twice():
    result = create_complete_combinations_queries(["a", "b", "c"], ["1", "2", "3"], 39)
    assert list(result) == [
        '("a" OR "b") AND ("1" OR "2")',
        '("a" OR "b") AND ("3")',
        '("c") AND ("1" OR "2")',
        '("c") AND ("3")',
    ]
