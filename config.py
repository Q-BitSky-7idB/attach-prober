# config.py

import os
import re

# --- Шляхи та папки ---
DOWNLOAD_DIR = os.path.join(os.path.expanduser('~'), 'Downloads')

# --- Налаштування Cloudscraper ---
SCRAPER_PARAMS = {
    'delay': 10, 
    'browser': {'browser': 'chrome', 'platform': 'windows', 'mobile': False}
}

DEFAULT_TIMEOUT = 30

# --- Шаблон URL ---
FILENAME_PATTERN = r'filename\*?=(?:utf-8\'\')?"?([^"]+)"?'

# Регулярний вираз для пошуку та розбиття URL: (префікс)(ID)(суфікс)
URL_ID_PATTERN = r'(.*id=)(\d+)(.*)'
URL_SUFIX = 'id='	# TODO: тут треба автознаходження а не константа

def get_meta_from_headers(response):
    """
    Витягує назву файлу та Content-Length із заголовків відповіді.
    Повертає кортеж: (filename, content_length)
    """
    
    # 1. Отримання Content-Length (Розмір файлу)
    content_length_str = response.headers.get('Content-Length')
    try:
        # Конвертуємо у ціле число. Якщо заголовок відсутній, повернемо None.
        content_length = int(content_length_str)
    except (TypeError, ValueError):
        content_length = None # Розмір не визначено або не є числом

    # 2. Отримання Назви Файлу (Існуюча логіка)
    filename = None
    cd = response.headers.get('Content-Disposition')
        
    if cd:
        # Шукаємо назву у Content-Disposition
        match = re.search(FILENAME_PATTERN, cd, re.I)
        if match:
            filename = match.group(1).strip('"\' ')
        
        # Якщо назва не знайдена в Content-Disposition, беремо її з URL
        if not filename:
            filename = os.path.basename(response.url.split('?')[0])

    # 3. Повернення обох значень
    return filename, content_length

# --- Керування діями (для io_handler) ---
ACTIONS = {
    'r': 'RETURN',
    'к': 'RETURN', # Кирилична 'к'
    
    'd': 'DECREMENT',
    'в': 'DECREMENT', # Кирилична 'в'
    
    'e': 'INCREMENT',
    'у': 'INCREMENT', # Кирилична 'у'

    'c': 'QUICK_EXIT', # It was 'EXIT_SOFT' : q - ('ы'\'і')
    'с': 'QUICK_EXIT', # Кирилична 'с'
    
    'q': 'EXIT',
    'й': 'EXIT', # Кирилична 'й'

    'o': 'DEBUG',
    'щ': 'DEBUG', # Кирилична 'щ'
}

# Дії для DOWNLOAD
ADD_DOWNLOAD = {'g': 'DOWNLOAD', 'п': 'DOWNLOAD'} # Кирилична 'п'

# Дії для TRY_BYPASS
ADD_BYPASS = {'t': 'TRY_BYPASS', 'е': 'TRY_BYPASS'} # Кирилична 'е'

OPTIONS_STRATEGY = {
    200: (
      f"Оберіть дію: (E/D: продовжити, G/П: скачати, C/Q: вийти): ",
      {**ACTIONS, **ADD_DOWNLOAD}
    ),
    403: (
      f"Оберіть дію: [T/Е] - Обхід, [D/В] - Декремент, [E/У] - Інкремент, [C/Q] - Вийти: ",
      {**ACTIONS, **ADD_BYPASS}
    ),
    410: (
      f"Оберіть дію: [D/В] - Декремент, [E/У] - Інкремент, [G/П] – Скачати, [C/Q] - Вийти: ",
      {**ACTIONS, **ADD_DOWNLOAD}
    ),
      0: (f"Оберіть дію: [D/В] - Декремент, [E/У] - Інкремент, [C/Q] - Вийти: ", None)
}

def PassiveMsgChose(current_block):
    if current_block.Status == 200:
         return f"{URL_SUFIX}{current_block.Index} : {current_block.Size: >11} : {current_block.FileName} ;", 'GREEN'
    if current_block.Status == 403:
         return f"{URL_SUFIX}{current_block.Index} : Доступ заборонено (403)! : Файл не отримано!", 'RED'
    elif current_block.Status < 500:
         return f"{URL_SUFIX}{current_block.Index} : Помилка - ({current_block.Status}) : Файл не отримано!", 'YELLOW'
    else:
         return f"{URL_SUFIX}{current_block.Index} : Помилка - ({current_block.Status}) : Неочікувана відповідь!", 'RED'

PASSIVE_MSGS = {
    'DEFAULT': lambda current_block: (PassiveMsgChose(current_block)),
    #'RETURN': ("", None),
    'DOWNLOAD': lambda current_block: (
        f"{URL_SUFIX}{current_block.Index} : "
        f"{current_block.Size: >11} : Downloading {current_block.FileName}...", 
        'CYAN'
    ),
    'DOWNLOADED': lambda current_block: (
        f"{URL_SUFIX}{current_block.Index} : "
        f"{current_block.Size: >11} : DOWNLOADED << {current_block.FileName}", 
        'CYAN'
    ),
    'TRY_BYPASS': lambda current_block: (
        f"{URL_SUFIX}{current_block.Index} : "
        f"Доступ заборонено (403)! : Файл не отримано!",
        'YELLOW'
    )
}

# Дії для конфлікту файлів (File Conflict)
ACTIONS_FILE_CONFLICT = {
    'c': 'COPY',
    'с': 'COPY',      # Кирилична 'с'
    
    'r': 'REWRITE',
    'к': 'REWRITE',   # Кирилична 'к'
    
    's': 'SKIP',
    'і': 'SKIP',      # Кирилична 'і'
    'ы': 'SKIP',      # Кирилична 'ы'
}