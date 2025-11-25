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
    'r': 'RETURN',
    'к': 'RETURN', # Кирилична 'к'
    'К': 'RETURN', # Кирилична 'к'
    
    'd': 'DECREMENT',
    'в': 'DECREMENT', # Кирилична 'в'
    'В': 'DECREMENT', # Кирилична 'В'
    
    'e': 'INCREMENT',
    'у': 'INCREMENT', # Кирилична 'у'
    'У': 'INCREMENT', # Кирилична 'У'
    
    'g': 'DOWNLOAD',
    'п': 'DOWNLOAD', # Кирилична 'п'
    'П': 'DOWNLOAD', # Кирилична 'П'
    'c': 'QUICK_EXIT', # It was 'EXIT_SOFT' : q - ('ы'\'і')
    'с': 'QUICK_EXIT', # Кирилична 'с'
    'С': 'QUICK_EXIT', # Кирилична 'С'
    'q': 'EXIT_NORMAL',
    'й': 'EXIT_NORMAL', # Кирилична 'й'
    'Й': 'EXIT_NORMAL', # Кирилична 'Й'
    't': 'TRY_BYPASS',
    'е': 'TRY_BYPASS', # Кирилична 'е'
    'Е': 'TRY_BYPASS', # Кирилична 'Е'
    'o': 'DEBUG_OUTPUT',
    'щ': 'DEBUG_OUTPUT', # Кирилична 'щ'
    'Щ': 'DEBUG_OUTPUT'  # Кирилична 'Щ'
}