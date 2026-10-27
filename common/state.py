# -*- coding: utf-8 -*-
import json
import os
from typing import Dict, Any

DEFAULT_STATE_FILE = os.getenv("CHECKIN_STATE_FILE", "/ql/data/checkin_state.json")

def _load(path: str) -> Dict[str, Any]:
    try:
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}

def _save(path: str, data: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception:
        pass

def get_fail_count(key: str, state_file: str = DEFAULT_STATE_FILE) -> int:
    data = _load(state_file)
    return int(data.get(key, {}).get("fail_count", 0) or 0)

def set_fail_count(key: str, count: int, state_file: str = DEFAULT_STATE_FILE) -> None:
    data = _load(state_file)
    obj = data.get(key, {})
    obj["fail_count"] = int(count)
    data[key] = obj
    _save(state_file, data)

def reset_fail(key: str, state_file: str = DEFAULT_STATE_FILE) -> None:
    set_fail_count(key, 0, state_file=state_file)
