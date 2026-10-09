"""挑出還沒有對話型 AI 題的 FAQ（依點閱高到低），切成 N 批輸入檔給出題代理。
用法：python prep.py [則數=520] [批數=10]   → 輸出到 work/in_00.json…；出完題再 python merge.py --write"""
import json, os, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, '..')   # repo 根目錄
N_FAQ = int(sys.argv[1]) if len(sys.argv) > 1 else 520
N_BATCH = int(sys.argv[2]) if len(sys.argv) > 2 else 10
PER_ORG = int(os.environ.get("PER_ORG", 40))
m = json.load(open(os.path.join(SITE, 'data', 'index.json'), encoding='utf-8'))
cs = json.load(open(os.path.join(SITE, 'cstest.json'), encoding='utf-8'))
covered = {f for q in cs if q['lv'] != 'L0' for f in q['faqs']}
units, allf = m['units'], []
for o in m['orgs']:
    ans = json.load(open(os.path.join(SITE, 'data', o['f'] + '.json'), encoding='utf-8'))
    for r, a in zip(o['items'], ans):
        allf.append(dict(sid=r[4], org=o['o'], unit=units[r[1]], q=r[0], d=r[2], h=r[3], a=(a or '')[:1800]))
cand = sorted((f for f in allf if f['sid'] and f['sid'] not in covered and len(f['a']) >= 40), key=lambda f: -f['h'])
cnt, pick = collections.Counter(), []
for f in cand:
    if cnt[f['org']] >= PER_ORG: continue
    cnt[f['org']] += 1; pick.append(f)
    if len(pick) >= N_FAQ: break
out = os.path.join(HERE, 'work'); os.makedirs(out, exist_ok=True)
for b in range(N_BATCH):
    json.dump([{k: f[k] for k in ('sid', 'org', 'unit', 'q', 'd', 'a')} for f in pick[b::N_BATCH]],
              open(os.path.join(out, f'in_{b:02d}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'全題庫 {len(allf)} 則，已有 AI 題 {len(covered)} 則，尚缺 {len(cand)} 則；本次挑 {len(pick)} 則分 {N_BATCH} 批 → {out}')
print('注意：出題說明.md 的 id 前綴 GBB- 請改成新前綴（例如 H），避免跟既有 G00~G09 重複')
