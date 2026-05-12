from typing import List

def sort(lst: List[int]) -> List[int]:
    """Return a new list sorted in ascending order using quicksort."""
    if not isinstance(lst, list):
        raise TypeError("Input must be a list")
    if not all(isinstance(x, int) for x in lst):
        raise ValueError("All elements must be integers")
    if len(lst) <= 1:
        return lst[:]  # return a copy for consistency
    pivot = lst[0]
    left = [x for x in lst[1:] if x <= pivot]
    right = [x for x in lst[1:] if x > pivot]
    return sort(left) + [pivot] + sort(right)