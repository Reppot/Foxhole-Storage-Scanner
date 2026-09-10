#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_mapping.py
====================

Разовый генератор для проекта Foxhole Stockpiles / relay.py.

ПРОБЛЕМА:
  fs.exe шлёт в relay.py "сырые" официальные коды предметов игры
  (например 'GrenadeW', 'RifleHeavyW', 'Revolver'), а файлы иконок
  в папке "Icons Foxhole" названы вручную, по-своему
  (например '001_Barge.png', '12.7Mm.png', 'No2Loughcaster.png').
  Из-за этого relay.py не может сопоставить код с картинкой -> в
  unmapped_items.log сплошной icon_missing=true.

ЧТО ДЕЛАЕТ ЭТОТ СКРИПТ:
  1. Читает официальный каталог data/catalog.json (коды + английские
     названия предметов).
  2. Сканирует папку с иконками (рекурсивно).
  3. Пытается опционально подтянуть уже существующие русские названия
     из старого item_codes.py (если он есть) - чтобы не потерять
     ранее сделанные вручную переводы.
  4. Сопоставляет каждый код из каталога с наиболее подходящим файлом
     иконки: точное совпадение -> сравнение без регистра/разделителей
     -> нечёткое сравнение (difflib).
  5. Пишет НОВЫЙ item_codes.py вида:

        ITEM_CODES = {
            "GrenadeW": {
                "name_en": "Grenade",
                "name_ru": None,               # если не удалось найти старый перевод
                "icon": "001_Barge.png",
                "match_score": 1.0,
                "match_method": "exact_code",
            },
            ...
        }

  6. Печатает подробный прогресс и в конце - список кодов без иконки
     (чтобы доразобрать вручную, как раньше делали по unmapped_items.log).

ИСПОЛЬЗОВАНИЕ:
    python generate_mapping.py
        (запускать из корня проекта - там, где лежат data/catalog.json
         и папка "Icons Foxhole"; либо поменяй пути в разделе НАСТРОЙКИ ниже)

Используются только стандартные библиотеки Python: os, sys, json, re,
difflib, shutil, datetime.
"""

import os
import sys
import json
import re
import difflib
import shutil
from datetime import datetime

# ============================== НАСТРОЙКИ ==================================

# Путь к официальному каталогу предметов приложения fs.exe
CATALOG_PATH = os.environ.get("FS_CATALOG_PATH", os.path.join("data", "catalog.json"))

# Путь к папке с твоими вручную вырезанными иконками
ICONS_DIR = os.environ.get(
    "FS_ICONS_DIR",
    r"D:\Games\foxhole-stockpiles-main\Icons Foxhole",
)

# Старый item_codes.py, из которого попробуем подтянуть уже готовые
# русские названия (необязателен - если файла нет, просто пропустим этот шаг)
OLD_ITEM_CODES_PATH = os.environ.get("FS_OLD_ITEM_CODES_PATH", "item_codes.py")

# Куда писать результат
OUTPUT_PATH = os.environ.get("FS_OUTPUT_ITEM_CODES_PATH", "item_codes.py")

# Расширения файлов, которые считаем иконками
ICON_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

# Порог "уверенности" для нечёткого (fuzzy) сопоставления: 0.0-1.0.
# Всё что ниже - не сопоставляем автоматически, попадает в список "не найдено".
FUZZY_THRESHOLD = 0.72

# =============================================================================


def log(msg):
    """Простой принт с меткой времени - чтобы было видно прогресс в консоли."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def normalize(s):
    """
    Приводит строку к 'ключу для сравнения':
    - нижний регистр
    - убирает всё, кроме букв и цифр (пробелы, точки, подчёркивания,
      дефисы, апострофы, кавычки и т.п. - всё выкидывается)
    Так 'No.2 Loughcaster' и 'No2Loughcaster.png' дают одинаковый ключ.
    """
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"[^a-zа-я0-9]", "", s)
    return s


def strip_leading_number(stem):
    """
    Убирает ведущий числовой префикс вида '001_' или '12-' из имени файла
    без расширения, чтобы '001_Barge' тоже сравнивалось как 'barge'.
    Возвращает исходную строку, если префикса нет.
    """
    m = re.match(r"^\d+[_\-\s]+(.*)$", stem)
    return m.group(1) if m else stem


# --------------------------------------------------------------------------
# Шаг 1: чтение официального каталога
# --------------------------------------------------------------------------

def load_catalog(path):
    """
    Читает data/catalog.json и возвращает список словарей вида
    {"code": <официальный код>, "name_en": <английское имя или None>}.

    Каталог может быть представлен по-разному (список или словарь,
    разные названия полей) - поэтому парсинг максимально терпимый.
    """
    log(f"Читаю каталог: {path}")
    if not os.path.isfile(path):
        log(f"  ОШИБКА: файл каталога не найден по пути '{path}'.")
        log("  Проверь путь (переменная окружения FS_CATALOG_PATH) и повтори запуск.")
        sys.exit(1)

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as e:
        log(f"  ОШИБКА: не удалось разобрать JSON ({e}).")
        sys.exit(1)
    except OSError as e:
        log(f"  ОШИБКА чтения файла: {e}")
        sys.exit(1)

    # Возможные варианты структуры каталога:
    #   - список записей: [ {...}, {...}, ... ]
    #   - объект-обёртка: { "items": [ {...}, ... ] }
    #   - словарь код -> запись: { "GrenadeW": {...}, ... }
    if isinstance(raw, dict) and "items" in raw and isinstance(raw["items"], list):
        entries = raw["items"]
    elif isinstance(raw, list):
        entries = raw
    elif isinstance(raw, dict):
        # словарь код -> данные; допишем код внутрь записи, если его там нет
        entries = []
        for k, v in raw.items():
            if isinstance(v, dict):
                v = dict(v)
                v.setdefault("code", k)
                entries.append(v)
    else:
        log("  ОШИБКА: неожиданная структура catalog.json (ни список, ни словарь).")
        sys.exit(1)

    # Возможные названия поля с кодом предмета
    CODE_KEYS = ("code", "Code", "CodeName", "code_name", "itemCode", "id")
    # Возможные названия поля с английским именем
    NAME_KEYS = ("name", "Name", "DisplayName", "display_name", "EnglishName")

    result = []
    skipped = 0
    for entry in entries:
        if not isinstance(entry, dict):
            skipped += 1
            continue

        code = None
        for k in CODE_KEYS:
            if entry.get(k):
                code = str(entry[k])
                break

        if not code:
            skipped += 1
            continue

        name_en = None
        for k in NAME_KEYS:
            if entry.get(k):
                name_en = str(entry[k])
                break

        # Иногда имя лежит вложенно, например DisplayNameLocales: {"en": "...", ...}
        if not name_en:
            locales = entry.get("DisplayNameLocales") or entry.get("displayNameLocales")
            if isinstance(locales, dict):
                name_en = locales.get("en") or next(iter(locales.values()), None)

        result.append({"code": code, "name_en": name_en})

    log(f"  Загружено кодов из каталога: {len(result)} (пропущено записей без кода: {skipped})")

    if len(result) == 0:
        log("")
        log("  !!! ДИАГНОСТИКА: не удалось распознать ни одного кода. Структура файла:")
        log(f"      Тип корневого элемента JSON: {type(raw).__name__}")
        if isinstance(raw, dict):
            top_keys = list(raw.keys())[:20]
            log(f"      Ключи верхнего уровня (первые 20): {top_keys}")
            # покажем, что лежит под первым ключом - вдруг список записей спрятан глубже
            if top_keys:
                first_val = raw[top_keys[0]]
                log(f"      Тип значения под ключом {top_keys[0]!r}: {type(first_val).__name__}")
                if isinstance(first_val, dict):
                    log(f"      Его ключи (первые 20): {list(first_val.keys())[:20]}")
                elif isinstance(first_val, list) and first_val:
                    log(f"      Длина списка: {len(first_val)}, тип первого элемента: {type(first_val[0]).__name__}")
                    if isinstance(first_val[0], dict):
                        log(f"      Ключи первого элемента списка: {list(first_val[0].keys())[:20]}")
        elif isinstance(raw, list) and raw:
            log(f"      Длина списка: {len(raw)}")
            log(f"      Тип первого элемента: {type(raw[0]).__name__}")
            if isinstance(raw[0], dict):
                log(f"      Ключи первого элемента: {list(raw[0].keys())[:20]}")
                log(f"      Пример первого элемента (обрезано): {json.dumps(raw[0], ensure_ascii=False)[:500]}")
        log("  !!! Пришли этот блок диагностики (или сам catalog.json / его начало) "
            "для донастройки CODE_KEYS/NAME_KEYS в скрипте.")
        log("")

    return result


