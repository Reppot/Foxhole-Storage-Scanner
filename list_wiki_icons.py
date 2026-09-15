#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
list_wiki_icons.py
====================

Первый шаг для подключения новой папки со скачанными с Foxhole Wiki
иконками (D:\\Games\\foxhole-stockpiles-main\\Icons Foxhole\\FoxholeWikiPhotos).

Этот скрипт НИЧЕГО не сопоставляет и не переименовывает — он просто
рекурсивно собирает список всех файлов-изображений в указанной папке
и печатает/сохраняет его в текстовый файл. Дальше этот список нужно
прислать обратно (как раньше присылались icons_list.txt /
listofallfiles.txt) - по нему уже будет строиться сопоставление имя
файла -> код предмета.

Для каждого файла в выводе показаны:
  - относительный путь от корня папки (для дублей/подпапок)
  - "нормализованный ключ" - то же самое имя, приведённое к нижнему
    регистру и очищенное от пробелов/дефисов/подчёркиваний/точек -
    именно так их потом будет сравнивать generate_mapping.py /
    fix_icon_mapping.py, так что уже на этом шаге видно, где могут
    быть неочевидные совпадения или коллизии.

ИСПОЛЬЗОВАНИЕ:
    python list_wiki_icons.py

Пути и расширения - см. НАСТРОЙКИ ниже. Используются только
стандартные библиотеки: os, re, sys, collections.
"""

import os
import re
import sys
from collections import defaultdict

# ============================== НАСТРОЙКИ ==================================

WIKI_ICONS_DIR = os.environ.get(
    "FS_WIKI_ICONS_DIR",
    r"D:\Games\foxhole-stockpiles-main\Icons Foxhole\FoxholeWikiPhotos",
)

OUTPUT_PATH = os.environ.get("FS_WIKI_ICONS_LIST_PATH", "wiki_icons_list.txt")

# Расширения, которые считаем изображениями. У вики-картинок форматы бывают
# разнообразнее, чем у вручную вырезанных иконок, поэтому список шире.
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".bmp"}

# =============================================================================


def normalize(s):
    """Нижний регистр + только буквы/цифры (без пробелов, точек, дефисов и т.п.)."""
    if not s:
        return ""
    return re.sub(r"[^a-z0-9]", "", s.lower())


def main():
    print(f"Папка с иконками с вики: {WIKI_ICONS_DIR}")
    if not os.path.isdir(WIKI_ICONS_DIR):
        print(f"ОШИБКА: папка не найдена по пути '{WIKI_ICONS_DIR}'.")
        print("Проверь путь (можно переопределить переменной окружения FS_WIKI_ICONS_DIR).")
        sys.exit(1)

    files = []
    for dirpath, _dirnames, filenames in os.walk(WIKI_ICONS_DIR):
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in IMAGE_EXTENSIONS:
                continue
            rel_path = os.path.relpath(os.path.join(dirpath, fname), WIKI_ICONS_DIR)
            stem = os.path.splitext(fname)[0]
            files.append({
                "rel_path": rel_path,
                "filename": fname,
                "ext": ext,
                "key": normalize(stem),
            })

    if not files:
        print("Изображений не найдено - проверь путь и расширения файлов (IMAGE_EXTENSIONS в скрипте).")
        sys.exit(1)

    files.sort(key=lambda f: f["rel_path"].lower())

    # Статистика по расширениям
    by_ext = defaultdict(int)
    for f in files:
        by_ext[f["ext"]] += 1

    # Поиск коллизий нормализованных ключей (разные файлы -> одинаковый ключ)
    by_key = defaultdict(list)
    for f in files:
        by_key[f["key"]].append(f["rel_path"])
    collisions = {k: v for k, v in by_key.items() if len(v) > 1}

    print(f"Всего найдено изображений: {len(files)}")
    print("По расширениям:")
    for ext, count in sorted(by_ext.items()):
        print(f"  {ext}: {count}")
    print(f"Коллизий нормализованных ключей (разные файлы с 'одинаковым' именем): {len(collisions)}")
    if collisions:
        print("  (это не ошибка сама по себе, просто на заметку - список ниже в файле)")

    lines = []
    lines.append(f"# Список изображений из: {WIKI_ICONS_DIR}")
    lines.append(f"# Всего файлов: {len(files)}")
    lines.append("# Формат строки: <относительный_путь>\\t<нормализованный_ключ>")
    lines.append("")
    for f in files:
        lines.append(f'{f["rel_path"]}\t{f["key"]}')

    if collisions:
        lines.append("")
        lines.append("# === КОЛЛИЗИИ (разные файлы дают одинаковый нормализованный ключ) ===")
        for key, paths in sorted(collisions.items()):
            lines.append(f"#   key={key!r}: {paths}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nСписок сохранён в: {OUTPUT_PATH}")
    print("Пришли этот файл обратно - следующим шагом сопоставим имена с кодами предметов.")


if __name__ == "__main__":
    main()
