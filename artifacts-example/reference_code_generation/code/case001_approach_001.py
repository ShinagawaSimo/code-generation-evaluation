def sort(lst: list) -> list:
    if not isinstance(lst, list):
        raise TypeError("Input must be a list")
    return sorted(lst)