def sort(lst: list[int]) -> list[int]:
    if not lst:
        return []
    if len(lst) <= 1:
        return lst[:]
    mid = len(lst) // 2
    left = sort(lst[:mid])
    right = sort(lst[mid:])
    i = j = 0
    merged = []
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged