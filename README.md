# 青龙面板常用签到脚本合集 (qinglongScripts)

本项目汇总了青龙面板日常运行的高频实用签到脚本，涵盖网盘、社区论坛、机场、PT站、海外通讯工具及 Telegram Bot 批量打卡等任务。

所有脚本均已遵循青龙面板规范深度优化，**独立单文件设计，绝无多余无用任务生成**。内置多账号支持、防风控随机延时、自动重试与全渠道推送通知能力。

---

## 📋 脚本清单与定时建议

| 任务名称 | 脚本文件 | 建议 Cron | 运行环境 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| **天翼云盘签到** | `ty_netdisk_checkin.py` | `1 16 * * *` | Python3 | 每日打卡与空间抽奖，支持多账号密码自动 RSA 加密登录 |
| **百度贴吧签到** | `tieba_checkin.py` | `1 0 * * *` | Python3 | 批量签到账号下关注的全部贴吧，支持多账号与随机延时 |
| **恩山论坛签到** | `enshan_checkin.py` | `39 12 * * *` | Python3 | 恩山论坛自动访问签到领恩山币，支持 Cookie 多账号 |
| **ikuuu签到** | `ikuuu_checkin.py` | `0 21 * * *` | Python3 | ikuuu 机场每日自动打卡续命领取流量，支持多账号 |
| **PT站批量签到** | `pt_checkin.py` | `0 8 * * *` | Python3 | PT 站点自动签到（内置 PTZone，支持灵活配置与扩展） |
| **PingMe签到** | `PingMeSignin.js` | `0 16 * * *` | Node.js | PingMe App 每日金币签到与自动看视频奖励 |
| **Telegram多账号多任务签到** | `tg_multi_checkin.py` | `0 8 * * *` | Python3 | 纯轻量化 MTProto 批处理签到，支持多账号、多Bot、按钮点击、SOCKS5代理 |

---

## 🚀 青龙面板订阅 / 拉库配置

仓库已做**极致精简优化**，每个脚本严格对应一个定时任务。在青龙面板中订阅时**无需繁琐的白名单或黑名单配置**，直接拉取即可：

### 订阅命令
```bash
ql repo https://github.com/jiu-you/qinglongScripts.git "" "" "" "main"
```

> **面板配置指引：**
> - **名称**：自用签到脚本
> - **链接**：`https://github.com/jiu-you/qinglongScripts.git`
> - **定时规则**：`0 8 * * *`（每天自动检查脚本更新）
> - **白名单 / 黑名单 / 依赖文件**：**留空即可**（不会创建任何多余的任务）
> - **分支**：`main`
> - **自动添加/删除任务**：全部勾选「是」

---

## 📦 依赖安装指南（重要）

为确保所有脚本平稳运行，**请务必在运行前安装以下依赖**。

### 1. 青龙面板 WebUI 安装（推荐）

进入青龙面板 -> **「依赖管理」**，分别在对应标签页下添加：

#### 🐍 Python3 依赖
| 依赖名称 | 说明 | 必需脚本 |
| :--- | :--- | :--- |
| `requests` | 网络请求基础库 | 全部 Python 脚本 |
| `rsa` | RSA 非对称加密 | 天翼云盘签到 |
| `pyrogram` | Telegram MTProto 客户端 | Telegram 多账号多任务签到 |
| `tgcrypto` | Telegram 加解密性能加速 | Telegram 多账号多任务签到 |
| `pysocks` | SOCKS4/SOCKS5 代理路由支持 | Telegram 多账号多任务签到 |
| `pycryptodome` | 常用密码学工具包 | 安全校验/PT辅助 |

#### 🟢 Node.js 依赖
| 依赖名称 | 说明 | 必需脚本 |
| :--- | :--- | :--- |
| `got@11` | 轻量级 HTTP 请求库 | PingMe 签到 |
| `tough-cookie` | RFC6265 Cookie 容器与解析 | PingMe 签到 |
| `iconv-lite` | 纯 JS 字符编码转换 | PingMe 签到 |
| `crypto-js` | 常用加密解密算法 | 签名计算与安全校验 |

#### 🐧 Linux 依赖（若 Python 编译 tgcrypto 等需要）
- `gcc` `g++` `make` `libffi-dev` `openssl-dev`

---

### 2. 命令行一键安装（进入青龙容器后执行）

```bash
# 安装 Python3 依赖
pip3 install -r requirements.txt

# 安装 Node.js 依赖
pnpm add -g got@11 tough-cookie iconv-lite crypto-js
```

---

### 3. 持久化到 `extra.sh`（强烈推荐）

青龙容器在升级或重建镜像时可能会重置基础环境。建议进入青龙面板 -> **「配置文件」** -> `extra.sh`，在末尾添加自动安装指令，容器每次启动时会自动检测并补齐依赖：

