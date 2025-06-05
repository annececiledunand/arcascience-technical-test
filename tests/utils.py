from src.utils import flatten_dict_to_list


def test_flatten_dict_to_list():
    dict_to_flatten = {
        "a": ["aa"],
        "b": ["bb", "bbb"],
        "c": ["cc", "ccc", "cccc"],
    }
    expected_flattened = ["a", "aa", "b", "bb", "bbb", "c", "cc", "ccc", "cccc"]

    result = flatten_dict_to_list(dict_to_flatten)
    assert result == expected_flattened
