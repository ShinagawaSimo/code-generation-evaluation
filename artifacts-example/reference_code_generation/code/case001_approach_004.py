def sort(lst: list) -> list:
    if not isinstance(lst, list):
        raise TypeError("Input must be a list")
    if not lst:
        return []
    arr = lst.copy()
    n = len(arr)
    for i in range(1, n):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr