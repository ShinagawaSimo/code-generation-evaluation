from typing import List

def sort(lst: List[int]) -> List[int]:
    """Return a new list sorted in ascending order using insertion sort."""
    if not isinstance(lst, list):
        raise TypeError("Input must be a list")
    if not all(isinstance(x, int) for x in lst):
        raise ValueError("All elements must be integers")
    result = []
    for x in lst:
        # find insertion point
        i = 0
        while i < len(result) and result[i] <= x:
            i += 1
        result.insert(i, x)
    return result