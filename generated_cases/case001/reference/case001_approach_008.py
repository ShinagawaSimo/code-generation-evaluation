from typing import List

def sort(lst: List[int]) -> List[int]:
    """Return a new list sorted in ascending order using counting sort.
       Only works for non‑negative integers."""
    if not isinstance(lst, list):
        raise TypeError("Input must be a list")
    if not all(isinstance(x, int) for x in lst):
        raise ValueError("All elements must be integers")
    if not lst:
        return []
    if min(lst) < 0:
        raise ValueError("CountingSort requires non‑negative integers")
    max_val = max(lst)
    count = [0] * (max_val + 1)
    for x in lst:
        count[x] += 1
    result = []
    for val, cnt in enumerate(count):
        result.extend([val] * cnt)
    return result