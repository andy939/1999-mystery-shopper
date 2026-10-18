"""合併多輪追問腳本（tools/追問出題說明.md 產出的 fout_*.json）到根目錄 followups.json。

驗證（任一不過就不寫入）：
  - sid 是現行 FAQ（讀 data/，跟網站同一份資料）
  - 開場＋追問 1~2 句；每句問句最多一個問號
  - 每個 quote 都是該則答覆原文的子字串（去掉空白後比對）＝答案一定在 FAQ 裡

用法：python tools/merge_fu.py tools/work/fu           試跑驗證
      python tools/merge_fu.py tools/work/fu --write   驗證通過才寫入（同 sid 以新的覆蓋）
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kwsearch import ROOT

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

OUT = os.path.join(ROOT, 'followups.json')
sq = lambda t: re.sub(r'\s+', '', str(t or ''))

m = json.load(open(os.path.join(ROOT, 'data', 'index.json'), encoding='utf-8'))
ans = {}
for o in m['orgs']:
    aa = json.load(open(os.path.join(ROOT, 'data', o['f'] + '.json'), encoding='utf-8'))
    for r, a in zip(o['items'], aa):
        if r[4]:
            ans[r[4]] = a or ''

new, bad = [], []
for f in sorted(glob.glob(os.path.join(sys.argv[1], 'fout_*.json'))):
    for x in json.load(open(f, encoding='utf-8')):
        sid = x.get('sid')
        if sid not in ans:
            bad.append((x.get('id'), 'sid 不在現行 FAQ'))
            continue
        lines = [x['open']] + x.get('turns', [])
        if not 1 <= len(x.get('turns', [])) <= 2:
            bad.append((x['id'], f'追問 {len(x.get("turns", []))} 句'))
        for t in lines:
            if len(re.findall(r'[？?]', t['q'])) > 1:
                bad.append((x['id'], '一句多問：' + t['q']))
            if not t.get('quote') or sq(t['quote']) not in sq(ans[sid]):
                bad.append((x['id'], 'quote 不在答覆原文：' + str(t.get('quote'))[:30]))
        new.append(x)

print(f'腳本 {len(new)} 份、追問 {sum(len(x["turns"]) for x in new)} 句、問題 {len(bad)} 項')
for b in bad:
    print(' ', *b)
if bad or '--write' not in sys.argv:
    sys.exit(1 if bad else 0)
old = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else []
keep = {x['sid']: x for x in old}
for x in new:
    keep[x['sid']] = x
json.dump(list(keep.values()), open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'已寫入 followups.json：共 {len(keep)} 份')
