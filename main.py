# main.py

import sys
import argparse
import os

# Додаємо поточну папку до шляху для імпорту локальних модулів
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scanner_loop import run_scanner_loop

def main():
    """Основна функція для парсингу аргументів та запуску сканера."""
    parser = argparse.ArgumentParser(description="Інтерактивний сканер файлів із змінним ID.")
    parser.add_argument('url', type=str, help='Початкове посилання, що містить змінний ID (наприклад, base?id=123)')
    args = parser.parse_args()
    
    run_scanner_loop(args.url)

if __name__ == '__main__':
    main()
