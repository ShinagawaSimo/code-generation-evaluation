def sort(lst: list[int]) -> list[int]:
    if not lst:
        return []
    import heapq
    arr = lst[:]
    heapq.heapify(arr)
    return [heapq.heappop(arr) for _ in range(len(lst))]