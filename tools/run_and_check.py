# -*- coding: utf-8 -*-
"""触发 GitHub Actions 并读取最新一次运行日志。

用法： python tools/run_and_check.py
"""
from __future__ import annotations

import base64
import io
import json
import os
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

REPO = "leondellee/zzzdm-filter"
WORKFLOW = "filter.yml"
GIT = (r"C:\Users\leon\.workbuddy\binaries\PortableGit\versions\1.3.0"
       r"\mingw64\bin\git-credential-wincred.exe")

for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
    os.environ.pop(k, None)
_opener = urllib.request.build_opener(urllib.request.ProxyHandler(
    {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}))
urllib.request.install_opener(_opener)


def token() -> str:
    out = subprocess.run(
        [GIT, "get"], input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True).stdout
    return dict(l.split("=", 1) for l in out.strip().splitlines()
                if "=" in l).get("password", "")


def api(path: str, method: str = "GET", payload=None) -> bytes:
    req = urllib.request.Request(
        f"https://api.github.com{path}", method=method,
        data=json.dumps(payload).encode() if payload else None,
        headers={"Authorization": f"Bearer {token()}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "wb"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def main() -> int:
    # 触发
    api(f"/repos/{REPO}/actions/workflows/{WORKFLOW}/dispatches",
        "POST", {"ref": "main"})
    print("已触发 workflow_dispatch，等待新 run 出现…")

    run = None
    for _ in range(20):
        time.sleep(6)
        runs = json.loads(api(f"/repos/{REPO}/actions/runs?per_page=5"))
        for r in runs["workflow_runs"]:
            if r["event"] == "workflow_dispatch" and r["status"] != "completed":
                run = r
                break
        if run is None:
            for r in runs["workflow_runs"]:
                if r["event"] == "workflow_dispatch":
                    run = r
                    break
        if run and run["status"] == "completed":
            break
    if run is None:
        print("未找到运行记录")
        return 1
    print(f"run #{run['run_number']}  {run['status']} / {run['conclusion']}")

    if run["status"] != "completed":
        print("仍在运行，稍后重试")
        return 1
    if run["conclusion"] != "success":
        print(f"失败：{run['html_url']}")
        return 1

    # 下日志 zip
    logs = api(f"/repos/{REPO}/actions/runs/{run['id']}/logs")
    zf = zipfile.ZipFile(io.BytesIO(logs))
    root = Path(__file__).resolve().parent.parent
    out = root / "output" / f"online_run_{run['run_number']}.txt"
    with out.open("w", encoding="utf-8") as f:
        for name in zf.namelist():
            if name.endswith("/"):
                continue
            try:
                text = zf.read(name).decode("utf-8", errors="replace")
            except Exception:
                continue
            f.write(f"===== {name} =====\n{text}\n")
    print(f"日志已存 {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
