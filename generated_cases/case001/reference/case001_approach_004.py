def insertion_sort(lst: list) -> list:
    """Return a new list sorted by insertion sort (in-place on a copy)."""
    if not isinstance(lst, list):
        raise TypeError("Input must be a list")
    sorted_lst = lst[:]
    for i in range(1, len(sorted_lst)):
        key = sorted_lst[i]
        j = i - 1
        while j >= 0 and sorted_lst[j] > key:
            sorted_lst[j + 1] = sorted_lst[j]
            j -= 1
        sorted_lst[j + 1] = key
    return sorted_lst