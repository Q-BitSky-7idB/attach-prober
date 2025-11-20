import sys
import re
import os
import argparse
import cloudscraper
import pyperclip
import time
from colorama import Fore, Style, init

# Ініціалізація colorama для підтримки кольорів у Windows
init(autoreset=True)

# --- Налаштування ---
DOWNLOAD_DIR = os.path.join(os.path.expanduser('~'), 'Downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
# --------------------

def create_new_scraper():
    """Створює та повертає новий екземпляр cloudscraper."""
    return cloudscraper.create_scraper(
        delay=10, 
        browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
    )

def get_filename_from_headers(response):
    """Витягує назву файлу із заголовка Content-Disposition."""
    cd = response.headers.get('Content-Disposition')
    if cd:
        match = re.search(r'filename\*?=(?:utf-8\'\')?"?([^"]+)"?', cd, re.I)
        if match:
            return match.group(1).strip('"\' ')
    return os.path.basename(response.url.split('?')[0])

def download_file(scraper, url, filename):
    """Скачує вміст файлу."""
    print(f"\n[Завантаження] Розпочато скачування: {filename}")
    try:
        with scraper.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            file_path = os.path.join(DOWNLOAD_DIR, filename)
            
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"[Успіх] Файл збережено до: {file_path}")
    except Exception as e:
        print(f"[Помилка завантаження] Не вдалося завантажити файл: {e}")

def handle_403_error(current_id, target_url):
    """
    Обробляє помилку 403, пропонуючи користувачеві оновити скрепер.
    Повертає: (новий_scraper, новий_id)
    """
    while True:
        # Перезаписуємо поточний рядок
        sys.stdout.write(f"\r{Fore.RED}ID-{current_id}: Доступ заборонено (403)! Опції: [t] - Створити новий Scraper (Обхід), [c/r] - Змінити ID, [s] - Вийти. ")
        sys.stdout.flush()

        action = input().lower().strip()

        if action in ('t', 'т'):
            sys.stdout.write("\r" + " " * 120 + "\r") # Очищуємо рядок
            print(f"\n[Обхід] Спроба створення нового екземпляра Scraper для ID {current_id}...")
            
            # Створюємо НОВИЙ ЕКЗЕМПЛЯР скрепера
            new_scraper = create_new_scraper()
            
            # Спробуємо одразу перевірити цільовий URL
            try:
                new_scraper.head(target_url, allow_redirects=True, timeout=30)
                print(f"{Fore.GREEN}[Обхід] Сесія успішно відновлена!{Style.RESET_ALL}")
                # Повертаємо новий скрепер і поточний ID, щоб перевірити його знову
                return new_scraper, current_id 
            except Exception as e:
                print(Fore.RED + f"[Обхід] Не вдалося відновити сесію. Спробуйте пізніше. {e}")
                # Повертаємо початковий скрепер, щоб не ламати логіку (але це не допомогло)
                time.sleep(1) 
                continue

        elif action in ('c', 'с'):
            sys.stdout.write("\r" + " " * 120 + "\r")
            return None, current_id - 1
        elif action in ('r', 'к'):
            sys.stdout.write("\r" + " " * 120 + "\r")
            return None, current_id + 1
        elif action in ('s', 'ы', 'і', 'q', 'й'):
            sys.stdout.write("\r" + " " * 120 + "\r")
            print("Процес зупинено користувачем.")
            return None, -1 # Спеціальний код для виходу
        else:
            pass # Залишаємось у циклі
            
    return None, current_id

def get_target_url(prefix, current_id, suffix):
    """Складає цільовий URL."""
    return f"{prefix}{current_id}{suffix}"

