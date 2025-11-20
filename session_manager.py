# session_manager.py

import re
import os
# Змінюємо імпорт: використовуємо requests з curl_cffi
from curl_cffi import requests # <-- НОВА БІБЛІОТЕКА
# Додаємо імпорт для специфічної помилки cURL, яка може бути причиною
#from curl_cffi.requests import CurlError 
from curl_cffi import CurlError

import config
import io_handler

# Конфігурація для імітації браузера
BROWSER_IMPERSONATE = "chrome120"
# Конфігурація для обходу CF (може знадобитися для GET-запитів)
CF_BYPASS_PARAMS = {
    "impersonate": BROWSER_IMPERSONATE,
    "verify": True, # Залишаємо перевірку SSL
    "allow_redirects": True
}


class FileScannerSession:
    """Керує сесією curl_cffi та операціями з файлами."""
    
    def __init__(self, initial_url_to_check): # <--- ЦЕЙ АРГУМЕНТ ПОТРІБЕН!
        # Сесія curl_cffi створюється лише один раз
        self.session = self._create_session()
        # Проводимо початкове "прогрівання"
        self._warmup_session(initial_url_to_check)


    def _create_session(self):
        """Створює новий екземпляр сесії curl_cffi."""
        # curl_cffi дозволяє створити сесію, як і requests
        s = requests.Session()
        return s

    def _warmup_session(self, url):
        """Виконує початковий GET-запит для обходу CF та отримання куків."""
        io_handler.print_message("[/] Спроба 'прогріву' сесії... Обхід CF!")
        
        # Використовуємо self.session для збереження куків
        try:
            # Виконуємо GET, щоб переконатися, що JS-Challenge пройдено і куки збережені
            self.session.get(url, timeout=DEFAULT_TIMEOUT, **CF_BYPASS_PARAMS) 
            io_handler.print_message("[+] Сесія успішно 'прогріта'!", color='GREEN')
            return True
        except Exception as e:
            io_handler.print_message(f"Не вдалося 'прогріти' сесію при запуску. \n{e}", color='RED')
            return False


    def renew_session(self, url_to_check):
        """Створює новий об'єкт сесії та намагається перевірити URL для оновлення куків."""
        io_handler.print_message("Спроба створення нової сесії та обхід CF...")
        
        # 1. Створюємо абсолютно нову сесію
        new_session = self._create_session()
        
        try:
            # 2. Пробуємо одразу "прогріти" нову сесію
            new_session.get(url_to_check, timeout=30, **CF_BYPASS_PARAMS)
            
            # 3. Якщо успішно, замінюємо стару сесію на нову
            self.session = new_session
            io_handler.print_message("Сесія успішно відновлена!", color='GREEN')
            return True
        except Exception as e:
            io_handler.print_message(f"Не вдалося відновити сесію. {e}", color='RED')
            return False

    
    def check_url_head(self, url):
        """Виконує HEAD-запит для отримання заголовків, використовуючи імітацію."""
        try:
            # Тепер ми використовуємо self.session, який має збережені куки CF
            # та вказуємо impersonate для кожного запиту
            response = self.session.head(
                url, 
                timeout=15, 
                impersonate=BROWSER_IMPERSONATE, # <-- Додаємо імітацію
                allow_redirects=True
            )
            return response, response.status_code
        except Exception:
            return None, -1 # Помилка з'єднання/таймаут

    
    def get_filename_from_headers(self, response):
        """Витягує назву файлу (залишаємо без змін)."""
        cd = response.headers.get('Content-Disposition')
        if cd:
            match = re.search(r'filename\*?=(?:utf-8\'\')?"?([^"]+)"?', cd, re.I)
            if match:
                # Очищення та декодування, якщо потрібно (наприклад, %-кодування)
                return match.group(1).strip('"\' ')
        return os.path.basename(response.url.split('?')[0])
    
    
    def download_fileX(self, url, filename):
        """Виконує завантаження файлу."""
        io_handler.print_message(f"Розпочато скачування: {filename}")
        try:
            # Використовуємо GET-запит з імітацією
            with self.session.get(
                url, 
                stream=True, 
                timeout=30, 
                impersonate=BROWSER_IMPERSONATE # <-- Додаємо імітацію
            ) as r:
                r.raise_for_status()
                file_path = os.path.join(config.DOWNLOAD_DIR, filename)
                
                # ... (логіка запису файлу залишається без змін)
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                io_handler.print_message(f"Файл збережено до: {file_path}", color='GREEN')
        except Exception as e:
            io_handler.print_message(f"Не вдалося завантажити файл: {e}", color='RED')

    def download_fileY(self, url, filename):
        """
        Виконує завантаження файлу. 
        ВИПРАВЛЕНО: Прибрано with навколо self.session.get(), 
        залишено лише with навколо об'єкта відповіді (r).
        """
        io_handler.print_message(f"Розпочато скачування: {filename}")
        try:
            # 1. Виконуємо GET-запит (не використовуємо with тут)
            r = self.session.get(
                url, 
                stream=True, 
                timeout=30, 
                impersonate=BROWSER_IMPERSONATE
            )
            
            # 2. Використовуємо with r для гарантованого закриття з'єднання
            with r:
                r.raise_for_status()
                file_path = os.path.join(config.DOWNLOAD_DIR, filename)
                
                # ... (логіка запису файлу залишається без змін)
                with open(file_path, 'wb') as f:
                    # r.iter_content може видати помилку, якщо r.raise_for_status() пройде
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                io_handler.print_message(f"Файл збережено до: {file_path}", color='GREEN')
        except Exception as e:
            io_handler.print_message(f"Не вдалося завантажити файл: {e}", color='RED')

    def download_fileZ(self, url, filename):
        """
        Виконує завантаження файлу. 
        Розширено обробку винятків для діагностики помилок рівня CurlError.
        """
        io_handler.print_message(f"Розпочато скачування: {filename}")
        r = None # Ініціалізуємо змінну відповіді
        try:
            # 1. Виконуємо GET-запит (не використовуємо with тут)
            r = self.session.get(
                url, 
                stream=True, 
                timeout=30, 
                impersonate=BROWSER_IMPERSONATE
            )
            
            # 2. Використовуємо with r для гарантованого закриття з'єднання
            with r:
                r.raise_for_status()
                file_path = os.path.join(config.DOWNLOAD_DIR, filename)
                
                # ... (логіка запису файлу залишається без змін)
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                io_handler.print_message(f"Файл збережено до: {file_path}", color='GREEN')
        
        except CurlError as e:
            # Специфічне захоплення помилок рівня cURL (ConnectionError, Timeout тощо)
            io_handler.print_message(f"Не вдалося завантажити файл (CurlError): {e}", color='RED')
        
        except Exception as e:
            # Загальне захоплення. Виводимо тип помилки, щоб побачити, що саме сталося.
            error_type = type(e).__name__
            io_handler.print_message(f"Не вдалося завантажити файл ({error_type}): {e}", color='RED')

    def download_fileW(self, url, filename):
        """
        Виконує завантаження файлу. 
        Розширено обробку винятків для діагностики помилок рівня CurlError.
        """
        io_handler.print_message(f"Розпочато скачування: {filename}")
        r = None # Ініціалізуємо змінну відповіді
        try:
            # 1. Виконуємо GET-запит (не використовуємо with тут)
            r = self.session.get(
                url, 
                stream=True, 
                timeout=30, 
                impersonate=BROWSER_IMPERSONATE
            )
            
            # 2. Використовуємо with r для гарантованого закриття з'єднання
            with r:
                r.raise_for_status()
                file_path = os.path.join(config.DOWNLOAD_DIR, filename)
                
                # ... (логіка запису файлу залишається без змін)
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                io_handler.print_message(f"Файл збережено до: {file_path}", color='GREEN')
        
        except CurlError as e:
            # Специфічне захоплення помилок рівня cURL (ConnectionError, Timeout тощо)
            io_handler.print_message(f"Не вдалося завантажити файл (CurlError): {e}", color='RED')
        
        except Exception as e:
            # Загальне захоплення. Виводимо тип помилки, щоб побачити, що саме сталося.
            error_type = type(e).__name__
            io_handler.print_message(f"Не вдалося завантажити файл ({error_type}): {e}", color='RED')

    def download_file(self, url, filename):
        """
        Виконує завантаження файлу. 
        ВИПРАВЛЕНО: Прибрано with r: та додано r.close() у finally блоці.
        Це усуває AttributeError: __enter__, оскільки Response об'єкт curl_cffi 
        не підтримує контекстний менеджер для цього випадку.
        """
        io_handler.print_message(f"Розпочато скачування: {filename}")
        r = None # Ініціалізуємо змінну відповіді
        try:
            # 1. Виконуємо GET-запит (для потокового завантаження)
            r = self.session.get(
                url, 
                stream=True, 
                timeout=60, 
                impersonate=BROWSER_IMPERSONATE
            )
            
            # 2. Перевіряємо статус коду
            r.raise_for_status()
            file_path = os.path.join(config.DOWNLOAD_DIR, filename)
            
            # 3. Записуємо файл
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            io_handler.print_message(f"Файл збережено до: {file_path}", color='GREEN')
        
        except CurlError as e:
            # Специфічне захоплення помилок рівня cURL (ConnectionError, Timeout тощо)
            io_handler.print_message(f"Не вдалося завантажити файл (CurlError): {e}", color='RED')
        
        except Exception as e:
            # Загальне захоплення. Виводимо тип помилки, щоб побачити, що саме сталося.
            error_type = type(e).__name__
            io_handler.print_message(f"Не вдалося завантажити файл ({error_type}): {e}", color='RED')
        
        finally:
            # Обов'язково закриваємо з'єднання, якщо об'єкт r було створено
            if r:
                r.close()
