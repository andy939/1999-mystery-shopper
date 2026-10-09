"""檢查智能題庫（cstest.json）有沒有因為 FAQ 改版而過時。GitHub Actions 在爬蟲同步後自動執行。

做法：上次確認時的 FAQ 內容存在 tools/faq_snapshot.json，拿來跟 data/ 的最新 FAQ 比對。
  🔴 一定要改：FAQ 已下架；或應答要點裡的數字，舊版 FAQ 有、新版沒有（例：婚假 8 日→14 日）
  🟡 人工確認：應答要點的文字在新版答覆找不到
  另列答覆有改的 FAQ（附相似度）

輸出：
  stale.json             網站讀這個檔，在智能出題頁標示過時題目、出題時先跳過 🔴
  tools/過時檢查報告.md   給人看的報告（GitHub Issue 也用這份）

用法：
  python tools/check_stale.py            檢查
  python tools/check_stale.py --accept   題目修好後執行：快照更新成目前的 FAQ 版本（新出題合併後也要跑）
"""
import json, os, re, sys, difflib, datetime
try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass
TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
SNAP = os.path.join(TOOLS, 'faq_snapshot.json')
REPORT = os.path.join(TOOLS, '過時檢查報告.md')
OUT = os.path.join(ROOT, 'stale.json')


def load_current():
    m = json.load(open(os.path.join(ROOT, 'data', 'index.json'), encoding='utf-8'))
    cur = {}
    for o in m['orgs']:
        ans = json.load(open(os.path.join(ROOT, 'data', o['f'] + '.json'), encoding='utf-8'))
        for r, a in zip(o['items'], ans):
            if r[4]:
                cur[r[4]] = {'q': r[0], 'a': a or ''}
    return m, cur


def norm(t): return re.sub(r'[\s，。、；：:,.（）()「」『』？?！!\-－—/／]', '', str(t))


def nums(t):
    t = str(t).translate(str.maketrans('０１２３４５６７８９', '0123456789')).replace(',', '')
    return set(re.findall(r'\d+(?:\.\d+)?', t))


def overlap(p, src): return sum(c in src for c in norm(p)) / max(1, len(norm(p)))


meta, cur = load_current()
bank = json.load(open(os.path.join(ROOT, 'cstest.json'), encoding='utf-8'))
used = sorted({s for q in bank for s in q['faqs']})
snap = json.load(open(SNAP, encoding='utf-8')) if os.path.exists(SNAP) else {}

if '--accept' in sys.argv:
    for s in used:
        if s in cur: snap[s] = {'q': cur[s]['q'], 'a': cur[s]['a']}
    json.dump(snap, open(SNAP, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'快照已更新：{len(snap)} 則（FAQ 資料 {meta["generated"]}）')
    sys.exit()

by_sid = {}
for q in bank:
    for s in q['faqs']: by_sid.setdefault(s, []).append(q)

gone = [s for s in used if s not in cur]
nosnap = [s for s in used if s in cur and s not in snap]
changed, items = [], {}          # items：題號 → {lv: red/yellow, why: [...]}


def flag(q, lv, why):
    it = items.setdefault(q['id'], {'id': q['id'], 'level': lv, 'why': []})
    if lv == 'red': it['level'] = 'red'
    it['why'].append(why)


for s in gone:
    for q in by_sid[s]: flag(q, 'red', 'FAQ 已下架')
for s in used:
    if s not in cur or s not in snap: continue
    old, new = snap[s], cur[s]
    if norm(old['a']) == norm(new['a']) and norm(old['q']) == norm(new['q']): continue
    ratio = difflib.SequenceMatcher(None, norm(old['a']), norm(new['a'])).ratio()
    changed.append({'sid': s, 'title': new['q'], 'ratio': round(ratio, 2), 'ids': [q['id'] for q in by_sid[s]]})
    on, nn, osrc, nsrc = nums(old['a'] + old['q']), nums(new['a'] + new['q']), norm(old['a']), norm(new['a'])
    for q in by_sid[s]:
        for p in q.get('points') or []:
            miss = sorted(n for n in nums(p) if n in on and n not in nn)
            if miss: flag(q, 'red', f'要點「{p}」的 {"、".join(miss)} 已不在新版 FAQ')
            elif overlap(p, osrc) >= 0.6 and overlap(p, nsrc) < 0.6: flag(q, 'yellow', f'要點「{p}」在新版 FAQ 找不到')

red = [v for v in items.values() if v['level'] == 'red']
yel = [v for v in items.values() if v['level'] == 'yellow']
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
out = {'checked': now.strftime('%Y-%m-%d %H:%M'), 'faqDate': meta['generated'],
       'red': len(red), 'yellow': len(yel), 'items': sorted(items.values(), key=lambda v: v['id']),
       'changed': sorted(changed, key=lambda c: c['ratio']), 'gone': gone}
# 結果沒變就不改檔（只有時間不同時不寫，避免每天多一個 commit）
old_out = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}
if {k: v for k, v in old_out.items() if k not in ('checked', 'faqDate')} != {k: v for k, v in out.items() if k not in ('checked', 'faqDate')}:
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

title = {s: cur.get(s, {}).get('q', s) for s in used}
L = ['# 智能題庫過時檢查報告', '',
     f'- 檢查時間：{out["checked"]}（台北時間），FAQ 資料：{meta["generated"]}（{len(cur)} 則）',
     f'- 題庫 {len(bank)} 題，對應 FAQ {len(used)} 則', '',
     '| 項目 | 數量 |', '|---|---|',
     f'| 🔴 一定要改 | {len(red)} 題 |', f'| 🟡 人工確認 | {len(yel)} 題 |',
     f'| FAQ 已下架 | {len(gone)} 則 |', f'| FAQ 答覆有改 | {len(changed)} 則 |',
     f'| 沒有快照（無法比對） | {len(nosnap)} 則 |', '']
for name, arr in (('🔴 一定要改', red), ('🟡 人工確認', yel)):
    if arr:
        L += [f'## {name}', '', '| 題號 | 原因 |', '|---|---|']
        L += [f'| {v["id"]} | {"；".join(v["why"])} |' for v in arr] + ['']
if changed:
    L += ['## FAQ 答覆有改（相似度越低改越多）', '', '| 相似度 | FAQ | 題號 |', '|---|---|---|']
    L += [f'| {c["ratio"]:.2f} | {c["title"][:34]} | {"、".join(c["ids"])} |' for c in out['changed']] + ['']
L += ['修正方式：在 Claude Code 說「修正過時題目」；修好後執行 `python tools/check_stale.py --accept` 更新快照。']
open(REPORT, 'w', encoding='utf-8').write('\n'.join(L))
print('\n'.join(L[:12]))
# 給 GitHub Actions 用：有沒有要改的
gh = os.environ.get('GITHUB_OUTPUT')
if gh:
    with open(gh, 'a', encoding='utf-8') as f:
        f.write(f'red={len(red)}\nyellow={len(yel)}\nchanged={len(changed)}\n')