def main():
    parser = argparse.ArgumentParser(description="Інтерактивний сканер файлів із змінним ID.")
    parser.add_argument('url', type=str, help='Початкове посилання, що містить змінний ID (наприклад, base?id=123)')
    args = parser.parse_args()

    match = re.search(r'(.*id=)(\d+)(.*)', args.url, re.I)
    if not match:
        print(Fore.RED + "Помилка: Не вдалося знайти шаблон 'id=[number]' у посиланні.")
        sys.exit(1)

    base_url_prefix = match.group(1)
    current_id = int(match.group(2))
    base_url_suffix = match.group(3)

    scraper = create_new_scraper() # Початкова ініціалізація
    last_successful_url = args.url

    print("--- Cloudflare Interactive File Scanner ---")
    print(f"Базове посилання: {base_url_prefix}**[ID]**{base_url_suffix}")
    print(f"Папка завантажень: {DOWNLOAD_DIR}")

    # Початкова перевірка сесії
    initial_url = get_target_url(base_url_prefix, current_id, base_url_suffix)
    try:
        print("[Сесія] Ініціалізація...")
        scraper.head(initial_url, timeout=15)
        print("[Сесія] Успішно ініціалізовано сесію.")
    except Exception:
        print(Fore.YELLOW + "[Сесія] Увага: Початкова перевірка не пройшла. Спробуйте 't' (обхід) пізніше.")


    while True:
        if current_id < 0:
            break
            
        target_url = get_target_url(base_url_prefix, current_id, base_url_suffix)
        
        # --- ВИКОНАННЯ ЗАПИТУ HEAD ---
        try:
            response = scraper.head(target_url, allow_redirects=True, timeout=15)
            status_code = response.status_code
        except Exception:
            status_code = -1 
        
        # --- ОБРОБКА КОДІВ ---
        if status_code == 200:
            filename = get_filename_from_headers(response)
            
            print(f"\nID-{current_id} : {Fore.GREEN}Файл знайдено: {filename}{Style.RESET_ALL}")
            last_successful_url = target_url

            action = input(f"Оберіть дію (c/r: продовжити, d: скачати, s/q: вийти) [Поточний ID: {current_id}]: ").lower()

            if action in ('c', 'с'):
                current_id -= 1
            elif action in ('r', 'к'):
                current_id += 1
            elif action in ('d', 'в'):
                download_file(scraper, target_url, filename)
                current_id += 1 # Після скачування переходимо до наступного ID
            elif action in ('s', 'ы', 'і'):
                print("Процес зупинено користувачем.")
                break
            elif action in ('q', 'й'):
                pyperclip.copy(last_successful_url)
                print(f"Повернення останнього успішного URL '{last_successful_url}' до буфера обміну. Вихід.")
                break
            else:
                print("Невідома команда. Продовжуємо з інкрементом.")
                current_id += 1

        elif status_code == 403:
            # Викликаємо обробник помилки 403.
            # handle_403_error поверне або новий скрепер, або змінений ID
            new_scraper, new_id = handle_403_error(current_id, target_url)
            
            if new_id == -1: # Користувач обрав вихід
                break
            
            # Якщо handle_403_error повернув новий скрепер, оновлюємо змінну
            if new_scraper:
                scraper = new_scraper
                # current_id залишиться тим же, щоб перевірити його з новим скрепером
                continue # Повертаємось на початок циклу, щоб негайно перевірити той самий ID
            else:
                # Якщо скрепер не оновлювався, але ID змінився (c або r)
                current_id = new_id

        elif status_code == 404:
            print(f"ID-{current_id} : {Fore.YELLOW}Файл не знайдено (404){Style.RESET_ALL}")
            current_id += 1
        elif status_code != -1:
            print(f"ID-{current_id} : {Fore.RED}Невідома помилка: {status_code}{Style.RESET_ALL}")
            current_id += 1
        else: 
            print(f"ID-{current_id} : {Fore.RED}Помилка з'єднання/таймаут. {Style.RESET_ALL}")
            action = input("Продовжити сканування (y/n)? ").lower()
            if action != 'y':
                break
            current_id += 1
            
if __name__ == '__main__':
    main()