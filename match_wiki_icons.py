#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
match_wiki_icons.py
====================

Иконки, скачанные с Foxhole Wiki (папка FoxholeWikiPhotos), в большинстве
своём названы ТЕМИ ЖЕ внутренними кодами, что шлёт fs.exe (GrenadeW.webp,
PistolAmmo.webp, MortarTankAmmoBR.webp и т.п.) - а не транслитерацией
русского названия, как было с вручную вырезанными иконками. Поэтому здесь
сравнение идёт код <-> имя файла напрямую (латиница-латиница), что гораздо
надёжнее, чем сравнение с русским названием предмета.

Это же открывает то, что раньше сознательно не трогали: иконки техники.
Раньше не было надёжного источника имён файлов для техники - теперь есть.

ЧТО ДЕЛАЕТ СКРИПТ:
  1. Собирает ПОЛНЫЙ список известных кодов предметов:
       - ключи словаря ITEM_NAMES_RU внутри relay.py
       - ключи словаря ITEM_ICON_FILES внутри relay.py
       - ключи ITEM_CODES из item_codes.py (если файл есть рядом)
  2. Читает список файлов с вики (wiki_icons_list.txt, сгенерированный
     list_wiki_icons.py) - НЕ сканирует диск заново, работает с готовым
     списком, который ты прислал.
  3. Для каждого кода ищет подходящий файл:
       - точное совпадение нормализованного кода с нормализованным
         именем файла;
       - если нет - нечёткое (fuzzy) совпадение (порог ниже, чем для
         точного, но выше, чем для сравнения с русским именем, т.к.
         тут сравниваются заведомо похожие по смыслу строки).
  4. Пишет wiki_icon_fixes.py со словарём WIKI_ICON_FIXES (код -> имя
     файла). Подпапку FoxholeWikiPhotos указывать не нужно - у relay.py
     индекс иконок строится рекурсивно по ВСЕМ подпапкам ICONS_DIR, так
     что достаточно просто имени файла.
  5. Печатает отчёт: сколько кодов сопоставлено, сколько осталось без
     пары (и что именно - в т.ч. отдельно техника, раз уж она теперь
     тоже в игре).

ВАЖНО: сопоставление НИЧЕГО не перезаписывает и не имеет приоритета над
тем, что уже прописано вручную в relay.py - результат подключается через
setdefault (см. инструкцию в конце вывода скрипта), точно так же, как
icon_fixes.py и item_codes.py раньше.

ИСПОЛЬЗОВАНИЕ:
    python match_wiki_icons.py

