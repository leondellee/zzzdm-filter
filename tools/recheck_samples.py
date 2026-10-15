# -*- coding: utf-8 -*-
"""真实样本复核：保留清单 + 品牌命中明细。"""
import sys

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from src.classifier import Classifier  # noqa: E402
from src.parser import parse  # noqa: E402

clf = Classifier()
for f in ("output/fresh_sample.html", "output/raw_page.html"):
    posts = parse(open(f, encoding="utf-8").read())
    kept = [p for p in posts if not clf.classify(p.title, p.body, p.price).drop]
    rate = 100 * (len(posts) - len(kept)) // len(posts)
    print(f"{f}: {len(posts)} 条 → 保留 {len(kept)}（剔除率 {rate}%）")

print()
posts = parse(open("output/fresh_sample.html", encoding="utf-8").read())
print("=== 新样本：当前保留清单（人工复核）===")
for i, p in enumerate([p for p in posts if not clf.classify(p.title, p.body, p.price).drop], 1):
    print(f"{i:>2}. {p.title[:76]}")

print()
print("=== 品牌命中 / 新品类命中明细 ===")
new_cats = {"汽车保养", "学习机", "1号会员店"}
for p in posts:
    v = clf.classify(p.title, p.body, p.price)
    if v.drop and (v.category in new_cats or str(v.matched).startswith("品牌·")):
        print(f"  [{v.category}｜{v.matched}] {p.title[:58]}")
