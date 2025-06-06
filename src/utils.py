import json
import time
from collections.abc import Callable
from pathlib import Path

from loguru import logger


def flatten_dict_to_list(d: dict[str, list[str]]) -> list:
    """Flatten a dictionary into a list of its keys and values.

    Args:
        d (dict): The dictionary to flatten.

    Returns:
        list: A flattened list containing keys and values.

    """
    return [item for key, values in d.items() for item in [key, *values]]


def add_timer_and_logger(task_description: str) -> Callable:  # pragma: no cover
    """Add logs to following method start and end execution time.

    Notes:
        You can use the method decorated with an additional argument `prefix_log` to prefix
        each call with a specific value (current run number for example).

    Args:
        task_description (str): used to describe the current method task in logs

    """

    def decorator(method: Callable) -> Callable:
        def wrapper(*args, prefix_log: str = "", **kwargs):  # noqa: ANN002, ANN003, ANN202
            start = time.time()

            logger.info(f"{prefix_log}Starting {task_description}")
            result = method(*args, **kwargs)
            logger.info(
                f"{prefix_log}Finished {task_description}, took {time.time() - start} seconds",
            )
            return result

        return wrapper

    return decorator


def store_data_as_json(data: list | dict, file_path: Path) -> None:
    """Store data into a json file.

    Args:
        data (dict or list): sdata to store into file
        file_path (Path): path of file to store into (.json extension)

    """
    if file_path.suffix != ".json":
        msg = f"File name {file_path} should be of json extension"
        raise ValueError(msg)

    logger.debug(f"Writing data into {file_path}")

    file_path.parent.mkdir(exist_ok=True)
    with file_path.open("w") as json_writer:
        json.dump(data, json_writer, indent=4)
