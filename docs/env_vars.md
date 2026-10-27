# 环境变量说明（自动生成）

> 所有站点变量遵循：`{PREFIX}_XXXX`（例如：PTZONE_BASE_URL）

## 必填（每个站点）

- `{PREFIX}_BASE_URL`：站点基础地址，例如 `https://ptzone.xyz`
- `{PREFIX}_COOKIE`：登录后的整段 Cookie

## 站点开关

- `{PREFIX}_ENABLE`：是否启用该站点（默认 1）

## 请求相关（可选）

- `{PREFIX}_SIGN_PATH`：签到路径（默认 `/attendance.php`）
- `{PREFIX}_METHOD`：GET/POST（默认 GET）
- `{PREFIX}_POST_DATA`：POST 参数（JSON 或 `a=1&b=2`）
- `{PREFIX}_PREFLIGHT_PATH`：签到前先访问页面（用于拿 token）
- `{PREFIX}_REFERER`：Referer 头（默认 BASE_URL + /）
- `{PREFIX}_UA`：User-Agent
- `{PREFIX}_TIMEOUT`：请求超时秒数（默认 20）

## 随机签到（可选）

> 默认启用。run_all 会全局随机一次，子脚本自动跳过随机。

- `{PREFIX}_RANDOM_DELAY`：是否启用随机（默认 1；被 `CHECKIN_SKIP_RANDOM_DELAY=1` 覆盖）
- `{PREFIX}_RANDOM_START_HOUR`：开始小时（默认 8）
- `{PREFIX}_RANDOM_END_HOUR`：结束小时（默认 20）
- `{PREFIX}_RANDOM_SEED`：固定随机种子（调试用）

## 通知（可选）

- `{PREFIX}_NOTIFY_ON_SUCCESS`：成功也通知（默认 0）
- `{PREFIX}_FAIL_NOTIFY_THRESHOLD`：连续失败达到阈值才通知（默认 1）

## run_all 全局随机（可选）

- `CHECKIN_RANDOM_DELAY`：run_all 是否全局随机（默认 1）
- `CHECKIN_RANDOM_START_HOUR`：默认 8
- `CHECKIN_RANDOM_END_HOUR`：默认 20
- `CHECKIN_SKIP_RANDOM_DELAY`：内部用，run_all 会设置为 1（让子脚本不再随机）