```bash
## 确保 Python3 核心依赖
pip3 install -q requests rsa pyrogram tgcrypto pysocks pycryptodome >/dev/null 2>&1 || true

## 确保 Node.js 核心依赖
pnpm add -g got@11 tough-cookie iconv-lite crypto-js >/dev/null 2>&1 || true
```

---

## ⚙️ 环境变量配置详解

在青龙面板 **「环境变量」** 中根据需要配置以下变量：

### 1. 天翼云盘签到 (`ty_netdisk_checkin.py`)
| 变量名 | 是否必填 | 格式与示例 | 说明 |
| :--- | :--- | :--- | :--- |
| `TY_USERNAME` | **必填** | `13800138000` 或 `账号1&账号2` | 天翼云盘登录手机号/账号，多账号用 `&` 分隔 |
| `TY_PASSWORD` | **必填** | `Pwd12345` 或 `密码1&密码2` | 对应账号的登录密码，多账号用 `&` 分隔，数量需一致 |
| `RANDOM_SIGNIN` | 可选 | `true` (默认) / `false` | 是否开启执行前的随机延时，防止整点风控 |
| `MAX_RANDOM_DELAY` | 可选 | `3600` (秒，默认 1 小时) | 随机延时的最大秒数范围 (0 ~ 最大秒数) |

---

### 2. 百度贴吧签到 (`tieba_checkin.py`)
| 变量名 | 是否必填 | 格式与示例 | 说明 |
| :--- | :--- | :--- | :--- |
| `TIEBA_COOKIE` | **必填** | `BDUSS=xxx; ...` | 百度账号 Cookie，多账号用换行 `\n` 分隔 |
| `RANDOM_SIGNIN` | 可选 | `true` (默认) / `false` | 是否开启随机延时 |
| `MAX_RANDOM_DELAY` | 可选 | `3600` (默认 3600 秒) | 随机延时最大秒数 |

