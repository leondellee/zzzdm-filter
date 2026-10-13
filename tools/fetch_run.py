# -*- coding: utf-8 -*-
"""等待指定 run 完成并下载日志。

用法： python tools/fetch_run.py <run_number>
"""
from __future__ import annotations

import io
import json
import sys
import time
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_and_check as R  # noqa: E402

REPO = R.REPO
root = Path(__file__).resolve().parent.parent


def main() -> int:
    target = int(sys.argv[1])
    run = None
    for _ in range(40):
        runs = json.loads(R.api(f"/repos/{REPO}/actions/runs?per_page=20"))
        run = next((r for r in runs["workflow_runs"]
                    if r["run_number"] == target), None)
        if run and run["status"] == "completed":
            break
        time.sleep(8)
    if run is None:
        print(f"未找到 run #{target}")
        return 1
    if run["status"] != "completed":
        print(f"run #{target} 仍在运行…")
        return 1

    print(f"run #{run['run_number']}  {run['conclusion']}  "
          f"sha={run['head_sha'][:7]}  ({run['event']})")
    if run["conclusion"] != "success":
        print(f"失败：{run['html_url']}")
        return 1

    logs = R.api(f"/repos/{REPO}/actions/runs/{run['id']}/logs")
    zf = zipfile.ZipFile(io.BytesIO(logs))
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
