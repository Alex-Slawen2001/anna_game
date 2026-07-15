# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║  ИМПОРТЁР ВОПРОСОВ  →  assets/question_bank.json                     ║
╚══════════════════════════════════════════════════════════════════════╝

Позволяет добавлять свои вопросы, не редактируя JSON руками.

КАК ПОЛЬЗОВАТЬСЯ
────────────────
1) Создай текстовый файл, например my_questions.txt, в таком формате:

    # тема: pharmacology
    Антидот при отравлении метанолом:
    * Этанол
    - Налоксон
    - Атропин
    - Витамин K
    = Этанол конкурирует за алкогольдегидрогеназу.

    # тема: anatomy
    Сколько долей у левого лёгкого?
    - 1
    * 2
    - 3
    - 4
    = Слева две доли — место занимает сердце.

   Правила:
     «# тема: X»  — задаёт тему для следующих вопросов (обязательно)
     первая строка вопроса — сам вопрос
     строки «* » — ПРАВИЛЬНЫЙ вариант (ровно один)
     строки «- » — неправильные варианты
     строка «= »  — пояснение (fact), необязательна
     пустая строка разделяет вопросы

2) Запусти:
     python import_questions.py my_questions.txt

   Скрипт проверит формат, отбросит дубликаты и допишет вопросы в банк.
   Старые вопросы не удаляются.

ДОСТУПНЫЕ ТЕМЫ (привязаны к курсам в main.py → COURSE_TOPICS):
   1 курс: anatomy, latin
   2 курс: physiology, biochemistry, microbiology
   3 курс: pharmacology
   4 курс: surgery, internal, obstetrics
   5 курс: emergency, neurology, internal
   финал : rehabilitation
Можно завести новую тему — просто впиши её в COURSE_TOPICS нужного курса.
"""
import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BANK_FILE = os.path.join(BASE_DIR, "assets", "question_bank.json")


def parse(path):
    """Разбирает текстовый файл в список (тема, вопрос)."""
    with open(path, encoding="utf-8") as f:
        lines = [ln.rstrip() for ln in f]

    out, errors = [], []
    topic = None
    block, start = [], 0

    def flush(block, ln_no):
        if not block:
            return
        if topic is None:
            errors.append(f"строка {ln_no}: вопрос до объявления «# тема: ...»")
            return
        q_text = block[0].strip()
        answers, correct, fact = [], None, ""
        for raw in block[1:]:
            s = raw.strip()
            if s.startswith("*"):
                if correct is not None:
                    errors.append(f"«{q_text[:40]}»: больше одного правильного ответа")
                correct = len(answers)
                answers.append(s[1:].strip())
            elif s.startswith("-"):
                answers.append(s[1:].strip())
            elif s.startswith("="):
                fact = s[1:].strip()
        if len(answers) != 4:
            errors.append(f"«{q_text[:40]}»: нужно ровно 4 варианта, найдено {len(answers)}")
            return
        if correct is None:
            errors.append(f"«{q_text[:40]}»: не отмечен правильный ответ (строка со «*»)")
            return
        out.append((topic, {"q": q_text, "a": answers,
                            "correct": correct, "fact": fact}))

    for i, ln in enumerate(lines, 1):
        s = ln.strip()
        if s.lower().startswith("# тема:") or s.lower().startswith("# topic:"):
            flush(block, start); block = []
            topic = s.split(":", 1)[1].strip()
            continue
        if not s:
            flush(block, start); block = []
            continue
        if not block:
            start = i
        block.append(ln)
    flush(block, start)
    return out, errors


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("Использование: python import_questions.py файл_с_вопросами.txt")
        return 1

    src = sys.argv[1]
    if not os.path.isfile(src):
        print(f"Файл не найден: {src}")
        return 1

    parsed, errors = parse(src)
    if errors:
        print("ОШИБКИ В ФАЙЛЕ (ничего не импортировано):")
        for e in errors:
            print("  ✗", e)
        return 1
    if not parsed:
        print("В файле не найдено ни одного вопроса.")
        return 1

    bank = {}
    if os.path.isfile(BANK_FILE):
        with open(BANK_FILE, encoding="utf-8") as f:
            bank = json.load(f)

    existing = {q["q"].strip()
                for k, v in bank.items()
                if isinstance(v, list)
                for q in v if isinstance(q, dict) and "q" in q}

    added, skipped = 0, 0
    for topic, q in parsed:
        if q["q"].strip() in existing:
            skipped += 1
            continue
        bank.setdefault(topic, []).append(q)
        existing.add(q["q"].strip())
        added += 1

    os.makedirs(os.path.dirname(BANK_FILE), exist_ok=True)
    with open(BANK_FILE, "w", encoding="utf-8") as f:
        json.dump(bank, f, ensure_ascii=False, indent=1)

    print(f"Добавлено: {added}   Пропущено дубликатов: {skipped}")
    print("\nТеперь в банке:")
    for k, v in sorted(bank.items()):
        if isinstance(v, list):
            print(f"  {k:<16} {len(v):>3}")
    total = sum(len(v) for v in bank.values() if isinstance(v, list))
    print(f"  {'ИТОГО':<16} {total:>3}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
