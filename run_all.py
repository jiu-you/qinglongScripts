#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cron: 0 8 * * *
new Env('PT站签到')
"""

"""一键执行 scripts/*_checkin.py

已实现：
- 只随机一次（run_all 自己随机 sleep，子脚本跳过随机）
- 失败汇总通知（有失败才通知）
"""

import os
import sys
import glob
import time
import random
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(ROOT, "scripts")

def now():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def random_sleep_once():
    if os.getenv("CHECKIN_RANDOM_DELAY", "1").strip().lower() in ("0","false","no","off",""):
        return
    try:
        start = int(os.getenv("CHECKIN_RANDOM_START_HOUR", "8"))
    except Exception:
        start = 8
    try:
        end = int(os.getenv("CHECKIN_RANDOM_END_HOUR", "20"))
    except Exception:
        end = 20
    if end < start:
        start, end = end, start
    if end == start:
        end = start + 1
    start = max(0, min(23, start))
    end = max(1, min(24, end))
    delay_max = (end - start) * 3600
    delay = random.randint(0, max(0, delay_max))
    print(f"[{now()}] [RunAllRandomDelay] window={start:02d}:00-{end:02d}:00 sleep={delay}s")
    time.sleep(delay)

def main():
    random_sleep_once()

    files = sorted(glob.glob(os.path.join(SCRIPTS_DIR, "*_checkin.py")))
    if not files:
        print("未找到 *_checkin.py")
        return 0

    print(f"发现 {len(files)} 个签到脚本：")
    for f in files:
        print(" -", os.path.relpath(f, ROOT))

    child_env = os.environ.copy()
    child_env["CHECKIN_SKIP_RANDOM_DELAY"] = "1"

    failed = []
    for f in files:
        rel = os.path.relpath(f, ROOT)
        print("\n==============================")
        print("RUN:", rel)
        print("==============================")
        p = subprocess.run([sys.executable, f], cwd=ROOT, env=child_env, capture_output=True, text=True)

        out = (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")
        if out.strip():
            print(out.rstrip())

        if p.returncode != 0:
            snippet = out[-800:] if len(out) > 800 else out
            failed.append((rel, p.returncode, (snippet or "").strip()))

    if failed:
        try:
            sys.path.insert(0, ROOT)
            from common.notify_ql import send as notify_send
            lines = [f"失败数量：{len(failed)}", ""]
            for rel, code, snippet in failed:
                lines.append(f"- {rel} (code={code})")
                if snippet:
                    lines.append("  输出(截断)：")
                    for line in snippet.splitlines()[-12:]:
                        lines.append("    " + line[:240])
                lines.append("")
            notify_send("签到汇总：存在失败", "\n".join(lines).strip())
        except Exception as e:
            print(f"[RunAll] notify failed: {e}")
        return 1

    print(f"[{now()}] ✅ 全部脚本执行成功")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())