# -*- coding: utf-8 -*-
import os
import sys

def send(title: str, content: str):
    """青龙通知（sendNotify/notify），并尽量保证在青龙环境可导入。"""
    ql_scripts = "/ql/data/scripts"
    if os.path.isdir(ql_scripts) and ql_scripts not in sys.path:
        sys.path.insert(0, ql_scripts)

    for mod_name in ("sendNotify", "notify"):
        try:
            mod = __import__(mod_name)
            if hasattr(mod, "sendNotify"):
                mod.sendNotify(title, content)
                return
            if hasattr(mod, "send"):
                mod.send(title, content)
                return
        except Exception as e:
            print(f"[Notify] {mod_name} failed: {e}")
            continue

    print("[Notify] no notifier available (sendNotify/notify not found)")
