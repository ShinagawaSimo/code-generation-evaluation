def sort_people_by_unit(people_list: list) -> list:
    arr = people_list[:]

    def quicksort(lo, hi):
        if lo >= hi:
            return
        pivot = arr[hi].unit
        i = lo
        for j in range(lo, hi):
            if arr[j].unit <= pivot:
                arr[i], arr[j] = arr[j], arr[i]
                i += 1
        arr[i], arr[hi] = arr[hi], arr[i]
        quicksort(lo, i - 1)
        quicksort(i + 1, hi)

    quicksort(0, len(arr) - 1)
    return arr