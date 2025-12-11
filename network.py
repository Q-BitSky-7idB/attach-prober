# network.py

import re
import os
import time
from urllib.parse import urlparse
# Змінюємо імпорт: використовуємо requests з curl_cffi
from curl_cffi import requests # <-- НОВА БІБЛІОТЕКА
# Додаємо імпорт для специфічної помилки cURL, яка може бути причиною
#from curl_cffi.requests import CurlError 
from curl_cffi import CurlError

import config
import console as io
import context
import system

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
    
    def __init__(self, initial_url=None): # <--- ЦЕЙ АРГУМЕНТ ПОТРІБЕН!
        # Сесія curl_cffi створюється лише один раз
        #global CURRENT
        self.session = self._create_session()
        
        # 1. Атрибут для ТИПІЗАЦІЇ: Домени, які погано обробляють HEAD
        #self.non_standard_head_domains = {} 
        # 2. Атрибут для ПРОФІЛЮВАННЯ: Зберігання базової затримки домену (latency)
        #self.domain_base_latency = {} 
        
        # Проводимо початкове "прогрівання"
        #self._cf_bypass(context.CURRENT.URL)
        if context.CURRENT is not None:
             self._cf_bypass(context.CURRENT.URL)
        else:
             # Обробка випадку, коли CURRENT ще не ініціалізовано
             # Можна передати initial_url як дефолтний
             pass


    def _create_session(self):
        """Створює новий екземпляр сесії curl_cffi."""
        # curl_cffi дозволяє створити сесію, як і requests
        s = requests.Session()
        return s

    def _cf_bypass(self, url):
        """Виконує початковий GET-запит для обходу CF та отримання куків без скачування контенту."""
        io.printf("[·] Спроба обходу CloudFlare...")
        
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
            
            io.prints(f"\r{' ' * 42}\r[+] Обхід CF успішний!", color='GREEN')
            return True
            
        except Exception as e:
            io.prints(f"\r{' ' * 42}\r[!] обійти CF не вдалось! Причина:\n{e}", color='RED')
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
        io.prints(f"[/] Розпочато профілювання базової швидкості для {domain}...", color='MAGENTA')
        
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
                io.prints(
                    f"[+] Профілювання завершено. Базова затримка: {base_latency:.2f} сек. (Таймаут: {self._get_timeout(domain):.2f})", 
                    color='MAGENTA'
                )
                return base_latency
            else:
                io.prints(
                    f"[!] Профілювання не вдалося (статус {response.status_code}). Використовуємо таймаут за замовчуванням.", 
                    color='YELLOW'
                )
                return None
            
        except Exception as e:
            io.prints(f"[!] Профілювання не вдалося. {e}", color='RED')
            return None

    def renew_session(self, url_to_check):
        """Створює новий об'єкт сесії та намагається перевірити URL для оновлення куків."""
        io.prints("[·] Спроба створення нової сесії та обхід CF...")
        
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
            io.prints("[+] Сесія успішно відновлена!", color='GREEN')
            return True
        except Exception as e:
            io.prints(f"[!] Не вдалося відновити сесію:\n{e}", color='RED')
            return False

    
    # --- МЕТОДИ ПЕРЕВІРКИ URL ---

    def check_url_head(self, url=None):
        """Виконує HEAD-запит, використовуючи адаптивний таймаут."""
        if context.CURRENT is not None:
          url = context.CURRENT.URL
        else:
          return
        if not url:
          raise Exception("EMPTY_URL")
        #global context.CURRENT
        
        try:
            #domain = urllib.parse.urlparse(url).netloc
            #current_timeout = self._get_timeout(domain)
            current_timeout = 30
            
            #io_handler.print_msg(f"Використовуємо таймаут: {current_timeout:.2f} сек. (HEAD)", color='CYAN') 
            response = self.session.head(
                url, 
                timeout=current_timeout, 
                impersonate=BROWSER_IMPERSONATE,
                allow_redirects=True
            )
            #response_string = response.text
            #if response.status_code == 403:
            context.CURRENT.Status = response.status_code
            context.CURRENT.Body = response
            #print(f"\nX:{response.status_code}\nY:{response.headers};\n")
            #io.get_action_from_user()
            return response, response.status_code
        except Exception as e:
            io.prints(f"Network(HEAD)Error:\n{e}")
            return None, -1

    def _check_url_with_range(self, url):
        """
        Виконує GET-запит із заголовком Range: bytes=0-1, 
        використовуючи адаптивний таймаут. Це резервний метод.
        """
        try:
            domain = urlparse(url).netloc
            current_timeout = self._get_timeout(domain)
            
            io_handler.prints(f"Використовуємо таймаут: {current_timeout:.2f} сек. (Range)", color='BLUE') 

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
            io.prints(f"GET з Range також не вдався. {e}", color='RED')
            return None, -1


    def check_url_safe(self, url):
        """
        ⚡️ АДАПТИВНА ПЕРЕВІРКА: Головний метод.
        1. Профілює швидкість (якщо домен новий).
        2. Використовує HEAD, але переключається на GET+Range для "проблемних" доменів.
        """
        try:
            domain = urlparse(url).netloc
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
        io.prints(f"HEAD-запит для {domain} зазнав невдачі. Вважаємо його 'нестандартним'.", color='YELLOW')
        
        # 4. Класифікація (Типізація)
        self.non_standard_head_domains[domain] = True
        io.prints(f"Домен {domain} додано до 'чорного списку'. Повторна перевірка...", color='RED')
        
        # 5. Повторюємо перевірку з Резервним (Range) методом
        return self._check_url_with_range(url)
    
    
    # ... (download_file залишаються без змін) ...

    def download_file(self, url=None, filename=None):
        """
        Виконує завантаження файлу. 
        ВИПРАВЛЕНО: Прибрано with r: та додано r.close() у finally блоці.
        Це усуває AttributeError: __enter__, оскільки Response об'єкт curl_cffi 
        не підтримує контекстний менеджер для цього випадку.
        """
        if not url:
            url=context.CURRENT.URL
        if not filename:
            filename=context.CURRENT.FileName
        #io.printf(f"Розпочато скачування: {filename}")
        r = None # Ініціалізуємо змінну відповіді
        
        expected_size = getattr(context.CURRENT, 'Size', 0)
        
        try:
            # 1. Виконуємо GET-запит (для потокового завантаження)
            r = self.session.get(
                url, 
                stream=True, 
                timeout=60, 
                impersonate=BROWSER_IMPERSONATE
            )
            
            # ВИПРАВЛЕНО: Прибрано with навколо self.session.get(), 
            # залишено лише with навколо об'єкта відповіді (r).
             # # #
            # 2. Використовуємо with r для гарантованого закриття з'єднання
            #with r:
            #    r.raise_for_status()
            #    ...
            
            # 2. Перевіряємо статус коду
            r.raise_for_status()
            #file_path = os.path.join(config.DOWNLOAD_DIR, filename)
            
            # Виходить він пише по чанку разом у файл
            # 3. Записуємо файл
            #with open(file_path, 'wb') as f:
            #    for chunk in r.iter_content(chunk_size=8192):
            #        f.write(chunk)
            
            # 3. ДЕЛЕГУЄМО ЗАПИС У SYSTEM
            # Ми передаємо генератор (r.iter_content), а не байти.
            # system.py буде "тягнути" дані з цього генератора.
            stream_gen = r.iter_content(chunk_size=8192)
            result = system.save_stream_content(
                stream_iterator=stream_gen,
                filename=filename,
                expected_size=expected_size
            )
            
            return result
            
            #io.printf(f"Файл збережено до: {file_path}", color='GREEN')
            #return True
        
        except CurlError as e:
            # Специфічне захоплення помилок рівня cURL (ConnectionError, Timeout тощо)
            io.prints(f"Не вдалося завантажити файл (CurlError):\n{e}", color='RED')
            return False
        
        except Exception as e:
            # Загальне захоплення. Виводимо тип помилки, щоб побачити, що саме сталося.
            error_type = type(e).__name__
            io.prints(f"Не вдалося завантажити файл ({error_type}):\n{e}", color='RED')
            return False
            
        finally:
            # Обов'язково закриваємо з'єднання, якщо об'єкт r було створено
            if r:
                r.close()
