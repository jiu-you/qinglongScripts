# 如何新增一个 PT 站点脚本

1. 复制现有脚本：
   `scripts/ptzone_checkin.py` → `scripts/mysite_checkin.py`

2. 修改子类：
- site_name
- env_prefix
- default_sign_path / default_method
- 如需 token：配置 default_preflight_path + csrf_regex + csrf_field_name
- 如需自定义成功判定：override is_success()

3. 青龙环境变量：
- {PREFIX}_BASE_URL
- {PREFIX}_COOKIE

4. 运行：
- python3 scripts/mysite_checkin.py

5. 全部执行：
- python3 run_all.py
