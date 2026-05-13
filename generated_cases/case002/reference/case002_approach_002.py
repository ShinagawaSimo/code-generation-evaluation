def sort_people_by_unit(people_list: list) -> list:
    result = people_list[:]
    result.sort(key=lambda p: p.unit)
    return result