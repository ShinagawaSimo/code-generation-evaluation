from typing import List

def sort(lst: List[int]) -> List[int]:
    """Return a new list sorted in ascending order using merge sort."""
    if not isinstance(lst, list):
        raise TypeError("Input must be a list")
    if not all(isinstance(x, int) for x in lst):
        raise ValueError("All elements must be integers")
    if len(lst) <= 1:
        return lst[:]
    mid = len(lst) // 2
    left = sort(lst[:mid])
    right = sort(lst[mid:])
    return _merge(left, right)

def _merge(left: List[int], right: List[int]) -> List[int]:
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result