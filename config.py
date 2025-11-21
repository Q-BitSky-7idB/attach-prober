# config.py

import os

# --- Шляхи та папки ---
DOWNLOAD_DIR = os.path.join(os.path.expanduser('~'), 'Downloads')

# --- Налаштування Cloudscraper ---
SCRAPER_PARAMS = {
    'delay': 10, 
    'browser': {'browser': 'chrome', 'platform': 'windows', 'mobile': False}
}

DEFAULT_TIMEOUT = 30

# --- Шаблон URL ---
# Регулярний вираз для пошуку та розбиття URL: (префікс)(ID)(суфікс)
URL_ID_PATTERN = r'(.*id=)(\d+)(.*)'
URL_ID_SUFIX = 'id='

# --- Керування діями (для io_handler) ---
ACTIONS = {
    'c': 'DECREMENT',
    'с': 'DECREMENT', # Кирилична 'с'
    'r': 'INCREMENT',
    'к': 'INCREMENT', # Кирилична 'к'
    'd': 'DOWNLOAD',
    'в': 'DOWNLOAD', # Кирилична 'в'
    's': 'EXIT_SOFT',
    'ы': 'EXIT_SOFT', # Кирилична 'ы'
    'і': 'EXIT_SOFT', # Кирилична 'і'
    'q': 'EXIT_CLIPBOARD',
    'й': 'EXIT_CLIPBOARD', # Кирилична 'й'
    't': 'TRY_BYPASS',
    'е': 'TRY_BYPASS' # Кирилична 'е'
}