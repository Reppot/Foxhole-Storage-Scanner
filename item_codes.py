# -*- coding: utf-8 -*-
"""
Восстановленный и дополненный словарь локализации.
Связывает официальные коды fs.exe с русскими названиями.

Очищено от дублирующихся ключей (было 118 записей на 106 уникальных
кодов - 12 ключей повторялись, из них 5 с РАЗНЫМИ значениями, из-за
чего первое значение молча терялось при загрузке словаря в Python).
Ниже оставлено по одной записи на код; там, где значения отличались,
в комментарии сохранено отброшенное значение - на случай, если оно
было нужнее.
"""

ITEM_CODES = {
    # === Ваши новые переводы ===
    'ATRPGAmmo': 'АРПГ Снаряды',
    'GasMaskFilter': 'Фильтр для противогаза',
    'MediumBoatW': 'Средняя лодка варденов',
    'EmplacedHeavyArtilleryW': 'Стационарная тяжелая артиллерия',

    # === Оружие и патроны ===
    'GrenadeW': 'Осколочная граната A3 Harpa',
    'PistolAmmo': '8-мм',
    'Revolver': 'Ferro 879 / Револьвер',
    'RifleHeavyW': 'Хангман 757',
    'RevolverAmmo': '.44 Магнум',
    'RifleLightW': 'Винтовка Blakerow 871',
    'RifleLongW': 'Clancy Cinder M3',
    'RifleW': 'Винтовка No.2 Loughcaster',
    'RifleAmmo': '7.62-мм',
    'ShotgunW': 'Дробовик No.4 The Pillory',
    'ShotgunAmmo': 'Дробь',
    'SMGHeavyW': 'Пистолет-пулемет No.1 "The Liar"',
    'SMGW': 'Пистолет-пулемет Fiddler Model 868',
    'SMGAmmo': '9-мм',
    'ATRifleW': 'Противотанковое ружье Neville',
    'ATRifleAmmo': '14.5mm',
    'GreenAsh': 'Газовая граната',
    'MGAmmo': '12.7-мм',
    'MortarAmmoSH': 'Осколочный минометный снаряд',
    'MortarAmmo': 'Минометный Снаряд',
    'HEGrenade': 'Mammon 91-b / Маммонка',
    'AircraftAmmo': '20мм',
    'DemolitionRocketAmmo': 'Разрушающая ракета',
    'HeavyArtilleryAmmo': '150-мм',
    'LightAAAmmo': 'Зенитный снаряд "Absol"',
    'LightArtilleryAmmo': '120-мм',
    'MiniTankAmmo': 'Снаряды малого танка',  # было также: '912 Shrike Rounds'
    'ATGrenadeW': 'Граната BF5 White Ash Flask',
    'LightTankAmmo': '40-мм',
    'SatchelChargeW': 'Хавок Заряд',
    'HeavyExplosive': 'Тяжёлая взрывчатка',
    'Explosive': 'Порох',

    # === Материалы и Снаряжение ===
    'SurfaceWaterMine': 'E681-B Hullbreaker Mine',
    'WaterWallMaterials': 'Naval Buoy',
    'BarbedWireMaterials': 'Колючая проволока',
    'Bayonet': 'Штык-нож',
    'Binoculars': 'Бинокль',
    'FlameBackpackW': "Топливо для Willow's Bane",
    'MetalBeamMaterials': 'Металлическая балка',
    'RadioBackpack': 'Радиорюкзак',
    'SandbagMaterials': 'Мешок с песком',
    'Tripod': 'Тренога',
    'WorkWrench': 'Гаечный ключ',
    'Water': 'Вода',
    'WaterBucket': 'Ведро для воды',
    'GrenadeAdapter': 'Подствольный гранатомёт',
    'Radio': 'Рация',
    'Bandages': 'Бинты',
    'FirstAidKit': 'Набор Первой Помощи',
    'TraumaKit': 'Реанимационный набор',
    'BloodPlasma': 'Плазма',
    'SoldierSupplies': 'Солдатское снаряжение (рубашки)',
    'Diesel': 'Дизель',
    'Cloth': 'Базовые материалы (биматы)',
    'GasMask': 'Противогаз',
    'Shovel': 'Лопата',
    'SledgeHammer': 'Кувалда',
    'ListeningKit': 'Набор для прослушивания',
    'ExplosiveTripod': 'Станковый Fissura gd.I',
    'SatchelChargeT': 'Заряд Аллигатор',  # было также: 'Alligator Charge'
    'FacilityMaterials4': 'Сборочные материалы IV',
    'FacilityMaterials1': 'Сборочные материалы I',

    # === Униформы ===
    'AmmoUniformW': 'Шинель специалиста',
    'ArmourUniformW': 'Стальная кираса',
    'EngineerUniformW': 'форма инженера',
    'MedicUniformW': 'Медицинская форма',
    'NavalUniformW': 'форма моряка',
    'OfficerUniformW': 'Офицерская регалия',
    'ScoutUniformW': 'Камуфляж разведчика',
    'SnowUniformW': 'Утеплённая шинель',
    'TankUniformW': 'Комбинезон танкиста',

    # === Техника и конструкции ===
    'BusW': 'Автобус',
    'Construction': 'CV / Строительное оборудование',
    'FlatbedTruck': 'Бортовой грузовик BMS - Packmule',
    'Gunboat2W': 'БТР-Амфибия (Mulloy)',
    'LightBoatInfantryW': 'Лёгкая пехотная лодка',
    'TrailerLiquid': 'Жидкостный прицеп',  # было также: 'Жидкостный контейнер (Трейлер)'
    'TrailerResource': 'Ресурсный прицеп',  # было также: 'Контейнер для ресурсов (Трейлер)'
    'TruckLiquidW': 'Танкер RR-3 "Stolon" (Бензовоз)',
    'TruckResourceW': 'Самосвал Dunne Loadlugger 3c',
    'TruckW': 'Dunne Transport / Грузовик',
    'AmbulanceW': 'Скорая помощь R-12 - "Salus"',
    'ArmoredCar2TwinW': "O'Brien V.101 Freeman / Twin AC",
    'ArmoredCar2LargeW': 'Бронированная машина',
    'ArmoredCarMobilityW': 'Мобильная бронемашина',
    'ScoutVehicleW': "O'Brien V.110 / Скаут",
    'LargeFieldMultiW': 'Полевая многозарядная установка',  # было также: 'Полевая установка'
    'Crane': 'Мобильный автокран БМС 2 класса',
    'FreighterLight': 'Das Krokodil by VAC',
    'Freighter': 'BMS - Ironship',
    'EmplacedATW': 'Стационарная противотанковая установка',
    'MaterialPlatform': 'Поддон для материалов',
    'ResourceContainer': 'Контейнер для ресурсов',
    'ShippingContainer': 'Грузовой контейнер',
    'LiquidContainer': 'Жидкостный контейнер',
    'EmplacedInfantryW': 'Стационарная пехотная установка',
    'EmplacedLightArtilleryW': 'Стационарная лёгкая артиллерийская установка',

    'FieldCannonW': 'Полевое орудие',
    'HELaunchedGrenade': 'Осколочный снаряд РПГ',
    'LightTankArtilleryW': 'Легкий арт-танк',
    'MGTW': 'Станковый пулемет варденов',
    'PilotMask': 'Маска пилота',

    # === Добавлено по данным Foxhole Wiki (foxhole.wiki.gg), уточнить на скрине ===
    # -- высокая уверенность: прямое совпадение с официальным списком боеприпасов/техники --
    'FlameAmmo': 'Огненные патроны',                    # wiki: "Flame Ammo" (магазинный тип, не топливо ранцевого огнемёта)
    'MortarAmmoFlame': 'Зажигательный миномётный снаряд',  # wiki: "Incendiary Mortar Shell"
    'ATAmmo': '68-мм',                                   # калибр Field AT Gun / Collins Cannon
    'AAAmmo': 'Зенитный снаряд 950-70b',                 # тяжёлый AA-снаряд (Shell), отдельно от LightAAAmmo/Absol
    'FieldATW': 'Полевая противотанковая пушка',         # wiki: "Field AT Gun"
    'FieldMGW': 'Полевой пулемёт',                       # wiki: "Field Machine Gun"

    # -- средняя уверенность: класс техники подтверждён, конкретная модель не установлена --
    'HalfTrackW': 'Полугусеничный бронеавтомобиль',
    'MotorcycleW': 'Мотоцикл',
    'MediumTank2W': 'Средний танк (тир 2)',
    'ArmoredCarFlameW': 'Бронеавтомобиль с огнемётом',
    'MortarTankAmmo': 'Снаряд миномётного танка',
    'MortarTankAmmoBR': 'Снаряд миномётного танка (бронебойный)',

    # -- низкая уверенность: предположение по паттерну кода, нужна проверка --
    'ATRPGW': 'Противотанковый РПГ (станковый)',
    'RPGTW': 'РПГ (танковый вариант)',
    'ConstructionUtility': 'Строительная техника',
}

UNMATCHED_CODES = {}
