def merge_sort(lst: list) -> list:
    """Return a new list sorted by merge sort (top-down, recursive)."""
    if not isinstance(lst, list):
        raise TypeError("Input must be a list")
    if len(lst) <= 1:
        return lst[:]
    mid = len(lst) // 2
    left = merge_sort(lst[:mid])
    right = merge_sort(lst[mid:])
    return _merge(left, right)

def _merge(left: list, right: list) -> list:
    """Merge two sorted lists into one sorted list."""
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