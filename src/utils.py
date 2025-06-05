def flatten_dict_to_list(d: dict[str, list[str]]) -> list:
    """
    Flatten a dictionary into a list of its keys and values.

    Args:
        d (dict): The dictionary to flatten.

    Returns:
        list: A flattened list containing keys and values.
    """
    return [item for key, values in d.items() for item in [key] + values]
