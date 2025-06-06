import pytest

from cross_database_search import keep_tuple_with_most_infos, merge_article_ids


def test_merge_article_ids():
    collection1 = [
        {"pmcid": 1, "pmid": "a"},
        {"pmcid": 2, "pmid": None},
        {"pmcid": 3, "pmid": None},
    ]
    collection2 = [
        {"pmcid": 1, "pmid": "a"},
        {"pmcid": None, "pmid": "a"},
        {"pmcid": 2, "pmid": "b"},
        {"pmcid": None, "pmid": "c"},
    ]
    expected = [
        {"pmcid": 3, "pmid": None},
        {"pmcid": None, "pmid": "c"},
        {"pmcid": 1, "pmid": "a"},
        {"pmcid": 2, "pmid": "b"},
    ]

    result = merge_article_ids(collection1, collection2)
    # list of dict is not sortable easily ...
    assert len(result) == len(expected)
    assert all(r in expected for r in result)


def test_merge_article_ids_no_duplication():
    collection1 = [{"pmcid": 1, "pmid": "a"}, {"pmcid": 3, "pmid": None}]
    collection2 = [{"pmcid": 2, "pmid": "b"}, {"pmcid": None, "pmid": "c"}]
    expected = [
        {"pmcid": 3, "pmid": None},
        {"pmcid": None, "pmid": "c"},
        {"pmcid": 1, "pmid": "a"},
        {"pmcid": 2, "pmid": "b"},
    ]

    result = merge_article_ids(collection1, collection2)
    # list of dict is not sortable easily ...
    assert len(result) == len(expected)
    assert all(r in expected for r in result)


def test_keep_tuple_with_most_infos():
    result = keep_tuple_with_most_infos(
        {
            ("a", "b"),
            ("a", None),  # duplicated first key
            ("aa", "bb"),
            ("aa", None),  # duplicated first key
            ("1", None),  #  not duplicated
            ("c", "d"),
            (None, "d"),  # duplicated second key
            ("cc", "dd"),
            (None, "dd"),  # duplicated second key
            (None, "2"),  #  not duplicated
            ("zz", "zz"),  #  not duplicated
        },
    )
    assert result == {
        ("a", "b"),
        ("aa", "bb"),
        ("c", "d"),
        ("cc", "dd"),
        ("1", None),
        (None, "2"),
        ("zz", "zz"),
    }


def test_keep_tuple_with_most_infos_error_duplicates():
    with pytest.raises(ValueError, match="Too many duplicates for 1st key=a"):
        keep_tuple_with_most_infos({("a", "b"), ("a", None), ("a", "c")})

    with pytest.raises(ValueError, match="Too many duplicates for 2nd key=b"):
        keep_tuple_with_most_infos({("a", "b"), ("aa", "b"), (None, "b")})
