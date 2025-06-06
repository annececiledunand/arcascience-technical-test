import time
from typing import Callable

from loguru import logger


def flatten_dict_to_list(d: dict[str, list[str]]) -> list:
    """
    Flatten a dictionary into a list of its keys and values.

    Args:
        d (dict): The dictionary to flatten.

    Returns:
        list: A flattened list containing keys and values.
    """
    return [item for key, values in d.items() for item in [key] + values]


def add_timer_and_logger(task_description: str):
    """Decorator that logs (INFO) the task start and end time.

    Notes:
        You can use the method decorated with an additional argument `prefix_log` to prefix each call with a
        specific value (current run number for example).

    Args:
        task_description (str): used to describe the current method task in logs
    """

    def decorator(method: Callable):
        def wrapper(*args, prefix_log: str = "", **kwargs):
            start = time.time()

            logger.info(f"{prefix_log}Starting {task_description}")
            result = method(*args, **kwargs)
            logger.info(
                f"{prefix_log}Finished {task_description}, took {time.time() - start} seconds"
            )
            return result

        return wrapper

    return decorator
