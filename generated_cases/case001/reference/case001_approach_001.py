def sort(lst: list) -> list:
    """Return a new list sorted in ascending order using Python's built-in sorted()."""
    if not isinstance(lst, list):
        raise TypeError("Input must be a list")
    return sorted(lst)