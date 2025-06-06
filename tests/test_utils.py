import json
from pathlib import Path

import pytest

from src.utils import flatten_dict_to_list, store_data_as_json


def test_flatten_dict_to_list():
    dict_to_flatten = {
        "a": ["aa"],
        "b": ["bb", "bbb"],
        "c": ["cc", "ccc", "cccc"],
    }
    expected_flattened = ["a", "aa", "b", "bb", "bbb", "c", "cc", "ccc", "cccc"]

    result = flatten_dict_to_list(dict_to_flatten)
    assert result == expected_flattened


def test_store_data_as_json(tmp_path: Path):
    file_path = tmp_path / "file.json"
    data = {"bonjour": ["1", "2"]}

    assert not file_path.exists()
    store_data_as_json(data, file_path)
    with file_path.open() as reader:
        result = json.load(reader)
        assert result == data


def test_store_data_as_json_error(tmp_path: Path):
    file_path = tmp_path / "file.txt"
    data = {"bonjour": ["1", "2"]}

    with pytest.raises(ValueError, match="should be of json extension"):
        store_data_as_json(data, file_path)
