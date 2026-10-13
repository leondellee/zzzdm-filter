# -*- coding: utf-8 -*-
"""抓取 zzzdm 公开预览页样本，落盘 output/fresh_sample.html。

用法： python tools/fetch_samples.py [页数]
"""
from __future__ import annotations

import os
import sys
import time
import urllib.request
from pathlib import Path

CHANNEL = "zzzdm"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# 沙箱/本机常注入失效代理，先清掉，再显式指定
for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
    os.environ.pop(k, None)

PROXIES = [None, "http://127.0.0.1:7890", "http://127.0.0.1:7897",
           "http://127.0.0.1:10809"]


def fetch(url: str, proxy: str | None) -> str:
    op = urllib.request.build_opener(
        urllib.request.ProxyHandler({} if proxy is None
                                    else {"http": proxy, "https": proxy}))
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Referer": "https://t.me/",
        "Accept-Language": "zh-CN,zh;q=0.9",
    })
    with op.open(req, timeout=25) as r:
        return r.read().decode("utf-8", errors="replace")


def main() -> int:
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    root = Path(__file__).resolve().parent.parent
    out = root / "output" / "fresh_sample.html"

    # 先探一次代理
    good = None
    for px in PROXIES:
        try:
            html = fetch(f"https://t.me/s/{CHANNEL}", px)
            if "tgme_widget_message" in html:
                good = px
                print(f"代理可用：{px or '直连'}")
                break
        except Exception as e:
            print(f"  试探失败 {px or '直连'}: {type(e).__name__} {str(e)[:60]}")
    if good is None:
        print("全部通道失败")
        return 1

    chunks = [html]
    # 用最后一条纯数字消息 ID 翻页
    import re
    for i in range(pages - 1):
        ids = re.findall(r'data-post="%s/(\d+)"' % CHANNEL, chunks[-1])
        if not ids:
            break
        before = ids[0]
        try:
            nxt = fetch(f"https://t.me/s/{CHANNEL}?before={before}", good)
        except Exception as e:
            print(f"  第{i+2}页失败: {e}")
            break
        if "tgme_widget_message" not in nxt:
            break
        chunks.append(nxt)
        print(f"  已取 {i+2} 页（before={before}）")
        time.sleep(1.0)

    out.write_text("\n".join(chunks), encoding="utf-8")
    print(f"落盘 {out}  共 {len(chunks)} 页")
    return 0


if __name__ == "__main__":
    sys.exit(main())
