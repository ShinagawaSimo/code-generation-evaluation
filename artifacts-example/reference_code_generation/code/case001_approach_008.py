def sort(lst: list) -> list:
    if not isinstance(lst, list):
        raise TypeError("Input must be a list")
    if not lst:
        return []
    if not all(isinstance(x, int) for x in lst):
        raise TypeError("All elements must be integers")

    arr = lst.copy()
    min_val = min(arr)
    max_val = max(arr)
    offset = -min_val
    range_len = max_val - min_val + 1
    count = [0] * range_len

    for num in arr:
        count[num + offset] += 1

    # Modify count to store cumulative positions
    for i in range(1, len(count)):
        count[i] += count[i - 1]

    output = [0] * len(arr)
    # Traverse from end to maintain stability
    for num in reversed(arr):
        idx = count[num + offset] - 1
        output[idx] = num
        count[num + offset] -= 1

    return output