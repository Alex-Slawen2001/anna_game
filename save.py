# -*- coding: utf-8 -*-
import os
import json

_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(_DIR, "savegame.json")


def load():
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return None
        return data
    except Exception:
        return None


def save(state):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=1)
        return True
    except Exception:
        return False


def clear():
    try:
        if os.path.isfile(SAVE_FILE):
            os.remove(SAVE_FILE)
    except Exception:
        pass


def has_save():
    return os.path.isfile(SAVE_FILE)
