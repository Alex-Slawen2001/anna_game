# -*- coding: utf-8 -*-
import random
import copy

from question_pool import EXTRA_POOL, FINAL_EXTRA, EXAM_SIZE, FINAL_SIZE
import live_questions


def _shuffle_options(q):
    q = copy.deepcopy(q)
    correct_text = q["a"][q["correct"]]
    opts = q["a"][:]
    random.shuffle(opts)
    q["a"] = opts
    q["correct"] = opts.index(correct_text)
    return q


def _dedup(questions):
    seen = set()
    out = []
    for q in questions:
        key = q["q"].strip().lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(q)
    return out


def build_year_exam(year):
    base = list(year["exam"]["questions"])
    extra = list(EXTRA_POOL.get(year["num"], []))
    pool = _dedup(base + extra)
    random.shuffle(pool)

    take = min(EXAM_SIZE, len(pool))
    chosen = pool[:take]

    live = []
    if year["num"] in (2, 3):
        live = live_questions.get_live_questions(1)
    if live and len(chosen) > 0:
        chosen[-1] = live[0]

    chosen = [_shuffle_options(q) for q in chosen]
    random.shuffle(chosen)
    return chosen


def build_final_exam(final):
    name = final["name"]
    base = list(final["questions"])
    extra = list(FINAL_EXTRA.get(name, []))
    pool = _dedup(base + extra)
    random.shuffle(pool)

    take = min(FINAL_SIZE.get(name, 6), len(pool))
    chosen = pool[:take]

    if name == "Аккредитация":
        live = live_questions.get_live_questions(1)
        if live:
            chosen[-1] = live[0]

    chosen = [_shuffle_options(q) for q in chosen]
    random.shuffle(chosen)
    return chosen
