def custom_mask_str(value: str) -> str:
    """Custom masking function that only shows the last 4 characters."""
    if len(value) > 4:
        return "****" + value[-4:]

    return value
