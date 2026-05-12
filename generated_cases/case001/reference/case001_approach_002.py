def quick_sort(lst: list) -> list:
    """Return a new list sorted by quicksort (recursive, returns new list)."""
    if not isinstance(lst, list):
        raise TypeError("Input must be a list")
    if len(lst) <= 1:
        return lst[:]
    pivot = lst[len(lst) // 2]
    left = [x for x in lst if x < pivot]
    middle = [x for x in lst if x == pivot]
    right = [x for x in lst if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)