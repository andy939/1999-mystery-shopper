"""用網站「問答查詢」同一套規則，檢查智能題庫裡每一題 L0 關鍵詞題：
  - 正確那則 FAQ 找不找得到
  - 符合幾則（太多＝關鍵詞太廣，測不出檢索能力；上限 8）
  - 在問答查詢預設排序（發布日期新→舊）排第幾

用法：python tools/check_l0.py          列出有問題的題目
      python tools/check_l0.py --all    每一題都列
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kwsearch import ROOT, search

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
LIMIT = 8

m = json.load(open(os.path.join(ROOT, 'data', 'index.json'), encoding='utf-8'))
date = {r[4]: r[2] for o in m['orgs'] for r in o['items'] if r[4]}
title = {r[4]: r[0] for o in m['orgs'] for r in o['items'] if r[4]}
bank = json.load(open(os.path.join(ROOT, 'cstest.json'), encoding='utf-8'))
L0 = [q for q in bank if q['lv'] == 'L0']

stat, bad = collections.Counter(), []
for q in L0:
    tgt = q['faqs'][0]
    hits = sorted(search(q['q']), key=lambda s: date.get(s, ''), reverse=True)
    if tgt not in date:
        why = 'FAQ 已下架'
    elif tgt not in hits:
        why = '找不到'
    elif len(hits) > LIMIT:
        why = f'符合 {len(hits)} 則（太廣），排第 {hits.index(tgt) + 1}'
    else:
        why = ''
    stat[why.split('，')[0].split(' ')[0] if why else '正常'] += 1
    if why or '--all' in sys.argv:
        bad.append((q['id'], q['q'], title.get(tgt, '')[:28], why or f'符合 {len(hits)} 則，排第 {hits.index(tgt) + 1}'))

print(f'L0 共 {len(L0)} 題：' + '、'.join(f'{k} {v}' for k, v in stat.most_common()))
for b in bad:
    print(' ', ' | '.join(b))
