# session_manager.py

import re
import os
import time
import urllib.parse
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

# КОНСТАНТИ АДАПТИВНОСТІ
DEFAULT_TIMEOUT = 15 # Початковий таймаут за замовчуванням
TIMEOUT_BUFFER_SEC = 5 # Додатковий буфер часу поверх базової затримки


class FileScannerSession:
    """Керує сесією curl_cffi та операціями з файлами."""
    
    def __init__(self, initial_url_to_check): # <--- ЦЕЙ АРГУМЕНТ ПОТРІБЕН!
        # Сесія curl_cffi створюється лише один раз
        self.session = self._create_session()
        
        # 1. Атрибут для ТИПІЗАЦІЇ: Домени, які погано обробляють HEAD
        self.non_standard_head_domains = {} 
        # 2. Атрибут для ПРОФІЛЮВАННЯ: Зберігання базової затримки домену (latency)
        self.domain_base_latency = {} 
        
        # Проводимо початкове "прогрівання"
        self._warmup_session(initial_url_to_check)


    def _create_session(self):
        """Створює новий екземпляр сесії curl_cffi."""
        # curl_cffi дозволяє створити сесію, як і requests
        s = requests.Session()
        return s

    def _warmup_session(self, url):
        """Виконує початковий GET-запит для обходу CF та отримання куків без скачування контенту."""
        io_handler.print_msg("[·] Спроба 'прогріву' сесії... Обхід CF!")
        
        response = None
        # Використовуємо self.session для збереження куків
        try:
            # Виконуємо GET, щоб переконатися, що JS-Challenge пройдено і куки збережені
            # Виконуємо GET з stream=True, щоб запобігти автоматичному завантаженню тіла відповіді.
            response = self.session.get(
                url, 
                timeout=DEFAULT_TIMEOUT, 
                stream=True,  
                **CF_BYPASS_PARAMS
            )
            # Якщо CF повертає JS-Challenge, curl_cffi обробляє його та встановлює куки.
            # Нам не потрібно читати response.content, куки вже встановлені.
            
            io_handler.print_msg(f"\033M\r{' ' * 41}\r[+] Сесія успішно 'прогріта'!", color='GREEN')
            return True
            
        except Exception as e:
            io_handler.print_msg(f"[!] Не вдалося 'прогріти' сесію при запуску: \n{e}", color='RED')
            return False
        
        finally:
            # Закриваємо з'єднання, щоб переконатися, що великий файл не завантажується
            if response:
                response.close()


    # --- МЕХАНІКА АДАПТИВНОГО ТАЙМАУТУ ---

    def _get_timeout(self, domain):
        """Повертає адаптивний таймаут для домену."""
        base_latency = self.domain_base_latency.get(domain)
        
        if base_latency is not None:
            # Адаптивний таймаут = (Базова затримка + Буфер)
            return base_latency + TIMEOUT_BUFFER_SEC
        else:
            # Таймаут за замовчуванням
            return DEFAULT_TIMEOUT


    def _profile_server_speed(self, url, domain):
        """
        Вимірює базову затримку сервера за допомогою GET+Range.
        Результат зберігається у self.domain_base_latency.
        rem:	⌛️ ✅ ⚠️ ❌ | 😎 🎪 ❓ ❗
        """
        io_handler.print_msg(f"[/] Розпочато профілювання базової швидкості для {domain}...", color='MAGENTA')
        
        start_time = time.time()
        
        try:
            # Використовуємо найнадійніший метод - GET з Range: bytes=0-1
            custom_headers = {'Range': 'bytes=0-1'}
            response = self.session.get(
                url, 
                timeout=30, # Використовуємо більший таймаут для первинного профілювання
                impersonate=BROWSER_IMPERSONATE,
                allow_redirects=True,
                headers=custom_headers
            )
            
            end_time = time.time()
            base_latency = end_time - start_time
            
            # Перевіряємо статус (206, 200, 3xx). 
            if 200 <= response.status_code < 400:
                self.domain_base_latency[domain] = base_latency
                io_handler.print_msg(
                    f"[+] Профілювання завершено. Базова затримка: {base_latency:.2f} сек. (Таймаут: {self._get_timeout(domain):.2f})", 
                    color='MAGENTA'
                )
                return base_latency
            else:
                io_handler.print_msg(
                    f"[!] Профілювання не вдалося (статус {response.status_code}). Використовуємо таймаут за замовчуванням.", 
                    color='YELLOW'
                )
                return None
            
        except Exception as e:
            io_handler.print_msg(f"[!] Профілювання не вдалося. {e}", color='RED')
            return None

    def renew_session(self, url_to_check):
        """Створює новий об'єкт сесії та намагається перевірити URL для оновлення куків."""
        io_handler.print_msg("[·] Спроба створення нової сесії та обхід CF...")
        
        # 1. Створюємо абсолютно нову сесію
        new_session = self._create_session()
        
        # Використовуємо адаптований _warmup_session для "прогріву" нової сесії
        # Примітка: Логіка renew_session не перевіряє домен на профілювання
        # для простоти, оскільки вона викликається лише при 403.
        
        response = None
        try:
            # Використовуємо GET з stream=True, як і в _warmup_session
            response = new_session.get(
                url_to_check, 
                timeout=30, 
                stream=True, 
                **CF_BYPASS_PARAMS
            )
            response.close() # Закриваємо з'єднання
            
            # Якщо успішно, замінюємо стару сесію на нову
            self.session = new_session
            io_handler.print_msg("[+] Сесія успішно відновлена!", color='GREEN')
            return True
        except Exception as e:
            io_handler.print_msg(f"[!] Не вдалося відновити сесію:\n{e}", color='RED')
            return False

    
    # --- МЕТОДИ ПЕРЕВІРКИ URL ---

    def check_url_head(self, url):
        """Виконує HEAD-запит, використовуючи адаптивний таймаут."""
        
        try:
            domain = urllib.parse.urlparse(url).netloc
            #current_timeout = self._get_timeout(domain)
            current_timeout = 30
            
            #io_handler.print_msg(f"Використовуємо таймаут: {current_timeout:.2f} сек. (HEAD)", color='CYAN') 
            response = self.session.head(
                url, 
                timeout=current_timeout, 
                impersonate=BROWSER_IMPERSONATE,
                allow_redirects=True
            )
            return response, response.status_code
        except Exception:
            return None, -1

    def _check_url_with_range(self, url):
        """
        Виконує GET-запит із заголовком Range: bytes=0-1, 
        використовуючи адаптивний таймаут. Це резервний метод.
        """
        try:
            domain = urllib.parse.urlparse(url).netloc
            current_timeout = self._get_timeout(domain)
            
            io_handler.print_message(f"Використовуємо таймаут: {current_timeout:.2f} сек. (Range)", color='BLUE') 

            custom_headers = {'Range': 'bytes=0-1'}
            response = self.session.get(
                url, 
                timeout=current_timeout, 
                impersonate=BROWSER_IMPERSONATE,
                allow_redirects=True,
                headers=custom_headers 
            )

            return response, response.status_code

        except Exception as e:
            io_handler.print_message(f"GET з Range також не вдався. {e}", color='RED')
            return None, -1


    def check_url_safe(self, url):
        """
        ⚡️ АДАПТИВНА ПЕРЕВІРКА: Головний метод.
        1. Профілює швидкість (якщо домен новий).
        2. Використовує HEAD, але переключається на GET+Range для "проблемних" доменів.
        """
        try:
            domain = urllib.parse.urlparse(url).netloc
        except:
            domain = url
            
        # 0. ПРОФІЛЮВАННЯ: Якщо домен ще не профілювався, робимо це один раз
        if domain not in self.domain_base_latency:
            self._profile_server_speed(url, domain)

        # 1. Перевірка Типу Сервера
        if domain in self.non_standard_head_domains:
            return self._check_url_with_range(url)
        
        # 2. Перша спроба: HEAD
        response, status = self.check_url_head(url)
        
        # 3. Аналіз Результату HEAD
        if status != -1:
            return response, status

        # Помилка: (-1), яка є тайм-аутом або іншою помилкою. Типізація
        io_handler.print_message(f"HEAD-запит для {domain} зазнав невдачі. Вважаємо його 'нестандартним'.", color='YELLOW')
        
        # 4. Класифікація (Типізація)
        self.non_standard_head_domains[domain] = True
        io_handler.print_message(f"Домен {domain} додано до 'чорного списку'. Повторна перевірка...", color='RED')
        
        # 5. Повторюємо перевірку з Резервним (Range) методом
        return self._check_url_with_range(url)
    
    
    # ... (get_filename_from_headers та download_file залишаються без змін) ...
    

    def get_meta_from_headers(self, response):
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
            match = re.search(r'filename\*?=(?:utf-8\'\')?"?([^"]+)"?', cd, re.I)
            if match:
                filename = match.group(1).strip('"\' ')
        
        # Якщо назва не знайдена в Content-Disposition, беремо її з URL
        if not filename:
            filename = os.path.basename(response.url.split('?')[0])

        # 3. Повернення обох значень
        return filename, content_length
        
        
    
    def download_fileX(self, url, filename):
        """Виконує завантаження файлу."""
        io_handler.print_msg(f"Розпочато скачування: {filename}")
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
                
                io_handler.print_msg(f"Файл збережено до: {file_path}", color='GREEN')
        except Exception as e:
            io_handler.print_msg(f"Не вдалося завантажити файл: {e}", color='RED')

    def download_fileY(self, url, filename):
        """
        Виконує завантаження файлу. 
        ВИПРАВЛЕНО: Прибрано with навколо self.session.get(), 
        залишено лише with навколо об'єкта відповіді (r).
        """
        io_handler.print_msg(f"Розпочато скачування: {filename}")
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
                
                io_handler.print_msg(f"Файл збережено до: {file_path}", color='GREEN')
        except Exception as e:
            io_handler.print_msg(f"Не вдалося завантажити файл: {e}", color='RED')

    def download_fileZ(self, url, filename):
        """
        Виконує завантаження файлу. 
        Розширено обробку винятків для діагностики помилок рівня CurlError.
        """
        io_handler.print_msg(f"Розпочато скачування: {filename}")
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
                
                io_handler.print_msg(f"Файл збережено до: {file_path}", color='GREEN')
        
        except CurlError as e:
            # Специфічне захоплення помилок рівня cURL (ConnectionError, Timeout тощо)
            io_handler.print_msg(f"Не вдалося завантажити файл (CurlError): {e}", color='RED')
        
        except Exception as e:
            # Загальне захоплення. Виводимо тип помилки, щоб побачити, що саме сталося.
            error_type = type(e).__name__
            io_handler.print_msg(f"Не вдалося завантажити файл ({error_type}): {e}", color='RED')

    def download_fileW(self, url, filename):
        """
        Виконує завантаження файлу. 
        Розширено обробку винятків для діагностики помилок рівня CurlError.
        """
        io_handler.print_msg(f"Розпочато скачування: {filename}")
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
                
                io_handler.print_msg(f"Файл збережено до: {file_path}", color='GREEN')
        
        except CurlError as e:
            # Специфічне захоплення помилок рівня cURL (ConnectionError, Timeout тощо)
            io_handler.print_msg(f"Не вдалося завантажити файл (CurlError): {e}", color='RED')
        
        except Exception as e:
            # Загальне захоплення. Виводимо тип помилки, щоб побачити, що саме сталося.
            error_type = type(e).__name__
            io_handler.print_msg(f"Не вдалося завантажити файл ({error_type}): {e}", color='RED')

    def download_file(self, url, filename):
        """
        Виконує завантаження файлу. 
        ВИПРАВЛЕНО: Прибрано with r: та додано r.close() у finally блоці.
        Це усуває AttributeError: __enter__, оскільки Response об'єкт curl_cffi 
        не підтримує контекстний менеджер для цього випадку.
        """
        io_handler.print_msg(f"Розпочато скачування: {filename}")
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
            
            io_handler.print_msg(f"Файл збережено до: {file_path}", color='GREEN')
        
        except CurlError as e:
            # Специфічне захоплення помилок рівня cURL (ConnectionError, Timeout тощо)
            io_handler.print_msg(f"Не вдалося завантажити файл (CurlError): {e}", color='RED')
        
        except Exception as e:
            # Загальне захоплення. Виводимо тип помилки, щоб побачити, що саме сталося.
            error_type = type(e).__name__
            io_handler.print_msg(f"Не вдалося завантажити файл ({error_type}): {e}", color='RED')
        
        finally:
            # Обов'язково закриваємо з'єднання, якщо об'єкт r було створено
            if r:
                r.close()
