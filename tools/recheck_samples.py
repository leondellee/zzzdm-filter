# -*- coding: utf-8 -*-
"""真实样本复核：保留清单 + 童装/婴幼儿相关条目定位。"""
import re
import sys

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from src.classifier import Classifier  # noqa: E402
from src.parser import parse  # noqa: E402

KID = re.compile(r"儿童|童装|童鞋|男童|女童|小童|中童|大童|婴幼儿|婴儿|新生儿|宝宝|亲子")

clf = Classifier()
for f in ("output/fresh_sample.html", "output/raw_page.html"):
    posts = parse(open(f, encoding="utf-8").read())
    kept = [p for p in posts if not clf.classify(p.title, p.body, p.price).drop]
    rate = 100 * (len(posts) - len(kept)) // len(posts)
    print(f"{f}: {len(posts)} 条 → 保留 {len(kept)}（剔除率 {rate}%）")

print()
posts = parse(open("output/fresh_sample.html", encoding="utf-8").read())
print("=== 新样本：含童装/婴幼儿词的条目 ===")
hit = [p for p in posts if KID.search(p.title)]
if not hit:
    print("  （样本中没有）")
for p in hit:
    v = clf.classify(p.title, p.body, p.price)
    tag = f"剔 {v.category}｜{v.matched}" if v.drop else "保"
    print(f"  [{tag:<22}] {p.title[:66]}")

print()
print("=== 新样本：当前保留清单（人工复核）===")
for i, p in enumerate([p for p in posts if not clf.classify(p.title, p.body, p.price).drop], 1):
    print(f"{i:>2}. {p.title[:72]}")
