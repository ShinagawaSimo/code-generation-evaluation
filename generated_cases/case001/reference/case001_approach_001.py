from typing import List

def sort(lst: List[int]) -> List[int]:
    """Return a new list sorted in ascending order."""
    if not isinstance(lst, list):
        raise TypeError("Input must be a list")
    if not all(isinstance(x, int) for x in lst):
        raise ValueError("All elements must be integers")
    return sorted(lst)