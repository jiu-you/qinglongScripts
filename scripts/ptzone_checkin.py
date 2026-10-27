#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""PTZone 自动签到（继承 PTCheckinBase）"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from common.pt_base import PTCheckinBase


class PTZoneCheckin(PTCheckinBase):
    site_name = "PTZone"
    env_prefix = "PTZONE"
    default_sign_path = "/attendance.php"
    default_method = "GET"


def main():
    res = PTZoneCheckin().run(notify=True)
    raise SystemExit(0 if res.ok else 1)


if __name__ == "__main__":
    main()
