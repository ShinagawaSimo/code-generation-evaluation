def sort_people_by_unit(people_list: list) -> list:
    return sorted(people_list, key=lambda p: p.unit)