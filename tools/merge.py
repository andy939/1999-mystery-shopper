"""驗證 <資料夾>/out_XX.json 並合併進 cstest.json。用法：python merge.py [資料夾] [--write]（預設資料夾 work）"""
import json, glob, os, re, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
G = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'work')
SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')   # repo 根目錄
LV = {'L1', 'L2', 'L3', 'L4'}
TY = {'口語情境', '多意圖', '錯誤前提', '用詞落差', '條件判斷', '時效', '無答案'}
EX = {'回答', '糾正', '轉介'}

ans = {}
for f in glob.glob(G + '/in_*.json'):
    for r in json.load(open(f, encoding='utf-8')):
        ans[r['sid']] = r
def norm(t): return re.sub(r'[\s，。、；：:,.（）()「」『』？?！!\-－—/／]', '', str(t))

bank = json.load(open(SITE + '/cstest.json', encoding='utf-8'))
seen_q = {norm(q['q']) for q in bank}
seen_id = {q['id'] for q in bank}
good, bad = [], collections.Counter()
weak = 0
for f in sorted(glob.glob(G + '/out_*.json')):
    arr = json.load(open(f, encoding='utf-8'))
    for q in arr:
        why = None
        if not all(k in q for k in ('id', 'q', 'lv', 'type', 'faqs', 'expect', 'points', 'avoid', 'note')): why = '欄位不齊'
        elif q['lv'] not in LV: why = 'lv'
        elif not q['type'] or any(t not in TY for t in q['type']): why = 'type'
        elif q['expect'] not in EX: why = 'expect'
        elif not q['faqs'] or any(s not in ans for s in q['faqs']): why = 'sid'
        elif not (8 <= len(q['q']) <= 120): why = '長度'
        elif not q['points']: why = '無要點'
        elif norm(q['q']) in seen_q: why = '重複'
        elif q['id'] in seen_id: why = 'id 重複'
        if why: bad[why] += 1; continue
        # 要點是否出自原文（字元重疊率）
        src = norm(''.join(ans[s]['a'] for s in q['faqs']))
        ov = [sum(c in src for c in norm(p)) / max(1, len(norm(p))) for p in q['points']]
        if min(ov) < 0.6: weak += 1
        q['src'] = 'AI'
        q['points'] = [str(p) for p in q['points']][:4]
        seen_q.add(norm(q['q'])); seen_id.add(q['id'])
        good.append(q)
    print(os.path.basename(f), len(arr))
print('通過', len(good), '剔除', dict(bad), '要點與原文重疊偏低', weak)
c = collections.Counter(q['lv'] for q in good); print('新增難度', dict(c))
c = collections.Counter(t for q in good for t in q['type']); print('新增題型', dict(c))
print('合併後總數', len(bank) + len(good))
if '--write' in sys.argv:
    json.dump(bank + good, open(SITE + '/cstest.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('已寫入 cstest.json')