# --------------------------------------------------------------------------
# Шаг 2: сканирование папки с иконками
# --------------------------------------------------------------------------

def scan_icons(icons_dir):
    """
    Рекурсивно собирает все файлы-иконки в icons_dir.
    Возвращает список словарей:
      {"filename": "001_Barge.png", "path": <относительный путь от icons_dir>,
       "key_full": normalize(stem), "key_no_prefix": normalize(strip_leading_number(stem))}
    """
    log(f"Сканирую папку иконок: {icons_dir}")
    if not os.path.isdir(icons_dir):
        log(f"  ОШИБКА: папка с иконками не найдена по пути '{icons_dir}'.")
        log("  Проверь путь (переменная окружения FS_ICONS_DIR) и повтори запуск.")
        sys.exit(1)

    icons = []
    for dirpath, _dirnames, filenames in os.walk(icons_dir):
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in ICON_EXTENSIONS:
                continue
            stem = os.path.splitext(fname)[0]
            rel_path = os.path.relpath(os.path.join(dirpath, fname), icons_dir)
            no_prefix = strip_leading_number(stem)
            icons.append({
                "filename": fname,
                "rel_path": rel_path,
                "key_full": normalize(stem),
                "key_no_prefix": normalize(no_prefix),
            })

    log(f"  Найдено файлов-иконок: {len(icons)}")
    if not icons:
        log("  ПРЕДУПРЕЖДЕНИЕ: ни одной иконки не найдено - проверь путь и расширения файлов.")
    return icons


# --------------------------------------------------------------------------
# Шаг 3 (опционально): подтянуть старые русские названия
# --------------------------------------------------------------------------

def load_old_ru_names(path):
    """
    Пытается достать читаемые русские/оригинальные названия из старого
    item_codes.py (формат: ITEM_CODES = {"КлючТранслит": "Читаемое имя", ...}).
    Возвращает список читаемых значений (без ключей - ключи в старом файле
    были транслитерацией, а не официальным кодом, поэтому сопоставлять
    будем позже по совпадению нормализованного значения с key_no_prefix
    иконки / с английским именем из каталога).

    Если файла нет или он не читается - просто возвращает пустой список
    и не останавливает работу скрипта (это необязательный шаг).
    """
    log(f"Ищу старый item_codes.py для подтяжки готовых названий: {path}")
    if not os.path.isfile(path):
        log("  Старый item_codes.py не найден - пропускаю этот шаг (не критично).")
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        log(f"  Не удалось прочитать старый item_codes.py ({e}) - пропускаю.")
        return {}

    # Если это уже результат самого generate_mapping.py (структура code -> {...}),
    # а не старый плоский словарь code -> "читаемое имя" - НЕ пытаемся из него
    # тащить "переводы": иначе служебные ключи (name_en/name_ru/icon/match_score/
    # match_method) и значения вроде 'exact_code' попадут в словарь как мусор.
    if "Автоматически сгенерировано generate_mapping.py" in content or '"match_method"' in content:
        log("  Обнаружено, что это уже сгенерированный ранее item_codes.py "
            "(новый формат) - пропускаю харвест переводов из него, чтобы не "
            "натащить мусора (name_en/icon/match_score как будто это переводы).")
        return {}

    # Достаём пары "ключ": "значение" простым регэкспом, не выполняя файл
    # как код (безопаснее и не требует, чтобы файл был валидным модулем).
    pairs = re.findall(r'["\']([^"\']+)["\']\s*:\s*["\']([^"\']*)["\']', content)
    if not pairs:
        log("  В старом item_codes.py не нашлось пар ключ-значение - пропускаю.")
        return {}

    # Индексируем по нормализованному значению -> само значение (читаемое имя),
    # а также по нормализованному ключу -> значение (вдруг ключ уже был кодом игры).
    by_norm_value = {}
    by_norm_key = {}
    for k, v in pairs:
        if v:
            by_norm_value[normalize(v)] = v
        if k and v:
            by_norm_key[normalize(k)] = v

    log(f"  Прочитано пар из старого файла: {len(pairs)}")
    return {"by_value": by_norm_value, "by_key": by_norm_key}


# --------------------------------------------------------------------------
# Шаг 4: сопоставление код -> иконка
# --------------------------------------------------------------------------

def match_items(catalog_entries, icons, old_ru):
    """
    Для каждой записи каталога подбирает лучший файл иконки.
    Возвращает (matched: dict, unmatched: list).

    matched[code] = {
        "name_en": ...,
        "name_ru": ... или None,
        "icon": <filename>,
        "match_score": 0..1,
        "match_method": "exact_code" | "exact_name" | "fuzzy",
    }
    """
    log("Начинаю сопоставление кодов с файлами иконок...")

    # Индекс иконок по точному нормализованному ключу (с префиксом и без)
    # -> список иконок (могут быть тёзки, хотя обычно один файл на ключ)
    icons_by_key = {}
    all_keys_for_fuzzy = []  # (key, icon) для нечёткого поиска
    for icon in icons:
        for key in {icon["key_full"], icon["key_no_prefix"]}:
            if not key:
                continue
            icons_by_key.setdefault(key, []).append(icon)
            all_keys_for_fuzzy.append((key, icon))

    used_files = set()  # чтобы не отдать один и тот же файл двум разным кодам
    matched = {}
    unmatched = []

    total = len(catalog_entries)
    for i, entry in enumerate(catalog_entries, start=1):
        code = entry["code"]
        name_en = entry["name_en"]

        code_key = normalize(code)
        name_key = normalize(name_en) if name_en else ""

        chosen_icon = None
        method = None
        score = 0.0

        # --- Уровень 1: точное совпадение по коду ---
        for candidate in icons_by_key.get(code_key, []):
            if candidate["filename"] not in used_files:
                chosen_icon = candidate
                method = "exact_code"
                score = 1.0
                break

        # --- Уровень 2: точное совпадение по английскому имени ---
        if chosen_icon is None and name_key:
            for candidate in icons_by_key.get(name_key, []):
                if candidate["filename"] not in used_files:
                    chosen_icon = candidate
                    method = "exact_name"
                    score = 1.0
                    break

        # --- Уровень 3: нечёткое (fuzzy) совпадение по коду ИЛИ имени ---
        if chosen_icon is None:
            best_score = 0.0
            best_icon = None
            for key, icon in all_keys_for_fuzzy:
                if icon["filename"] in used_files:
                    continue
                s1 = difflib.SequenceMatcher(None, code_key, key).ratio() if code_key else 0.0
                s2 = difflib.SequenceMatcher(None, name_key, key).ratio() if name_key else 0.0
                s = max(s1, s2)
                if s > best_score:
                    best_score = s
                    best_icon = icon
            if best_icon is not None and best_score >= FUZZY_THRESHOLD:
                chosen_icon = best_icon
                method = "fuzzy"
                score = round(best_score, 3)

        # --- Русское название: пробуем найти в старом item_codes.py ---
        name_ru = None
        if old_ru:
            name_ru = (
                old_ru.get("by_key", {}).get(code_key)
                or old_ru.get("by_value", {}).get(name_key)
            )

        if chosen_icon is not None:
            used_files.add(chosen_icon["filename"])
            matched[code] = {
                "name_en": name_en,
                "name_ru": name_ru,
                "icon": chosen_icon["filename"],
                "match_score": score,
                "match_method": method,
            }
        else:
            unmatched.append({"code": code, "name_en": name_en, "name_ru": name_ru})

        if i % 50 == 0 or i == total:
            log(f"  ...обработано {i}/{total}")

    log(f"Сопоставление завершено: успешно {len(matched)}, не найдено {len(unmatched)}")
    return matched, unmatched


