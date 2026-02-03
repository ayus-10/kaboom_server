from typing import Any

from typing_extensions import Optional


def get_sanitized_str(data: Any, key: str) -> Optional[str]:
    value = data.get(key)
    if not isinstance(value, str):
        return None
    value_stripped = value.strip()
    return value_stripped or None

def get_sanitized_bool(data: Any, key: str) -> Optional[bool]:
    value = data.get(key)
    if not isinstance(value, bool):
        return None
    return value
