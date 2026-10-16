"""L0 關鍵詞題的比對，給 merge.py（新 L0 題）和 check_l0.py（全部 L0 題）共用。

  - 關鍵字用空白分開，每個詞都要出現在「標題＋答覆＋發布單位」裡（不限順序）
  - search(q)            嚴格比對：官網是什麼字就是什麼字，全形半形、大小寫都要一樣。
                         L0 測的是最基本的檢索，別的系統（智能客服）不一定會統一全形半形，
                         所以題目的關鍵詞必須照官網原字。驗證一律用這個。
  - search(q, loose=True) 寬鬆比對：統一全形英數字→半形、大小寫，跟網站搜尋框一樣（方便人查）。
                         只拿來找出「寬鬆找得到、嚴格找不到」＝寫法跟官網不同的題目。
"""
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
_FW = {c: c - 0xFEE0 for c in range(0xFF01, 0xFF5F)}
_FW[0x3000] = 0x20


def fold(s):
    return str(s or '').translate(_FW).lower()


_CORPUS = None


def corpus():
    """sid → 原文「標題 答覆 發布單位」（讀 data/，跟網站同一份資料）"""
    global _CORPUS
    if _CORPUS is None:
        m = json.load(open(os.path.join(ROOT, 'data', 'index.json'), encoding='utf-8'))
        units = m['units']
        _CORPUS = {}
        for o in m['orgs']:
            aa = json.load(open(os.path.join(ROOT, 'data', o['f'] + '.json'), encoding='utf-8'))
            for r, a in zip(o['items'], aa):
                if r[4]:
                    _CORPUS[r[4]] = (r[0] or '') + ' ' + (a or '') + ' ' + (units[r[1]] or '')
    return _CORPUS


def search(q, loose=False):
    """回傳符合的 sid 清單。預設嚴格比對（官網原字）。"""
    if loose:
        ts = fold(q).split()
        return [s for s, t in corpus().items() if all(w in fold(t) for w in ts)]
    ts = str(q).split()
    return [s for s, t in corpus().items() if all(w in t for w in ts)]


def official(word, sid):
    """把關鍵詞換成這則 FAQ 原文裡的寫法（例：KTV → ＫＴＶ）；原文找不到就回傳 None"""
    t = corpus().get(sid, '')
    if word in t:
        return word
    i = fold(t).find(fold(word))
    return t[i:i + len(word)] if i >= 0 else None
