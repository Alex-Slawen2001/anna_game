# -*- coding: utf-8 -*-
import threading
import random
import urllib.request
import json

_live = []
_lock = threading.Lock()
_started = False


def _fetch_fda_reactions():
    url = ("https://api.fda.gov/drug/event.json?"
           "count=patient.reaction.reactionmeddrapt.exact")
    with urllib.request.urlopen(url, timeout=8) as r:
        data = json.load(r)
    terms = [it["term"].capitalize() for it in data.get("results", [])[:25]
             if it.get("term")]
    out = []
    if len(terms) >= 4:
        for i in range(min(8, len(terms))):
            correct = terms[i]
            others = [t for t in terms if t != correct]
            if len(others) < 3:
                break
            wrong = random.sample(others, 3)
            opts = wrong + [correct]
            random.shuffle(opts)
            out.append({
                "q": "Какой побочный эффект препаратов чаще фиксируется в базе FDA?",
                "a": opts,
                "correct": opts.index(correct),
                "fact": "Данные открытой базы нежелательных явлений FDA (openFDA).",
                "live": True,
            })
    return out


def _fetch_fda_classes():
    url = ("https://api.fda.gov/drug/label.json?"
           "count=openfda.pharm_class_epc.exact")
    with urllib.request.urlopen(url, timeout=8) as r:
        data = json.load(r)
    terms = [it["term"] for it in data.get("results", [])[:25] if it.get("term")]
    out = []
    for i in range(min(6, len(terms))):
        correct = terms[i]
        others = [t for t in terms if t != correct]
        if len(others) < 3:
            break
        opts = random.sample(others, 3) + [correct]
        random.shuffle(opts)
        out.append({
            "q": "Какой фармакологический класс реально существует (по базе FDA)?",
            "a": [o if len(o) < 42 else o[:39] + "…" for o in opts],
            "correct": opts.index(correct),
            "fact": "Классы препаратов из базы этикеток FDA (openFDA).",
            "live": True,
        })
    return out


def _worker():
    global _live
    collected = []
    for fn in (_fetch_fda_reactions, _fetch_fda_classes):
        try:
            collected += fn()
        except Exception:
            pass
    if collected:
        with _lock:
            _live = collected


def start_fetching():
    global _started
    if _started:
        return
    _started = True
    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def get_live_questions(n=1):
    with _lock:
        if not _live:
            return []
        return random.sample(_live, min(n, len(_live)))
