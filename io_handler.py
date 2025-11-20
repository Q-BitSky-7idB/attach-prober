# io_handler.py

import sys
import os
from colorama import Fore, Style, init
import config

# Умовний імпорт для негайного зчитування символу
try:
    import msvcrt
except ImportError:
    # Заглушка для систем, відмінних від Windows (Linux/macOS)
    import termios, tty
    def getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

# Ініціалізація кольорів
init(autoreset=True)

COLOR_MAP = {
    'GREEN': Fore.GREEN,
    'RED': Fore.RED,
    'YELLOW': Fore.YELLOW,
    'CYAN': Fore.CYAN,
    'DEFAULT': Style.RESET_ALL,
}

def print_message(message, color='DEFAULT'):
    """Виводить повідомлення з кольором та новим рядком."""
    sys.stdout.write(f"{COLOR_MAP.get(color, Style.RESET_ALL)}{message}{Style.RESET_ALL}\n")
    sys.stdout.flush()

def overwrite_message(message, color='DEFAULT'):
    """Перезаписує поточний рядок без нового рядка."""
    sys.stdout.write(f"\r{COLOR_MAP.get(color, Style.RESET_ALL)}{message}{Style.RESET_ALL}")
    sys.stdout.flush()

def get_action_from_user(options_str):
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
