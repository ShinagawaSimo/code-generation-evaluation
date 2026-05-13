def sort(lst: list[int]) -> list[int]:
    if not lst:
        return []
    if len(lst) <= 1:
        return lst[:]
    pivot = lst[-1]
    less = [x for x in lst[:-1] if x <= pivot]
    greater = [x for x in lst[:-1] if x > pivot]
    return sort(less) + [pivot] + sort(greater)