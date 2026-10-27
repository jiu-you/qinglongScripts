# -*- coding: utf-8 -*-
import os
import time
import requests

def must_env(name: str) -> str:
    v = os.getenv(name)
    if v is None or not str(v).strip():
        raise RuntimeError(f"缺少环境变量：{name}")
    return str(v).strip()

def opt_env(name: str, default: str = "") -> str:
    v = os.getenv(name)
    if v is None:
        return default
    return str(v).strip()

def env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    s = str(v).strip().lower()
    return s not in ("0", "false", "no", "off", "")

def env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None or str(v).strip() == "":
        return default
    try:
        return int(str(v).strip())
    except Exception:
        return default

def join_url(base: str, path: str) -> str:
    base = base.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return base + path

def build_session(cookie: str, ua: str = None, referer: str = None) -> requests.Session:
    s = requests.Session()
    headers = {
        "Cookie": cookie,
        "User-Agent": ua or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/120 Safari/537.36",
    }
    if referer:
        headers["Referer"] = referer
    s.headers.update(headers)
    return s

def now_ts() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
