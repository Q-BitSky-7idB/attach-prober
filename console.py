# console.py

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
    'REDB': Fore.LIGHTRED_EX,
    'DEFAULT': Style.RESET_ALL,
}

def printf(message, color='DEFAULT'):
    global LAST_LINE_SIZE
    """Виводить повідомлення з кольором та новим рядком."""
    sys.stdout.write(f"{COLOR_MAP.get(color, Style.RESET_ALL)}{message}{Style.RESET_ALL}")
    sys.stdout.flush()
    LAST_LINE_SIZE = len(message)
    
def prints(message, color='DEFAULT'):
    global LAST_LINE_SIZE
    """Виводить повідомлення з кольором та новим рядком."""
    sys.stdout.write(f"{COLOR_MAP.get(color, Style.RESET_ALL)}{message}{Style.RESET_ALL}\n")
    sys.stdout.flush()
    LAST_LINE_SIZE = len(message)

def overwrite(message, color='DEFAULT'):
    global LAST_LINE_SIZE
    """Перезаписує поточний рядок без нового рядка."""
    if message == "":
        return
    sys.stdout.write(f"\r{' ' * LAST_LINE_SIZE}\r{COLOR_MAP.get(color, Style.RESET_ALL)}{message}{Style.RESET_ALL}")
    sys.stdout.flush()
    LAST_LINE_SIZE = len(message)

def get_action_from_user(options_str="", acts_dict=None):
    """
    Чекає негайного натискання клавіші, ігнорує нерозпізнані символи/стрілки,
    та повертає відповідну дію.
    """
    sys.stdout.write("\n" + options_str)
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
        
        if not acts_dict:
            acts_dict=config.ACTIONS
        # 4. Обробка дій
        action = acts_dict.get(key)
        
        if action:
            # Очищаємо рядок після отримання символу
            sys.stdout.write("\r" + " " * len(options_str) + " " * 12 + "\r\033M") # Очищаємо рядок та повертаємось на позицію повідомлення
            sys.stdout.flush()
            return action
        
        # 5. Ігноруємо невідомі символи
        # Якщо action None, просто продовжуємо цикл і чекаємо наступне натискання.
        # Це запобігає "крашу" та ігнорує невідомі клавіші.
        # Примітка: Додайте print(f"Невідома клавіша: {key}") для налагодження, якщо потрібно.