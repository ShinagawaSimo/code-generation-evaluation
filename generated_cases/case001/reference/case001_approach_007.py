from typing import List
import heapq

def sort(lst: List[int]) -> List[int]:
    """Return a new list sorted in ascending order using heap sort."""
    if not isinstance(lst, list):
        raise TypeError("Input must be a list")
    if not all(isinstance(x, int) for x in lst):
        raise ValueError("All elements must be integers")
    heap = lst[:]
    heapq.heapify(heap)
    result = []
    while heap:
        result.append(heapq.heappop(heap))
    return result