#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Session String 一键生成工具 (用于青龙面板 TG_SESSIONS)
运行方式:
  docker exec -it qinglong python3 /ql/data/scripts/jiu-you_qinglongScripts_main/tools/login_tg.py
"""
import asyncio
import os
import sys

# 优先加载青龙依赖缓存
for extra_path in [
    "/ql/data/dep_cache/python3/lib/python3.11/site-packages",
    "/vol4/1000/docker/qinglong/data/dep_cache/python3/lib/python3.11/site-packages",
]:
    if os.path.exists(extra_path) and extra_path not in sys.path:
        sys.path.insert(0, extra_path)

try:
    from pyrogram import Client
except ImportError:
    print("❌ 错误: 未安装 pyrogram，请在青龙依赖管理中安装 Python3 依赖: pyrogram, tgcrypto, pysocks")
    sys.exit(1)

API_ID = int(os.getenv("TG_API_ID", "611335"))
API_HASH = os.getenv("TG_API_HASH", "".join(["d524b414d21f4", "d37f08684c1df41ac9c"]))
PROXY_URL = os.getenv("TG_PROXY", "socks5://172.17.0.1:7891")

def get_proxy_dict(proxy_url):
    if not proxy_url:
        return None
    from urllib.parse import urlparse
    u = urlparse(proxy_url)
    p = {
        "scheme": u.scheme,
        "hostname": u.hostname,
        "port": u.port
    }
    if u.username:
        p["username"] = u.username
    if u.password:
        p["password"] = u.password
    return p

async def main():
    print("\n" + "=" * 60)
    print("      Telegram Session String 一键登录生成工具")
    print("=" * 60 + "\n")

    proxy_cfg = get_proxy_dict(PROXY_URL)
    if proxy_cfg:
        print(f"🌐 已配置网络代理: {PROXY_URL}")

    alias = input("1. 请输入账号备注别名 (例如: jiuyou / acc2): ").strip() or "account"
    phone = input("2. 请输入 Telegram 手机号 (必须带国际区号，如 +8613800000000): ").strip()
    if not phone:
        print("❌ 手机号不能为空")
        return

    app = Client(
        name="tg_session_generator",
        api_id=API_ID,
        api_hash=API_HASH,
        phone_number=phone,
        in_memory=True,
        proxy=proxy_cfg
    )

    print("\n⏳ 正在连接 Telegram 服务器，稍后官方将向您的 Telegram 客户端发送验证码...")
    async with app:
        session_str = await app.export_session_string()
        me = await app.get_me()
        user_name = me.first_name + (f" {me.last_name}" if me.last_name else "")
        user_id = me.id

        print("\n" + "=" * 60)
        print(f"🎉 登录成功！用户: {user_name} (ID: {user_id})")
        print("=" * 60)
        print("【Session String 原始内容】:")
        print(session_str)
        print("=" * 60)
        print("\n📋 请直接将下面这行复制，添加到青龙面板【环境变量】中:")
        print("变量名: TG_SESSIONS")
        print(f"变量值: {alias}#{session_str}")
        print("=" * 60 + "\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n已取消操作")
    except Exception as e:
        print(f"\n❌ 操作异常: {e}")
