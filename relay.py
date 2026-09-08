"""
Foxhole Stockpiles -> Discord relay.

Принимает POST-запросы с JSON от FS (output handler "webhook") и
пересылает отформатированное сообщение в настоящий Discord webhook.

Запуск:
    pip install flask requests
    set DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/....   (Windows: set, Linux/Mac: export)
    python relay.py

В настройках FS (Выводы -> Новый обработчик -> webhook) укажите URL этого relay:
    http://127.0.0.1:5001/relay
(auth_type оставьте null/пустым — relay не требует авторизации от FS,
 сам relay отдельно авторизуется в Discord через свой webhook URL).
"""

import os
import logging

from flask import Flask, request, jsonify
import requests

# ---- Настройки -------------------------------------------------------

# Реальный webhook URL вашего Discord-канала.
# ВАЖНО: не хардкодьте его в коде, если будете куда-то выкладывать скрипт.
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

# Порт, на котором relay слушает запросы от FS
RELAY_PORT = int(os.environ.get("RELAY_PORT", "5001"))

# Не слать сообщение, если ни один предмет не найден / все нули
SKIP_EMPTY_SCANS = True

# ------------------------------------------------------------------------

# ---- Словарь переводов предметов ---------------------------------------
# Ключ — код предмета из FS (поле "code"), значение — как показывать в Discord.
# Список неполный: добавляйте свои коды/переводы по мере встречи новых предметов.
# Если кода нет в словаре — имя будет "причёсано" автоматически (см. prettify_code).
ITEM_NAMES_RU = {
    # Ресурсы и материалы
    "AluminumA": "Алюминий",
    "CopperA": "Медь",
    "SandbagMaterials": "Мешки с песком (материалы)",
    "MetalBeamMaterials": "металлическая балка",
    "FacilityOil1": "Нефть для объекта I",
    "FacilityOil2": "Нефть для объекта II",
    "FacilityOil3": "Нефть для объекта III",
    "HeavyExplosive": "Тяжёлая взрывчатка",
    "Components": "Компоненты",
    "RareMaterials": "Редкие материалы",
    "RareMetal": "Редкий металл",
    "Oil": "Нефть",
    "Diesel": "Дизель",
    "Petrol": "Бензин",
    "Water": "вода",
    # "PipeMaterials": ???  — код встречается, но название неизвестно/ошибочно, ждём уточнения от пользователя
    "BarbedWireMaterials": "колючая проволока",
    "WaterWallMaterials": "naval buoy",
    "Cloth": "биматы",
    "GroundMaterials": "гравий",
    "Explosive": "порох",

    # Медицина / расходники
    "TraumaKit": "Травма-аптечка",
    "Bandages": "бинт",
    "GasMask": "противогаз",
    "StickyBomb": "липкая бомба (стика)",
    "MaintenanceSupplies": "Сопли",

    # Обмундирование
    "SoldierSupplies": "рубашки",
    "SnowUniformW": "зимняя униформа",
    "MedicUniformW": "форма медика",
    "ScoutUniformW": "форма разведчика",
    "TankUniformW": "форма танкиста",
    "EngineerUniformW": "форма инженера",
    "NavalUniformW": "форма моряка",
    "ArmourUniformW": "Стальная кираса",
    "OfficerUniformW": "офицерская форма",
    "AmmoUniformW": "шинель специалиста",

    # Оружие
    "Bayonet": "штык-нож",
    "Revolver": "револьвер",
    "Shovel": "лопата",
    "WorkWrench": "Гаечный ключ",
    "RifleAutomaticW": 'Винтовка Sampo 77',
    "SmokeGrenade": "дымовая граната",
    "ATRifleW": "противотанковое ружье 20мм",
    "HEGrenade": "Маммонка",
    "RifleLightW": "винтовка Blakerov",
    "SMGHeavyW": 'Пистолет-пулемёт No.1 "The Liar"',
    "SMGW": "Пистолет пулемет Fiddler",
    "RadioBackpack": "Радиорюкзак",
    "RifleW": "Винтовка No.2 Loughcaster",
    "GrenadeAdapter": "Подствольный гранатомёт",
    "GrenadeW": "Осколочная граната",
    "GreenAsh": "газовая граната",
    "SledgeHammer": "кувалда",
    "Binoculars": "бинокль",
    "Radio": "рация",
    "SurfaceWaterMine": "Морская мина E681-B",

    # Боеприпасы
    "LightArtilleryAmmo": "120мм снаряды",
    "MGAmmo": "12.7 мм (пулемётные) патроны",
    "ATLargeAmmo": "94.5мм снаряды",
    "AircraftAmmo": "20мм (зенитные) патроны",
    "MortarAmmo": "миномётный снаряд",
    "AssaultRifleAmmo": "7.92 мм",
    "ShotgunAmmo": "дробь",
    "MiniTorpedoAmmo": "торпеда",
    "MortarAmmoFL": "Осветительный миномётный снаряд",
    "ATRifleAmmo": "14.5 мм",
    "PistolAmmo": "8мм (пистолет)",
    "RevolverAmmo": ".44 Магнум",
    "RpgAmmo": "снаряд РПГ",
    "MortarAmmoSH": "Осколочный миномётный снаряд",
    "SMGAmmo": "9мм",

    # Техника
    "FortLargeRadarPart": "самосвал",
    "TruckResourceW": "самосвал",
    "FlatbedTruck": "Флэтбед (пакмул)",
    "TruckDefensiveW": "Дюна",
    "TruckLiquidW": "Дюна бензовоз",
    "MediumBoatC": "пожарная машина",
    "AmbulanceFlameW": "пожарная машина",
    "AmbulanceW": "скорая помощь",
    "ScoutVehicleUtilityC": "Машина скорой помощи",
    "Freighter": "судно Ironship",
    "FreighterLight": "судно Krokodil",
    "Construction": "CV (тир 1)",
    "ArmoredCar2LargeW": "бронированная дюна",
    "ArmoredCarW": "O'Brien бронеавтомобиль",
    "ScoutTankW": "King Spire Mk.1 (скаут танк)",
    "HeavyTruckW": "кнут",
    "Barge": "баржа",
    "Gunboat2W": "БТР-Амфибия (Mulloy)",
    "LandingCraftW": "БТР-Амфибия (Mulloy)",
    "LightTankC": "строительный прицеп",
    "TrailerMaterial": "строительный прицеп",
    "Crane": "мобильный кран",
    "TruckMobilityW": "Landrunner",
    "ScoutVehicleOffensiveW": "Spitfire",
    "TruckW": "грузовик",
    "BusW": "автобус",
    "EmplacedInfantryW": "стационарная пехотная установка",  # предположительно, уточните

    # Контейнеры / логистика
    "ResourceContainer": "ресурсный контейнер",
    "ShippingContainer": "грузовой контейнер",
    "MaterialPlatform": "поддон",
    "LiquidContainer": "бочка",

    # Прочее
    "Unknown": "Неизвестно",
}

# Переводы типов складов (необязательно, для красоты)
STOCKPILE_TYPE_RU = {
    "Seaport": "Морской порт",
    "Storage Depot": "Склад",
    "Facility": "Объект",
    "Small Facility": "Малый объект",
    "Field": "Полевой склад",
}

# Короткие (заглавными буквами) названия типов для строки "Регион:"
STOCKPILE_TYPE_SHORT_RU = {
    "Seaport": "ПОРТ",
    "Storage Depot": "СКЛАД",
    "Facility": "ОБЪЕКТ",
    "Small Facility": "МАЛЫЙ ОБЪЕКТ",
    "Field": "ПОЛЕВОЙ СКЛАД",
}


def prettify_code(code: str) -> str:
    """Разбивает CamelCase-код на читаемые слова, если перевода нет в словаре.
    Например 'MetalBeamMaterials' -> 'Metal Beam Materials'."""
    import re
    # Вставляем пробел перед каждой заглавной буквой (кроме первой) и перед цифрами
    spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", code)
    spaced = re.sub(r"(?<=[a-zA-Z])(?=\d)", " ", spaced)
    return spaced.strip()


def display_item_name(code: str) -> str:
    if code in ITEM_NAMES_RU:
        return ITEM_NAMES_RU[code]
    return prettify_code(code)


def display_stockpile_type(stype: str) -> str:
    return STOCKPILE_TYPE_RU.get(stype, stype)

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")
log = logging.getLogger("relay")

app = Flask(__name__)


def prettify_hex(hex_code: str) -> str:
    """Превращает код региона в читаемое название.
    Например 'BasinSionnachHex' -> 'Basin Sionnach'."""
    text = hex_code
    if text.endswith("Hex"):
        text = text[:-3]
    return prettify_code(text)


def format_stockpile_embed(stockpile: dict) -> dict:
    """Превращает один объект stockpile в Discord embed."""
    name = stockpile.get("name", "Unknown")
    stype_raw = stockpile.get("type", "Unknown")
    stype = display_stockpile_type(stype_raw)
    shard = stockpile.get("shard", "")
    reserve = stockpile.get("is_reserve", False)
    timestamp = stockpile.get("timestamp", "")
    resolution = stockpile.get("resolution", "")
    hex_raw = stockpile.get("hex")

    items = stockpile.get("items", [])

    # Строим список предметов, пропуская явно пустые слоты (quantity == 0)
    lines = []
    for item in items:
        qty = item.get("quantity", 0)
        if qty == 0:
            continue
        code = item.get("code", "?")
        display_name = display_item_name(code)
        crated = " (в ящике)" if item.get("crated") else ""
        lines.append(f"• **{display_name}** — {qty}{crated}")

    if not lines:
        lines = ["_Предметы не обнаружены_"]

    hex_display = prettify_hex(hex_raw) if hex_raw else "—"
    type_short = STOCKPILE_TYPE_SHORT_RU.get(stype_raw, stype_raw.upper())

    header_lines = [
        f"**Гекс:** {hex_display}",
        f"**Регион:** {type_short}",
        f"**Склад:** {name or '—'}",
        "",
    ]

    title = "📦 Отчёт по складу"
    if reserve:
        title += " (резервный)"

    fields = [
        {"name": "Шард", "value": shard or "—", "inline": True},
        {"name": "Разрешение", "value": resolution or "—", "inline": True},
    ]

    embed = {
        "title": title,
        "description": "\n".join(header_lines + lines),
        "color": 0x5865F2,  # discord blurple
        "fields": fields,
        "footer": {"text": timestamp or ""},
    }
    return embed


@app.route("/relay", methods=["POST"])
def relay():
    if not DISCORD_WEBHOOK_URL:
        log.error("DISCORD_WEBHOOK_URL не задан — нечего пересылать")
        return jsonify({"error": "relay misconfigured: DISCORD_WEBHOOK_URL not set"}), 500

    data = request.get_json(silent=True)
    if data is None:
        log.warning("Получен запрос без валидного JSON")
        return jsonify({"error": "invalid json"}), 400

    log.info("Получен payload от FS: %s байт", len(request.data))

    # FS может прислать либо {"stockpiles": [...]}, либо один stockpile напрямую
    stockpiles = data.get("stockpiles") if "stockpiles" in data else [data]

    embeds = []
    for sp in stockpiles:
        items = sp.get("items", [])
        has_data = any(i.get("quantity", 0) > 0 for i in items)
        if SKIP_EMPTY_SCANS and not has_data:
            log.info("Склад '%s' пуст/не распознан — пропускаю отправку", sp.get("name"))
            continue
        embeds.append(format_stockpile_embed(sp))

    if not embeds:
        log.info("Нечего отправлять (все склады пусты)")
        return jsonify({"status": "skipped", "reason": "no data"}), 200

    # Discord позволяет до 10 embeds за один запрос
    discord_payload = {"embeds": embeds[:10]}

    try:
        resp = requests.post(DISCORD_WEBHOOK_URL, json=discord_payload, timeout=10)
        log.info("Discord ответил: %s %s", resp.status_code, resp.text[:200])
        resp.raise_for_status()
    except requests.RequestException as e:
        log.error("Ошибка при отправке в Discord: %s", e)
        return jsonify({"error": "discord delivery failed", "detail": str(e)}), 502

    return jsonify({"status": "ok", "sent_embeds": len(embeds)}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "discord_configured": bool(DISCORD_WEBHOOK_URL)}), 200


if __name__ == "__main__":
    if not DISCORD_WEBHOOK_URL:
        log.warning(
            "DISCORD_WEBHOOK_URL не задан! Установите переменную окружения перед запуском:\n"
            "  Windows (PowerShell): $env:DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/...'\n"
            "  Windows (cmd): set DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...\n"
            "  Linux/Mac: export DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/..."
        )
    log.info("Relay запущен на http://127.0.0.1:%s/relay", RELAY_PORT)
    app.run(host="127.0.0.1", port=RELAY_PORT)
