from typing import Dict, Any

def validate_data(d: Dict[str, Any]) -> bool:
    if not isinstance(d, dict):
        return False
    if "drugs" not in d or not isinstance(d["drugs"], list):
        return False
    for item in d["drugs"]:
        if not isinstance(item, dict):
            return False
        if not item.get("name"):
            return False
    return True
