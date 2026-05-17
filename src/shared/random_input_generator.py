import json
import random
import string
from typing import Any, Dict, List


def generate_random_inputs(
    param_type: str,
    count: int,
    class_defs: Dict[str, List[str]] | None = None,
) -> str:
    """Generate random stdin lines for program_io evaluation.

    Each line represents one function call. Simple types (int, float, string, list[...])
    use plain text; custom class types use one JSON object per line.
    """
    lines = [_generate_line(param_type, class_defs or {}) for _ in range(count)]
    return "\n".join(lines)


def _generate_line(param_type: str, class_defs: Dict[str, List[str]]) -> str:
    t = param_type.strip().lower()

    if t in ("int", "integer"):
        return str(random.randint(-1000, 1000))

    if t == "float":
        return str(round(random.uniform(-1000.0, 1000.0), 4))

    if t == "string":
        return _random_string()

    if t.startswith("list[int]") or t.startswith("list[integer]"):
        return _random_list(lambda: str(random.randint(-1000, 1000)))

    if t.startswith("list[float]"):
        return _random_list(lambda: str(round(random.uniform(-1000.0, 1000.0), 4)))

    if t.startswith("list[str]") or t.startswith("list[string]"):
        return _random_list(_random_string)

    if t == "list":
        return _random_list(lambda: str(random.randint(-1000, 1000)))

    # Custom class: check if param_type or its list-wrapped form matches a class_def
    cls_name = t
    is_list = False
    if t.startswith("list[") and t.endswith("]"):
        cls_name = t[5:-1].strip()
        is_list = True

    # Look up class_defs case-insensitively
    match = next((v for k, v in class_defs.items() if k.lower() == cls_name.lower()), None)
    if match is not None:
        fields = match
        if is_list:
            instance_count = random.randint(3, 8)
            instances = [_random_class_instance(fields) for _ in range(instance_count)]
            return "\n".join(json.dumps(i) for i in instances)
        else:
            return json.dumps(_random_class_instance(fields))

    return ""  # fallback: empty input


def _random_class_instance(fields: List[str]) -> Dict[str, Any]:
    vals = {}
    for f in fields:
        fl = f.lower()
        if "name" in fl:
            vals[f] = _random_name()
        elif "gender" in fl or "sex" in fl:
            vals[f] = random.choice(["M", "F"])
        elif "age" in fl:
            vals[f] = random.randint(18, 65)
        elif "score" in fl or "grade" in fl or "mark" in fl:
            vals[f] = random.randint(0, 100)
        elif "unit" in fl or "dept" in fl or "department" in fl:
            vals[f] = random.choice(["Engineering", "Marketing", "Sales", "HR", "Finance"])
        else:
            vals[f] = _random_string()
    return vals


def _random_string() -> str:
    length = random.randint(3, 15)
    chars = []
    for _ in range(length):
        c = random.choice(string.ascii_letters)
        # ~40% chance of uppercase to create mixed-case strings
        if random.random() < 0.3:
            c = c.lower()
        chars.append(c)
    return "".join(chars)


def _random_name() -> str:
    first = random.choice(["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"])
    return first


def _random_list(fn) -> str:
    n = random.randint(3, 10)
    return " ".join(fn() for _ in range(n))
