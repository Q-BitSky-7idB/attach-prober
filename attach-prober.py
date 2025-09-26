import sys
import re
import os
import argparse
import cloudscraper
import pyperclip  # Бібліотека для роботи з буфером обміну (потрібно встановити: pip install pyperclip)

# --- Налаштування ---
DOWNLOAD_DIR = os.path.join(os.path.expanduser('~'), 'Downloads')
print("Drop folder: " + DOWNLOAD_DIR)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
# --------------------

def get_filename_from_headers(response):
    """Витягує назву файлу із заголовка Content-Disposition."""
    cd = response.headers.get('Content-Disposition')
    if cd:
        # Регулярний вираз для пошуку filename="..."
        match = re.search(r'filename\*?=(?:utf-8\'\')?"?([^"]+)"?', cd, re.I)
        if match:
            # Декодуємо URL, якщо потрібно, хоча cloudscraper/requests це часто роблять
            return match.group(1).strip()
    
    # Якщо заголовок не знайдено, використовуємо частину URL
    return os.path.basename(response.url.split('?')[0])

def download_file(scraper, url, filename):
    """Скачує вміст файлу."""
    print(f"\n[Завантаження] Розпочато скачування: {filename}")
    try:
        # Використовуємо GET-запит, але вже без 'HEAD'
        with scraper.get(url, stream=True) as r:
            r.raise_for_status()
            file_path = os.path.join(DOWNLOAD_DIR, filename)
            total_size = int(r.headers.get('content-length', 0))
            
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"[Успіх] Файл збережено до: {file_path}")
    except Exception as e:
        print(f"[Помилка завантаження] Не вдалося завантажити файл: {e}")

def main():
    parser = argparse.ArgumentParser(description="Інтерактивний сканер файлів із змінним ID.")
    parser.add_argument('url', type=str, help='Початкове посилання, що містить змінний ID (наприклад, base?id=123)')
    args = parser.parse_args()

    # Регулярний вираз для пошуку та розділення: base?id=123
    match = re.search(r'(.*id=)(\d+)(.*)', args.url, re.I)
    if not match:
        print("Помилка: Не вдалося знайти шаблон 'id=[number]' у посиланні.")
        sys.exit(1)

    base_url_prefix = match.group(1) # Частина URL до ID: "https://example.com/?id="
    current_id = int(match.group(2)) # Поточне число ID
    base_url_suffix = match.group(3) # Частина URL після ID (якщо є)

    # Ініціалізація сесії cloudscraper. Це важливо для збереження доступу (куків).
    scraper = cloudscraper.create_scraper(
        delay=10,  # Затримка для кращої імітації людини
        browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
    )

    last_successful_url = args.url

    print("--- Cloudflare Interactive File Scanner ---")
    print(f"Базове посилання: {base_url_prefix}**[ID]**{base_url_suffix}")
    print(f"Стандартна папка завантажень: {DOWNLOAD_DIR}")
    
    # Виконуємо перший запит, щоб пройти початкову перевірку
    try:
        scraper.head(args.url)
        print("[Сесія] Успішно ініціалізовано сесію (пройдено першу перевірку).")
    except Exception as e:
        print(f"[Сесія] Увага: Не вдалося пройти початкову перевірку! {e}")
        # Не виходимо, даємо шанс наступним запитам

    while True:
        target_url = f"{base_url_prefix}{current_id}{base_url_suffix}"
        
        print(f"\n--- Перевірка ID: {current_id} ---")
        
        try:
            # 1. Виконуємо запит HEAD (тільки заголовки, без вмісту)
            response = scraper.head(target_url, allow_redirects=True, timeout=15)
            
            if response.status_code == 200:
                filename = get_filename_from_headers(response)
                
                # 3.1) Вивід інформації
                print(f"ID-{current_id} : \033[92m{filename}\033[0m") # Виділяємо зеленим
                last_successful_url = target_url

                # 3.1) Вибір опцій
                action = input(f"Оберіть дію (c/r: продовжити, d: скачати, s/q: вийти) [Поточний ID: {current_id}]: ").lower()

                if action in ('c', 'с'):
                    current_id -= 1  # Декремент
                elif action in ('r', 'к'):
                    current_id += 1  # Інкремент
                elif action in ('d', 'в'):
                    # Скачування: використовуємо той же scraper і отримане ім'я
                    download_file(scraper, target_url, filename)
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

            elif response.status_code == 404:
                print(f"ID-{current_id} : \033[93mФайл не знайдено (404)\033[0m")
                current_id += 1 # Зазвичай продовжуємо шукати
            elif response.status_code == 403:
                print(f"ID-{current_id} : \033[91mДоступ заборонено Cloudflare (403)\033[0m. Спроба обійти.")
                # Спроба відновити сесію (Cloudscraper спробує пройти перевірку знову)
                current_id += 1
            else:
                print(f"ID-{current_id} : \033[91mНевідома помилка: {response.status_code}\033[0m")
                current_id += 1

        except Exception as e:
            print(f"Сталася помилка запиту: {e}")
            action = input("Продовжити сканування (y/n)? ").lower()
            if action != 'y':
                break
            current_id += 1

if __name__ == '__main__':
    main()