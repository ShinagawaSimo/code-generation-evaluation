from typing import List

def sort(lst: List[int]) -> List[int]:
    """Return a new list sorted in ascending order using bucket sort.
       Assumes integer range is moderate for good performance."""
    if not isinstance(lst, list):
        raise TypeError("Input must be a list")
    if not all(isinstance(x, int) for x in lst):
        raise ValueError("All elements must be integers")
    if not lst:
        return []
    min_val = min(lst)
    max_val = max(lst)
    # Determine number of buckets – heuristic: √len
    n = len(lst)
    bucket_count = max(1, int(n ** 0.5))
    bucket_range = (max_val - min_val) // bucket_count + 1

    buckets = [[] for _ in range(bucket_count)]
    for x in lst:
        idx = (x - min_val) // bucket_range
        # Ensure index within range (edge case for max value)
        if idx >= bucket_count:
            idx = bucket_count - 1
        buckets[idx].append(x)

    result = []
    for bucket in buckets:
        # sort each bucket (use insertion sort, but any sort works)
        for i in range(1, len(bucket)):
            key = bucket[i]
            j = i - 1
            while j >= 0 and bucket[j] > key:
                bucket[j + 1] = bucket[j]
                j -= 1
            bucket[j + 1] = key
        result.extend(bucket)
    return result