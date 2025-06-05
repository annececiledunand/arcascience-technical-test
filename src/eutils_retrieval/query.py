def create_one_combination_query(devices: list[str], indicators: list[str]) -> str:
    """
    Create a search query combining hemostatic devices and urology indicators.

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
