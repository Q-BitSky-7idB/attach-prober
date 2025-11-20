# check_header_with_curl_cffi.py

from curl_cffi import requests
import sys

# -----------------
# КОНФІГУРАЦІЯ
# -----------------
file_url = "https://itorrents-igruha.org/engine/download.php?id=91795"
# Імітуємо один із найпоширеніших браузерних слідів
BROWSER_IMPERSONATE = "chrome120" 
TIMEOUT = 15

def check_url_header(url: str):
    """
    Виконує HEAD-запит з імітацією браузера для обходу Cloudflare.
    
    Якщо HEAD-запит блокується (наприклад, 403), виконується GET-запит
    для ініціації обходу JS-перевірки Cloudflare.
    """
    print(f"-> Перевірка URL: {url}")
    print(f"-> Імітація: {BROWSER_IMPERSONATE}")
    
    try:
        # 1. Спроба виконати HEAD-запит для отримання лише заголовків
        response = requests.head(
            url,
            impersonate=BROWSER_IMPERSONATE,
            allow_redirects=True,
            timeout=TIMEOUT
        )
        
        status_code = response.status_code
        print(f"-> Статус HEAD-запиту: {status_code}")
        
        # 2. Обробка, якщо Cloudflare вимагає JS-перевірки (Challenge)
        if status_code >= 400 or "cf-browser-verification" in response.text:
            print("-> Виявлено Cloudflare Challenge або помилку. Спроба GET-запиту для обходу...")
            
            # Якщо HEAD-запит провалився, виконуємо GET, щоб curl_cffi виконав обхід (JS)
            response = requests.get(
                url,
                impersonate=BROWSER_IMPERSONATE,
                allow_redirects=True,
                timeout=TIMEOUT * 2, # Збільшуємо таймаут для обходу JS
                # `verify=False` може знадобитися для деяких конфігурацій, 
                # але спробуйте спочатку без нього
            )
            
            status_code = response.status_code
            print(f"-> Статус GET-запиту після обходу: {status_code}")


        # 3. Виведення результату
        if status_code == 200:
            # Отримання назви файлу із заголовка Content-Disposition
            filename = response.headers.get('Content-Disposition')
            
            # Оскільки ми виконували HEAD (або GET), Content-Disposition може бути відсутній
            # Якщо його немає, ми виведемо іншу корисну інформацію.
            if filename is None:
                filename_info = "Відсутній. (Перевірте Content-Type або URL)"
            else:
                filename_info = filename
                
            print("-" * 30)
            print(f"✅ Статус: Успішно ({status_code})")
            print(f"ℹ️ Content-Disposition: {filename_info}")
            print(f"ℹ️ Content-Type: {response.headers.get('Content-Type')}")
            print(f"🔗 Фінальний URL: {response.url}")
            print("-" * 30)
            
        else:
            print(f"❌ Помилка: {status_code}. Не вдалося отримати заголовки (Cloudflare або інше блокування).")
            print(f"Текст відповіді (перші 200 символів): {response.text[:200]}...")

    except requests.RequestsError as e:
        print(f"❌ Критична помилка запиту: {e}", file=sys.stderr)
    except Exception as e:
        print(f"❌ Виникла неочікувана помилка: {e}", file=sys.stderr)

if __name__ == "__main__":
    check_url_header(file_url)