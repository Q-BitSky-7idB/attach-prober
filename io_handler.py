# io_handler.py

import sys
import os
from colorama import Fore, Style, init
import config

LAST_LINE_SIZE = 0

# --- Імпорт rich ---

# Умовний імпорт для негайного зчитування символу
if os.name == 'nt':
    # Windows: використовуємо msvcrt
    try:
        import msvcrt
    except ImportError:
        # Це малоймовірно, але залишаємо для повної надійності
        msvcrt = None 
else:
    # Linux/macOS: використовуємо термінал
    try:
        import termios, tty
        
        def getch_unix():
            """Читає один символ негайно (Unix/Linux/macOS)."""
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch
            
    except ImportError:
        # Запасний варіант, якщо termios недоступний
        def getch_unix():
            return sys.stdin.read(1)
            

# Ініціалізація кольорів
init(autoreset=True)

#Fore/Back: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
#Style: DIM, NORMAL, BRIGHT, RESET_ALL

#Fore/Back: LIGHTBLACK_EX, LIGHTRED_EX, LIGHTGREEN_EX, LIGHTYELLOW_EX, LIGHTBLUE_EX, LIGHTMAGENTA_EX, LIGHTCYAN_EX, LIGHTWHITE_EX

COLOR_MAP = {
    'GREEN': Fore.GREEN,
    'RED': Fore.RED,
    'YELLOW': Fore.YELLOW,
    'YELLOWB': Fore.LIGHTYELLOW_EX,
    'CYAN': Fore.CYAN,
    'GREENB': Fore.LIGHTGREEN_EX,
    'CYANB': Fore.LIGHTCYAN_EX,
    'DEFAULT': Style.RESET_ALL,
}

def printf_msg(message, color='DEFAULT'):
    """Виводить повідомлення з кольором та новим рядком."""
    sys.stdout.write(f"{COLOR_MAP.get(color, Style.RESET_ALL)}{message}{Style.RESET_ALL}")
    sys.stdout.flush()
    LAST_LINE_SIZE = len(message)
    
def print_msg(message, color='DEFAULT'):
    """Виводить повідомлення з кольором та новим рядком."""
    sys.stdout.write(f"{COLOR_MAP.get(color, Style.RESET_ALL)}{message}{Style.RESET_ALL}\n")
    sys.stdout.flush()

def overwrite_msg(message, color='DEFAULT'):
    """Перезаписує поточний рядок без нового рядка."""
    sys.stdout.write(f"\r{' ' * LAST_LINE_SIZE}\r{COLOR_MAP.get(color, Style.RESET_ALL)}{message}{Style.RESET_ALL}")
    sys.stdout.flush()

def Xget_action_from_user(options_str):
    """
    Чекає негайного натискання клавіші та повертає відповідну дію з config.
    """
    sys.stdout.write(options_str)
    sys.stdout.flush()

    while True:
        # Зчитуємо один символ негайно
        key = msvcrt.getch().decode('utf-8').lower() if os.name == 'nt' else getch().lower()
        
        action = config.ACTIONS.get(key)
        
        if action:
            # Очищаємо рядок після отримання символу
            sys.stdout.write("\r" + " " * 120 + "\r")
            sys.stdout.flush()
            return action
        # Ігноруємо невідомі клавіші та продовжуємо чекати

def get_action_from_user(options_str):
    """
    Чекає негайного натискання клавіші, ігнорує нерозпізнані символи/стрілки,
    та повертає відповідну дію.
    """
    sys.stdout.write(options_str)
    sys.stdout.flush()

    while True:
        # 1. Зчитування байтів
        if os.name == 'nt':
            key_bytes = msvcrt.getch()
        else:
            # Це залежить від вашої реалізації getch. Якщо вона повертає байти, це добре.
            # Якщо повертає символ, доведеться адаптувати. Припускаємо, що повертає байти.
            key_bytes = sys.stdin.read(1).encode('utf-8')
        
        key = None
        
        # 2. Обробка спеціальних клавіш (Windows)
        if os.name == 'nt' and key_bytes in (b'\x00', b'\xe0'):
            # Це початок послідовності стрілки або F-клавіші. 
            # Зчитуємо другий байт і ігноруємо послідовність.
            msvcrt.getch() 
            continue # Повертаємось до початку циклу
        
        # 3. Декодування та нормалізація
        try:
            # Декодуємо. Кирилиця повинна декодуватися коректно.
            key = key_bytes.decode('utf-8').lower()
        except UnicodeDecodeError:
            # Ігноруємо нерозпізнані байти або неповні послідовності.
            continue
        
        # 4. Обробка дій
        action = config.ACTIONS.get(key)
        
        if action:
            # Очищаємо рядок після отримання символу
            sys.stdout.write("\r" + " " * len(options_str) + " " * 30 + "\r") # Очищаємо рядок
            sys.stdout.flush()
            return action
        
        # 5. Ігноруємо невідомі символи
        # Якщо action None, просто продовжуємо цикл і чекаємо наступне натискання.
        # Це запобігає "крашу" та ігнорує невідомі клавіші.
        # Примітка: Додайте print(f"Невідома клавіша: {key}") для налагодження, якщо потрібно.

def handle_403_prompt(current_id):
    """
    Інтерактивний запит при помилці 403.
    Повертає обрану дію.
    """
    options_str = (
        f"\r{Fore.RED}ID-{current_id}: Доступ заборонено (403)! Опції: "
        f"[t/т] - Обхід, [c/с] - Декремент, [r/к] - Інкремент, [s/q] - Вийти. "
    )
    return get_action_from_user(options_str)
