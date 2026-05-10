def sort(lst: list) -> list:
    if not isinstance(lst, list):
        raise TypeError("Input must be a list")
    if not lst:
        return []
    arr = lst.copy()
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr