"""
Foxhole Stockpiles -> Discord relay (с рендером картинки).

Принимает POST-запросы с JSON от FS (output handler "webhook") и
пересылает отформатированное СООБЩЕНИЕ-КАРТИНКУ в настоящий Discord webhook:
иконка предмета - название предмета - количество, на фоне gray-background.jpg.

Запуск:
    pip install flask requests pillow
    set DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/....   (Windows: set, Linux/Mac: export)
    python relay.py

В настройках FS (Выводы -> Новый обработчик -> webhook) укажите URL этого relay:
    http://127.0.0.1:5001/relay
(auth_type оставьте null/пустым — relay не требует авторизации от FS,
 сам relay отдельно авторизуется в Discord через свой webhook URL).

Диагностика нераспознанных предметов (тех, что рендерятся пустым квадратом
и/или английским "причёсанным" кодом вместо перевода):
  - каждая такая находка пишется в консоль строкой с тегом UNMAPPED_ITEM;
  - плюс копится в файле unmapped_items.log (рядом со скриптом, JSON-lines,
    одна строка = один код, без дублей);
  - плюс доступна на GET http://127.0.0.1:5001/unmapped в виде JSON;
  - после каждого запроса /relay в лог печатается сводный блок
    "=== НЕРАСПОЗНАННЫЕ ПРЕДМЕТЫ ===" — его удобнее всего целиком
    скопировать и прислать для разбора, вместо скриншотов.
"""

import os
import io
import re
import json
import time
import logging
import difflib
import unicodedata

from flask import Flask, request, jsonify
import requests
from PIL import Image, ImageDraw, ImageFont

# item_codes.py должен лежать рядом с relay.py (та же папка).
# Содержит автосгенерированный словарь ITEM_CODES: код -> оригинальное
# название предмета (транслит из кириллицы, без перевода смысла).

# Объявляем пути и импортируем локализацию из ядра приложения
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RU_TRANSLATIONS_PATH = os.path.join(SCRIPT_DIR, "foxhole_stockpiles", "i18n", "translations", "ru.json")

# Загружаем базовый перевод из ru.json
try:
    with open(RU_TRANSLATIONS_PATH, "r", encoding="utf-8") as f:
        ITEM_CODES = json.load(f)
except Exception as e:
    print(f"Предупреждение: Не удалось загрузить ru.json: {e}")
    ITEM_CODES = {}

# Дополняем базу кастомными переводами из вашего item_codes.py
try:
    from item_codes import ITEM_CODES as CUSTOM_CODES
    for key, val in CUSTOM_CODES.items():
        ITEM_CODES[key] = val
except Exception as e:
    print(f"Предупреждение: Не удалось дополнить базу из item_codes.py: {e}")

# Английские названия предметов ТОЧНО как в игре (колонка "Page Name" на
# foxhole.wiki.gg/wiki/Codenames) — используются как fallback для кодов,
# у которых ещё нет ни ручного перевода, ни строки в ITEM_CODES выше.
# Без этого слоя display_item_name() скатывался бы в некрасивый
# prettify_code() (например "ATRPGTW" -> "A T R P G T W" вместо
# нормального "Mounted Bonesaw MK.3").
try:
    from wiki_page_names import WIKI_PAGE_NAMES
except Exception as e:
    print(f"Предупреждение: Не удалось загрузить wiki_page_names.py: {e}")
    WIKI_PAGE_NAMES = {}


# ---- Настройки -------------------------------------------------------

# Реальный webhook URL вашего Discord-канала.
# ВАЖНО: не хардкодьте его в коде, если будете куда-то выкладывать скрипт.
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

# Порт, на котором relay слушает запросы от FS
RELAY_PORT = int(os.environ.get("RELAY_PORT", "5001"))

# Не слать сообщение, если ни один предмет не найден / все нули
SKIP_EMPTY_SCANS = True

# Пути к ресурсам для рендера картинки.
# ВАЖНО: если меняете значения по умолчанию — убедитесь, что реальная папка
# Icons действительно лежит по этому пути на вашей машине. Раньше здесь
# стоял путь относительно самого relay.py, но это привело к тому, что
# ICONS_DIR не находился (у вас реальная папка иконок лежит по старому
# пути на диске D:), из-за чего ВСЕ иконки разом переставали находиться.
# Переопределить можно через переменные окружения BACKGROUND_PATH / ICONS_DIR.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPT_DIR = SCRIPT_DIR

# Теперь, если переменные окружения не заданы, пути соберутся автоматически из папки скрипта
BACKGROUND_PATH = os.environ.get(
    "BACKGROUND_PATH",
    os.path.join(SCRIPT_DIR, "scr", "gray-background.jpg")
)
ICONS_DIR = os.environ.get(
    "ICONS_DIR",
    os.path.join(SCRIPT_DIR, "Icons Foxhole", "FoxholeWikiPhotos")
    # ВАЖНО: сузили источник иконок ТОЛЬКО до папки с вики-иконками, по
    # прямой просьбе - старые вручную вырезанные иконки (лежащие в других
    # подпапках "Icons Foxhole") больше не учитываются вообще, даже если
    # на них есть ссылка в ITEM_ICON_FILES / icon_fixes.py / item_codes.py.
    # Если нужно вернуть прежнее поведение (искать везде) - убери
    # ", "FoxholeWikiPhotos"" из пути выше, либо задай ICONS_DIR явно.
)
# Шрифт с поддержкой кириллицы. На Windows arial.ttf/arialbd.ttf почти всегда есть.
FONT_PATH = os.environ.get("FONT_PATH", r"C:\Windows\Fonts\arial.ttf")
FONT_BOLD_PATH = os.environ.get("FONT_BOLD_PATH", r"C:\Windows\Fonts\arialbd.ttf")

# Геометрия картинки
CANVAS_WIDTH = 1000
HEADER_HEIGHT = 190  # 3 строки шапки (Гекс / Тип / Склад) + место под "Стр. X/Y"
ROW_HEIGHT = 110
ICON_SIZE = 90
PADDING_X = 40
ROW_FONT_SIZE = 46
HEADER_FONT_SIZE = 40

# Сколько предметов помещать на одну картинку. Если у склада предметов больше —
# рендерим несколько картинок (страниц) и шлём их отдельными сообщениями в Discord,
# чтобы не получалась одна нечитаемая "простыня" на 3000+ пикселей высотой.
MAX_ROWS_PER_IMAGE = int(os.environ.get("MAX_ROWS_PER_IMAGE", "12"))

# Пауза между отдельными сообщениями в Discord (сек), чтобы не упереться в рейт-лимит
# вебхуков (Discord ограничивает ~5 запросов/2 сек на один webhook).
DISCORD_SEND_DELAY = float(os.environ.get("DISCORD_SEND_DELAY", "0.4"))

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
    "RifleAutomaticW": "Винтовка Sampo 77",
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
    # Три строки ниже раньше были грубыми угадайками ("стационарная ...
    # установка" без названия модели) под кодами EmplacedInfantryW /
    # EmplacedATW / EmplacedLightArtilleryW. По официальной вики Foxhole
    # (Codenames) эти самые коды на деле принадлежат конкретным турелям
    # ("Leary Snare Trap 20", "Leary Shellbore 68mm", "Huber Lariat 120mm")
    # — настоящие записи см. в блоке "Сооружения" ниже, дубли отсюда убраны.

    # Контейнеры / логистика
    "ResourceContainer": "контейнер для ресурсов",
    "ShippingContainer": "Грузовой контейнер",
    "MaterialPlatform": "Поддон для материалов",
    "LiquidContainer": "Жидкостный контейнер",

    # Прочее
    "Unknown": "Неизвестно",

    # Добавлено по факту встречи в реальных данных FS (коды, которых не было
    # в первоначальном списке — оружие/боеприпасы, отсутствовавшие выше)
    "ShotgunW": "дробовик",
    "Mortar": "миномёт",
    "HeavyArtilleryAmmo": "150мм снаряды",
    "LandingCraftC": "десантный катер",
    "LightBoatInfantryW": "лёгкая пехотная лодка",

    # Добавлено: коды, которые раньше отсутствовали в словаре и поэтому
    # показывались "причёсанным" английским кодом вместо перевода
    # (сопоставлены по совпадающему количеству предметов на скриншотах Discord).
    "RifleHeavyW": "Хангман 757",
    "RifleLongW": "Clancy Cinder M3",
    "RifleAmmo": "7.62-мм",
    "FlameBackpackW": "Топливо для Willow's Bane",
    "Tripod": "Тренога",
    "FirstAidKit": "Набор Первой Помощи",
    "BloodPlasma": "Плазма",
    "DemolitionRocketAmmo": "Разрушающая ракета",
    "LightAAAmmo": 'Зенитный снаряд “Absol”',

    # --- Сооружения (структуры) ---
    # ВНИМАНИЕ: коды слева (кроме первых 4 контейнеров выше) — это МОИ
    # ПРЕДПОЛОЖЕНИЯ, а не подтверждённые коды из реального JSON от FS —
    # у нас не было ни одного реального payload с этими предметами, только
    # скриншот инвентаря и текстовое название. Если после реального скана
    # склада с этими структурами предмет всё ещё показывается непереведённым
    # (см. UNMAPPED_ITEM в консоли / unmapped_items.log) — возьмите оттуда
    # настоящий code и замените ключ здесь на него.
    "ConcreteMixer": "Бетономешалка",
    "ConstructionEquipment": "Строительное оборудование",
    "EmplacedAircraftC": "DAE 5b Zeal",
    "EmplacedAircraftW": "Leary AA-70 Bolas",
    "EmplacedATLargeW": "Huber Starbreaker 94.5",
    "EmplacedATW": "Leary Shellbore 68-мм",
    "EmplacedCannonLargeC": "DAE 2a-1 Ruptura",
    "EmplacedHeavyArtilleryC": "50-500 Thunderbolt Cannon",
    "EmplacedHeavyArtilleryW": "Huber Exalt 150mm",
    "EmplacedIndirectC": "DAE 1o-3 Polybolos",
    "EmplacedInfantryC": "DAE 1b-2 Serra",
    "EmplacedInfantryW": "Leary Snare Trap 20",
    "EmplacedLightArtilleryW": "Huber Lariat 120мм",
    "EmplacedMultiC": "DAE 3b-2 Hades Net",
    "FortConstructionPart": "Строительные детали",
    "FortGarrisonStationPart": "Детали подземной крепости",
    "FortIntelCenterPart": "Разведывательный Центр",
    "FortLargeRadarPart": "SC-3 Aerial Interceptor Array Parts",
    "FortLRArtilleryPart": "Детали Штурмового Орудия",
    "StructureCrate": "Ящик с сооружениями",
    "FortWeatherStationPart": "Детали погодной станции",
    "RocketPartBottom": "AOE-9 Ракетный Ускоритель",
    "RocketPartCenter": "Корпус ракеты AOE-9",
    "RocketPartTop": "AOE-9 ракетная боеголовка",
    "ShipPart1": "Корабельный сегмент корпуса",
    "ShipPart2": "Корабельная обшивка корпуса",
    "ShipPart3": "Компоненты морских турбин",
}

# Правка: "WaterWallMaterials" уже был в словаре выше со значением "naval buoy"
# в нижнем регистре — приводим к оригинальному написанию названия предмета.
ITEM_NAMES_RU["WaterWallMaterials"] = "Naval Buoy"

# Добавляем автосгенерированные коды (item_codes.py) в общий словарь имён.
# Приоритет остаётся за записями, заданными вручную выше: если код уже
# есть в ITEM_NAMES_RU, значение из ITEM_CODES его не перезаписывает.
for _code, _name in ITEM_CODES.items():
    ITEM_NAMES_RU.setdefault(_code, _name)

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

# Явное сопоставление код предмета -> имя файла иконки в ICONS_DIR.
# Заполняйте сюда, если автоматический поиск (см. find_icon_path) не нашёл
# нужный файл или нашёл не тот — тогда явное правило будет иметь приоритет.
# Пример: "AluminumA": "Aluminum.png",
ITEM_ICON_FILES = {
    # Ключ — код предмета из FS (поле "code"), значение — имя файла в ICONS_DIR.
    # Файлы в ICONS_DIR названы кодами из item_codes.py (см. соседний файл) —
    # поэтому большинству предметов, которые приходят из item_codes.py напрямую
    # (через автодополнение ITEM_NAMES_RU чуть выше), явная запись тут вообще
    # не нужна: find_icon_path() найдёт "<code>.png" автоматическим точным
    # совпадением. Ниже — только "исторические" коды FS, которые называются
    # иначе, чем файл иконки, и поэтому требуют явной связки.

    # --- Ресурсы и материалы ---
    "AluminumA": "AlyuminievyySplav.png",
    "WaterBucket": "VedroDlyaVody.png",
    "ListeningKit": "NaborDlyaProslushivaniya.png",
    "ExplosiveTripod": "StankovyyFissuragdI.png",
    "FacilityMaterials4": "SborochnyeMaterialyIV.png",
    "FacilityMaterials1": "SborochnyeMaterialyI.png",
    "PilotMask": "MaskaPilota.png",
    "CopperA": "MednyySplav.png",
    "SandbagMaterials": "MeshokSPeskom.png",
    "MetalBeamMaterials": "MetallicheskayaBalka.png",
    "FacilityOil1": "Neft.png",       # нет отдельной иконки под "нефть для объекта", используем обычную нефть
    "FacilityOil2": "Neft.png",
    "FacilityOil3": "Neft.png",
    "RareMaterials": "RedkieMaterialy.png",
    "RareMetal": "RedkiyMetall.png",
    "Oil": "Neft.png",
    "Diesel": "Dizel.png",
    "Petrol": "Benzin.png",
    "Water": "Voda.png",
    "BarbedWireMaterials": "KolyuchayaProvoloka.png",
    "WaterWallMaterials": "NavalBuoy.png",
    "Cloth": "BazovyeMaterialy.png",   # "биматы" = базовые материалы
    "GroundMaterials": "Graviy.png",
    "Explosive": "Porokh.png",

    # --- Медицина / расходники ---
    "TraumaKit": "NaborPervoyPomoshchi.png",
    "Bandages": "Binty.png",
    "GasMask": "Protivogaz.png",
    "StickyBomb": "ProtivotankovayaLipkayaBomba.png",
    "MaintenanceSupplies": "PripasyObsluzhivaniya.png",

    # --- Обмундирование ---
    "SoldierSupplies": "SoldatskoeSnaryazhenie.png",
    "SnowUniformW": "UteplennayaShinel.png",
    "MedicUniformW": "MeditsinskayaForma.png",
    "ScoutUniformW": "KamuflyazhRazvedchika.png",
    "TankUniformW": "KombinezonTankista.png",
    "EngineerUniformW": "SapernoeSnaryazhenie.png",
    "ArmourUniformW": "StalnayaKirasa.png",
    "OfficerUniformW": "OfitserskayaRegaliya.png",
    "AmmoUniformW": "ShinelSpetsialista.png",

    # --- Оружие ---
    "Revolver": "CometaT29.png",
    "Shovel": "Lopata.png",
    "WorkWrench": "GaechnyyKlyuch.png",
    "RifleAutomaticW": "AvtomaticheskayaVintovkaSampo77.png",
    "SmokeGrenade": "DymovayaGranataPT815.png",
    "ATRifleW": "ProtivotankovoeRuzheNeville.png",
    "HEGrenade": "Mammon91b.png",
    "RifleLightW": "Blakerow871.png",
    "SMGHeavyW": "PistoletPulemetNo1TheLiar.png",
    "SMGW": "PistoletPulemetFiddlerModel868.png",
    "RadioBackpack": "Radioryukzak.png",
    "RifleW": "No2Loughcaster.png",
    "GrenadeAdapter": "PodstvolnyyGranatomet.png",
    "GrenadeW": "OskolochnayaGranataA3Harpa.png",
    "GreenAsh": "GazovayaGranata.png",
    "SledgeHammer": "Kuvalda.png",
    "Binoculars": "Binokl.png",
    "Radio": "Ratsiya.png",
    "SurfaceWaterMine": "E681BHullbreakerMine.png",

    # --- Боеприпасы ---
    "LightArtilleryAmmo": "120Mm.png",
    "MGAmmo": "12.7Mm.png",
    "ATLargeAmmo": "94.5Mm.png",
    "AircraftAmmo": "20Mm.png",
    "MortarAmmo": "MinometnyySnaryad.png",
    "AssaultRifleAmmo": "7.92Mm.png",
    "ShotgunAmmo": "Drob.png",
    "MiniTorpedoAmmo": "TorpedaQuillback.png",
    "MortarAmmoFL": "OsvetitelnyyMinometnyySnaryad.png",
    "ATRifleAmmo": "14.5mm.png",
    "PistolAmmo": "8Mm.png",
    "RevolverAmmo": "44Magnum.png",
    "RpgAmmo": "Rpg.png",
    "MortarAmmoSH": "OskolochnyyMinometnyySnaryad.png",
    "SMGAmmo": "9Mm.png",

    # --- Техника ---
    # Технику сопоставляем аккуратно: у FS коды вида "TruckW"/"ArmoredCarW" —
    # обобщённые, а в item_codes.py под них может быть несколько конкретных
    # моделей (разных фракций/тиров). Ниже — только те случаи, где сопоставление
    # однозначно; остальные оставлены закомментированными для ручной проверки.
    # ScoutTankW ("KingSpireMkI.png") и Freighter ("BMSIronship.png") и
    # FlatbedTruck ("BortovoyGruzovikBMSPackmule.png") были прописаны на
    # несуществующие файлы — таких иконок нет нигде в ICONS_DIR (проверено
    # по полному листингу icons_list.txt). Записи убраны, чтобы не сыпать
    # ложным warning "файл не найден"; теперь эти 3 кода просто попадут в
    # unmapped_items.log как обычные icon_missing=true, пока не появится
    # подходящий файл иконки.
    "FreighterLight": "005_Krokodil.png",      # было DasKrokodilbyVAC.png (не существует) - реальный файл найден
    "TruckResourceW": "013_Loadlugger.png",    # было SamosvalDunneLoadlugger3c.png (не существует) - реальный файл найден
    "FlatbedTruck": "003_Flatbed.png",         # было BortovoyGruzovikBMSPackmule.png (не существует) - реальный файл найден
    # Ниже — новые сопоставления, ставшие возможны после того, как в
    # ICONS_DIR добавили корневой каталог техники (001-117), см. relay.py
    # build_icon_index(): числовой префикс "NNN_" при индексации срезается,
    # но для наглядности тут оставлены полные оригинальные имена файлов.
    "TruckMobilityW": "114_Landrunner.png",           # подтверждено в переписке: Landrunner
    "ScoutVehicleOffensiveW": "101_Spitfire_7.92.png",  # подтверждено в переписке: Spitfire
    "Construction": "030_CV.png",                      # "CV (тир 1)" = Construction Vehicle
    "Gunboat2W": "060_Mulloy.png",                      # "БТР-Амфибия (Mulloy)"
    "LandingCraftW": "060_Mulloy.png",                  # тот же Mulloy, второй FS-код на то же судно
    "ArmoredCarW": "028_OBrien_7.92.png",               # "O'Brien бронеавтомобиль"
    "AmbulanceFlameW": "016_Salva.png",                 # "пожарная машина" = Salva
    "MediumBoatC": "016_Salva.png",                     # тот же Salva, старый FS-код с тем же значением
    "AmbulanceW": "015_Salus.png",                      # "скорая помощь" = Salus
    "ScoutVehicleUtilityC": "015_Salus.png",            # "Машина скорой помощи" — тоже Salus
    # Пока не сопоставлено явно (нет уверенного 1-в-1 соответствия с файлом
    # из корневого каталога техники) — оставлено для ручной проверки:
    # "TruckDefensiveW": ???     — "Дюна"
    # "TruckLiquidW": ???        — "Дюна бензовоз"
    # "ArmoredCar2LargeW": ???
    # "HeavyTruckW": ???         — "кнут"
    # "LightTankC": ???
    # "TrailerMaterial": ???
    # "TruckW": ???              — просто "грузовик", слишком общий код для однозначного выбора
    # "BusW": ???                — "автобус"
    # "EmplacedInfantryW": ???

    # --- Добавлено по факту встречи в реальных данных FS ---
    "ShotgunW": "No4ThePilloryScattergun.png",
    "Mortar": "MinometCremari.png",
    "HeavyArtilleryAmmo": "150Mm.png",
    # "LandingCraftC": ???      — файла иконки для этой техники пока нет
    # "LightBoatInfantryW": ??? — файла иконки для этой техники пока нет

    # --- Контейнеры / логистика ---
    "ResourceContainer": "KonteynerDlyaResursov.png",
    "ShippingContainer": "GruzovoyKonteyner.png",
    "MaterialPlatform": "PoddonDlyaMaterialov.png",
    "LiquidContainer": "ZhidkostnyyKonteyner.png",

    # --- Добавлено: иконки для кодов, которые давали пустой квадрат ---
    # Ранее без иконки (файл сопоставлен по совпадению количества на скрине):
    "RifleHeavyW": "Khangman757.png",
    "RifleLongW": "ClancyCinderM3.png",
    "RifleAmmo": "7.62Mm.png",
    "FlameBackpackW": "ToplivoDlyaWillowsBane.png",
    "Tripod": "Trenoga.png",
    "FirstAidKit": "NaborPervoyPomoshchi.png",
    "BloodPlasma": "Plazma.png",
    # Имя уже было в ITEM_NAMES_RU, но иконка раньше не была сопоставлена:
    "Bayonet": "BuckhornCCQ18.png",
    "NavalUniformW": "GentlemansPeacoat.png",
    "DemolitionRocketAmmo": "RazrushayushchayaRaketa.png",
    "LightAAAmmo": "ZenitnyySnaryadAbsol.png",

    # --- Сооружения (структуры) ---
    # Коды здесь — предположения (см. пояснение у этих же кодов в
    # ITEM_NAMES_RU выше), а вот имена файлов — честные, транслитерация
    # выверена по уже существующим записям (см. блок "Контейнеры /
    # логистика" чуть выше — схема совпала 1-в-1).
    "ConcreteMixer": "Betonomeshalka.png",
    "ConstructionEquipment": "StroitelnoeOborudovanie.png",
    "EmplacedAircraftC": "DAE5bZeal.png",
    "EmplacedAircraftW": "LearyAA70Bolas.png",
    "EmplacedATLargeW": "HuberStarbreaker94.5.png",
    "EmplacedATW": "LearyShellbore68Mm.png",
    "EmplacedCannonLargeC": "DAE2a1Ruptura.png",
    "EmplacedHeavyArtilleryC": "50500ThunderboltCannon.png",
    "EmplacedHeavyArtilleryW": "HuberExalt150mm.png",
    "EmplacedIndirectC": "DAE1o3Polybolos.png",
    "EmplacedInfantryC": "DAE1b2Serra.png",
    "EmplacedInfantryW": "LearySnareTrap20.png",
    "EmplacedLightArtilleryW": "HuberLariat120mm.png",
    "EmplacedMultiC": "DAE3b2HadesNet.png",
    "FortConstructionPart": "StroitelnyeDetali.png",
    "FortGarrisonStationPart": "DetaliPodzemnoyKreposti.png",
    "FortIntelCenterPart": "RazvedyvatelnyyTsentr.png",
    "FortLargeRadarPart": "SC3AerialInterceptorArrayParts.png",
    "FortLRArtilleryPart": "DetaliShturmovogoOrudiya.png",
    "StructureCrate": "YashchikSSooruzheniyami.png",
    "FortWeatherStationPart": "DetaliPogodnoyStantsii.png",
    "RocketPartBottom": "AOE9RaketnyyUskoritel.png",
    "RocketPartCenter": "KorpusRaketyAOE9.png",
    "RocketPartTop": "AOE9RaketnayaBoegolovka.png",
    "ShipPart1": "KorabelnyySegmentKorpusa.png",
    "ShipPart2": "KorabelnayaObshivkaKorpusa.png",
    "ShipPart3": "KomponentyMorskikhTurbin.png",
}

# Иконки с Foxhole Wiki (результат match_wiki_icons.py). ПРИОРИТЕТ ОТДАН ИМ:
# ICONS_DIR теперь указывает ТОЛЬКО на папку FoxholeWikiPhotos, поэтому любая
# старая ссылка в ITEM_ICON_FILES (на файл вне этой папки) всё равно никогда
# не найдётся - оставлять её в приоритете нет смысла, она просто маскирует
# рабочее вики-совпадение. Поэтому здесь прямая перезапись, а не setdefault.
try:
    from wiki_icon_fixes import WIKI_ICON_FIXES
    for _code, _fname in WIKI_ICON_FIXES.items():
        ITEM_ICON_FILES[_code] = _fname
except ImportError as e:
    print(f"Предупреждение: wiki_icon_fixes.py не подключен: {e}")


def prettify_code(code: str) -> str:
    """Разбивает CamelCase-код на читаемые слова, если перевода нет в словаре.
    Например 'MetalBeamMaterials' -> 'Metal Beam Materials'."""
    spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", code)
    spaced = re.sub(r"(?<=[a-zA-Z])(?=\d)", " ", spaced)
    return spaced.strip()


def display_item_name(code: str) -> str:
    if code in ITEM_NAMES_RU:
        return ITEM_NAMES_RU[code]
    # Нет русского перевода — берём настоящее английское название из игры
    # (колонка "Page Name" на foxhole.wiki.gg/wiki/Codenames), а не корёжим
    # сам код пробелами по CamelCase. Так "PistolLightW" покажется как
    # "Cascadier 873", а не как "Pistol Light W".
    if code in WIKI_PAGE_NAMES:
        return WIKI_PAGE_NAMES[code]
    return prettify_code(code)


def display_stockpile_type(stype: str) -> str:
    return STOCKPILE_TYPE_RU.get(stype, stype)


def prettify_hex(hex_code: str) -> str:
    """Превращает код региона в читаемое название.
    Например 'BasinSionnachHex' -> 'Basin Sionnach'."""
    text = hex_code
    if text.endswith("Hex"):
        text = text[:-3]
    return prettify_code(text)


logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")
log = logging.getLogger("relay")

app = Flask(__name__)

# ---- Лог нераспознанных предметов --------------------------------------
# Каждый раз, когда для предмета не нашлось перевода в ITEM_NAMES_RU и/или
# иконки в ITEM_ICON_FILES/ICONS_DIR, это пишется:
#   1) сразу в консоль одной строкой с тегом UNMAPPED_ITEM (удобно грепать),
#   2) в файл unmapped_items.log рядом со скриптом, в формате JSON-lines —
#      по одной записи на код, с дедупликацией (при повторной встрече
#      обновляется last_seen/quantity, а не плодятся дубли).
# Если нужно прислать Клоду для разбора — проще всего приложить именно
# этот файл целиком, а не скриншоты.
UNMAPPED_LOG_PATH = os.environ.get(
    "UNMAPPED_LOG_PATH",
    os.path.join(_SCRIPT_DIR, "unmapped_items.log"),
)

_unmapped_registry = {}  # code -> dict с последними деталями (для дедупликации в рамках рантайма)


def _record_unmapped(code, prettified_guess, quantity, crated, stockpile_name, hex_display,
                      name_missing, icon_missing):
    """Регистрирует нераспознанный предмет: логирует одной строкой в консоль
    и дописывает/обновляет запись в UNMAPPED_LOG_PATH (JSON-lines)."""
    if not name_missing and not icon_missing:
        return

    entry = {
        "code": code,
        "guess": prettified_guess,
        "quantity": quantity,
        "crated": crated,
        "stockpile": stockpile_name,
        "hex": hex_display,
        "name_missing": name_missing,
        "icon_missing": icon_missing,
    }
    _unmapped_registry[code] = entry

    log.warning(
        "UNMAPPED_ITEM code=%s guess=%r qty=%s crated=%s stockpile=%s hex=%s name_missing=%s icon_missing=%s",
        code, prettified_guess, quantity, crated, stockpile_name, hex_display, name_missing, icon_missing,
    )

    try:
        with open(UNMAPPED_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as e:
        log.error("Не удалось записать unmapped_items.log: %s", e)


def _log_unmapped_summary():
    """Печатает в консоль сводку по всем нераспознанным предметам, встреченным
    с момента запуска relay — удобно скопировать целиком и прислать для разбора."""
    if not _unmapped_registry:
        return
    lines = ["=== НЕРАСПОЗНАННЫЕ ПРЕДМЕТЫ (скопируйте этот блок целиком) ==="]
    for code, e in sorted(_unmapped_registry.items()):
        missing = []
        if e["name_missing"]:
            missing.append("имя")
        if e["icon_missing"]:
            missing.append("иконка")
        lines.append(
            f'code={code} qty={e["quantity"]} crated={e["crated"]} '
            f'stockpile={e["stockpile"]} hex={e["hex"]} guess="{e["guess"]}" '
            f'отсутствует=({", ".join(missing)})'
        )
    lines.append("=== КОНЕЦ ===")
    log.info("\n" + "\n".join(lines))

# ---- Поиск файлов иконок ------------------------------------------------

_icon_index_cache = None


def _normalize(s: str) -> str:
    """Убирает всё, кроме букв/цифр, приводит к нижнему регистру —
    так 'Metal Beam Materials.png' и 'MetalBeamMaterials' совпадут."""
    s = s.lower()
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"[^a-z0-9а-яё]", "", s)
    return s


def build_icon_index() -> dict:
    """Рекурсивно сканирует ICONS_DIR (и ВСЕ его подпапки — раньше сканировалась
    только одна конкретная подпапка, из-за чего большинство иконок не находилось)
    и строит индекс: нормализованное_имя_файла -> полный путь к файлу.

    Для файлов с числовым префиксом вида "001_Barge.png" (каталог техники в
    корне ICONS_DIR) индекс дополнительно получает запись БЕЗ префикса
    ("barge" -> путь), чтобы такие файлы находились по обычному коду/имени
    предмета точно так же, как и все остальные иконки.

    Если два разных файла в разных подпапках дают одинаковый нормализованный
    ключ — побеждает первый найденный (порядок обхода os.walk), остальные
    только логируются на уровне DEBUG, чтобы не шуметь в консоли.
    """
    global _icon_index_cache
    if _icon_index_cache is not None:
        return _icon_index_cache

    index = {}
    collisions = 0
    if os.path.isdir(ICONS_DIR):
        for dirpath, _dirnames, filenames in os.walk(ICONS_DIR):
            for fname in filenames:
                ext = os.path.splitext(fname)[1].lower()
                if ext not in (".png", ".jpg", ".jpeg", ".webp"):
                    continue
                path = os.path.join(dirpath, fname)
                stem = os.path.splitext(fname)[0]

                keys = {_normalize(stem)}
                # числовой префикс "001_", "042_" и т.п. — убираем и добавляем
                # вторым вариантом ключа
                no_prefix = re.sub(r"^\d+_", "", stem)
                if no_prefix != stem:
                    keys.add(_normalize(no_prefix))

                for key in keys:
                    if not key:
                        continue
                    if key in index and index[key] != path:
                        collisions += 1
                        log.debug("Коллизия ключа иконки '%s': %s уже указывает на %s, "
                                  "новый файл %s пропущен", key, key, index[key], path)
                        continue
                    index[key] = path

        log.info("Проиндексировано %d иконок (ключей) из %s и его подпапок%s",
                  len(index), ICONS_DIR,
                  f" ({collisions} коллизий имён пропущено)" if collisions else "")
    else:
        log.warning("Папка с иконками не найдена: %s", ICONS_DIR)

    _icon_index_cache = index
    return index


def find_icon_path(code: str, display_name: str):
    """Пытается найти файл иконки для предмета:
    1) явная запись в ITEM_ICON_FILES,
    2) точное совпадение по коду / причёсанному коду / рус. имени,
    3) нечёткое совпадение (difflib) на случай небольших расхождений в имени файла.
    Возвращает путь к файлу или None, если ничего не найдено."""
    index = build_icon_index()

    if code in ITEM_ICON_FILES:
        forced_name = ITEM_ICON_FILES[code]
        # ВАЖНО: ICONS_DIR теперь корневая папка, а сама иконка может лежать
        # в любой из вложенных подпапок — поэтому ищем её через индекс
        # (build_icon_index сканирует рекурсивно) по нормализованному имени
        # файла, а не склеиваем путь напрямую через os.path.join(ICONS_DIR, ...).
        forced_stem = os.path.splitext(forced_name)[0]
        forced_key = _normalize(forced_stem)
        if forced_key in index:
            return index[forced_key]
        # На случай, если значение в ITEM_ICON_FILES — уже полный путь
        # (относительный или абсолютный), а не просто имя файла:
        direct_path = os.path.join(ICONS_DIR, forced_name)
        if os.path.isfile(direct_path):
            return direct_path
        log.warning("Файл из ITEM_ICON_FILES не найден ни в индексе, ни на диске: %s", forced_name)

    candidates = [code, prettify_code(code), display_name]
    for cand in candidates:
        key = _normalize(cand)
        if key in index:
            return index[key]

    # cutoff поднят с 0.6 до 0.85: при 0.6 нечёткое совпадение слишком часто
    # находило ПОХОЖУЮ, но НЕВЕРНУЮ иконку (например, короткие русские названия
    # вроде "штык-нож" или "форма моряка" совпадали с случайным другим файлом).
    # Лучше показать пустой квадрат-заглушку и лог-предупреждение, чем тихо
    # подставить неправильную картинку.
    keys = list(index.keys())
    for cand in candidates:
        key = _normalize(cand)
        matches = difflib.get_close_matches(key, keys, n=1, cutoff=0.85)
        if matches:
            return index[matches[0]]

    return None



# Запасные шрифты с поддержкой кириллицы на случай, если основной FONT_PATH/
# FONT_BOLD_PATH не найден (например, relay запускают не на Windows).
# ImageFont.load_default() кириллицу не умеет вообще — молча превращает
# весь русский текст в "тофу"-прямоугольники, поэтому его используем только
# как самый последний вариант.
_FALLBACK_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "C:\\Windows\\Fonts\\segoeui.ttf",
    "C:\\Windows\\Fonts\\calibri.ttf",
]
_FALLBACK_FONTS_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "C:\\Windows\\Fonts\\segoeuib.ttf",
    "C:\\Windows\\Fonts\\calibrib.ttf",
]


