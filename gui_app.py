import os
import sys
import pandas as pd
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QScrollArea, QFrame, QFileDialog, 
                             QMessageBox, QStackedWidget, QSizePolicy, QDialog, QTextEdit)
from PySide6.QtGui import QFont, QPixmap, QIcon

# ⚔️ ОФИЦИАЛЬНЫЙ РЕЕСТР ПРЕДМЕТОВ FOXHOLE CLAN SINDARIS
try:
    import item_codes
    ITEM_NAME_TO_CODE = {v: k for k, v in item_codes.ITEM_CODES.items()}
    ITEM_OPTIONS = sorted(list(ITEM_NAME_TO_CODE.keys()))
except:
    ITEM_OPTIONS = [
        ".44 Магнум", "12.7-мм", "120-мм", "14.5mm", "150-мм", "20мм", "250mm “Fury” Shell",
        "250mm “Purity” Shell", "300-мм", "30мм", "40-мм", "68мм", "7.52-мм", "7.62-мм",
        "7.92-мм", "8-мм", "912 Shrike Rounds", "94.5мм", "950-70b Зенитный снаряд", "9-мм",
        "A3 Harpa Осколочная граната", "Aalto Автоматическая винтовка 24", "Abisme AT-99 Mine",
        "Alligator Charge", "Argenti r.II Винтовка", "B2 Varsi Anti-Tank Grenade", "Bane 45",
        "Blakerow 871", "Bomastone Граната", "Bonesaw MK.3", "Booker Greyhound Model 910",
        "Buckhorn CCQ-18", "Catara mo.II", "Clancy Cinder M3", "Clancy-Raca M4", "Cometa T2-9",
        "Crow’s Foot Mine", "Cutler Foebreaker", "Cutler Launcher 4", "Daucus isg.III",
        "Ferro 879", "Fuscina pi.I", "GA6 “Cestus”", "Ignifist 30", "KRF1-750 Dragonfly",
        "KRR2-790 Omen", "KRR3-792 Auger", "Lamentum mm.IV", "Malone MK.2", "Malone Ratcatcher MK.1",
        "Mammon 91-b", "No.2 Loughcaster", "No.2B Hawthorne", "No.4 The Pillory Scattergun",
        "Noble Firebrand Mk. XVII", "Noble Widow MK. XIV", "O’Brien V.101 Freeman", "O’Brien V.110",
        "O’Brien V.113 Gravekeeper", "O’Brien V.112", "O’Brien v.200 Squire", "O’Brien V.130 Wild Jack",
        "Swallowtail emergency services", "Volta r.I Repeater", "Базовые материалы", "Бинты", "Бинокль",
        "Бронебойный навесной/РПГ", "Бронебойный/РПГ", "Ведро для воды", "Ветроуказатель",
        "Вода", "Гаечный ключ", "Газовая граната", "Детонатор Хавок Заряда", "Дизель",
        "Дробь", "Дымовая граната PT-815", "Зажигал. минометный снаряд", "Зенитный снаряд “Absol”",
        "Колючая проволока", "Кувалда", "Лопата", "Металлическая балка", "Мешок с песком",
        "Миномёт Cremari", "Минометный Снаряд", "Молоток", "Набор для прослушивания",
        "Набор Первой Помощи", "Нестабильные материалы", "Огнемётное топливо", "Осколочная граната A3 Harpa",
        "Осколочный минометный снаряд", "Осветительный Минометный Снаряд", "Плазма", "Повреждённый Колониальный авиадвигатель",
        "Подствольный гранатомёт", "Порох", "Припасы Обслуживания", "Противогаз", "Радиорюкзак",
        "Рация", "Реанимационный набор", "Редкий металл", "Реликтовые материалы", "РПГ",
        "РПГ \"Carnyx\"", "Рюкзак Десантника", "Сапёрное снаряжение", "Сирена воздушной тревоги",
        "Сборочные материалы I", "Сборочные материалы II", "Солдатские припасы (Имки)", "Сталь",
        "Строительные материалы", "Торпеда \"Quillback\"", "Тренога", "Труба", "Тяжелое топливо",
        "Тяжёлый порох", "Фильтр для противогаза", "Флаг Колонистов", "Флаг Варденов", "Хавок Заряд",
        "Шинель специалиста", "Штурмовая винтовка Aalto 24", "Штурмовая винковк Booker Model 838"
    ]
    ITEM_NAME_TO_CODE = {x: "UnknownCode" for x in ITEM_OPTIONS}

# 🗺️ НАЧАЛЬНАЯ МАТРИЦА РЕГИОНОВ И ИСТОРИИ ИЗМЕНЕНИЙ СКЛАДОВ
STOCKPILE_TIMERS_DATABASE = [
    {"ID": 0, "Region": "Clanshead Valley", "Location": "Порт Clanshead", "TimeLeft": 56257, "History": ["[СИСТЕМА]: Инициализация терминала секторов."]},
    {"ID": 1, "Region": "The Linn of Lights", "Location": "Склад снабжения Запад", "TimeLeft": 3420, "History": ["[СИСТЕМА]: Обнаружена критическая просадка по времени."]},
    {"ID": 2, "Region": "Heartlands HQ", "Location": "Центральный Лог-Хаб", "TimeLeft": 86400, "History": ["[СИСТЕМА]: Склад зарегистрирован интендантской службой."]},
    {"ID": 3, "Region": "Marban Hollow", "Location": "Передовой бункер", "TimeLeft": 12450, "History": ["[СИСТЕМА]: Запущена резервная линия мониторинга."]},
    {"ID": 4, "Region": "Drowned Vale", "Location": "Морской Док", "TimeLeft": 1800, "History": ["[СИСТЕМА]: Зафиксирован дефицит поставок."]}
]

# 📝 ТАКТИЧЕСКИЙ СПИСОК КАСТОМНЫХ ФРАЗ ШТАБА
TACTICAL_CUSTOM_PHRASES = [
    "Работай сука",
    "Сделай САНДАЛИС снова великим!",
    "💀ЦЫГАНИС на связи. Спутниковый мониторинг шейкелей колонистов...",
    "Розыгрыш карвалола"
]

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'): 
        return os.path.join(sys._MEIPASS, relative_path)
    # Исправленный запуск через Python 3.14 (берем строго нулевой индекс sys.argv)
    return os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), relative_path)
