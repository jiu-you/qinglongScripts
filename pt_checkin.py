#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cron: 0 8 * * *
new Env('PT站签到')
"""

from __future__ import annotations

import json
import os
import random
import re
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Type
from urllib.parse import parse_qsl

import warnings
warnings.filterwarnings("ignore")

import requests

# ---------------- 统一通知模块加载 ----------------
for p in ["/ql/data/scripts", "..", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]:
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)
os.environ.setdefault("HITOKOTO", "false")

hadsend = False
send = None
try:
    from notify import send
    hadsend = True
except Exception:
    pass

def notify_send(title: str, content: str):
    if hadsend and send:
        try:
            send(title, content)
            return
        except Exception as e:
            print(f"[Notify] 发送通知失败: {e}")
    print(f"📢 {title}\n{content}")

# ---------------- 通用状态持久化 ----------------
DEFAULT_STATE_FILE = os.getenv("CHECKIN_STATE_FILE", "/ql/data/checkin_state.json")

def _load_state(path: str) -> Dict[str, Any]:
    try:
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}

def _save_state(path: str, data: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception:
        pass

def get_fail_count(key: str, state_file: str = DEFAULT_STATE_FILE) -> int:
    data = _load_state(state_file)
    return int(data.get(key, {}).get("fail_count", 0) or 0)

def set_fail_count(key: str, count: int, state_file: str = DEFAULT_STATE_FILE) -> None:
    data = _load_state(state_file)
    obj = data.get(key, {})
    obj["fail_count"] = int(count)
    data[key] = obj
    _save_state(state_file, data)

def reset_fail(key: str, state_file: str = DEFAULT_STATE_FILE) -> None:
    set_fail_count(key, 0, state_file=state_file)

# ---------------- 工具辅助函数 ----------------
def now_ts() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def opt_env(name: str, default: str = "") -> str:
    v = os.getenv(name)
    return default if v is None else str(v).strip()

def env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return str(v).strip().lower() not in ("0", "false", "no", "off", "")

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

def _parse_post_data(raw: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    raw = (raw or "").strip()
    if not raw:
        return "none", None
    if raw.startswith("{") and raw.endswith("}"):
        try:
            return "json", json.loads(raw)
        except Exception:
            pass
    return "form", dict(parse_qsl(raw, keep_blank_values=True))

@dataclass
class CheckinResult:
    ok: bool
    message: str
    status_code: int = 0
    url: str = ""
    notified: bool = False

# ---------------- PT 站点基类 ----------------
class PTCheckinBase:
    site_name: str = "PT Site"
    env_prefix: str = "PT"

    default_sign_path: str = "/attendance.php"
    default_method: str = "GET"
    default_preflight_path: str = ""

    success_keywords = [
        r"success", r"签到成功", r"已签到", r"check.?in", r"attend",
        r"奖励", r"魔力", r"积分", r"bonus",
    ]

    csrf_regex: str = ""
    csrf_field_name: str = "csrf_token"

    retries: int = 1
    retry_sleep_sec: float = 2.0

    enable_random_delay: bool = True
    default_random_start_hour: int = 8
    default_random_end_hour: int = 20

    default_notify_on_success: bool = True
    default_fail_notify_threshold: int = 1
    default_enable: bool = True

    def env(self, name: str, default: str = "") -> str:
        return opt_env(f"{self.env_prefix}_{name}", default)

    def enabled(self) -> bool:
        return env_bool(f"{self.env_prefix}_ENABLE", self.default_enable)

    def base_url(self) -> str:
        return self.env("BASE_URL").strip()

    def cookie(self) -> str:
        return self.env("COOKIE").strip()

    def ua(self) -> str:
        return self.env(
            "UA",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120 Safari/537.36",
        )

    def referer(self) -> str:
        base = self.base_url()
        return self.env("REFERER", base.rstrip("/") + "/" if base else "")

    def method(self) -> str:
        return (self.env("METHOD", self.default_method) or "GET").upper()

    def sign_path(self) -> str:
        return self.env("SIGN_PATH", self.default_sign_path) or self.default_sign_path

    def preflight_path(self) -> str:
        return self.env("PREFLIGHT_PATH", self.default_preflight_path)

    def post_data_raw(self) -> str:
        return self.env("POST_DATA", "")

    def timeout(self) -> int:
        return env_int(f"{self.env_prefix}_TIMEOUT", 20)

    def build(self) -> requests.Session:
        return build_session(cookie=self.cookie(), ua=self.ua(), referer=self.referer())

    def notify_on_success(self) -> bool:
        return env_bool(f"{self.env_prefix}_NOTIFY_ON_SUCCESS", self.default_notify_on_success)

    def fail_notify_threshold(self) -> int:
        return env_int(f"{self.env_prefix}_FAIL_NOTIFY_THRESHOLD", self.default_fail_notify_threshold)

    def _should_notify_on_fail(self, fail_count: int) -> bool:
        th = max(1, self.fail_notify_threshold())
        return fail_count >= th

    def random_delay_enabled(self) -> bool:
        if env_bool("CHECKIN_SKIP_RANDOM_DELAY", False):
            return False
        v = self.env("RANDOM_DELAY", "1" if self.enable_random_delay else "0").strip().lower()
        return v not in ("0", "false", "no", "off", "")

    def random_window(self) -> Tuple[int, int]:
        start = env_int(f"{self.env_prefix}_RANDOM_START_HOUR", self.default_random_start_hour)
        end = env_int(f"{self.env_prefix}_RANDOM_END_HOUR", self.default_random_end_hour)
        if end < start:
            start, end = end, start
        if end == start:
            end = min(24, start + 1)
        start = max(0, min(23, start))
        end = max(1, min(24, end))
        if end <= start:
            end = min(24, start + 1)
        return start, end

    def maybe_sleep_random(self):
        if not self.random_delay_enabled():
            return
        seed = self.env("RANDOM_SEED", "").strip()
        if seed:
            try:
                random.seed(seed)
            except Exception:
                pass
        start, end = self.random_window()
        delay_max = (end - start) * 3600
        delay = random.randint(0, max(0, delay_max))
        print(f"[{now_ts()}] [RandomDelay] {self.site_name} window={start:02d}:00-{end:02d}:00 sleep={delay}s")
        time.sleep(delay)

    def build_payload(self, csrf_token: str = "") -> Tuple[str, Optional[Dict[str, Any]]]:
        kind, data = _parse_post_data(self.post_data_raw())
        if csrf_token and kind != "none" and data is not None and self.csrf_field_name:
            data.setdefault(self.csrf_field_name, csrf_token)
        return kind, data

    def extract_csrf(self, html: str) -> str:
        if not self.csrf_regex:
            return ""
        m = re.search(self.csrf_regex, html or "", re.I)
        return m.group(1) if m else ""

    def is_success(self, resp: requests.Response, text: str) -> bool:
        if not (200 <= resp.status_code < 400):
            return False
        for pat in self.success_keywords:
            if re.search(pat, text or "", re.I):
                return True
        return False

    def format_message(self, ok: bool, url: str, resp: Optional[requests.Response], text: str, note: str = "") -> str:
        sc = resp.status_code if resp is not None else 0
        snippet = (text[:220] + "...") if text and len(text) > 220 else (text or "")
        status = "✅" if ok else "❌"
        extra = f"\n{note}" if note else ""
        return (
            f"[{now_ts()}]\n"
            f"{status} {self.site_name} 签到{'成功' if ok else '失败/未识别'}\n"
            f"URL: {url}\nHTTP: {sc}{extra}\n"
            f"Snippet: {snippet}"
        )

    def run(self, notify: bool = True) -> CheckinResult:
        title = f"{self.site_name} 签到"
        base = self.base_url()
        cookie = self.cookie()

        if not base or not cookie:
            msg = f"[{now_ts()}]\n⏭️ 未配置 {self.env_prefix}_BASE_URL 或 {self.env_prefix}_COOKIE，跳过该站点"
            print(msg)
            return CheckinResult(ok=True, message=msg, status_code=0, url="", notified=False)

        if not self.enabled():
            msg = f"[{now_ts()}]\n⏭️ {self.site_name} 已禁用（{self.env_prefix}_ENABLE=0）"
            print(msg)
            return CheckinResult(ok=True, message=msg, status_code=0, url="", notified=False)

        self.maybe_sleep_random()

        s = self.build()
        sign_url = join_url(base, self.sign_path())
        preflight = (self.preflight_path() or "").strip()

        last_err = ""
        for attempt in range(self.retries + 1):
            try:
                csrf = ""
                note = ""
                if preflight:
                    pf_url = join_url(base, preflight)
                    pf = s.get(pf_url, timeout=self.timeout(), allow_redirects=True)
                    csrf = self.extract_csrf(pf.text or "")
                    if self.csrf_regex:
                        note = f"CSRF: {'OK' if csrf else 'EMPTY'}"

                m = self.method()
                kind, payload = self.build_payload(csrf_token=csrf)

                if m == "POST":
                    if kind == "json":
                        resp = s.post(sign_url, json=payload, timeout=self.timeout(), allow_redirects=True)
                    elif kind == "form":
                        resp = s.post(sign_url, data=payload, timeout=self.timeout(), allow_redirects=True)
                    else:
                        resp = s.post(sign_url, timeout=self.timeout(), allow_redirects=True)
                else:
                    resp = s.get(sign_url, timeout=self.timeout(), allow_redirects=True)

                text = resp.text or ""
                ok = self.is_success(resp, text)

                state_key = self.env_prefix
                notified = False
                if ok:
                    reset_fail(state_key)
                else:
                    fc = get_fail_count(state_key) + 1
                    set_fail_count(state_key, fc)
                    if notify and self._should_notify_on_fail(fc):
                        notify_send(
                            title,
                            f"连续失败 {fc} 次（阈值 {self.fail_notify_threshold()}）\n\n"
                            + self.format_message(ok, sign_url, resp, text, note=note),
                        )
                        notified = True

                if ok and notify and self.notify_on_success():
                    notify_send(title, self.format_message(ok, sign_url, resp, text, note=note))
                    notified = True

                msg = self.format_message(ok, sign_url, resp, text, note=note)
                print(msg)
                return CheckinResult(ok=ok, message=msg, status_code=resp.status_code, url=sign_url, notified=notified)

            except Exception as e:
                last_err = str(e)
                if attempt < self.retries:
                    time.sleep(self.retry_sleep_sec)
                continue

        state_key = self.env_prefix
        fc = get_fail_count(state_key) + 1
        set_fail_count(state_key, fc)

        msg = f"[{now_ts()}]\n❌ {self.site_name} 签到异常：{last_err}\n连续失败 {fc} 次（阈值 {self.fail_notify_threshold()}）"
        print(msg)

        notified = False
        if notify and self._should_notify_on_fail(fc):
            notify_send(f"{self.site_name} 签到异常", msg)
            notified = True

        return CheckinResult(ok=False, message=msg, status_code=0, url=sign_url, notified=notified)

# ---------------- 具体站点实现 ----------------
class PTZoneCheckin(PTCheckinBase):
    site_name = "PTZone"
    env_prefix = "PTZONE"
    default_sign_path = "/attendance.php"
    default_method = "GET"

# 注册支持的站点列表
SUPPORTED_SITES: List[Type[PTCheckinBase]] = [
    PTZoneCheckin,
]

def global_random_sleep_once():
    # 默认 0 (立即执行)，避免手动测试或常规执行时无故等待数小时
    # 如需开启随机延迟，可在青龙环境变量中配置 CHECKIN_RANDOM_DELAY，例如：
    # CHECKIN_RANDOM_DELAY=300 (在 0~300 秒内随机等待)
    # CHECKIN_RANDOM_DELAY=60-180 (在 60~180 秒内随机等待)
    delay_config = opt_env("CHECKIN_RANDOM_DELAY", "0").strip().lower()
    if delay_config in ("0", "false", "no", "off", "", "none"):
        return

    delay = 0
    try:
        if "-" in delay_config or "~" in delay_config:
            parts = delay_config.replace("~", "-").split("-", 1)
            d_min = int(parts[0].strip())
            d_max = int(parts[1].strip())
            delay = random.randint(min(d_min, d_max), max(d_min, d_max))
        elif delay_config.isdigit():
            val = int(delay_config)
            if val == 1:
                # 兼容旧配置为 1 的情况：默认安全防风控延时 10~180 秒，绝不再休眠数小时
                delay = random.randint(10, 180)
            else:
                delay = random.randint(0, val)
        elif delay_config in ("true", "yes", "on"):
            delay = random.randint(10, 180)
    except Exception:
        delay = 0

    if delay > 0:
        print(f"[{now_ts()}] [RandomDelay] 防风控随机延时: 等待 {delay} 秒后开始签到...")
        time.sleep(delay)

def main():
    global_random_sleep_once()
    os.environ["CHECKIN_SKIP_RANDOM_DELAY"] = "1"

    failed = []
    ran_count = 0
    for site_cls in SUPPORTED_SITES:
        site = site_cls()
        if not site.base_url() or not site.cookie():
            continue
        ran_count += 1
        print("\n==============================")
        print(f"RUN PT: {site.site_name}")
        print("==============================")
        res = site.run(notify=True)
        if not res.ok:
            failed.append((site.site_name, res.message))

    if ran_count == 0:
        print(f"[{now_ts()}] ℹ️ 未配置任何 PT 站点环境变量（例如 PTZONE_BASE_URL 与 PTZONE_COOKIE）")
        return 0

    if failed:
        lines = [f"失败数量：{len(failed)}", ""]
        for name, msg in failed:
            lines.append(f"- {name} 签到失败")
        notify_send("PT站签到汇总：存在失败", "\n".join(lines).strip())
        return 1

    print(f"\n[{now_ts()}] ✅ 全部 PT 站点签到完成")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