Используются только стандартные библиотеки: os, sys, re, difflib,
datetime.
"""

import os
import sys
import re
import difflib
from datetime import datetime

# ============================== НАСТРОЙКИ ==================================

RELAY_PATH = os.environ.get("FS_RELAY_PATH", "relay.py")
ITEM_CODES_PATH = os.environ.get("FS_ITEM_CODES_PATH", "item_codes.py")
WIKI_LIST_PATH = os.environ.get("FS_WIKI_ICONS_LIST_PATH", "wiki_icons_list.txt")
OUTPUT_PATH = os.environ.get("FS_WIKI_ICON_FIXES_PATH", "wiki_icon_fixes.py")

# Порог нечёткого совпадения. Код <-> имя файла - обе строки латиницей и
# обычно почти идентичны, когда это один и тот же предмет, поэтому порог
# можно держать строгим.
FUZZY_THRESHOLD = 0.85

# =============================================================================


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def normalize(s):
    if not s:
        return ""
    return re.sub(r"[^a-z0-9]", "", s.lower())


def extract_dict_keys(content, dict_name):
    """
    Извлекает ключи словаря dict_name = { "ключ": ..., ... } из текста
    (regex + подсчёт баланса скобок для нахождения границ словаря).
    Работает и для плоских словарей (код: имя_файла), и для словарей
    с более сложными значениями - ключи всё равно строковые литералы.
    """
    m = re.search(rf"{dict_name}\s*=\s*\{{", content)
    if not m:
        return set()
    depth = 0
    start = m.end() - 1
    i = start
    for i in range(start, len(content)):
        if content[i] == "{":
            depth += 1
        elif content[i] == "}":
            depth -= 1
            if depth == 0:
                break
    block = content[start:i]
    keys = re.findall(r'["\']([A-Za-z0-9_]+)["\']\s*:', block)
    return set(keys)


def load_known_codes(relay_path, item_codes_path):
    log(f"Читаю relay.py: {relay_path}")
    if not os.path.isfile(relay_path):
        log(f"  ОШИБКА: relay.py не найден по пути '{relay_path}'.")
        sys.exit(1)
    with open(relay_path, "r", encoding="utf-8") as f:
        relay_content = f.read()

    names_keys = extract_dict_keys(relay_content, "ITEM_NAMES_RU")
    icons_keys = extract_dict_keys(relay_content, "ITEM_ICON_FILES")
    log(f"  ITEM_NAMES_RU: {len(names_keys)} кодов, ITEM_ICON_FILES: {len(icons_keys)} кодов")

    item_codes_keys = set()
    if os.path.isfile(item_codes_path):
        with open(item_codes_path, "r", encoding="utf-8") as f:
            item_codes_content = f.read()
        item_codes_keys = extract_dict_keys(item_codes_content, "ITEM_CODES")
        log(f"  item_codes.py (ITEM_CODES): {len(item_codes_keys)} кодов")
    else:
        log(f"  item_codes.py не найден по пути '{item_codes_path}' - пропускаю (не критично).")

    all_codes = names_keys | icons_keys | item_codes_keys
    log(f"  Итого уникальных известных кодов: {len(all_codes)}")
    return sorted(all_codes)


def load_wiki_icons(wiki_list_path):
    log(f"Читаю список иконок с вики: {wiki_list_path}")
    if not os.path.isfile(wiki_list_path):
        log(f"  ОШИБКА: файл не найден по пути '{wiki_list_path}'.")
        log("  Это файл, который создаёт list_wiki_icons.py - запусти его сначала.")
        sys.exit(1)

    icons = []
    with open(wiki_list_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            if "\t" not in line:
                continue
            rel_path, key = line.split("\t", 1)
            filename = os.path.basename(rel_path)
            icons.append({"rel_path": rel_path, "filename": filename, "key": key})

    log(f"  Загружено файлов: {len(icons)}")
    return icons


def match(codes, icons):
    log("Сопоставляю коды с файлами...")
    icons_by_key = {}
    for icon in icons:
        icons_by_key.setdefault(icon["key"], icon)

    all_keys = list(icons_by_key.keys())

    exact = []       # (code, filename)
    prefix = []       # (code, filename) - код является префиксом имени файла (или наоборот)
    fuzzy = []        # (code, filename, score)
    unmatched = []    # code

    for code in codes:
        code_key = normalize(code)
        if not code_key:
            unmatched.append(code)
            continue

        if code_key in icons_by_key:
            exact.append((code, icons_by_key[code_key]["filename"]))
            continue

        # Совпадение по префиксу: часто вики добавляет суффикс вроде
        # "Vehicle"/"Item"/"War"/"C" к тому же самому коду. Порог длины 4,
        # чтобы короткие коды (типа "MGW") не матчились на всё подряд.
        prefix_candidates = []
        if len(code_key) >= 4:
            for key in all_keys:
                if key.startswith(code_key) or code_key.startswith(key):
                    # чем ближе длины - тем увереннее совпадение
                    prefix_candidates.append((abs(len(key) - len(code_key)), key))
        if prefix_candidates:
            prefix_candidates.sort()
            best_key = prefix_candidates[0][1]
            prefix.append((code, icons_by_key[best_key]["filename"]))
            continue

        best_score = 0.0
        best_icon = None
        for key in all_keys:
            s = difflib.SequenceMatcher(None, code_key, key).ratio()
            if s > best_score:
                best_score = s
                best_icon = icons_by_key[key]
        if best_icon is not None and best_score >= FUZZY_THRESHOLD:
            fuzzy.append((code, best_icon["filename"], round(best_score, 3)))
        else:
            unmatched.append(code)

    log(f"  Точных совпадений: {len(exact)}")
    log(f"  Совпадений по префиксу (код + суффикс вроде Vehicle/Item/War): {len(prefix)}")
    log(f"  Нечётких совпадений (>= {FUZZY_THRESHOLD}): {len(fuzzy)}")
    log(f"  Не сопоставлено: {len(unmatched)}")
    return exact, prefix, fuzzy, unmatched


def write_output(exact, prefix, fuzzy, output_path):
    log(f"Записываю результат в: {output_path}")
    lines = []
    lines.append('"""')
    lines.append("Автоматически сгенерировано match_wiki_icons.py")
    lines.append(f"Дата генерации: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Точных: {len(exact)}, по префиксу: {len(prefix)}, нечётких: {len(fuzzy)}")
    lines.append('"""')
    lines.append("")
    lines.append("# code -> имя файла иконки с Foxhole Wiki (лежит в подпапке FoxholeWikiPhotos,")
    lines.append("# но указывать подпапку не нужно - индекс иконок в relay.py рекурсивный)")
    lines.append("WIKI_ICON_FIXES = {")
    for code, fname in exact:
        lines.append(f"    {code!r}: {fname!r},  # точное совпадение")
    for code, fname in prefix:
        lines.append(f"    {code!r}: {fname!r},  # совпадение по префиксу - проверь при случае")
    for code, fname, score in fuzzy:
        lines.append(f"    {code!r}: {fname!r},  # нечёткое совпадение, score={score} - ПРОВЕРЬ")
    lines.append("}")
    lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log(f"  Готово, записано {len(exact) + len(prefix) + len(fuzzy)} сопоставлений.")


def print_report(unmatched):
    log("")
    log(f"=== НЕ СОПОСТАВЛЕНО ({len(unmatched)}) ===")
    for code in unmatched:
        log(f"  {code}")
    log("=== конец списка ===")


def main():
    log("=== match_wiki_icons.py: старт ===")
    codes = load_known_codes(RELAY_PATH, ITEM_CODES_PATH)
    icons = load_wiki_icons(WIKI_LIST_PATH)
    exact, prefix, fuzzy, unmatched = match(codes, icons)
    write_output(exact, prefix, fuzzy, OUTPUT_PATH)
    print_report(unmatched)

    log("")
    log("=== ГОТОВО ===")
    log(f"Итог: {len(exact)} точных + {len(prefix)} по префиксу + {len(fuzzy)} нечётких = "
        f"{len(exact) + len(prefix) + len(fuzzy)} из {len(codes)} кодов получили иконку с вики.")
    log("")
    log("Чтобы подключить в relay.py, добавь рядом с существующими merge'ами")
    log("(item_codes.py / icon_fixes.py) ещё один блок:")
    log("")
    log("    from wiki_icon_fixes import WIKI_ICON_FIXES")
    log("    for code, fname in WIKI_ICON_FIXES.items():")
    log("        ITEM_ICON_FILES.setdefault(code, fname)")
    log("")
    log("(setdefault - значит вручную прописанные в relay.py иконки как всегда в приоритете)")


if __name__ == "__main__":
    main()
