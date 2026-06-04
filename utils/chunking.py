def chunked(items, size: int):
    """Return items split into fixed-size chunks."""
    if size < 1:
        raise ValueError("chunk size must be at least 1")
    return [items[i:i + size] for i in range(0, len(items), size)]