> **获取提示：** 电脑浏览器登录 [百度贴吧网页版](https://tieba.baidu.com)，按 F12 打开开发者工具，在网络 (Network) 请求标头中复制 Cookie（包含 `BDUSS` 即可）。

---

### 3. 恩山论坛签到 (`enshan_checkin.py`)
| 变量名 | 是否必填 | 格式与示例 | 说明 |
| :--- | :--- | :--- | :--- |
| `enshan_cookie` | **必填** | 论坛完整 Cookie 字符串 | 恩山论坛 Cookie，多账号用换行 `\n` 分隔 |
| `PRIVACY_MODE` | 可选 | `true` (默认) / `false` | 隐私模式，通知与日志中会对用户名进行掩码脱敏 |
| `RANDOM_SIGNIN` | 可选 | `true` (默认) / `false` | 是否开启随机延时 |
| `MAX_RANDOM_DELAY` | 可选 | `3600` | 随机延时最大秒数 |

---

### 4. ikuuu签到 (`ikuuu_checkin.py`)
| 变量名 | 是否必填 | 格式与示例 | 说明 |
| :--- | :--- | :--- | :--- |
| `IKUUU_EMAIL` | **必填** | `user@gmail.com` 或 `邮箱1&邮箱2` | ikuuu 登录邮箱，多账号用 `&` 分隔 |
| `IKUUU_PASSWD` | **必填** | `password123` 或 `密码1&密码2` | 登录密码，多账号用 `&` 分隔，需与邮箱一一对应 |
| `PRIVACY_MODE` | 可选 | `true` (默认) / `false` | 隐私脱敏模式 |
| `RANDOM_SIGNIN` | 可选 | `true` / `false` | 是否启用随机延时 |

---

### 5. PT站批量签到 (`pt_checkin.py`)
采用 NexusPHP 通用架构设计，自动加载配置的 PT 站点并执行每日打卡：

| 变量名 | 是否必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `{PREFIX}_BASE_URL` | **必填** | 例：`https://ptzone.xyz` | 站点完整根网址 |
| `{PREFIX}_COOKIE` | **必填** | `nexusphp_u2=xxx; ...` | 站点登录后的完整 Cookie |
| `{PREFIX}_ENABLE` | 可选 | `1` | 是否启用该站点（`1` 启用，`0` 禁用） |
| `{PREFIX}_SIGN_PATH` | 可选 | `/attendance.php` | 签到请求路径 |
| `{PREFIX}_METHOD` | 可选 | `GET` | 请求方式（`GET` 或 `POST`） |
| `CHECKIN_RANDOM_DELAY` | 可选 | `1` | 是否先执行全局随机等待（默认开启） |
| `CHECKIN_RANDOM_START_HOUR` | 可选 | `8` | 随机签到窗口起始时间（点） |
| `CHECKIN_RANDOM_END_HOUR` | 可选 | `20` | 随机签到窗口截止时间（点） |

> **以 PTZone 为例：**
> - `PTZONE_BASE_URL` = `https://ptzone.xyz`
> - `PTZONE_COOKIE` = `填入您的 PTZone 完整 Cookie`

---

### 6. PingMe签到 (`PingMeSignin.js`)
| 变量名 | 是否必填 | 说明 |
| :--- | :--- | :--- |
| `pingme_capture_v3` | **必填** | 使用抓包工具抓取 PingMe App 签到请求所得的完整 JSON 数据结构，包含 `headers` 与 `paramsRaw` |

---

### 7. Telegram多账号多任务通用签到 (`tg_multi_checkin.py`)
采用轻量级进程批处理模式，执行完成后立即释放连接，避免常驻后台导致的死锁与风控：

| 变量名 | 是否必填 | 格式与示例 | 说明 |
| :--- | :--- | :--- | :--- |
| `TG_SESSIONS` | **必填** | 方式1：`账号别名#Session字符串`<br>方式2：多条独立同名环境变量 | Pyrogram 会话字符串。多账号可用 `&` 或换行连接，也支持创建多个同名变量 |
| `TG_SIGN_TASKS` | 可选 | `SheerID验证#@sheeridverifier_bot#/checkin`<br>`某机场#@xxx_bot#/checkin#点击签到` | 签到任务清单。格式为 `任务名称#@Bot用户名#指令#按钮文本(可选)`，多任务用换行或 `&` 分隔；支持标准 JSON 格式 |
| `TG_PROXY` | 可选 | `socks5://172.17.0.1:7891` | 网络代理地址。国内机器必须配置能够访问 Telegram 的 HTTP 或 SOCKS5 代理 |
| `RANDOM_DELAY` | 可选 | `0` (立即执行) 或 `300-1800` (秒) | 脚本启动前的全局随机防风控延时范围 |
| `TG_ACCOUNT_DELAY` | 可选 | `15-45` (秒) 或 `60-180` | 多账号之间的轮换间隔延时 |
| `TG_TASK_DELAY` | 可选 | `3-8` (秒) | 同一账号连续给不同 Bot 发指令的间隔延时 |

---

## 📢 统一通知渠道配置

所有脚本均自动集成青龙面板全局通知系统（直接调用青龙面板内置的 `notify.py` / `sendNotify.js`），支持以下主流推送渠道，直接在青龙面板「环境变量」中配置对应渠道的 Key 即可：

- **PushPlus**: 配置 `PUSH_PLUS_TOKEN`
- **Server酱**: 配置 `PUSH_KEY`
- **Telegram 机器人**: 配置 `TG_BOT_TOKEN` 与 `TG_USER_ID`
- **Bark (iOS)**: 配置 `BARK_PUSH`
- **企业微信应用 / 机器人**: 配置 `QYWX_AM` 或 `QYWX_KEY`
- **钉钉机器人**: 配置 `DD_BOT_TOKEN` 与 `DD_BOT_SECRET`
- **飞书机器人**: 配置 `FSKEY`
- **邮箱通知**: 配置 `SMTP_SERVER`, `SMTP_EMAIL`, `SMTP_PASSWORD`
- **自定义 Webhook**: 配置 `WEBHOOK_URL`

---

## 🛠️ 目录结构

```text
.
├── .gitignore              # Git 忽略配置
├── LICENSE                 # 开源许可
├── README.md               # 项目使用说明文档
├── requirements.txt        # Python3 依赖清单
├── package.json            # Node.js 依赖清单
│
├── ty_netdisk_checkin.py   # 天翼云盘自动签到抽奖
├── tieba_checkin.py        # 百度贴吧一键签到
├── enshan_checkin.py       # 恩山无线论坛打卡
├── ikuuu_checkin.py        # ikuuu 机场流量打卡
├── pt_checkin.py           # PT 站自动签到
├── PingMeSignin.js         # PingMe 签到与视频硬币领取
└── tg_multi_checkin.py     # Telegram 多账号多任务通用签到
```

---

## ⚠️ 免责声明与注意事项

1. 本项目所有脚本仅供学习、交流与个人自动化测试使用，请勿用于非法用途或高频恶意请求。
2. 请妥善保管好个人的 Cookie、密码、Token 以及 Session 字符串，切勿将敏感信息直接硬编码或提交至公开代码仓库。
3. 部分站点有严格的反作弊或并发风控策略，建议开启脚本内置的 `RANDOM_SIGNIN` 或 `RANDOM_DELAY` 随机延时功能，规避整点封禁。