class LogisticsStudioApp(QWidget):
    def __init__(self):
        super().__init__()
        
        # 📂 БАЗОВЫЕ КОНФИГУРАЦИИ СИСТЕМЫ И ПУТЕЙ
        self.scr_dir = "scr"
        self.is_dark_theme = True
        
        # 👑 1. ПЕРЕМЕННЫЕ ИНИЦИАЛИЗАЦИИ ШРИФТОВ
        self.font_interface = QFont("Arial", 10, QFont.Weight.Bold)


        self.font_ticker = QFont("Consolas", 10, QFont.Weight.Bold)
        
        # 🔥 2. ГРАФИЧЕСКИЙ ДВИЖОК СВЕРХПЛАВНОГО КОНВЕЙЕРА (60 FPS)
        self.timer_labels = {}             # Ссылки на текстовые поля времени
        self.ticker_pixmap_offset = 0.0    # Точная субпиксельная координата X
        self.ticker_image_width = 0        # Физическая длина сгенерированной ленты
        
        # ⚙️ 3. КИНЕТИЧЕСКИЙ ДВИЖОК И ТАКТИЧЕСКИЕ ДАННЫЕ СНАБЖЕНИЯ
        self.ticker_offset = 0  
        self.raw_ticker_text = "ЗАГРУЗКА ВОЕННЫХ СПУТНИКОВ СЕКТОРА..."
        self.plain_ticker_text = ""
        self.current_order = {}
        self.storage_data = [] 
        self.timers_list = STOCKPILE_TIMERS_DATABASE
        
        # Переменные управления случайными радиоперехватами штаба
        self.active_custom_phrase = ""      # Текущая отображаемая фраза
        self.phrase_hold_seconds = 0       # Сколько секунд ей осталось висеть
        
        # 🖥️ 4. КОНФИГУРАЦИЯ ГЛАВНОГО ОКНА SINDARIS EDITION
        self.setWindowTitle("⚡ SINDARIS LOGISTICS OVERWATCH CONTROL TERMINAL")
        self.setGeometry(100, 100, 1350, 900)
        self.setMinimumSize(1150, 850)
        
                # Сохраняем текстовые QSS-стили обеих тем для мгновенного переключения на лету
        self.THEME_LIGHT_KHAKI = """
            QWidget { color: #ffffff; font-family: 'Segoe UI', Arial, sans-serif; }
            QLabel { color: #ffffff; background: transparent; border: none; }
            QFrame { background-color: transparent; border: 1px solid #222922; border-radius: 0px; }
            QLineEdit { background-color: rgba(0, 0, 0, 0.4); color: #ffffff; border: 1px solid #9c8f80; padding: 7px; border-radius: 4px; font-weight: bold; }
            QLineEdit:hover { border: 1px solid #7c6f60; }
            QLineEdit:focus { border: 2px solid #a3e635; }
            QPushButton { 
                background-color: rgba(244, 241, 235, 0.2); 
                color: #ffffff; 
                border: 1px solid #9c8f80; 
                padding: 8px 12px; 
                border-radius: 4px; 
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: rgba(74, 92, 49, 0.5); 
                color: #ffffff; 
                border: 1px solid #a3e635; 
            }

            QScrollArea { border: 2px solid #9c8f80; background-color: transparent; border-radius: 4px; }
            QTextEdit { background-color: rgba(0, 0, 0, 0.4); color: #ffffff; border: 1px solid #9c8f80; font-family: 'Consolas', monospace; border-radius: 4px; font-weight: bold; }
            #upper_ticker_frame { background-color: #dcd6cd; border-bottom: 2px solid #9c8f80; }
            #upper_ticker_label { color: #2b2e2b; font-weight: bold; }
        """

        self.THEME_DARK_CYBERPUNK = """
            QWidget { color: #ffffff; font-family: 'Segoe UI', Arial, sans-serif; }
            QLabel { color: #ffffff; background: transparent; border: none; }
            QFrame { background-color: transparent; border: 1px solid #222922; border-radius: 0px; }
            QLineEdit { background-color: rgba(0, 0, 0, 0.4); color: #ffffff; border: 1px solid #222922; padding: 7px; border-radius: 4px; }
            QLineEdit:hover { border: 1px solid #4d614d; }
            QLineEdit:focus { border: 1px solid #a3e635; }
            QPushButton { 
                background-color: rgba(24, 29, 24, 0.4); 
                color: #ffffff; 
                border: 1px solid #283328; 
                padding: 8px 12px; 
                border-radius: 4px; 
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: rgba(163, 230, 53, 0.3); 
                color: #ffffff; 
                border: 1px solid #a3e635; 
            }

            QScrollArea { border: 1px solid #1c221c; background-color: transparent; border-radius: 4px; }
            QTextEdit { background-color: rgba(0, 0, 0, 0.4); color: #ffffff; border: 1px solid #222922; font-family: 'Consolas', monospace; border-radius: 4px; }
            #upper_ticker_frame { background-color: #0c0e0c; border-bottom: 1px solid #222922; }
            #upper_ticker_label { color: #ffffff; font-weight: bold; }
        """



        
        # 🏛️ ПОРЯДОК РАЗВЕРТЫВАНИЯ СТРУКТУРЫ ИНТЕРФЕЙСА
        self.init_ui()
        self.setup_workspace()
        
        # По умолчанию активируем тему
        self.switch_terminal_theme()
        self.toggle_sidebar_menu()



        
        # Переключаем контейнер на первую страницу при старте
        self.pages_container.setCurrentIndex(0)
        
        # ⏱️ ТАЙМЕР №1: Расчет алертов и времени (1 Гц)
        self.global_timer = QTimer(self)
        self.global_timer.timeout.connect(self.update_tactical_timers)
        self.global_timer.start(1000)

        # 🏃‍♂️ ТАЙМЕР №2: Отрисовка плавной графики (60 Гц)
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate_ticker)
        self.animation_timer.start(16)

        # ⏱️ ТАЙМЕР №3: Бесшумный авто-мониторинг папки сканера (1 Гц)
        self.auto_sync_timer = QTimer(self)
        self.auto_sync_timer.timeout.connect(self.auto_load_scanner_file)
        self.auto_sync_timer.start(1000)

        # Стартовый сбор данных и запуск алертов
        self.update_tactical_timers()



    def init_ui(self):
        # Установка сквозного фона программы из папки scr
        self.main_bg = QLabel(self)
        bg_image_path = get_resource_path(os.path.join("scr", "Gg4RBJvXQAA5Zh2.jfif"))
        if os.path.exists(bg_image_path):
            self.main_bg.setPixmap(QPixmap(bg_image_path))
        self.main_bg.setScaledContents(True)
        self.main_bg.lower()

        # Создание тонировочной маски для регулировки яркости арта
        self.dark_overlay = QFrame(self)
        self.dark_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  # Пропускает клики сквозь себя
        self.dark_overlay.lower()
        self.main_bg.lower()  # Картинка на самом нижнем слое, маска чуть выше неё


        # ГЛАВНЫЙ ВЕРТИКАЛЬНЫЙ МАКЕТ ВСЕГО ОКНА
        window_wrapper = QVBoxLayout(self)
        window_wrapper.setContentsMargins(10, 10, 10, 10)
        window_wrapper.setSpacing(10)

        # ================================================================
        # 👑 ГЛОБАЛЬНАЯ СКВОЗНАЯ ШАПКА HUD (Видна во всех разделах)
        # ================================================================
        self.logo_frame = QFrame()
        self.logo_frame.setFixedHeight(65)
        logo_layout = QHBoxLayout(self.logo_frame)
        logo_layout.setContentsMargins(15, 5, 15, 5)
        logo_layout.setSpacing(15)

        # Контейнер для бегущей строки секторов
        self.ticker_frame = QFrame()
        self.ticker_frame.setFixedHeight(45)

        # Текстовый виджет бегущей строки внутри фрейма
        self.lbl_ticker_text = QLabel(self.raw_ticker_text, self.ticker_frame)
        self.lbl_ticker_text.setFont(self.font_ticker)
        self.lbl_ticker_text.setMinimumWidth(12000)
        self.lbl_ticker_text.move(200, 14)

        # Присваиваем ID виджетам для управления через глобальный QSS
        self.logo_frame.setObjectName("upper_logo_frame")
        self.ticker_frame.setObjectName("upper_ticker_frame")
        self.lbl_ticker_text.setObjectName("upper_ticker_label")

        # Тактическая динамическая стилизация шапки под текущую тему
        if self.is_dark_theme:
            self.logo_frame.setStyleSheet("background-color: #141714; border: 1px solid #222922; border-radius: 6px;")
            self.ticker_frame.setStyleSheet("background-color: #060806; border: 1px solid #1c221c; border-radius: 4px;")
            self.lbl_ticker_text.setStyleSheet("color: #e5e7eb; background: transparent; border: none;")
        else:
            self.logo_frame.setStyleSheet("background-color: #dcd6cd; border: 1px solid #9c8f80; border-radius: 6px;")
            self.ticker_frame.setStyleSheet("background-color: #ebe4db; border: 1px solid #9c8f80; border-radius: 4px;")
            self.lbl_ticker_text.setStyleSheet("color: #2b2e2b; background: transparent; border: none;")

        
        logo_layout.addWidget(self.ticker_frame, 1)
        window_wrapper.addWidget(self.logo_frame)

        # НИЖНЯЯ РАБОЧАЯ ОБЛАСТЬ (Разделяется на Сайдбар слева и Контент справа)
        app_layout = QHBoxLayout()
        app_layout.setContentsMargins(0, 0, 0, 0)
        app_layout.setSpacing(10) # Небольшой тактический зазор между баром и таблицей

        # Сворачиваем сайдбар в обычный виджет макета
        self.sidebar_frame = QFrame() 
        self.sidebar_frame.setFixedWidth(85) # Фиксированная монолитная ширина в свернутом виде
        self.pages_container = QStackedWidget()

        # 🎯 ВОЗВРАЩАЕМ СЕТКУ: Обнуляем левый отступ (0 вместо 95), чтобы таблицы встали вплотную к сайдбару!
        self.pages_container.setContentsMargins(0, 0, 0, 0)


        # Добавляем сначала сайдбар, а затем контейнер страниц в макет

        
        # ================================================================
        # 🧭 ЛЕВАЯ СТОРОНА: ВЫЕЗДНОЙ SIDEBAR УПРАВЛЕНИЯ (Sindaris HQ)
        # ================================================================

        self.sidebar_layout = QVBoxLayout(self.sidebar_frame)
        self.sidebar_layout.setContentsMargins(10, 15, 10, 15)
        self.sidebar_layout.setSpacing(15)
        self.sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 🔥 Фирменный логотип клана SINDARIS (Верхушка Sidebar)
        self.lbl_sidebar_logo = QLabel()
        logo_path = get_resource_path(os.path.join("scr", "clan-logo.png"))
        
        # Проверяем наличие боевых артов в папке scr и сохраняем статус
        art_check_path = get_resource_path(os.path.join("scr", "image_At1I7F.png"))
        self.has_art_bg = os.path.exists(art_check_path)
        
        if os.path.exists(logo_path):

            try:
                pixmap = QPixmap(logo_path)
                self.sidebar_logo_pixmap = pixmap.scaledToHeight(45, Qt.TransformationMode.SmoothTransformation)
                self.lbl_sidebar_logo.setPixmap(self.sidebar_logo_pixmap)
            except: pass
        self.lbl_sidebar_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sidebar_layout.addWidget(self.lbl_sidebar_logo)
        
        # ⚡ ГЛАВНАЯ КНОПКА-ГАЛОЧКА (Переключатель раскрытия боковой панели)
        self.btn_toggle_sidebar = QPushButton("❯") 
        self.btn_toggle_sidebar.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.btn_toggle_sidebar.setCheckable(True)
        self.btn_toggle_sidebar.clicked.connect(self.toggle_sidebar_menu)
        self.sidebar_layout.addWidget(self.btn_toggle_sidebar)
        
        # Импортируем модуль QMovie для поддержки GIF-анимаций в меню
        from PySide6.QtGui import QMovie
        from PySide6.QtCore import QSize
        
        # 🟢 1. РАЗДЕЛ: ЗАКАЗЫ (Иконка pre-order.gif)
        self.btn_nav_ops = QPushButton("  Заказы")
        self.btn_nav_ops.setFont(self.font_interface)
        self.btn_nav_ops.clicked.connect(lambda: self.pages_container.setCurrentIndex(0))
        self.sidebar_layout.addWidget(self.btn_nav_ops)
        
        # ⏳ 2. РАЗДЕЛ: ТАЙМЕРЫ (Иконка hourglass.gif)
        self.btn_nav_timers = QPushButton("  Таймеры")
        self.btn_nav_timers.setFont(self.font_interface)
        self.btn_nav_timers.clicked.connect(lambda: self.pages_container.setCurrentIndex(1))
        self.sidebar_layout.addWidget(self.btn_nav_timers)
        
        # 🧠 3. РАЗДЕЛ: ОБУЧЕНИЕ (Иконка brain.gif)
        self.btn_nav_training = QPushButton("  Обучение")
        self.btn_nav_training.setFont(self.font_interface)
        self.btn_nav_training.clicked.connect(lambda: self.pages_container.setCurrentIndex(2))
        self.sidebar_layout.addWidget(self.btn_nav_training)

        self.sidebar_layout.addStretch(1)
        
        # 🌓 КНОПКА СМЕНЫ ТЕМЫ: ТЕМА (Иконка night.gif)
        self.btn_toggle_theme = QPushButton("  Тема")
        self.btn_toggle_theme.setFont(self.font_interface)
        self.btn_toggle_theme.clicked.connect(self.switch_terminal_theme)
        self.sidebar_layout.addWidget(self.btn_toggle_theme)

        
        # ================================================================
        # 🎭 ПРАВАЯ СТОРОНА: СВЕРХБЫСТРЫЙ КОНТЕЙНЕР СТРАНИЦ ТЕРМИНАЛА
        # ================================================================
        self.pages_container = QStackedWidget()
        
        self.page_operations = QWidget()
        self.page_timers_matrix = QWidget()
        
        # 📚 ИНИЦИАЛИЗАЦИЯ ТРЕТЬЕГО РАЗДЕЛА "ОБУЧЕНИЕ"
        self.page_training = QWidget()
        training_layout = QVBoxLayout(self.page_training)
        training_layout.setContentsMargins(5, 5, 5, 5)
        training_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Защитная матовая рамка в центре экрана (стиль будет меняться вместе с темами)
        self.training_main_frame = QFrame()
        self.training_main_frame.setObjectName("training_main_frame")
        if self.is_dark_theme:
            self.training_main_frame.setStyleSheet("background-color: rgba(20, 23, 20, 0.75); border: 1px solid #222922; border-radius: 0px;")
        else:
            self.training_main_frame.setStyleSheet("background-color: rgba(60, 65, 60, 0.70); border: 2px solid #9c8f80; border-radius: 0px;")
            
        tf_layout = QVBoxLayout(self.training_main_frame)
        tf_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Размещаем плоское изображение палатки штаба по центру вкладки Обучения
        self.lbl_coming_soon = QLabel()
        tent_path = get_resource_path(os.path.join("scr", "image_cU6Sxy.png")) # Строго реальное имя со скрина
        if os.path.exists(tent_path):
            pix = QPixmap(tent_path)
            self.lbl_coming_soon.setPixmap(pix.scaled(280, 280, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.lbl_coming_soon.setText("📚 МАТЕРИАЛЫ ОБУЧЕНИЯ НАХОДЯТСЯ В РАЗРАБОТКЕ ШТАБА КЛАНА")
            self.lbl_coming_soon.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            self.lbl_coming_soon.setStyleSheet("color: #ffffff; background: transparent; border: none;")

            
        tf_layout.addWidget(self.lbl_coming_soon)
        training_layout.addWidget(self.training_main_frame)

        # ─── БЫСТРАЯ УСТАНОВКА СТАТИЧНЫХ ОРИГИНАЛЬНЫХ КАРТИНОК ДЛЯ КНОПОК МЕНЮ ───
        # Сопоставляем кнопки с вашими оригинальными файлами картинок из папки scr/
        image_bindings = [
            (self.btn_nav_ops, "products.png"),         # Ваша картинка коробки
            (self.btn_nav_timers, "deadline.png"),   # Новые плоские песочные часы
            (self.btn_nav_training, "brain.png"), # Новый плоский розовый мозг
            (self.btn_toggle_theme, "24-hour-clock.png")  # Иконка 24 часа для кнопки смены темы
        ]
        
        for btn, img_name in image_bindings:
            img_path = get_resource_path(os.path.join("scr", img_name))
            if os.path.exists(img_path):
                btn.setIcon(QIcon(img_path))
            # Фиксируем массивный тактический размер иконки на кнопке
            btn.setIconSize(QSize(54, 54))

        # 🎯 СБОРКА ИНТЕРФЕЙСА: Добавляем элементы в макет строго слева направо!
        app_layout.addWidget(self.sidebar_frame)       # 1. Сайдбар монолитно встает слева
        app_layout.addWidget(self.pages_container, 1)   # 2. Таблицы контента прижимаются к нему справа

        
        # Добавляем все три страницы в главный стек терминала управления
        self.pages_container.addWidget(self.page_operations)
        self.pages_container.addWidget(self.page_timers_matrix)
        self.pages_container.addWidget(self.page_training)

        
        window_wrapper.addLayout(app_layout)

    def toggle_sidebar_menu(self):
        """Управляет шириной сайдбара внутри макета и фиксирует отображение QIcon."""
        from PySide6.QtGui import QIcon
        
        # Карта сопоставления кнопок и оригинальных картинок из вашей папки scr/
        # Карта сопоставления кнопок и РЕАЛЬНЫХ имен файлов из вашей папки scr/
        sidebar_icons = {
            self.btn_nav_ops: "image_6fGsbO.png",       # Кнопка "Заказы" — Карточка с надписью PRE ORDER
            self.btn_nav_timers: "image_amQ8BV.png",    # Кнопка "Таймеры" — Белые плоские песочные часы
            self.btn_nav_training: "image_q11-he.png",  # Кнопка "Обучение" — Плоский розовый мозг
            self.btn_toggle_theme: "image_qH61K6.png"   # Кнопка "Тема" — Темная иконка военного бункера
        }


        base_btn_style = """
            QPushButton { 
                background-color: transparent; 
                border: 1px solid rgba(156, 143, 128, 0.2); 
                border-radius: 6px; 
                color: #ffffff;
                text-align: left;
                padding-left: 15px;
                height: 54px;
            }
            QPushButton:hover {
                background-color: rgba(163, 230, 53, 0.15);
                border: 1px solid #a3e635;
            }
        """
        
        if self.btn_toggle_sidebar.isChecked():
            # РАСКРЫТОЕ СОСТОЯНИЕ (Большой бар)
            self.sidebar_frame.setFixedWidth(280)
            self.btn_toggle_sidebar.setText("❮")
            self.btn_nav_ops.setText("  Заказы")
            self.btn_nav_timers.setText("  Таймеры")
            self.btn_nav_training.setText("  Обучение")
            self.btn_toggle_theme.setText("  Тема")
            
            for btn, img_name in sidebar_icons.items():
                btn.setStyleSheet(base_btn_style)
                img_path = get_resource_path(os.path.join("scr", img_name))
                if os.path.exists(img_path):
                    btn.setIcon(QIcon(img_path))
                btn.setIconSize(QSize(36, 36))
        else:
            # СВЕРНУТОЕ СОСТОЯНИЕ (Компактный бар монолитно 85px)
            self.sidebar_frame.setFixedWidth(85)
            self.btn_toggle_sidebar.setText("❯")
            self.btn_nav_ops.setText("")
            self.btn_nav_timers.setText("")
            self.btn_nav_training.setText("")
            self.btn_toggle_theme.setText("")
            
            compact_style = """
                QPushButton { 
                    background-color: transparent; 
                    border: 1px solid rgba(156, 143, 128, 0.15);
                    border-radius: 6px;
                    text-align: center; 
                    padding-left: 0px; 
                    padding-right: 0px; 
                    margin: 0px;
                    height: 54px;
                }
                QPushButton:hover {
                    background-color: rgba(163, 230, 53, 0.15);
                    border: 1px solid #a3e635;
                }
            """
            for btn, img_name in sidebar_icons.items():
                btn.setStyleSheet(compact_style)
                img_path = get_resource_path(os.path.join("scr", img_name))
                if os.path.exists(img_path):
                    btn.setIcon(QIcon(img_path))
                btn.setIconSize(QSize(36, 36))




    def switch_terminal_theme(self):
        """Смена темы с мягкой матовой прозрачностью панелей для идеальной читаемости текста."""
        self.is_dark_theme = not self.is_dark_theme

        # Применяем базовую таблицу стилей
        self.setStyleSheet(self.THEME_DARK_CYBERPUNK if self.is_dark_theme else self.THEME_LIGHT_KHAKI)

        # ─── ИСКЛЮЧЕНИЯ: Настройка плотных панелей (сайдбар и шапка) ───
        if self.is_dark_theme:
            self.sidebar_frame.setStyleSheet("background-color: #141714; border: 1px solid #222922; border-radius: 6px;")
            self.logo_frame.setStyleSheet("background-color: #141714; border: 1px solid #222922; border-radius: 6px;")
            self.ticker_frame.setStyleSheet("background-color: #060806; border: 1px solid #1c221c; border-radius: 4px;")
            
            # ТЁМНАЯ ТЕМА: Матовая темная дымка (75% плотности цвета) для панелей
            panel_bg = "background-color: rgba(20, 23, 20, 0.75); border: 1px solid #222922; border-radius: 0px;"
            
            if hasattr(self, 'dark_overlay'): self.dark_overlay.setStyleSheet("background-color: transparent; border: none;")
            if hasattr(self, 'lbl_left_title'): self.lbl_left_title.setStyleSheet("color: #ffffff; background: transparent; border: none;")
            if hasattr(self, 'lbl_right_title'): self.lbl_right_title.setStyleSheet("color: #ffffff; background: transparent; border: none;")
            if hasattr(self, 'item_btn_selector'): self.item_btn_selector.setStyleSheet("background-color: rgba(0, 0, 0, 0.4); color: #ffffff; border: 1px solid #222922; padding: 8px; border-radius: 4px; font-weight: bold;")
        else:
            self.sidebar_frame.setStyleSheet("background-color: #dcd6cd; border: 1px solid #9c8f80; border-radius: 6px;")
            self.logo_frame.setStyleSheet("background-color: #dcd6cd; border: 1px solid #9c8f80; border-radius: 6px;")
            self.ticker_frame.setStyleSheet("background-color: #ebe4db; border: 1px solid #9c8f80; border-radius: 4px;")
            
            # СВЕТЛАЯ ТЕМА: Делаем панели темными матовыми, чтобы белый текст читался идеально!
            panel_bg = "background-color: rgba(20, 24, 20, 0.82); border: 2px solid #9c8f80; border-radius: 0px;"
            
            if hasattr(self, 'dark_overlay'): 
                self.dark_overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.35); border: none;")
                
            if hasattr(self, 'lbl_left_title'): self.lbl_left_title.setStyleSheet("color: #ffffff; background: transparent; border: none;")
            if hasattr(self, 'lbl_right_title'): self.lbl_right_title.setStyleSheet("color: #ffffff; background: transparent; border: none;")
            
            # Поля ввода и селекторы делаем темными с белым текстом для максимального контраста
            if hasattr(self, 'item_btn_selector'): self.item_btn_selector.setStyleSheet("background-color: rgba(0, 0, 0, 0.6); color: #a3e635; border: 1px solid #9c8f80; padding: 8px; border-radius: 4px; font-weight: bold;")
            if hasattr(self, 'count_input'): self.count_input.setStyleSheet("background-color: rgba(0, 0, 0, 0.6); color: #ffffff; border: 1px solid #9c8f80; padding: 4px; border-radius: 4px; font-weight: bold;")
            if hasattr(self, 'filter_input'): self.filter_input.setStyleSheet("background-color: rgba(0, 0, 0, 0.6); color: #ffffff; border: 1px solid #9c8f80; padding: 4px; border-radius: 4px; font-weight: bold;")

        # ─── ПРИМЕНЕНИЕ ЗАЛИВКИ К ЛЕВОЙ И ПРАВОЙ ПАНЕЛЯМ ───
        if hasattr(self, 'left_frame'):
            self.left_frame.setStyleSheet(panel_bg)
            
            if hasattr(self, 'left_bg'): self.left_bg.clear()
            if hasattr(self, 'right_bg'): self.right_bg.clear()
            if hasattr(self, 'timers_page_bg'): self.timers_page_bg.clear()
            
            # УБИРАЕМ АРТЕФАКТЫ: Полностью отключаем рамки и скругления у внутренних скролл-объектов
            self.scroll_storage.setStyleSheet("QScrollArea { border: none; background: transparent; border-radius: 0px; padding: 0px; }")
            self.scroll_dropdown.setStyleSheet("QScrollArea { border: 1px solid rgba(156,143,128,0.4); background: transparent; border-radius: 0px; }")
            self.scroll_order.setStyleSheet("QScrollArea { border: none; background: transparent; border-radius: 0px; padding: 0px; }")
            
            self.storage_widget.setStyleSheet("background: transparent; border: none; border-radius: 0px;")
            self.dropdown_widget.setStyleSheet("background: transparent; border: none; border-radius: 0px;")
            self.order_widget.setStyleSheet("background: transparent; border: none; border-radius: 0px;")



        if hasattr(self, 'right_frame'):
            self.right_frame.setStyleSheet(panel_bg)

        # Синхронное обновление списков элементов
        if hasattr(self, 'left_frame'):
            self.refresh_storage_display()
            self.refresh_order_display()
            self.render_dropdown_buttons(ITEM_OPTIONS)
            self.rebuild_timers_cards()
            
        # Синхронизация рамки страницы обучения с активной глобальной темой
        if hasattr(self, 'training_main_frame'):
            if self.is_dark_theme:
                self.training_main_frame.setStyleSheet("background-color: rgba(20, 23, 20, 0.75); border: 1px solid #222922; border-radius: 0px;")
            else:
                self.training_main_frame.setStyleSheet("background-color: rgba(60, 65, 60, 0.70); border: 2px solid #9c8f80; border-radius: 0px;")
        # Автоматический пересчет и наложение прозрачных стилей на кнопки сайдбара под новую тему
        
        if hasattr(self, 'toggle_sidebar_menu') and hasattr(self, 'btn_toggle_sidebar'):
            # Временно симулируем переключение флага, чтобы обновить QSS без изменения ширины панели
            self.btn_toggle_sidebar.setChecked(not self.btn_toggle_sidebar.isChecked())
            self.toggle_sidebar_menu()
            self.btn_toggle_sidebar.setChecked(not self.btn_toggle_sidebar.isChecked())
            self.toggle_sidebar_menu()



    def setup_workspace(self):
        global QIcon  
        # Далее идет стандартный код: ops_layout = QHBoxLayout...

        # Внутренняя разметка для Раздела №1 (Операции)
        ops_layout = QHBoxLayout(self.page_operations)
        ops_layout.setContentsMargins(5, 5, 5, 5)
        ops_layout.setSpacing(12)

        # ================================================================
        # ЛЕВАЯ СТОРОНА: МОНИТОР СКЛАДА (Песочный матовый армейский стиль)
        # ================================================================
        self.left_frame = QFrame()
        self.left_frame.setStyleSheet("""
            background-color: #c9c0b5; 
            border: 2px solid #9c8f80; 
            border-radius: 6px;
        """)
        left_layout = QVBoxLayout(self.left_frame)
        # Фоновая подложка для монитора складов
        self.left_bg = QLabel(self.left_frame)
        self.left_bg.setScaledContents(True)
        self.left_bg.lower()

        left_layout.setContentsMargins(18, 18, 18, 18)

        self.lbl_left_title = QLabel("📦 МОНИТОР ТЕКУЩИХ ЗАПАСОВ СКЛАДА")
        self.lbl_left_title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.lbl_left_title.setStyleSheet("color: #1e2417; border: none; background: transparent;")
        left_layout.addWidget(self.lbl_left_title)


        l_ctrl = QHBoxLayout()
        
        # Кнопка загрузки JSON (Использует файл image_nmd5MD.png)
        btn_json = QPushButton()
        btn_json.setFixedSize(54, 40)
        json_p = get_resource_path(os.path.join("scr", "json.png"))
        if os.path.exists(json_p):
            btn_json.setIcon(QIcon(json_p))
            btn_json.setIconSize(QSize(28, 28))
            btn_json.setStyleSheet("background-color: rgba(0, 0, 0, 0.4); border: 1px solid #9c8f80; border-radius: 4px;")
            btn_json.setToolTip("ЗАГРУЗИТЬ JSON СКАНЕРА")
            l_ctrl.addWidget(btn_json)

        # Кнопка вставки из буфера (Использует файл image_8jrRWb.png)
        btn_clip = QPushButton()
        btn_clip.setFixedSize(54, 40)
        log_p = get_resource_path(os.path.join("scr", "log-file.png"))

        if os.path.exists(log_p):
            btn_clip.setIcon(QIcon(log_p))
        btn_clip.setIconSize(QSize(28, 28))
        btn_clip.setStyleSheet("background-color: rgba(0, 0, 0, 0.4); border: 1px solid #9c8f80; border-radius: 4px;")
        btn_clip.setToolTip("ВСТАВИТЬ ИЗ БУФЕРА ОБМЕНА")
        btn_clip.clicked.connect(self.load_storage_clipboard)
        l_ctrl.addWidget(btn_clip)
        
        left_layout.addLayout(l_ctrl)



        self.scroll_storage = QScrollArea()
        self.scroll_storage.setWidgetResizable(True)
        self.scroll_storage.setStyleSheet("""
            border: 1px solid #9c8f80; 
            background-color: #f4f1eb;
        """)
        self.storage_widget = QWidget()
        self.storage_widget.setStyleSheet("background-color: #f4f1eb;")
        self.storage_layout = QVBoxLayout(self.storage_widget)
        self.storage_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_storage.setWidget(self.storage_widget)
        left_layout.addWidget(self.scroll_storage)

        self.btn_mode_left = QPushButton("РЕЖИМ: ЭКСПОРТ ДАННЫХ")
        self.btn_mode_left.setCheckable(True)
        self.btn_mode_left.setFont(self.font_interface)
        self.btn_mode_left.clicked.connect(self.toggle_export_import_mode)  # <- ДОБАВИТЬ СТРОКУ
        left_layout.addWidget(self.btn_mode_left)
        l_btn_grid = QHBoxLayout()
        # Карта сопоставления форматов левой стороны и оригинальных имен файлов картинок
        export_formats = [
            ("TXT", "txt", "image_x4lfy4.png"),
            ("XLSX", "xlsx", "image_LLScL9.png"),
            ("PNG", "png", "image_KslIXG.png"),
            ("БУФЕР", "png_buffer", "image_rrLH-_.png")
        ]
        
        for label_text, fmt, img_file in export_formats:
            b = QPushButton(f" {label_text}") # Принудительно передаем текст в конструктор виджета
            b.setFixedSize(90, 42) # Оптимальная ширина под иконку + текст формата
            img_p = get_resource_path(os.path.join("scr", img_file))
            if os.path.exists(img_p):

                b.setIcon(QIcon(img_p))
            b.setIconSize(QSize(20, 24))
            b.setFont(self.font_interface)
            # Инлайново защищаем цвет текста кнопки от стирания глобальной темой
            b.setStyleSheet("background-color: rgba(244, 241, 235, 0.2); color: #ffffff; text-align: center; padding-left: 5px; border: 1px solid #9c8f80; border-radius: 4px;")
            b.clicked.connect(lambda checked=False, f=fmt: self.handle_file_action("склад", f))
            l_btn_grid.addWidget(b)
        left_layout.addLayout(l_btn_grid)

        ops_layout.addWidget(self.left_frame)

        # ================================================================
        # ПРАВАЯ СТОРОНА: КОНСТРУКТОР ЗАКАЗА (Песочный матовый армейский стиль)
        # ================================================================
        self.right_frame = QFrame()
        right_layout = QVBoxLayout(self.right_frame)
        # Фоновая подложка для конструктора заказов
        self.right_bg = QLabel(self.right_frame)
        self.right_bg.setScaledContents(True)
        self.right_bg.lower()

        right_layout.setContentsMargins(18, 18, 18, 18)

        self.lbl_right_title = QLabel("🛠️ КОНСТРУКТОР СНАБЖЕНИЯ БАЗЫ")
        self.lbl_right_title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        right_layout.addWidget(self.lbl_right_title)

        s_layout = QHBoxLayout()
        self.item_btn_selector = QLabel("Выбрать предмет из матрицы ниже...")
        self.item_btn_selector.setFont(self.font_interface)
        s_layout.addWidget(self.item_btn_selector, 3)

        self.count_input = QLineEdit()
        self.count_input.setPlaceholderText("КОЛ-ВО")
        self.count_input.setFont(self.font_interface)
        s_layout.addWidget(self.count_input, 1)

        # Интеграция кнопки переключения единиц измерения (ЯЩ / ШТ)
        self.btn_unit_toggle = QPushButton("ЯЩ")
        self.btn_unit_toggle.setCheckable(True)
        self.btn_unit_toggle.setFixedWidth(50)
        self.btn_unit_toggle.setFont(self.font_interface)
        # Настройка стиля кнопки, чтобы она была хорошо видна на прозрачном фоне
        self.btn_unit_toggle.setStyleSheet("""
            QPushButton { background-color: rgba(0, 0, 0, 0.5); color: #ffffff; border: 1px solid #9c8f80; border-radius: 4px; }
            QPushButton:checked { background-color: #ff9900; color: #000000; font-weight: bold; }
        """)
        self.btn_unit_toggle.clicked.connect(lambda: self.btn_unit_toggle.setText("ШТ" if self.btn_unit_toggle.isChecked() else "ЯЩ"))
        s_layout.addWidget(self.btn_unit_toggle)

        btn_add = QPushButton("ДОБАВИТЬ В ЗАКАЗ")
        btn_add.setFont(self.font_interface)
        btn_add.clicked.connect(self.add_item_to_order)
        s_layout.addWidget(btn_add)
        right_layout.addLayout(s_layout)

        # Фильтр матрицы предметов (Использует файл image_1TEVG0.png)
        filter_layout = QHBoxLayout()
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("🔍 ИНТЕРАКТИВНЫЙ ФИЛЬТР МАТРИЦЫ ПРЕДМЕТОВ...")
        self.filter_input.setFont(self.font_interface)
        self.filter_input.textChanged.connect(self.filter_items)
        filter_layout.addWidget(self.filter_input)
        
        lbl_search_ico = QLabel()
        search_p = get_resource_path(os.path.join("scr", "image_1TEVG0.png"))
        if os.path.exists(search_p):
            lbl_search_ico.setPixmap(QPixmap(search_p).scaled(34, 34, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        filter_layout.addWidget(lbl_search_ico)
        right_layout.addLayout(filter_layout)

        # Конструктор заказа с компактной кнопкой очистки паллета (Использует файл image_MXUXFY.png)
        order_ctrl_layout = QHBoxLayout()
        
        self.scroll_dropdown = QScrollArea()
        # ... (Код конфигурации self.scroll_dropdown оставляем без изменений) ...
        order_ctrl_layout.addWidget(self.scroll_dropdown, 5)

        # Компактная графическая кнопка полной очистки рапорта с привязкой к self
        self.btn_clear = QPushButton()
        self.btn_clear.setFixedSize(54, 120)
        clear_p = get_resource_path(os.path.join("scr", "image_MXUXFY.png"))
        if os.path.exists(clear_p):
            self.btn_clear.setIcon(QIcon(clear_p))
        self.btn_clear.setIconSize(QSize(32, 32))
        self.btn_clear.setToolTip("⚠️ ПОЛНАЯ ОЧИСТКА ТЕКУЩЕГО ЗАКАЗА")
        self.btn_clear.clicked.connect(self.clear_order)
        order_ctrl_layout.addWidget(self.btn_clear, 1) # Добавляем именно self.btn_clear

        
        right_layout.addLayout(order_ctrl_layout)


        self.scroll_dropdown = QScrollArea()
        self.scroll_dropdown.setWidgetResizable(True)
        self.scroll_dropdown.setFixedHeight(120)

        self.dropdown_widget = QWidget()
        self.dropdown_layout = QVBoxLayout(self.dropdown_widget)
        self.dropdown_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_dropdown.setWidget(self.dropdown_widget)
        right_layout.addWidget(self.scroll_dropdown)

        self.scroll_order = QScrollArea()
        self.scroll_order.setWidgetResizable(True)

        self.order_widget = QWidget()
        self.order_layout = QVBoxLayout(self.order_widget)
        self.order_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_order.setWidget(self.order_widget)
        right_layout.addWidget(self.scroll_order)

        self.btn_mode_right = QPushButton("РЕЖИМ: ЭКСПОРТ ДАННЫХ")
        self.btn_mode_right.setFont(self.font_interface)
        self.btn_mode_right.clicked.connect(self.toggle_export_import_mode)
        right_layout.addWidget(self.btn_mode_right)

        r_btn_grid = QHBoxLayout()
        r_export_formats = [
            ("TXT", "txt", "image_x4lfy4.png"),
            ("XLSX", "xlsx", "image_LLScL9.png"),
            ("PNG", "png", "image_KslIXG.png"),
            ("БУФЕР", "png_buffer", "image_rrLH-_.png")
        ]
        
        for label_text, fmt, img_file in r_export_formats:
            b = QPushButton(f" {label_text}") # Принудительный текст формата на кнопку
            b.setFixedSize(90, 42)
            img_p = get_resource_path(os.path.join("scr", img_file))
            if os.path.exists(img_p):
                b.setIcon(QIcon(img_p))
            b.setIconSize(QSize(20, 24))
            b.setFont(self.font_interface)
            # Жестко фиксируем белый цвет текста, защищая от влияния глобальных тем QSS
            b.setStyleSheet("background-color: rgba(244, 241, 235, 0.2); color: #ffffff; text-align: center; padding-left: 5px; border: 1px solid #9c8f80; border-radius: 4px;")
            b.clicked.connect(lambda checked=False, f=fmt: self.handle_file_action("заказ", f))
            r_btn_grid.addWidget(b)
        right_layout.addLayout(r_btn_grid)


        # 🎨 ДИНАМИЧЕСКИЙ СТАРТОВЫЙ СТИЛЬ ДЛЯ ПРАВОЙ ПАНЕЛИ
        if self.is_dark_theme:
            self.right_frame.setStyleSheet("background-color: #141714; border: 1px solid #222922; border-radius: 6px;")
            self.lbl_right_title.setStyleSheet("color: #a3e635; border: none; background: transparent;")
            self.item_btn_selector.setStyleSheet("background-color: #060706; color: #ffffff; border: 1px solid #222922; padding: 8px; border-radius: 4px; font-weight: bold;")
            self.scroll_dropdown.setStyleSheet("border: 1px solid #222922; background-color: #060706;")
            self.dropdown_widget.setStyleSheet("background-color: #060706;")
            self.btn_clear.setStyleSheet("background-color: transparent; border: 1px solid #222922; border-radius: 0px;")
            self.scroll_order.setStyleSheet("border: 1px solid #222922; background-color: #060706;")
            self.order_widget.setStyleSheet("background-color: #060706;")
        else:
            self.right_frame.setStyleSheet("background-color: #c9c0b5; border: 2px solid #9c8f80; border-radius: 6px;")
            self.lbl_right_title.setStyleSheet("color: #4a5c31; border: none; background: transparent;")
            self.item_btn_selector.setStyleSheet("background-color: #f4f1eb; color: #2b4c1e; border: 1px solid #9c8f80; padding: 8px; border-radius: 4px; font-weight: bold;")
            self.scroll_dropdown.setStyleSheet("border: 1px solid #9c8f80; background-color: #f4f1eb;")
            self.dropdown_widget.setStyleSheet("background-color: #f4f1eb;")
            self.btn_clear.setStyleSheet("background-color: transparent; border: 2px solid #9c8f80; border-radius: 0px;")
            self.scroll_order.setStyleSheet("border: 1px solid #9c8f80; background-color: #f4f1eb;")
            self.order_widget.setStyleSheet("background-color: #f4f1eb;")

        ops_layout.addWidget(self.right_frame)

        self.render_dropdown_buttons(ITEM_OPTIONS)
        self.refresh_order_display()
        self.setup_timers_matrix_workspace()

    def setup_timers_matrix_workspace(self):
        # ЗАЩИТА QT: Если макет у страницы уже есть — не создаем его заново (убирает 1 FPS лаги!)
        if not self.page_timers_matrix.layout():
            timers_layout = QVBoxLayout(self.page_timers_matrix)
            # Фоновая подложка для матрицы таймеров деспавна секторов
            self.timers_page_bg = QLabel(self.page_timers_matrix)
            self.timers_page_bg.setScaledContents(True)
            self.timers_page_bg.lower()

            timers_layout.setContentsMargins(15, 15, 15, 15)
            timers_layout.setSpacing(10)
            
            # Информационный счётчик рисков снабжения
            self.telemetry_frame = QFrame()
            self.telemetry_frame.setFixedHeight(35)
            
            # Адаптивный стиль рамки телеметрии рисков
            if self.is_dark_theme:
                self.telemetry_frame.setStyleSheet("background-color: #141714; border: 1px solid #222922; border-radius: 4px;")
            else:
                self.telemetry_frame.setStyleSheet("background-color: #ebe4db; border: 1px solid #9c8f80; border-radius: 4px;")

            telemetry_layout = QHBoxLayout(self.telemetry_frame)
            telemetry_layout.setContentsMargins(15, 0, 15, 0)
            
            # Боевые индикаторы статистики рисков деспавна
            self.lbl_crit_stat = QLabel("🚨 КРИТИЧЕСКИ ( <1ч): 0 БАЗ")
            self.lbl_crit_stat.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            
            self.lbl_warn_stat = QLabel("⚠️ ВНИМАНИЕ (<24ч): 0 БАЗ")
            self.lbl_warn_stat.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            
            self.lbl_safe_stat = QLabel("✅ В БЕЗОПАСНОСТИ (>1д): 0 БАЗ")
            self.lbl_safe_stat.setFont(QFont("Arial", 9, QFont.Weight.Bold))

            # Применяем контрастные цвета в зависимости от выбранной темы терминала
            if self.is_dark_theme:
                self.lbl_crit_stat.setStyleSheet("color: #ef4444; background: transparent; border: none;")
                self.lbl_warn_stat.setStyleSheet("color: #f59e0b; background: transparent; border: none;")
                self.lbl_safe_stat.setStyleSheet("color: #a3e635; background: transparent; border: none;")
            else:
                self.lbl_crit_stat.setStyleSheet("color: #8c1d1d; background: transparent; border: none;")
                self.lbl_warn_stat.setStyleSheet("color: #b25e00; background: transparent; border: none;")
                self.lbl_safe_stat.setStyleSheet("color: #2b4c1e; background: transparent; border: none;")

            telemetry_layout.addWidget(self.lbl_crit_stat)
            telemetry_layout.addWidget(self.lbl_warn_stat, 0, Qt.AlignmentFlag.AlignCenter)
            telemetry_layout.addWidget(self.lbl_safe_stat, 0, Qt.AlignmentFlag.AlignRight)

            
            timers_layout.addWidget(self.telemetry_frame)
            
            # Скролл-зона для парящих карточек складов
            self.scroll_timers = QScrollArea()
            self.scroll_timers.setWidgetResizable(True)
            self.scroll_timers.setStyleSheet("border: none; background-color: transparent;")
            
            self.timers_widget = QWidget()
            self.timers_widget.setStyleSheet("background-color: transparent;")
            self.timers_list_layout = QVBoxLayout(self.timers_widget)
            self.timers_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.scroll_timers.setWidget(self.timers_widget)
            
            timers_layout.addWidget(self.scroll_timers)
        
        # Перестраиваем карточки складов с текстурой card-bg.jpg
        self.rebuild_timers_cards()


    def rebuild_timers_cards(self):
        """ТЯЖЕЛАЯ ОПЕРАЦИЯ: Формирует структуру ярких, контрастных карточек и накладывает матовые Sci-Fi фоны."""
        while self.timers_list_layout.count():
            item = self.timers_list_layout.takeAt(0)
            if item.widget(): 
                item.widget().deleteLater()
        
        self.timer_labels.clear()
        sorted_stockpiles = sorted(self.timers_list, key=lambda x: x["TimeLeft"])
        
        # Проверяем наличие вашего ассета с рамкой в папке scr/
        card_bg_path = get_resource_path(os.path.join("scr", "card-bg.jpg"))
        has_bg = os.path.exists(card_bg_path)
        
        for idx, s in enumerate(sorted_stockpiles):
            card = QFrame()
            card.setFixedHeight(75) # Чуть увеличим высоту для лучшего зазора текста
            ts = s["TimeLeft"]
            
            # Везде принудительно делаем текст названия баз чисто БЕЛЫМ для идеальной читаемости
            text_c = "#ffffff"
            
            # Настраиваем ПЛОТНЫЕ контрастные цвета неоновых рамок и матовых подложек карточек
            if self.is_dark_theme:
                # --- ВЕТКА ТЁМНОЙ ТЕМЫ (CYBERPUNK) ---
                if ts < 3600:
                    border_c = "#ff4545"      # Яркий красный контур
                    fallback_bg = "rgba(46, 20, 20, 0.75)"   # Матовый красно-бордовый фон
                    time_c = "#ff5555"        # Светящееся время
                elif ts < 86400:
                    border_c = "#f59e0b"      # Яркий оранжевый контур
                    fallback_bg = "rgba(43, 32, 21, 0.75)"   # Матовый оранжево-коричневый фон
                    time_c = "#ff9900"        # Светящееся время
                else:
                    border_c = "#222922"      # Технологичный стальной контур
                    fallback_bg = "rgba(20, 23, 20, 0.75)"   # Глубокий графитово-зеленый фон
                    time_c = "#a3e635"        # Лаймовое безопасное время
                    
                btn_style = """
                    QPushButton { background-color: rgba(36, 43, 36, 0.6); color: #ffffff; border: 1px solid #3d4a3d; border-radius: 4px; }
                    QPushButton:hover { background-color: #a3e635; color: #000000; font-weight: bold; border: 1px solid #ffffff; }
                """
            else:
                # --- ВЕТКА СВЕТЛОЙ ТЕМЫ (СИЛЬНО ЗАТЕМНЕННЫЙ DESERT KHAKI) ---
                if ts < 3600:
                    border_c = "#ff5555"      # Насыщенный красный контур
                    fallback_bg = "rgba(140, 29, 29, 0.65)"   # Матовый красный защитный слой
                    time_c = "#ff5555"        # Чёткое критическое время
                elif ts < 86400:
                    border_c = "#ff9900"      # Оливково-оранжевый контур
                    fallback_bg = "rgba(178, 94, 0, 0.65)"    # Матовый песочно-рыжий защитный слой
                    time_c = "#ff9900"        # Чёткое время внимания
                else:
                    border_c = "#9c8f80"      # Защитный оливковый контур
                    fallback_bg = "rgba(40, 45, 40, 0.65)"    # Матовый тёмно-армейский фон карточки
                    time_c = "#a3e635"        # Лаймовое безопасное время
                    
                btn_style = """
                    QPushButton { background-color: rgba(244, 241, 235, 0.2); color: #ffffff; border: 1px solid #9c8f80; border-radius: 4px; }
                    QPushButton:hover { background-color: rgba(74, 92, 49, 0.5); color: #ffffff; border: 1px solid #4a5c31; }
                """

            # Генерируем таблицы стилей с учетом флага картинок
            if has_bg:
                style_string = f"""
                    QFrame {{
                        background-image: url('{card_bg_path.replace(os.sep, "/")}');
                        background-position: center;
                        background-repeat: no-repeat;
                        border: 2px solid {border_c};
                        border-left: 6px solid {time_c};
                        border-radius: 6px;
                    }}
                    QFrame:hover {{
                        background-color: {"rgba(34, 48, 34, 0.85)" if self.is_dark_theme else "rgba(60, 70, 60, 0.85)"};
                        border: 2px solid {"#a3e635" if self.is_dark_theme else "#9c8f80"};
                    }}
                """
            else:
                style_string = f"""
                    QFrame {{
                        background-color: {fallback_bg};
                        border: 2px solid {border_c};
                        border-left: 6px solid {time_c};
                        border-radius: 6px;
                    }}
                    QFrame:hover {{
                        background-color: {"rgba(31, 41, 31, 0.85)" if self.is_dark_theme else "rgba(70, 80, 70, 0.85)"};
                        border: 2px solid {"#a3e635" if self.is_dark_theme else "#ffffff"};
                    }}
                """

            card.setStyleSheet(style_string)

            cl = QHBoxLayout(card)
            cl.setContentsMargins(20, 0, 20, 0)

            # Контрастная инфо-панель (Текст стал белым во всех режимах)
            lbl_info = QLabel(f"📍 {s['Region'].upper()}  ▶  {s['Location']}")
            lbl_info.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            lbl_info.setStyleSheet(f"color: {text_c}; background: transparent; border: none;")
            cl.addWidget(lbl_info)

            # Электронный таймер
            lbl_time = QLabel("---:---:--")
            lbl_time.setFont(QFont("Consolas", 15, QFont.Weight.Bold))
            lbl_time.setStyleSheet(f"color: {time_c}; background: transparent; border: none;")
            cl.addWidget(lbl_time, 0, Qt.AlignmentFlag.AlignRight)

            # Связываем ссылку на текстовое поле с ID склада
            self.timer_labels[s["ID"]] = lbl_time

            # Кнопка ручного ввода таймеров и просмотра логов
            btn_manage = QPushButton("УПРАВЛЕНИЕ")
            btn_manage.setFixedSize(110, 34)
            btn_manage.setFont(self.font_interface)
            btn_manage.setStyleSheet(btn_style)

            btn_manage.clicked.connect(lambda checked=False, sid=s["ID"]: self.open_stockpile_manager(sid))
            cl.addWidget(btn_manage, 0, Qt.AlignmentFlag.AlignRight)
            
            self.timers_list_layout.addWidget(card)

        # Запускаем первичный легкий подсчет текста времени
        self.refresh_timers_matrix_display()

    def open_stockpile_manager(self, stockpile_id):
        """Интерактивное окно: раздельный ввод Дней/Часов/Минут и сохранение логов с фоновым артом госпиталя."""
        s = next(x for x in self.timers_list if x["ID"] == stockpile_id)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"🛠️ КАНАЛ СВЯЗИ: {s['Location']}")
        dialog.setFixedSize(550, 500)
        
        # 🏥 УСТАНОВКА БОЕВОЙ ПОДЛОЖКИ ДЛЯ ОКНА УПРАВЛЕНИЯ
        import os
        from PySide6.QtGui import QPixmap
        
        dialog_art_path = get_resource_path(os.path.join("scr", "image_oW-UDn.png"))
        if os.path.exists(dialog_art_path):
            # Привязываем подложку к объекту dialog, чтобы защитить от сборщика мусора
            dialog.bg = QLabel(dialog)
            dialog.bg.setGeometry(0, 0, 550, 500)
            dialog.bg.setPixmap(QPixmap(dialog_art_path).scaled(550, 500, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
            dialog.bg.lower()
        
        # Динамический QSS с полупрозрачным матовым слоем rgba для сохранения читаемости логов
        if self.is_dark_theme:

            dialog.setStyleSheet("""
                QDialog { background-color: rgba(20, 23, 20, 0.85); color: #e5e7eb; }
                QLabel { color: #e5e7eb; background: transparent; }
                QLineEdit { background-color: #060706; color: #ffffff; border: 1px solid #222922; padding: 5px; border-radius: 4px; font-weight: bold; }
                QLineEdit:focus { border: 1px solid #a3e635; }
            """)
        else:
            dialog.setStyleSheet("""
                QDialog { background-color: rgba(220, 214, 205, 0.88); color: #2b2e2b; }
                QLabel { color: #2b2e2b; background: transparent; }
                QLineEdit { background-color: #f4f1eb; color: #1b1d1b; border: 1px solid #9c8f80; padding: 5px; border-radius: 4px; font-weight: bold; }
                QLineEdit:focus { border: 2px solid #4a5c31; }
            """)



        dl = QVBoxLayout(dialog)
        dl.setContentsMargins(15, 15, 15, 15)
        dl.setSpacing(10)

        dl.addWidget(QLabel(f"🗺️ Регион: {s['Region']}"))
        dl.addWidget(QLabel(f"📍 Локация: {s['Location']}"))

        # Консоль вывода истории логов
        dl.addWidget(QLabel("📜 ИСТОРИЯ ОБНОВЛЕНИЙ И ЛОГОВ СКЛАДА:"))
        log_view = QTextEdit()
        log_view.setReadOnly(True)
        log_view.setPlainText("\n".join(s["History"]))
        
        # Адаптивный стиль для консоли логов интенданта
        if self.is_dark_theme:
            log_view.setStyleSheet("""
                QTextEdit { 
                    background-color: #060706; 
                    color: #86efac; 
                    border: 1px solid #222922; 
                    font-family: 'Consolas', monospace; 
                    border-radius: 4px; 
                }
            """)
        else:
            log_view.setStyleSheet("""
                QTextEdit { 
                    background-color: #f4f1eb; 
                    color: #2b4c1e; 
                    border: 1px solid #9c8f80; 
                    font-family: 'Consolas', monospace; 
                    border-radius: 4px; 
                    font-weight: bold;
                }
            """)
            
        dl.addWidget(log_view)

        # ⏱️ ТАКТИЧЕСКИЙ БЛОК РАЗДЕЛЬНОГО ВВОДА ВРЕМЕНИ
        time_input_frame = QFrame()
        
        # Адаптивный стиль для рамки-подложки ввода времени
        if self.is_dark_theme:
            time_input_frame.setStyleSheet("background-color: #0b0c0a; border: 1px solid #222922; border-radius: 4px;")
        else:
            time_input_frame.setStyleSheet("background-color: #ebe4db; border: 1px solid #9c8f80; border-radius: 4px;")
            
        time_input_layout = QHBoxLayout(time_input_frame)

        time_input_layout.setContentsMargins(10, 10, 10, 10)

        time_input_layout.addWidget(QLabel("ДНИ:"))
        days_input = QLineEdit()
        days_input.setPlaceholderText("0")
        days_input.setFixedWidth(50)
        days_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_input_layout.addWidget(days_input)

        time_input_layout.addWidget(QLabel("ЧАСЫ:"))
        hours_input = QLineEdit()
        hours_input.setPlaceholderText("0")
        hours_input.setFixedWidth(50)
        hours_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_input_layout.addWidget(hours_input)

        time_input_layout.addWidget(QLabel("МИНУТЫ:"))
        mins_input = QLineEdit()
        mins_input.setPlaceholderText("0")
        mins_input.setFixedWidth(50)
        mins_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_input_layout.addWidget(mins_input)

        dl.addWidget(time_input_frame)

        # Кнопки быстрых команд интенданта
        btn_layout = QHBoxLayout()
        
        btn_reset = QPushButton("♻️ СБРОСИТЬ НА 48 ЧАСОВ")
        btn_apply = QPushButton("✅ ЗАДАТЬТАЙМЕР")
        
        # Адаптивный стиль кнопок под тёмную и светлую темы
        if self.is_dark_theme:
            btn_reset.setStyleSheet("background-color: #1e291b; color: #a3e635; font-weight: bold; border: 1px solid #16a34a; padding: 10px; border-radius: 4px;")
            btn_apply.setStyleSheet("background-color: #1d221d; color: #ffffff; font-weight: bold; border: 1px solid #2c352c; padding: 10px; border-radius: 4px;")
        else:
            btn_reset.setStyleSheet("background-color: #cbd9be; color: #2b4c1e; font-weight: bold; border: 1px solid #7e8761; padding: 10px; border-radius: 4px;")
            btn_apply.setStyleSheet("background-color: #b5bc9a; color: #1e2417; font-weight: bold; border: 1px solid #7e8761; padding: 10px; border-radius: 4px;")

        btn_layout.addWidget(btn_reset)
        btn_layout.addWidget(btn_apply)
        dl.addLayout(btn_layout)


        # Логика обработки и пересчета времени в секунды
        def reset_to_max():
            s["TimeLeft"] = 172800  # 48 часов
            now_str = datetime.now().strftime("%d.%m / %H:%M:%S")
            s["History"].append(f"[{now_str}] Интендант выполнил быстрый сброс таймера на базовые 48 часов.")
            log_view.setPlainText("\n".join(s["History"]))
            self.rebuild_timers_cards()

        def apply_custom_time():
            d_txt = days_input.text().strip() or "0"
            h_txt = hours_input.text().strip() or "0"
            m_txt = mins_input.text().strip() or "0"
            
            if d_txt.isdigit() and h_txt.isdigit() and m_txt.isdigit():
                total_seconds = (int(d_txt) * 86400) + (int(h_txt) * 3600) + (int(m_txt) * 60)
                
                if total_seconds > 0:
                    s["TimeLeft"] = total_seconds
                    now_str = datetime.now().strftime("%d.%m / %H:%M:%S")
                    s["History"].append(f"[{now_str}] Установлено новое время удержания: {d_txt}д {h_txt}ч {m_txt}м.")
                    log_view.setPlainText("\n".join(s["History"]))
                    
                    days_input.clear()
                    hours_input.clear()
                    mins_input.clear()
                    self.rebuild_timers_cards()
                else:
                    QMessageBox.warning(dialog, "СБОЙ", "Итоговое время должно быть больше 0 секунд!")
            else:
                QMessageBox.warning(dialog, "СБОЙ СИНТАКСИСА", "Заполняйте поля только числовыми значениями!")

        btn_reset.clicked.connect(reset_to_max)
        btn_apply.clicked.connect(apply_custom_time)

        dialog.exec()
    def auto_load_scanner_file(self):
        """ФОНОВЫЙ МОНИТОРИНГ: Побайтово парсит структуру MapData.sav, используя базу ITEM_CODES."""
        file_path = r"C:\Users\romaf\AppData\Local\Foxhole\Saved\SaveGames\76561198805350792_MapData.sav"
        
        if not os.path.exists(file_path): 
            return
            
        try:
            # Читаем сохранение игры как сырые бинарные байты
            with open(file_path, "rb") as file:
                binary_data = file.read()
                
            parsed_dict = {}
            
            # Проходим по всем 396 кодам из подключенного модуля item_codes
            for code_name, details in ITEM_CODES.items():
                # Превращаем текстовый код предмета в байтовую строку для поиска
                code_bytes = code_name.encode('utf-8')
                
                # Ищем все вхождения предмета в бинарнике (склады, фабрики, pinned-метки)
                start_pos = 0
                while True:
                    pos = binary_data.find(code_bytes, start_pos)
                    if pos == -1:
                        break
                        
                    # Движок UE хранит Quantity ровно через зафиксированное смещение от имени свойства.
                    # Ищем маркер типа данных "Int16Property" в блоке данных сразу за именем
                    lookahead_block = binary_data[pos : pos + 60]
                    prop_marker = b"Int16Property"
                    
                    marker_pos = lookahead_block.find(prop_marker)
                    if marker_pos != -1:
                        # Значение количества (2 байта) находится ровно через 9 байт после "Int16Property"
                        val_pos = pos + marker_pos + len(prop_marker) + 9
                        if val_pos + 2 <= len(binary_data):
                            # Извлекаем 16-битное число (Short) в формате Little-Endian
                            raw_bytes = binary_data[val_pos : val_pos + 2]
                            count_val = int.from_bytes(raw_bytes, byteorder='little', signed=True)
                            
                            # Отсекаем мусорные значения и системные ID
                            if 0 < count_val < 32000:
                                # Берем красивое русское имя из словаря локализации
                                ru_name = details.get("name_ru") or details.get("name_en") or code_name
                                # Если один и тот же предмет найден в разных блоках, суммируем или берем максимальный
                                parsed_dict[ru_name] = max(parsed_dict.get(ru_name, 0), count_val)
                                
                    start_pos = pos + len(code_bytes)

            # Формируем массив для вывода в интерфейс программы
            parsed = [{"Name": k, "Count": v} for k, v in parsed_dict.items()]
            
            # Сортируем по алфавиту для красоты отображения в таблице
            parsed = sorted(parsed, key=lambda x: x["Name"])
            
            # Обновляем экран только при реальном изменении данных, чтобы не мерцали виджеты
            if parsed and parsed != getattr(self, 'last_parsed_data', None):
                self.last_parsed_data = parsed
                self.storage_data = parsed
                self.refresh_storage_display()
                
        except Exception as e:
            # Предотвращаем падение интерфейса, если игра эксклюзивно заблокировала файл во время автосейва
            pass


    def refresh_storage_display(self):
        while self.storage_layout.count():
            item = self.storage_layout.takeAt(0)
            if item.widget(): 
                item.widget().deleteLater()
        # Гарантированное восстановление иконок импорта при любых перерисовках тем

        if hasattr(self, 'left_frame'):
            for widget in self.left_frame.findChildren(QPushButton):
                if "JSON" in str(widget.toolTip()):
                    json_p = get_resource_path(os.path.join("scr", "json.png"))
                    if os.path.exists(json_p): widget.setIcon(QIcon(json_p))
                elif "БУФЕРА" in str(widget.toolTip()):
                    log_p = get_resource_path(os.path.join("scr", "log-file.png"))
                    if os.path.exists(log_p): widget.setIcon(QIcon(log_p))

                
        for idx, x in enumerate(self.storage_data):
            row = QFrame()
            row.setFixedHeight(36)
            
            # Адаптация под светлую тему: чередующиеся песочные строки с оливковым hover-эффектом
            row.setStyleSheet(f"""
                QFrame {{ 
                    background-color: {'#ebe4db' if idx % 2 == 0 else 'transparent'}; 
                    border: 1px solid transparent; 
                    border-radius: 4px; 
                }} 
                QFrame:hover {{ 
                    background-color: #d2d9be; 
                    border: 1px solid #7e8761; 
                }}
            """)
            
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(10, 0, 10, 0)
            
            lbl_name = QLabel(f"• {x['Name']}")
            lbl_name.setFont(self.font_interface)
            lbl_name.setStyleSheet("color: #ffffff; background: transparent; border: none;")
            row_layout.addWidget(lbl_name)
            
            p = QFrame()
            p.setFixedSize(80, 24)
            p.setStyleSheet("""
                background-color: #e2ebd5; 
                border: 1px solid #7e8761; 
                border-radius: 0px;
            """)
            pl = QVBoxLayout(p)
            pl.setContentsMargins(0, 0, 0, 0)
            
            lbl_c = QLabel(f"{x['Count']}")
            lbl_c.setFont(self.font_interface)
            lbl_c.setStyleSheet("color: #2b4c1e; background: transparent; border: none;")
            lbl_c.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pl.addWidget(lbl_c)
            
            row_layout.addWidget(p)
            self.storage_layout.addWidget(row)

    def refresh_order_display(self):
        """Очистка и полная перерисовка текущего заказа с адаптивными стилями под тему."""
        while self.order_layout.count():
            item = self.order_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        if not self.current_order:
            empty = QFrame()
            empty.setFixedHeight(45)
            if self.is_dark_theme:
                empty.setStyleSheet("background-color: #2e1414; border: 1px solid #7a3333; border-radius: 4px;")
                lbl_style = "color: #f87171; background: transparent; border: none;"
            else:
                empty.setStyleSheet("background-color: #f7e6e6; border: 1px solid #c79595; border-radius: 4px;")
                lbl_style = "color: #8c2b2b; background: transparent; border: none;"

                
            el = QVBoxLayout(empty)
            lbl = QLabel("Заказ пуст. Выберите предметы из матрицы выше...")
            lbl.setFont(self.font_interface)
            lbl.setStyleSheet(lbl_style)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            el.addWidget(lbl)
            self.order_layout.addWidget(empty)
            return
            
        # ОДИН единый адаптивный цикл для отрисовки элементов заказа (с поддержкой шт./ящ.)
        for idx, (item, data) in enumerate(self.current_order.items()):
            # Безопасная проверка: если данные — это просто число (старый формат), подставляем "ящ." по умолчанию
            if isinstance(data, tuple):
                count, unit = data
            else:
                count, unit = data, "ящ."
                
            row = QFrame()
            row.setFixedHeight(36)
            
            # Настройка цветов строки в зависимости от активной темы
            if self.is_dark_theme:
                row.setStyleSheet(f"""
                    QFrame {{
                        background-color: {'#141814' if idx % 2 == 0 else 'transparent'};
                        border: 1px solid transparent;
                        border-radius: 4px;
                    }}
                    QFrame:hover {{
                        background-color: #1b2e1b;
                        border: 1px solid #84cc16;
                    }}
                """)
                text_color = "#e5e7eb"
                badge_style = "background-color: #1e291b; border: 1px solid #16a34a; border-radius: 4px;"
                count_color = "#a3e635"
            else:
                # СВЕТЛАЯ ТЕМА ПОД КАРТИНКУ: Делаем строки темными полупрозрачными, чтобы текст не сливался со светлым небом!
                row.setStyleSheet(f"""
                    QFrame {{
                        background-color: {'rgba(0, 0, 0, 0.4)' if idx % 2 == 0 else 'rgba(0, 0, 0, 0.2)'};
                        border: 1px solid transparent;
                        border-radius: 4px;
                    }}
                    QFrame:hover {{
                        background-color: rgba(74, 92, 49, 0.6);
                        border: 1px solid #9c8f80;
                    }}
                """)
                text_color = "#ffffff"  # Чисто белый текст названия предмета
                badge_style = "background-color: rgba(0, 0, 0, 0.5); border: 1px solid #9c8f80; border-radius: 0px;"
                count_color = "#a3e635"  # Контрастный лаймовый цвет количества

            
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(10, 0, 10, 0)
            
            lbl_name = QLabel(f"• {item}")
            lbl_name.setFont(self.font_interface)
            lbl_name.setStyleSheet("color: #ffffff; background: transparent; border: none;")
            row_layout.addWidget(lbl_name)
            
            p = QFrame()
            p.setFixedSize(85, 24)
            p.setStyleSheet(badge_style)
            pl = QVBoxLayout(p)
            pl.setContentsMargins(0, 0, 0, 0)
            
            lbl_c = QLabel(f"{count} {unit}")
            lbl_c.setFont(self.font_interface)
            lbl_c.setStyleSheet(f"color: {count_color}; background: transparent; border: none;")
            lbl_c.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pl.addWidget(lbl_c)
            
            row_layout.addWidget(p)
            self.order_layout.addWidget(row)
            # Принудительное восстановление картинок сайдбара, защищающее от затирания QSS
        if hasattr(self, 'sidebar_frame'):

            sidebar_icons = {
                self.btn_nav_ops: "pre-order.gif",
                self.btn_nav_timers: "image_amQ8BV.png",
                self.btn_nav_training: "image_q11-he.png",
                self.btn_toggle_theme: "image_qH61K6.png"
            }
            for btn, img_name in sidebar_icons.items():
                img_path = get_resource_path(os.path.join("scr", img_name))
                if os.path.exists(img_path):
                    btn.setIcon(QIcon(img_path))
                    # Принудительно вызываем метод свертывания/развертывания меню, чтобы обновить маски QIcon





    def render_dropdown_buttons(self, items_list):
        """Отрисовка контрастных кнопок матрицы предметов под светлую хаки-тему."""
        while self.dropdown_layout.count():
            item = self.dropdown_layout.takeAt(0)
            if item.widget(): 
                item.widget().deleteLater()
                
        for item in items_list:
            btn = QPushButton(f"  {item}")
            btn.setFont(self.font_interface)
            
            # Адаптивная матрица кнопок под активную тему
            if self.is_dark_theme:
                btn.setStyleSheet("""
                    QPushButton { 
                        text-align: left; 
                        color: #d1d5db; 
                        background-color: transparent; 
                        border: 1px solid transparent; 
                        padding-left: 6px; padding-top: 6px; padding-bottom: 6px; border-radius: 4px;
                    } 
                    QPushButton:hover { 
                        background-color: #a3e635; 
                        color: #0c0e0c; 
                        border: 1px solid #ffffff;
                        padding-left: 16px; 
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton { 
                        text-align: left; 
                        color: #1b1d1b; 
                        background-color: #fcfbfa; 
                        border: 1px solid #ebe4db; 
                        padding-left: 6px; padding-top: 6px; padding-bottom: 6px; border-radius: 4px;
                        margin-bottom: 2px;
                    } 
                    QPushButton:hover { 
                        background-color: #4a5c31; 
                        color: #ffffff; 
                        border: 1px solid #354222;
                        padding-left: 16px; 
                    }
                """)
                
            btn.clicked.connect(lambda checked=False, val=item: self.select_dropdown_value(val))
            self.dropdown_layout.addWidget(btn)


    def select_dropdown_value(self, value):
        self.selected_item_name = value
        self.item_btn_selector.setText(value)

    def filter_items(self, text):
        """Интерактивный фильтр предметов по ключевым буквам."""
        q = text.lower().strip()
        if not q:
            self.render_dropdown_buttons(ITEM_OPTIONS)
            return
        f = [i for i in ITEM_OPTIONS if i.lower().startswith(q)] + [i for i in ITEM_OPTIONS if q in i.lower() and not i.lower().startswith(q)]
        self.render_dropdown_buttons(f if f else ["Ничего не найдено"])

    def add_item_to_order(self):
        """Добавляет предмет в конструктор снабжения с точным учетом переключателя (ШТ / ЯЩ)."""
        item = getattr(self, 'selected_item_name', "Выбрать предмет из матрицы ниже...")
        count = self.count_input.text().strip()
        if item in ["Выбрать предмет из матрицы ниже...", "Ничего не найдено"] or not count.isdigit():
            return
            
        # Считываем актуальное состояние кнопки-переключателя единиц
        unit = "шт." if self.btn_unit_toggle.isChecked() else "ящ."
        
        # Если предмет уже есть в заказе, проверяем его структуру данных
        if item in self.current_order:
            old_data = self.current_order[item]
            if isinstance(old_data, tuple):
                old_count, old_unit = old_data
                # Суммируем только если единицы измерения совпадают, иначе берем новую выбранную
                if old_unit == unit:
                    self.current_order[item] = (old_count + int(count), unit)
                else:
                    self.current_order[item] = (int(count), unit)
            else:
                # Защита на случай старого целочисленного формата в памяти
                self.current_order[item] = (int(count), unit)
        else:
            # Новый предмет добавляется строго с выбранной единицей измерения
            self.current_order[item] = (int(count), unit)
            
        self.count_input.clear()
        self.refresh_order_display()


    def clear_order(self):
        self.current_order.clear()
        self.refresh_order_display()
    def load_storage_json(self):
        """Ручной импорт текстового файла логов через диалоговое окно."""
        f, _ = QFileDialog.getOpenFileName(self, "Открыть отчет сканера", "", "Отчеты сканера (*.json *.txt);;Все файлы (*.*)")
        if not f: return
        try:
            parsed = []
            with open(f, "r", encoding="utf-8") as file:
                lines = file.readlines()
                
            for idx, line in enumerate(lines):
                line = line.strip()
                if not line: continue
                if idx == 0 and any(m in line.lower() for m in ["public", "private", "x:", "y:", "valley", "port", "king"]):
                    continue
                    
                if "," in line:
                    parts = line.rsplit(",", 1)
                    item_name = parts[0].strip()
                    count_str = parts[1].strip()
                    if count_str.isdigit():
                        count_val = int(count_str)
                        if count_val > 0:
                            parsed.append({"Name": item_name, "Count": count_val})
                            
            if parsed: 
                self.storage_data = parsed
                self.refresh_storage_display()
                QMessageBox.information(self, "СИНХРОНИЗАЦИЯ", f"Успешно загружено предметов: {len(parsed)}")
            else:
                QMessageBox.warning(self, "ОШИБКА АНАЛИЗА", "На складе нет активных предметов (все позиции равны 0).")
        except Exception as e: 
            QMessageBox.critical(self, "ОШИБКА", f"Сбой парсинга лога:\n{str(e)}")

    def load_storage_clipboard(self):
        """Парсинг лога из буфера обмена с поддержкой различных разделителей и очисткой мусорных символов."""
        try:
            clipboard = QApplication.clipboard()
            text = clipboard.text().strip()
            
            if not text:
                QMessageBox.warning(self, "БУФЕР ОБМЕНА", "Буфер обмена пуст или не содержит текстовых данных!")
                return
                
            parsed = []
            lines = text.splitlines()
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Определяем разделитель в строке (запятая, стрелочка или двоеточие)
                separator = "," if "," in line else "->" if "->" in line else ":" if ":" in line else None
                if separator:
                    parts = line.split(separator, 1)
                    
                    # Очищаем название предмета от точек и маркеров списков Discord (типа • или *)
                    name_part = parts[0].replace("•", "").replace("*", "").strip()
                    
                    # Очищаем количество от текстовых подписей "шт", "ящ", "ящиков"
                    count_part = parts[1].lower().replace("шт.", "").replace("ящ.", "").replace("шт", "").replace("ящ", "").replace("ящиков", "").strip()
                    
                    if count_part.isdigit() and int(count_part) > 0:
                        parsed.append({"Name": name_part, "Count": int(count_part)})
            
            if parsed:
                self.storage_data = parsed
                self.refresh_storage_display()
            else:
                QMessageBox.warning(
                    self, 
                    "ОШИБКА ФОРМАТА", 
                    "Не удалось распознать данные сканера. Убедитесь, что текст в формате:\n\n"
                    "Название Предмета, Количество\n"
                    "или\n"
                    "Название Предмета -> Количество"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "КРИТИЧЕСКИЙ СБОЙ", f"Сбой при обработке данных из буфера:\n{str(e)}")


    def handle_file_action(self, panel_type, file_format):
        btn = self.btn_mode_left if panel_type == "склад" else self.btn_mode_right
        if btn.isChecked(): 
            QMessageBox.information(self, "ИМПОРТ ДАННЫХ", f"Запущен импорт файлов для панели: {panel_type.upper()}")
        else:
            if file_format == "txt": self.export_text_data(panel_type, "txt")
            elif file_format == "xlsx": self.export_excel_data(panel_type)
            elif file_format == "png": self.export_image_data(panel_type, with_text=True, to_buffer=False)
            elif file_format == "png_buffer": self.export_image_data(panel_type, with_text=True, to_buffer=True)

    def toggle_export_import_mode(self):
        """Переключение режима конкретной нажатой кнопки с вызовом кастомного брендированного окна."""
        # Определяем, какая именно кнопка была нажата (левая или правая)
        sender_button = self.sender()
        if not sender_button:
            return

        # Проверяем текущий текст на кнопке, чтобы переключить его наоборот
        if "ЭКСПОРТ" in sender_button.text():
            text = "РЕЖИМ: ИМПОРТ ДАННЫХ"
            msg_title = "⚙️ СИСТЕМА: ИМПОРТ"
            msg_text = "ВНИМАНИЕ: Панель переключена в режим ИМПОРТА данных.\nНижние тактические клавиши теперь ожидают чтение внешних файлов."
        else:
            text = "РЕЖИМ: ЭКСПОРТ ДАННЫХ"
            msg_title = "📡 СИСТЕМА: ЭКСПОРТ"
            msg_text = "УВЕДОМЛЕНИЕ: Панель переключен в режим ЭКСПОРТА данных.\nДоступна выгрузка рапортов в форматы TXT, XLSX и графику PNG."
        
        # Меняем текст ТОЛЬКО на той кнопке, которую нажал пользователь
        sender_button.setText(text)

        # 🛸 СОЗДАЕМ КАСТОМНОЕ СТИЛЬНОЕ ОКНО УВЕДОМЛЕНИЯ
        notifier = QDialog(self)
        notifier.setWindowTitle(msg_title)
        notifier.setFixedSize(480, 250)
        
        # Стилизация элементов под текущую тему (без background-color у QDialog, чтобы работал фоновый рисунок)
        if self.is_dark_theme:
            notifier.setStyleSheet("""
                QLabel { color: #e5e7eb; font-family: 'Consolas', monospace; font-size: 11px; background-color: rgba(20, 23, 20, 0.85); border: 1px solid #222922; border-radius: 4px; padding: 10px; }
                QPushButton { background-color: #1e291b; color: #a3e635; font-weight: bold; border: 1px solid #16a34a; padding: 8px 16px; border-radius: 4px; font-family: 'Consolas', monospace; }
                QPushButton:hover { background-color: #a3e635; color: #0c0e0c; }
            """)
        else:
            notifier.setStyleSheet("""
                QLabel { color: #1e2417; font-family: 'Arial', sans-serif; font-size: 12px; font-weight: bold; background-color: rgba(220, 214, 205, 0.85); border: 1px solid #9c8f80; border-radius: 4px; padding: 10px; }
                QPushButton { background-color: #b5bc9a; color: #1e2417; font-weight: bold; border: 1px solid #7e8761; padding: 8px 16px; border-radius: 4px; }
                QPushButton:hover { background-color: #4a5c31; color: #ffffff; border: 1px solid #354222; }
            """)

        # 🎨 НАСТРОЙКА ЗАДНЕГО ФОНА С КЛАНОВЫМ ЛОГОТИПОМ
        import os
        from PySide6.QtGui import QPixmap
        
        logo_path = os.path.join("scr", "clan-logo.png")
        
        if os.path.exists(logo_path):
            # Создаем фоновый виджет, который растянется на все окно
            bg_label = QLabel(notifier)
            bg_label.setGeometry(0, 0, notifier.width(), notifier.height())
            
            # Загружаем герб и масштабируем его
            pixmap = QPixmap(logo_path).scaled(notifier.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            bg_label.setPixmap(pixmap)
            
            # Опускаем подложку на самый нижний слой, чтобы она не перекрывала текст и кнопку
            bg_label.lower()
        else:
            # Если файла нет, оставляем сплошную тактическую заливку
            if self.is_dark_theme:
                notifier.setStyleSheet(notifier.styleSheet() + " QDialog { background-color: #141714; border: 2px solid #a3e635; border-radius: 6px; }")
            else:
                notifier.setStyleSheet(notifier.styleSheet() + " QDialog { background-color: #dcd6cd; border: 2px solid #4a5c31; border-radius: 6px; }")


        nl = QVBoxLayout(notifier)
        nl.setContentsMargins(25, 25, 25, 25)
        nl.setSpacing(20)

        # Текст оповещения
        lbl_msg = QLabel(msg_text)
        lbl_msg.setWordWrap(True)
        lbl_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nl.addWidget(lbl_msg)

        # Кнопка подтверждения
        btn_ok = QPushButton("ПРИНЯТО")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.clicked.connect(notifier.accept)
        nl.addWidget(btn_ok, alignment=Qt.AlignmentFlag.AlignCenter)

        # Отображаем как модальное окно
        notifier.exec()




    def export_text_data(self, mode, ext):
        p, _ = QFileDialog.getSaveFileName(self, "Сохранить рапорт", "", "Text Files (*.txt)")
        if not p: return
        with open(p, "w", encoding="utf-8") as f:
            if mode == "склад":
                for x in self.storage_data: 
                    f.write(f"{x['Name']} -> {x['Count']} шт.\n")
            else:
                # Экспорт заказа с корректным выводом шт. или ящ.
                for k, data in self.current_order.items(): 
                    if isinstance(data, tuple):
                        count, unit = data
                    else:
                        count, unit = data, "ящ."
                    f.write(f"{k} -> {count} {unit}\n")

    def export_excel_data(self, mode):
        """Экспорт данных в Excel с поддержкой разделения на штуки и ящики для конструктора заказа."""
        p, _ = QFileDialog.getSaveFileName(self, "Сохранить таблицу", "", "Excel Files (*.xlsx)")
        if not p: 
            return
            
        # Формируем структуру данных под выбранный режим
        if mode == "склад":
            data = [
                {"Название": x["Name"], "Количество": x["Count"], "Ед. изм.": "шт."} 
                for x in self.storage_data
            ]
        else:
            data = []
            for k, val in self.current_order.items():
                # Безопасно распаковываем новые кортежи (кол-во, ед.изм.) или старые числа
                if isinstance(val, tuple):
                    count, unit = val
                else:
                    count, unit = val, "ящ."
                    
                data.append({
                    "Название заказа": k, 
                    "Количество": count, 
                    "Ед. изм.": unit
                })
                
        # Сохраняем сформированный список в файл .xlsx
        pd.DataFrame(data).to_excel(p, index=False)
        QMessageBox.information(self, "УСПЕХ", "Таблица сформирована!")


    def export_image_data(self, mode, with_text, to_buffer):
        """Разбивка списка предметов на аккуратные страницы и наложение на gray-background.jpg."""
        region, s_type, s_name = "Clanshead Valley", "ПОРТ", "Public"
        current_time_str = datetime.now().strftime("%H-%M_%d.%m.%Y")
        
        target_list = [{"Name": x["Name"], "Count": x["Count"]} for x in self.storage_data] if mode == "склад" else [{"Name": k, "Count": v} for k, v in self.current_order.items()]
            
        if not target_list:
            QMessageBox.warning(self, "ПУСТЫЕ ДАННЫЕ", "Нет элементов для генерации графических страниц!")
            return

        ITEMS_PER_PAGE = 12
        pages_chunks = [target_list[i:i + ITEMS_PER_PAGE] for i in range(0, len(target_list), ITEMS_PER_PAGE)]
        total_pages = len(pages_chunks)

        if to_buffer:
            img = self._render_single_tactical_page(pages_chunks[0], 1, total_pages, region, s_type, s_name)
            import io
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            q_pixmap = QPixmap()
            q_pixmap.loadFromData(buffer.getvalue(), "PNG")
            QApplication.clipboard().setPixmap(q_pixmap)
            QMessageBox.information(self, "FAST SHARE", "Первая страница отчета скопирована в буфер обмена Discord через Ctrl+V!")
            return

        base_dir = QFileDialog.getExistingDirectory(self, "Выберите директорию для выгрузки тактической папки страниц")
        if not base_dir: return

        folder_name = f"{current_time_str}_{region}_{s_type}_{s_name}"
        full_output_path = os.path.join(base_dir, folder_name)
        
        if not os.path.exists(full_output_path):
            os.makedirs(full_output_path)

        for page_num, chunk in enumerate(pages_chunks, start=1):
            img = self._render_single_tactical_page(chunk, page_num, total_pages, region, s_type, s_name)
            file_name = f"Стр_{page_num}_из_{total_pages}.png"
            img.save(os.path.join(full_output_path, file_name))

        QMessageBox.information(self, "ПЕЙДЖИНГ ЗАВЕРШЕН", f"Успешно создана тактическая папка:\n{folder_name}\nСтраниц: {total_pages}")

    def _render_single_tactical_page(self, items_chunk, page_num, total_pages, region, s_type, s_name):
        bg_p = get_resource_path(os.path.join("scr", "gray-background.jpg"))
        img = Image.open(bg_p).convert("RGB") if os.path.exists(bg_p) else Image.new("RGB", (650, 1000), color="#2d2d2d")
        img = img.resize((650, 1000), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(img)
        try: 
            font_header = ImageFont.truetype("arial.ttf", 20)
            font_body = ImageFont.truetype("arial.ttf", 18)
            font_page = ImageFont.truetype("arial.ttf", 16)
        except: 
            font_header = font_body = font_page = ImageFont.load_default()

        draw.text((40, 30), f"Гекс: {region}", fill="#ffffff", font=font_header)
        draw.text((40, 60), f"Тип: {s_type}", fill="#ffffff", font=font_header)
        draw.text((40, 90), f"Склад: {s_name}", fill="#ffffff", font=font_header)
        draw.text((520, 30), f"Стр. {page_num}/{total_pages}", fill="#60a5fa", font=font_page)
        draw.line([(40, 130), (610, 130)], fill="#4b5563", width=2)

        y_offset = 160
        for x in items_chunk:
            draw.text((40, y_offset), f"•  {x['Name']}", fill="#e5e7eb", font=font_body)
            draw.text((440, y_offset), f"x {x['Count']} (в ящике)", fill="#a3e635", font=font_body)
            y_offset += 65
        return img

    def update_tactical_timers(self):
        """Ежесекундный пересчет времени + обновление счетчиков рисков + сборка цветного HTML конвейера."""
        import random

        # 1. Фоновый отсчет таймеров деспавна складов
        for x in self.timers_list:
            if x["TimeLeft"] > 0: 
                x["TimeLeft"] -= 1

        # Обновление реальной статистики верхних индикаторов Раздела №2
        if hasattr(self, 'lbl_crit_stat'):
            crit = sum(1 for x in self.timers_list if x["TimeLeft"] < 3600)
            warn = sum(1 for x in self.timers_list if 3600 <= x["TimeLeft"] < 86400)
            safe = sum(1 for x in self.timers_list if x["TimeLeft"] >= 86400)
            self.lbl_crit_stat.setText(f"🚨 КРИТИЧЕСКИ (<1ч): {crit} БАЗ")
            self.lbl_warn_stat.setText(f"⚠️ ВНИМАНИЕ (<24ч): {warn} БАЗ")
            self.lbl_safe_stat.setText(f"✅ В БЕЗОПАСНОСТИ (>1д): {safe} БАЗ")

        html_messages = []
        plain_messages = []
        
        # 2. Формируем сообщения для проблемных складов (< 1 дня)
        for x in self.timers_list:
            if x["TimeLeft"] < 86400:
                ts = x["TimeLeft"]
                d, h, m, s_sec = ts // 86400, (ts % 86400) // 3600, (ts % 3600) // 60, ts % 60
                t_str = f"{d}д {h:02d}ч {m:02d}м {s_sec:02d}с" if d > 0 else f"{h:02d}:{m:02d}:{s_sec:02d}"
                
                # Цветовое кодирование: Красный для критических, Оранжевый для обычных алертов
                color_hex = "#ff5555" if ts < 3600 else "#f59e0b"
                status_icon = "🔴 [КРИТИЧЕСКИ]" if ts < 3600 else "🟠 [ВНИМАНИЕ]"
                raw_msg = f"{status_icon} Склад в порту {x['Region']} ({x['Location']}) пропадёт через {t_str}!"
                
                html_messages.append(f"<font color='{color_hex}'>{raw_msg}</font>")
                plain_messages.append(raw_msg)
        
        # 3. Случайный радиоперехват фраз штаба (Шанс 10%) в сочный зеленый цвет
        if self.phrase_hold_seconds > 0:
            self.phrase_hold_seconds -= 1
            if self.active_custom_phrase:
                html_messages.append(f"<font color='#a3e635'>🟢 {self.active_custom_phrase}</font>")
                plain_messages.append(f"🟢 {self.active_custom_phrase}")
        else:
            if random.random() < 0.10:
                self.active_custom_phrase = random.choice(TACTICAL_CUSTOM_PHRASES)
                self.phrase_hold_seconds = 12
                html_messages.append(f"<font color='#a3e635'>🟢 {self.active_custom_phrase}</font>")
                plain_messages.append(f"🟢 {self.active_custom_phrase}")
            else:
                self.active_custom_phrase = ""

        # 4. Склеиваем блоки и дублируем 3 раза для бесшовности конвейера
        if html_messages:
            base_html = "   •   ".join(html_messages) + "   •   "
            base_plain = "   •   ".join(plain_messages) + "   •   "
        else:
            base_html = "<font color='#a3e635'>🟢 ВСЕ СЕКТОРА СНАБЖЕНИЯ В ПОЛНОЙ БЕЗОПАСНОСТИ   •   </font>"
            base_plain = "🟢 ВСЕ СЕКТОРА СНАБЖЕНИЯ В ПОЛНОЙ БЕЗОПАСНОСТИ   •   "

        # Записываем цветной вариант для экрана и чистый вариант для замеров физики
        self.raw_ticker_text = base_html * 3
        self.plain_ticker_text = base_plain * 3
        
        self.refresh_timers_matrix_display()



    def refresh_timers_matrix_display(self):
        """ЛЕГКОВЕСНАЯ ОПЕРАЦИЯ: Безопасное обновление текста времени без нагрузки на систему."""
        if hasattr(self, 'lbl_crit_stat'):
            crit = sum(1 for x in self.timers_list if x["TimeLeft"] < 3600)
            warn = sum(1 for x in self.timers_list if 3600 <= x["TimeLeft"] < 86400)
            safe = sum(1 for x in self.timers_list if x["TimeLeft"] >= 86400)
            self.lbl_crit_stat.setText(f"🚨 КРИТИЧЕСКИ (<1ч): {crit} БАЗ")
            self.lbl_warn_stat.setText(f"⚠️ ВНИМАНИЕ (<24ч): {warn} БАЗ")
            self.lbl_safe_stat.setText(f"✅ В БЕЗОПАСНОСТИ (>1д): {safe} БАЗ")

        # Проверяем, существует ли словарь и не пуст ли он
        if hasattr(self, 'timer_labels') and self.timer_labels:
            for s in self.timers_list:
                if s["ID"] in self.timer_labels:
                    # Берем ссылку на надпись таймера
                    lbl = self.timer_labels[s["ID"]]
                    if lbl:
                        try:
                            ts = s["TimeLeft"]
                            d, h, m, s_sec = ts // 86400, (ts % 86400) // 3600, (ts % 3600) // 60, ts % 60
                            t_str = f"{d}д {h:02d}ч {m:02d}м {s_sec:02d}с" if d > 0 else f"{h:02d}:{m:02d}:{s_sec:02d}"
                            
                            # Безопасно обновляем текст, перехватывая любые удаления C++ объекта из памяти
                            lbl.setText(t_str)
                        except RuntimeError:
                            # Если Qt уже удалил эту карточку в параллельном потоке, просто пропускаем шаг
                            pass


    def animate_ticker(self):
        """ВЕКТОРНЫЙ ДВИЖОК 60 ГЦ: Безошибочный расчет смещения по чистому тексту с выводом цветного HTML."""
        if not hasattr(self, 'raw_ticker_text') or not self.raw_ticker_text:
            return

        # Сдвиг строго по целым пикселям для максимальной четкости букв ClearType
        self.ticker_offset -= 2
        
        # Измеряем точную физическую длину ОДНОЙ ТРЕТИ чистого текста (без учета скрытых тегов кода)
        total_width = self.lbl_ticker_text.fontMetrics().horizontalAdvance(self.plain_ticker_text)
        one_third_width = total_width // 3

        if one_third_width <= 0:
            return

        # Бесшовный сброс без швов и пауз
        if abs(self.ticker_offset) >= one_third_width:
            self.ticker_offset = 0

        # Выводим на экран шикарный цветной HTML рапорт
        self.lbl_ticker_text.setText(self.raw_ticker_text)
        
        # Двигаем текстовый блок по выверенным координатам
        final_x = int(self.sidebar_frame.width() + self.ticker_offset)
        self.lbl_ticker_text.move(final_x, 14)


    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'main_bg') and self.main_bg:
            self.main_bg.setGeometry(0, 0, self.width(), self.height())
        if hasattr(self, 'dark_overlay') and self.dark_overlay:
            self.dark_overlay.setGeometry(0, 0, self.width(), self.height())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LogisticsStudioApp()
    window.show()
    sys.exit(app.exec())

