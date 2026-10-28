#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cron: 0 8 * * *
new Env('Telegram多账号多任务通用签到')

====================================================================================================
                              【Telegram 多账号多任务通用签到配置指南】
====================================================================================================

一、环境变量说明 (在青龙面板 -> 环境变量 中添加或修改):

1. 账号凭据 (必需其一):
   -------------------------------------------------------------------------------------------------
   变量名: TG_SESSIONS 或 TG_SHEERID_SESSIONS
   说明: Telegram 会话字符串 (Pyrogram Session String)
   支持两种配置方式:
     【方式 A - 单条多行/&分隔】:
       值:
       jiuyou#BQAJVAcAir...
       gogostory#AQAJVAcAqn...
       或单行用 & 连接: jiuyou#BQA...&gogostory#AQA...
     【方式 B - 多条独立变量】(青龙推荐，便于单独启用/禁用):
       新建变量 1: 名称 TG_SESSIONS, 值 jiuyou#BQA..., 备注: 账号1
       新建变量 2: 名称 TG_SESSIONS, 值 gogostory#AQA..., 备注: 账号2

   注: 如果未配置以上环境变量，脚本会自动寻找本地 /ql/data/scripts/tg_sessions/*.session_string 作为后备。

2. 签到任务列表 (TG_SIGN_TASKS) - 支持两种语法格式:
   -------------------------------------------------------------------------------------------------
   变量名: TG_SIGN_TASKS
   说明: 需要签到的 Bot 及指令列表。如果未配置该变量，默认仅执行 SheerID 签到。

   【格式 1: 简易文本格式 (推荐，最简单直观)】
     每行一条任务，使用 # 分隔字段，格式为:
     任务名称#@Bot用户名#发送指令#需点击的按钮文字(可选)

     示例 (多任务换行或用 & 连接):
     SheerID验证签到#@sheeridverifier_bot#/checkin
     某机场签到#@example_bot#/checkin#今日签到
     极搜打卡#@jisou_bot#/sign

     字段详解:
       - 字段1: 任务自定义名称 (用于通知和日志中展示)
       - 字段2: 目标 Bot 用户名 (以 @ 开头，或直接填纯用户名)
       - 字段3: 需要向 Bot 发送的文本指令 (如 /checkin, /sign, 签到 等)
       - 字段4: (可选) 内联按钮文字。若有些 Bot 发送指令后会弹出一排按钮，需要点击其中一个
                按钮才算签到，在此填入按钮上的文字 (支持模糊匹配，如 "点击签到")。

   【格式 2: 标准 JSON 格式 (适合高级配置)】
     值例如:
     [
       {
         "name": "SheerID验证签到",
         "bot": "@sheeridverifier_bot",
         "cmd": "/checkin"
       },
       {
         "name": "某机场签到",
         "bot": "@example_bot",
         "cmd": "/checkin",
         "button": "今日签到"
       }
     ]

3. 网络代理 (TG_PROXY) [可选]:
   -------------------------------------------------------------------------------------------------
   变量名: TG_PROXY
   默认值: socks5://172.17.0.1:7891 (本地 glash 节点)
   格式: socks5://ip:port 或 http://ip:port (带认证: socks5://user:pwd@ip:port)

4. 防风控随机延时配置 [可选]:
   -------------------------------------------------------------------------------------------------
   【变量 1: 脚本启动全局随机延时 (RANDOM_DELAY)】
     变量名: RANDOM_DELAY
     默认值: 0 (立即执行)
     说明: 脚本启动后的初始随机等待时间。支持单个数字或范围:
           - 填 1800: 在 0~1800 秒 (0~30分钟) 内随机等待后再开始；
           - 填 300-1800: 在 5~30 分钟内随机等待。
     适用: 避免每天在固定秒数触发打卡。

   【变量 2: 账号间防风控随机间隔 (TG_ACCOUNT_DELAY)】
     变量名: TG_ACCOUNT_DELAY
     默认值: 15-45 (秒)
     说明: 跑完前一个账号后、开始跑下一个账号之间的随机等待间隔。
           - 推荐设置: 60-300 (即 1~5 分钟随机间隔)
           - 填 120: 在 0~120 秒内随机等待
     适用: 避免多个账号在同一时间密集向 Telegram 发起请求而被风控。

   【变量 3: 同一账号多任务间隔 (TG_TASK_DELAY)】
     变量名: TG_TASK_DELAY
     默认值: 3-8 (秒)
     说明: 同一个账号连续向不同 Bot 签到时的间隔缓冲时间。
           - 推荐设置: 5-15 (秒)

   【高阶方式: 单独为特定账号指定私有延迟】
     在 TG_SESSIONS 中支持第 3 个字段指定该账号独享延迟:
     格式: 账号别名#Session字符串#独享延迟秒数(如 60 或 60-180)
     示例: jiuyou#BQA...#120-300 (该账号会在执行前专属等待 2~5 分钟)

====================================================================================================
"""

import os
import sys
import json
import time
import random
import asyncio
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

# 确保在 Python 3.12+ / 3.14 下安全导入 pyrogram
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# 如果有额外的 site-packages (如青龙 dep_cache)
for extra_path in [
    "/ql/data/dep_cache/python3/lib/python3.11/site-packages",
    "/vol4/1000/docker/qinglong/data/dep_cache/python3/lib/python3.11/site-packages",
]:
    if os.path.exists(extra_path) and extra_path not in sys.path:
        sys.path.insert(0, extra_path)

import warnings
warnings.filterwarnings("ignore")

try:
    from pyrogram import Client
except ImportError:
    print("❌ 错误: 未安装 pyrogram，请在青龙依赖管理中安装 Python3 依赖: pyrogram, tgcrypto, pysocks")
    sys.exit(1)

# 尝试导入青龙通知
for p in ["/ql/data/scripts", "..", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]:
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)
os.environ.setdefault("HITOKOTO", "false")

try:
    from notify import send
except Exception:
    def send(title, content):
        pass

# 官方 Android API 凭据
DEFAULT_API_ID = 611335
DEFAULT_API_HASH = os.getenv("TG_API_HASH", "".join(["d524b414d21f4", "d37f08684c1df41ac9c"]))

# 默认保底任务 (若未配置任何环境变量时生效)
DEFAULT_TASKS = [
    {
        "name": "SheerID验证签到",
        "bot": "@sheeridverifier_bot",
        "cmd": "/checkin",
        "button": None
    }
]

def parse_delay_range(val: str, default_min: int, default_max: int) -> int:
    """
    解析延时配置，支持格式:
    - "60-300" 或 "60~300" (返回 60 到 300 之间的随机秒数)
    - "180" (返回 0 到 180 之间的随机秒数)
    - "0" (返回 0)
    """
    if not val:
        return random.randint(default_min, default_max) if default_max > default_min else default_min
    val = str(val).strip().replace("~", "-").replace("，", ",").replace(",", "-")
    try:
        if "-" in val:
            parts = val.split("-", 1)
            v_min = int(parts[0].strip())
            v_max = int(parts[1].strip())
            if v_min > v_max:
                v_min, v_max = v_max, v_min
            return random.randint(v_min, v_max)
        else:
            v = int(val)
            if v <= 0:
                return 0
            return random.randint(0, v)
    except Exception:
        return random.randint(default_min, default_max) if default_max > default_min else default_min

def parse_proxy(proxy_url: str):
    """解析 HTTP / SOCKS5 代理地址"""
    if not proxy_url:
        return None
    try:
        p = urlparse(proxy_url)
        scheme = p.scheme or "socks5"
        hostname = p.hostname or "127.0.0.1"
        port = p.port or 7891
        res = {
            "scheme": scheme,
            "hostname": hostname,
            "port": port
        }
        if p.username:
            res["username"] = p.username
        if p.password:
            res["password"] = p.password
        return res
    except Exception as e:
        print(f"⚠️ 解析代理地址 [{proxy_url}] 失败: {e}")
        return None

def load_accounts():
    """
    加载待签到的账号列表:
    1. 优先读取环境变量 TG_SESSIONS 或 TG_SHEERID_SESSIONS
    2. 其次读取本地 tg_sessions 目录下的 session_string 文件
    """
    accounts = []
    env_sessions = (os.getenv("TG_SESSIONS") or os.getenv("TG_SHEERID_SESSIONS", "")).strip()
    if env_sessions:
        raw_items = []
        for line in env_sessions.splitlines():
            line = line.strip()
            if not line:
                continue
            if "&" in line:
                raw_items.extend([x.strip() for x in line.split("&") if x.strip()])
            else:
                raw_items.append(line)

        for idx, item in enumerate(raw_items, 1):
            custom_delay = None
            if "#" in item:
                parts = item.split("#")
                name = parts[0]
                session_str = parts[1]
                if len(parts) >= 3 and parts[2]:
                    custom_delay = parts[2].strip()
            elif "@" in item and not (item.startswith("1") or item.startswith("BQA") or item.startswith("AQA") or item.startswith("BAA")):
                name, session_str = item.split("@", 1)
            else:
                name, session_str = f"Account_{idx}", item
            accounts.append({
                "name": name.strip(),
                "session": session_str.strip(),
                "delay": custom_delay
            })

    if not accounts:
        # 从本地 session 文件目录查找 fallback
        candidates = [
            Path("/ql/data/scripts/tg_sessions"),
            Path(__file__).parent / "tg_sessions",
            Path("/vol4/1000/docker/qinglong/data/scripts/tg_sessions"),
        ]
        for dir_path in candidates:
            if dir_path.exists():
                for sf in sorted(dir_path.glob("*.session_string")):
                    try:
                        content = sf.read_text(encoding="utf-8").strip()
                        if content:
                            accounts.append({"name": sf.stem, "session": content})
                    except Exception as e:
                        print(f"⚠️ 读取 Session 文件 {sf} 失败: {e}")
                if accounts:
                    break

    return accounts

def load_tasks():
    """
    加载签到任务列表:
    优先读取环境变量 TG_SIGN_TASKS (支持简易文本 # 格式与 JSON 格式)
    如果未配置，默认返回 DEFAULT_TASKS (SheerID签到)
    """
    tasks_env = os.getenv("TG_SIGN_TASKS", "").strip()
    if not tasks_env:
        return DEFAULT_TASKS

    tasks = []
    # 尝试作为 JSON 解析
    if tasks_env.startswith("[") or tasks_env.startswith("{"):
        try:
            data = json.loads(tasks_env)
            if isinstance(data, dict):
                data = [data]
            for item in data:
                tasks.append({
                    "name": item.get("name") or item.get("bot", "未知任务"),
                    "bot": item.get("bot", "").strip(),
                    "cmd": item.get("cmd", "/checkin").strip(),
                    "button": item.get("button", None)
                })
            return tasks
        except Exception as e:
            print(f"⚠️ 解析 TG_SIGN_TASKS 为 JSON 失败 ({e})，尝试按文本行解析...")

    # 按简易行格式解析: 任务名#@bot用户名#指令#按钮文字(可选)
    lines = []
    for line in tasks_env.splitlines():
        line = line.strip()
        if not line or line.startswith("//") or line.startswith("# "):
            continue
        if "&" in line and not line.startswith("@"):
            lines.extend([x.strip() for x in line.split("&") if x.strip()])
        else:
            lines.append(line)

    for idx, line in enumerate(lines, 1):
        parts = [p.strip() for p in line.split("#")]
        if len(parts) >= 3:
            name, bot, cmd = parts[0], parts[1], parts[2]
            button = parts[3] if len(parts) >= 4 and parts[3] else None
        elif len(parts) == 2:
            # 格式: @bot#/checkin 或 任务名#@bot
            if parts[0].startswith("@"):
                name, bot, cmd, button = f"Task_{idx}", parts[0], parts[1], None
            else:
                name, bot, cmd, button = parts[0], parts[1], "/checkin", None
        elif len(parts) == 1 and parts[0].startswith("@"):
            # 仅填了 @bot
            name, bot, cmd, button = f"Task_{idx}", parts[0], "/checkin", None
        else:
            continue

        if not bot.startswith("@"):
            bot = "@" + bot

        tasks.append({
            "name": name,
            "bot": bot,
            "cmd": cmd,
            "button": button
        })

    return tasks if tasks else DEFAULT_TASKS

async def click_inline_button(msg, button_text: str):
    """尝试在消息的 InlineKeyboard 中寻找匹配的按钮并点击"""
    if not msg.reply_markup or not hasattr(msg.reply_markup, "inline_keyboard"):
        return False
    for row in msg.reply_markup.inline_keyboard:
        for btn in row:
            if btn.text and button_text in btn.text:
                try:
                    await msg.click(btn.text)
                    return True
                except Exception as e:
                    print(f"⚠️ 点击按钮 [{btn.text}] 出错: {e}")
                    return False
    return False

async def execute_task(app: Client, task: dict):
    """针对单个账号执行单个任务"""
    task_name = task["name"]
    bot = task["bot"]
    cmd = task["cmd"]
    button = task.get("button")

    print(f"\n  ▶ 正在执行任务: 【{task_name}】 -> 目标: {bot}")
    res = {
        "task_name": task_name,
        "bot": bot,
        "status": "失败",
        "detail": ""
    }

    try:
        # 记录发送指令前 bot 的最新消息 id
        sent_time = time.time()
        last_msg_id = 0
        try:
            async for m in app.get_chat_history(bot, limit=1):
                last_msg_id = m.id
        except Exception:
            pass

        # 1. 发送签到指令
        print(f"    💬 发送指令: {cmd}")
        sent_msg = await app.send_message(bot, cmd)

        # 2. 轮询等待 Bot 返回结果
        reply_msg = None
        for _ in range(10):
            await asyncio.sleep(2)
            async for m in app.get_chat_history(bot, limit=3):
                if m.id > sent_msg.id:
                    reply_msg = m
                    break
            if reply_msg:
                break

        if not reply_msg:
            print(f"    ⚠️ 指令已发出，但在 20 秒内未收到 {bot} 的回复")
            res["status"] = "待确认"
            res["detail"] = "已发送指令，Bot 暂未返回消息"
            return res

        # 3. 如果配置了内嵌按钮，尝试点击按钮
        if button:
            print(f"    🔘 检测并尝试点击按钮: [{button}]...")
            clicked = await click_inline_button(reply_msg, button)
            if clicked:
                print(f"    ✅ 成功点击按钮 [{button}]，等待结算回执...")
                # 等待点击后的回执更新
                await asyncio.sleep(3)
                async for m in app.get_chat_history(bot, limit=2):
                    if m.id >= reply_msg.id:
                        reply_msg = m
                        break
            else:
                print(f"    ⚠️ 未在回复消息中匹配到包含 [{button}] 的按钮")

        # 4. 获取回执文本
        reply_text = reply_msg.text or reply_msg.caption or "[富文本/媒体消息]"
        print(f"    📩 收到回复:\n{reply_text}")
        res["status"] = "成功"
        res["detail"] = reply_text

    except Exception as e:
        print(f"    ❌ 执行任务出错: {e}")
        res["status"] = "失败"
        res["detail"] = str(e)

    return res

async def process_account(account_info: dict, tasks: list, proxy_config: dict, api_id: int, api_hash: str):
    """处理单个账号下的所有任务"""
    account_name = account_info["name"]
    session_string = account_info["session"]

    print(f"\n==================================================")
    print(f"🚀 开始处理账号: 【{account_name}】")
    print(f"==================================================")

    app = Client(
        name=f"runner_{account_name}",
        api_id=api_id,
        api_hash=api_hash,
        session_string=session_string,
        in_memory=True,
        proxy=proxy_config,
    )

    acc_report = {
        "account": account_name,
        "user_id": "",
        "username": "",
        "tasks": []
    }

    try:
        await app.start()
        me = await app.get_me()
        user_display = f"{me.first_name or ''} {me.last_name or ''}".strip()
        acc_report["user_id"] = str(me.id)
        acc_report["username"] = me.username or user_display or str(me.id)
        if account_name.startswith("Account_"):
            account_name = f"{account_name} ({me.username or user_display})"
            acc_report["account"] = account_name
        print(f"👤 账号登录成功: {user_display} (@{me.username or '无'}) [ID: {me.id}]")

        task_delay_env = os.getenv("TG_TASK_DELAY", "3-8")
        for idx, task in enumerate(tasks):
            t_res = await execute_task(app, task)
            acc_report["tasks"].append(t_res)
            if idx < len(tasks) - 1:
                t_sleep = parse_delay_range(task_delay_env, 3, 8)
                print(f"    ⏱️ 任务间隔等待 {t_sleep} 秒...")
                await asyncio.sleep(t_sleep)

    except Exception as e:
        print(f"❌ 账号处理异常: {e}")
        acc_report["tasks"].append({
            "task_name": "全局连接",
            "status": "失败",
            "detail": f"账号连接失败: {e}"
        })
    finally:
        try:
            if app.is_connected:
                await app.stop()
        except Exception:
            pass

    return acc_report

async def main():
    print(f"🕒 签到启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. 随机防风控延时 (脚本启动时)
    random_delay_env = os.getenv("RANDOM_DELAY", "0")
    start_delay = parse_delay_range(random_delay_env, 0, 0)
    if start_delay > 0:
        print(f"⏳ 触发全局启动随机防风控延时，等待 {start_delay} 秒...")
        await asyncio.sleep(start_delay)

    # 2. 代理设置
    proxy_env = os.getenv("TG_PROXY", "socks5://172.17.0.1:7891")
    proxy_config = parse_proxy(proxy_env)
    if proxy_config:
        print(f"🌐 网络代理: {proxy_config.get('scheme')}://{proxy_config.get('hostname')}:{proxy_config.get('port')}")
    else:
        print("🌐 未配置代理，直连模式")

    # 3. API 凭据
    api_id = int(os.getenv("TG_API_ID", str(DEFAULT_API_ID)))
    api_hash = os.getenv("TG_API_HASH", DEFAULT_API_HASH)

    # 4. 加载任务列表与账号列表
    tasks = load_tasks()
    accounts = load_accounts()

    print(f"📋 已加载任务 ({len(tasks)} 个): {[t['name'] for t in tasks]}")
    print(f"👥 已加载账号 ({len(accounts)} 个): {[a['name'] for a in accounts]}")

    if not accounts:
        err_msg = "❌ 未找到任何 Telegram Session 凭据！请在青龙环境变量配置 TG_SESSIONS。"
        print(err_msg)
        send("Telegram 多任务签到失败", err_msg)
        return

    # 5. 调度执行各账号
    account_delay_env = os.getenv("TG_ACCOUNT_DELAY", "15-45")
    has_private_delay = any(acc.get("delay") for acc in accounts)

    if has_private_delay:
        # 并发打散调度模式: 各账号根据自身设定的随机延迟独立计时，并在到达时间时自动触发
        async def run_single_pipeline(acc, idx):
            if acc.get("delay"):
                acc_custom_delay = parse_delay_range(acc["delay"], 0, 0)
            else:
                base_step = parse_delay_range(account_delay_env, 15, 45)
                acc_custom_delay = idx * base_step

            if acc_custom_delay > 0:
                print(f"⏳ 账号 【{acc['name']}】 随机防风控延时设定为 {acc_custom_delay} 秒 (约 {acc_custom_delay/60:.1f} 分钟)，等待唤醒...")
                await asyncio.sleep(acc_custom_delay)

            return await process_account(acc, tasks, proxy_config, api_id, api_hash)

        print(f"🚀 已检测到账号独立延时配置，启动并发打散调度模式 (共 {len(accounts)} 个账号)...")
        all_reports = await asyncio.gather(*(run_single_pipeline(acc, idx) for idx, acc in enumerate(accounts)))
    else:
        # 串行调度模式
        all_reports = []
        for idx, acc in enumerate(accounts):
            rep = await process_account(acc, tasks, proxy_config, api_id, api_hash)
            all_reports.append(rep)
            if idx < len(accounts) - 1:
                interval = parse_delay_range(account_delay_env, 15, 45)
                print(f"\n⏱️ 账号间防风控缓冲，等待 {interval} 秒...")
                await asyncio.sleep(interval)

    # 6. 生成汇总报表并推送
    summary_lines = [
        "【Telegram 多任务签到汇总】",
        f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 38
    ]

    has_any_fail = False
    for rep in all_reports:
        summary_lines.append(f"👤 账号: {rep['account']} (ID: {rep['user_id']})")
        for t in rep["tasks"]:
            icon = "✅" if "成功" in t["status"] else ("⏳" if "待确认" in t["status"] else "❌")
            if icon == "❌":
                has_any_fail = True
            # 取回执的第一行精简显示
            first_line = t["detail"].splitlines()[0] if t["detail"] else t["status"]
            summary_lines.append(f"  {icon} [{t['task_name']}]: {first_line}")
        summary_lines.append("-" * 38)

    summary_text = "\n".join(summary_lines)
    print("\n" + "=" * 45)
    print(summary_text)
    print("=" * 45)

    title = f"Telegram 多任务签到{'全部完成' if not has_any_fail else '部分异常'}"
    send(title, summary_text)

if __name__ == "__main__":
    asyncio.run(main())