def _load_font(path: str, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except Exception as e:
        log.warning("Не удалось загрузить шрифт %s (%s) — пробую запасные варианты", path, e)

    for fallback in (_FALLBACK_FONTS_BOLD if bold else _FALLBACK_FONTS):
        try:
            return ImageFont.truetype(fallback, size)
        except Exception:
            continue

    log.warning("Ни один TTF-шрифт с кириллицей не найден — русский текст "
                "не отобразится корректно. Проверьте FONT_PATH/FONT_BOLD_PATH.")
    return ImageFont.load_default()


def _load_background(width: int, height: int) -> Image.Image:
    """Загружает фон и растягивает/тайлит его на нужный размер картинки."""
    try:
        bg = Image.open(BACKGROUND_PATH).convert("RGB")
    except Exception as e:
        log.warning("Не удалось загрузить фон %s (%s) — использую сплошной серый", BACKGROUND_PATH, e)
        return Image.new("RGB", (width, height), (58, 58, 58))

    canvas = Image.new("RGB", (width, height))
    tile_w, tile_h = bg.size
    if tile_w <= 0 or tile_h <= 0:
        return Image.new("RGB", (width, height), (58, 58, 58))
    for y in range(0, height, tile_h):
        for x in range(0, width, tile_w):
            canvas.paste(bg, (x, y))
    return canvas


def _draw_header(canvas, draw, header_font, hex_display, stype_short, name, page_idx=None, total_pages=None):
    # Три отдельные строки (а не одна длинная "Гекс: ... Тип: ..."), чтобы
    # длинные имена гексов/типов не наезжали на бейдж "Стр. X/Y" в углу.
    line_h = HEADER_FONT_SIZE + 10
    header_lines = [
        f"Гекс: {hex_display}",
        f"Тип: {stype_short}",
        f"Склад: {name or '—'}",
    ]
    for i, line in enumerate(header_lines):
        draw.text((PADDING_X, 15 + i * line_h), line, font=header_font,
                   fill=(255, 255, 255) if i != 1 else (230, 230, 230))

    if total_pages and total_pages > 1:
        page_label = f"Стр. {page_idx}/{total_pages}"
        bbox = draw.textbbox((0, 0), page_label, font=header_font)
        pw = bbox[2] - bbox[0]
        # Бейдж страницы — отдельной строкой в правом верхнем углу, не делит
        # строку с текстом гекса/типа/названия.
        draw.text((canvas.width - PADDING_X - pw, 15), page_label, font=header_font, fill=(150, 180, 255))

    draw.line((PADDING_X, HEADER_HEIGHT - 15, canvas.width - PADDING_X, HEADER_HEIGHT - 15),
               fill=(120, 120, 120), width=2)


def _wrap_to_width(draw, text, font, max_width, max_lines=2):
    """Разбивает text на строки шириной не более max_width. Если после
    max_lines строк текст всё ещё не влезает — обрезает с многоточием."""
    if draw.textlength(text, font=font) <= max_width:
        return [text]

    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
            if len(lines) == max_lines:
                break
    if cur and len(lines) < max_lines:
        lines.append(cur)

    if len(lines) > max_lines:
        lines = lines[:max_lines]
    if lines and draw.textlength(lines[-1], font=font) > max_width:
        # подрезаем последнюю строку с многоточием, если она всё равно не влезает
        s = lines[-1]
        while s and draw.textlength(s + "…", font=font) > max_width:
            s = s[:-1]
        lines[-1] = s + "…"
    return lines or [text]


def _draw_item_row(canvas, draw, row_font, y, item, stockpile_name="?", hex_display="?"):
    code = item.get("code", "?")
    qty = item.get("quantity", 0)
    crated = item.get("crated", False)
    display_name = display_item_name(code)
    name_missing = code not in ITEM_NAMES_RU

    icon_y = y + (ROW_HEIGHT - ICON_SIZE) // 2
    icon_path = find_icon_path(code, display_name)
    icon_missing = icon_path is None
    if icon_path:
        try:
            icon_img = Image.open(icon_path).convert("RGBA")
            icon_img = icon_img.resize((ICON_SIZE, ICON_SIZE))
            canvas.paste(icon_img, (PADDING_X, icon_y), icon_img)
        except Exception as e:
            log.warning("Ошибка загрузки иконки %s: %s", icon_path, e)
            icon_path = None
            icon_missing = True
    if not icon_path:
        draw.rectangle(
            (PADDING_X, icon_y, PADDING_X + ICON_SIZE, icon_y + ICON_SIZE),
            outline=(200, 200, 200), width=2,
        )

    _record_unmapped(code, display_name, qty, crated, stockpile_name, hex_display,
                      name_missing, icon_missing)

    label = f"{display_name} x {qty}"
    if crated:
        label += " (в ящике)"

    text_x = PADDING_X + ICON_SIZE + 30
    max_text_width = canvas.width - text_x - PADDING_X

    lines = _wrap_to_width(draw, label, row_font, max_text_width, max_lines=2)
    # Если получилось 2 строки — используем чуть более компактный межстрочный
    # интервал, чтобы обе строки поместились по высоте в ROW_HEIGHT.
    line_bbox = draw.textbbox((0, 0), "Ag", font=row_font)
    single_line_h = line_bbox[3] - line_bbox[1]
    line_gap = 6
    total_h = len(lines) * single_line_h + (len(lines) - 1) * line_gap

    text_y = y + ROW_HEIGHT // 2 - total_h // 2 - line_bbox[1]
    for line in lines:
        draw.text((text_x, text_y), line, font=row_font, fill=(255, 255, 255))
        text_y += single_line_h + line_gap


def render_stockpile_images(stockpile: dict) -> list:
    """Рендерит один stockpile в ОДНУ ИЛИ НЕСКОЛЬКО PNG-картинок:
    иконка - название - количество, на фоне gray-background.jpg.

    Если предметов больше MAX_ROWS_PER_IMAGE — список предметов режется на
    несколько страниц (картинок), каждая со своей копией шапки склада и
    номером "Стр. X/Y", чтобы результат оставался читаемым, а не был одной
    гигантской простынёй.

    Возвращает список байтов PNG — по одной картинке на страницу.
    """
    name = stockpile.get("name", "Unknown")
    stype_raw = stockpile.get("type", "Unknown")
    stype_short = STOCKPILE_TYPE_SHORT_RU.get(stype_raw, str(stype_raw).upper())
    hex_raw = stockpile.get("hex")
    hex_display = prettify_hex(hex_raw) if hex_raw else "—"

    items = [i for i in stockpile.get("items", []) if i.get("quantity", 0) != 0]

    header_font = _load_font(FONT_BOLD_PATH, HEADER_FONT_SIZE, bold=True)
    row_font = _load_font(FONT_PATH, ROW_FONT_SIZE)

    # Бьём items на страницы по MAX_ROWS_PER_IMAGE штук
    if items:
        pages_items = [
            items[i:i + MAX_ROWS_PER_IMAGE]
            for i in range(0, len(items), MAX_ROWS_PER_IMAGE)
        ]
    else:
        pages_items = [[]]  # одна пустая страница с "Предметы не обнаружены"

    total_pages = len(pages_items)
    png_pages = []

    for page_idx, page_items in enumerate(pages_items, start=1):
        width = CANVAS_WIDTH
        height = HEADER_HEIGHT + max(1, len(page_items)) * ROW_HEIGHT + 30

        canvas = _load_background(width, height)
        draw = ImageDraw.Draw(canvas)

        _draw_header(canvas, draw, header_font, hex_display, stype_short, name,
                     page_idx=page_idx, total_pages=total_pages)

        if not page_items:
            draw.text((PADDING_X, HEADER_HEIGHT + 20), "Предметы не обнаружены",
                       font=row_font, fill=(230, 230, 230))
        else:
            y = HEADER_HEIGHT
            for item in page_items:
                _draw_item_row(canvas, draw, row_font, y, item,
                                stockpile_name=name, hex_display=hex_display)
                y += ROW_HEIGHT

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        buf.seek(0)
        png_pages.append(buf.getvalue())

    return png_pages


def _send_single_image_message(image_bytes: bytes, filename: str) -> None:
    """Шлёт ОДНО сообщение в Discord с ОДНОЙ картинкой-вложением.
    Поднимает requests.RequestException при ошибке доставки."""
    payload = {"embeds": [{"image": {"url": f"attachment://{filename}"}, "color": 0x5865F2}]}
    resp = requests.post(
        DISCORD_WEBHOOK_URL,
        data={"payload_json": json.dumps(payload)},
        files={"files[0]": (filename, image_bytes, "image/png")},
        timeout=20,
    )
    log.info("Discord ответил: %s %s", resp.status_code, resp.text[:200])
    resp.raise_for_status()


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

    to_render = []
    for sp in stockpiles:
        items = sp.get("items", [])
        has_data = any(i.get("quantity", 0) != 0 for i in items)
        if SKIP_EMPTY_SCANS and not has_data:
            log.info("Склад '%s' пуст/не распознан — пропускаю отправку", sp.get("name"))
            continue
        to_render.append(sp)

    if not to_render:
        log.info("Нечего отправлять (все склады пусты)")
        return jsonify({"status": "skipped", "reason": "no data"}), 200

    # Каждая страница каждого склада уходит ОТДЕЛЬНЫМ сообщением в Discord —
    # так длинный склад не превращается в одну нечитаемую простыню, а
    # разбивается на несколько сообщений с картинками, которые удобно листать.
    sent_images = 0
    failed_stockpiles = []
    first_send = True

    for sp in to_render:
        try:
            pages = render_stockpile_images(sp)
        except Exception as e:
            log.error("Ошибка рендера картинки для склада '%s': %s", sp.get("name"), e)
            failed_stockpiles.append(sp.get("name"))
            continue

        for page_idx, img_bytes in enumerate(pages, start=1):
            if not first_send:
                time.sleep(DISCORD_SEND_DELAY)
            first_send = False

            filename = f"stockpile_{_normalize(str(sp.get('name', 'unknown')))}_{page_idx}.png"
            try:
                _send_single_image_message(img_bytes, filename)
                sent_images += 1
            except requests.RequestException as e:
                log.error("Ошибка при отправке в Discord (%s, стр. %s): %s",
                          sp.get("name"), page_idx, e)
                failed_stockpiles.append(f"{sp.get('name')} (стр. {page_idx})")

    if sent_images == 0:
        _log_unmapped_summary()
        return jsonify({"status": "error", "reason": "no images delivered",
                         "failed": failed_stockpiles}), 502

    result = {"status": "ok", "sent_images": sent_images}
    if failed_stockpiles:
        result["partial_failures"] = failed_stockpiles
    _log_unmapped_summary()
    return jsonify(result), 200


@app.route("/unmapped", methods=["GET"])
def unmapped():
    """Отдаёт текущий (накопленный с момента запуска relay) список
    нераспознанных предметов в JSON — то же самое, что пишется в
    unmapped_items.log, но без необходимости лезть в файл руками."""
    return jsonify({"count": len(_unmapped_registry),
                     "items": list(_unmapped_registry.values())}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "discord_configured": bool(DISCORD_WEBHOOK_URL),
        "background_found": os.path.isfile(BACKGROUND_PATH),
        "icons_dir_found": os.path.isdir(ICONS_DIR),
        "icons_indexed": len(build_icon_index()) if os.path.isdir(ICONS_DIR) else 0,
    }), 200


if __name__ == "__main__":
    if not DISCORD_WEBHOOK_URL:
        log.warning(
            "DISCORD_WEBHOOK_URL не задан! Установите переменную окружения перед запуском:\n"
            "  Windows (PowerShell): $env:DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/...'\n"
            "  Windows (cmd): set DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...\n"
            "  Linux/Mac: export DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/..."
        )
    build_icon_index()  # прогреваем индекс иконок и логируем, если папка не найдена
    log.info("Relay запущен на http://127.0.0.1:%s/relay", RELAY_PORT)
    app.run(host="127.0.0.1", port=RELAY_PORT)
