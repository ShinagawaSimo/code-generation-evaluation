def sort_people_by_unit(people_list: list) -> list:
    def merge(left, right):
        merged = []
        i = j = 0
        while i < len(left) and j < len(right):
            if left[i].unit <= right[j].unit:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1
        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged

    def mergesort(arr):
        if len(arr) <= 1:
            return arr
        mid = len(arr) // 2
        left = mergesort(arr[:mid])
        right = mergesort(arr[mid:])
        return merge(left, right)

    return mergesort(people_list)