# --------------------------------------------------------------------------
# Шаг 5: запись результата
# --------------------------------------------------------------------------

def write_output(matched, unmatched, output_path):
    log(f"Записываю результат в: {output_path}")

    # Бэкап старого файла, если он существует и совпадает с путём вывода
    if os.path.isfile(output_path):
        backup_path = output_path + ".bak"
        try:
            shutil.copyfile(output_path, backup_path)
            log(f"  Старый файл сохранён как резервная копия: {backup_path}")
        except OSError as e:
            log(f"  ПРЕДУПРЕЖДЕНИЕ: не удалось сделать резервную копию ({e}), продолжаю без неё.")

    lines = []
    lines.append('"""')
    lines.append("Автоматически сгенерировано generate_mapping.py")
    lines.append(f"Дата генерации: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Сопоставлено кодов: {len(matched)}, не сопоставлено: {len(unmatched)}")
    lines.append('"""')
    lines.append("")
    lines.append("# code -> {name_en, name_ru, icon, match_score, match_method}")
    lines.append("ITEM_CODES = {")
    for code in sorted(matched.keys()):
        v = matched[code]
        lines.append(f"    {code!r}: {{")
        lines.append(f"        \"name_en\": {v['name_en']!r},")
        lines.append(f"        \"name_ru\": {v['name_ru']!r},")
        lines.append(f"        \"icon\": {v['icon']!r},")
        lines.append(f"        \"match_score\": {v['match_score']!r},")
        lines.append(f"        \"match_method\": {v['match_method']!r},")
        lines.append("    },")
    lines.append("}")
    lines.append("")
    lines.append("# Коды, для которых иконку подобрать не удалось (заполни вручную и перенеси")
    lines.append("# в ITEM_CODES выше, либо добавь недостающий файл в папку с иконками и")
    lines.append("# перезапусти generate_mapping.py).")
    lines.append("UNMATCHED_CODES = {")
    for item in unmatched:
        lines.append(
            f"    {item['code']!r}: {{\"name_en\": {item['name_en']!r}, "
            f"\"name_ru\": {item['name_ru']!r}}},"
        )
    lines.append("}")
    lines.append("")

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except OSError as e:
        log(f"  ОШИБКА: не удалось записать файл ({e}).")
        sys.exit(1)

    log(f"  Готово. Записано {len(matched)} сопоставленных кодов и {len(unmatched)} нераспознанных.")


def print_unmatched_report(unmatched):
    if not unmatched:
        log("Нераспознанных кодов нет - все коды из каталога получили иконку.")
        return
    log(f"=== КОДЫ БЕЗ ИКОНКИ ({len(unmatched)}) ===")
    for item in unmatched:
        log(f"  {item['code']:30s} (en: {item['name_en']})")
    log("=== конец списка ===")


def main():
    log("=== generate_mapping.py: старт ===")
    log(f"CATALOG_PATH = {CATALOG_PATH}")
    log(f"ICONS_DIR    = {ICONS_DIR}")
    log(f"OUTPUT_PATH  = {OUTPUT_PATH}")
    log("")

    catalog_entries = load_catalog(CATALOG_PATH)
    icons = scan_icons(ICONS_DIR)
    old_ru = load_old_ru_names(OLD_ITEM_CODES_PATH)

    matched, unmatched = match_items(catalog_entries, icons, old_ru)

    write_output(matched, unmatched, OUTPUT_PATH)
    print_unmatched_report(unmatched)

    log("")
    log("=== ГОТОВО ===")
    log(f"Итог: {len(matched)} из {len(catalog_entries)} кодов получили иконку "
        f"({len(unmatched)} остались без иконки).")
    if unmatched:
        log("Список нераспознанных кодов также записан в UNMATCHED_CODES внутри "
            f"{OUTPUT_PATH} - можно доправить руками, как раньше делали по unmapped_items.log.")


if __name__ == "__main__":
    main()
