def sort(lst: list) -> list:
    if not isinstance(lst, list):
        raise TypeError("Input must be a list")
    if not lst:
        return []

    def _quicksort(arr: list, low: int, high: int) -> None:
        if low < high:
            pi = _partition(arr, low, high)
            _quicksort(arr, low, pi - 1)
            _quicksort(arr, pi + 1, high)

    def _partition(arr: list, low: int, high: int) -> int:
        pivot = arr[high]
        i = low - 1
        for j in range(low, high):
            if arr[j] <= pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
        arr[i + 1], arr[high] = arr[high], arr[i + 1]
        return i + 1

    arr = lst.copy()
    _quicksort(arr, 0, len(arr) - 1)
    return arr