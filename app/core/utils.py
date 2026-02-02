from typing import Any


def get_sanitized_str(data: Any, key: str):
    value = data.get(key)
    if not isinstance(value, str):
        return None
    value_stripped = value.strip()
    return value_stripped or None
