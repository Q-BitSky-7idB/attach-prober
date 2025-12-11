# session_manager.py

import importlib
import re
import os
import cloudscraper

import config
import io_handler # Потрібен для виводу повідомлень під час обходу

class FileScannerSession:
    """Керує сесією cloudscraper та операціями з файлами."""
    
    def __init__(self):
        self.scraper = self._create_scraper()

    def _create_scraper(self):
        """Створює новий екземпляр cloudscraper, ініціюючи новий обхід CF."""
        return cloudscraper.create_scraper(**config.SCRAPER_PARAMS)

    def _create_and_reload_scraper(self, url_to_check):
        """
        Перезавантажує модуль cloudscraper, потім створює і прогріває новий скрепер.
        """
        try:
            # 1. Перезавантаження модуля cloudscraper
            io_handler.print_message("Перезавантаження модуля cloudscraper...", color='YELLOW')
            importlib.reload(cloudscraper)
            
            # 2. Створення нового скрепера (що тепер може використовувати оновлений стан)
            new_scraper = cloudscraper.create_scraper(**config.SCRAPER_PARAMS)
            
            # 3. 'Прогрівання' (обхід CF)
            new_scraper.head(url_to_check, allow_redirects=True, timeout=30)
            
            return new_scraper
        except Exception as e:
            io_handler.print_message(f"Критична помилка під час перезавантаження/обходу: {e}", color='RED')
            return None

    def renew_session(self, url_to_check):
        """Створює новий скрепер і намагається перевірити URL для оновлення куків."""
        io_handler.print_message("Спроба створення нового екземпляра Scraper (Обхід CF)...")
        try:
            if self.scraper and hasattr(self.scraper, 'close'):
                self.scraper.close()
                io_handler.print_message("Стара сесія scraper закрита.", color='YELLOW')
        except Exception:
            pass # Ігноруємо помилки закриття

        #new_scraper = self._create_scraper()
        new_scraper = self._create_and_reload_scraper(url_to_check)
        
        try:
            # Спробуємо одразу перевірити цільовий URL з новим скрепером
            resp = new_scraper.head(url_to_check, allow_redirects=True, timeout=30)

            self.scraper = new_scraper
            io_handler.print_message("Сесія успішно відновлена!", color='GREEN')
            io_handler.print_message(f"{resp.status_code}: {resp.headers}", color='GREEN')
            return True
        except Exception as e:
            io_handler.print_message(f"Не вдалося відновити сесію. Спробуйте пізніше. {e}", color='RED')
            # Важливо: якщо обхід не вдався, закрийте і цей новий об'єкт!
            if hasattr(new_scraper, 'close'):
                new_scraper.close()
            return False

    def check_url_head(self, url):
        """Виконує HEAD-запит для отримання заголовків."""
        try:
            response = self.scraper.head(url, allow_redirects=True, timeout=15)
            return response, response.status_code
        except Exception:
            return None, -1 # Помилка з'єднання/таймаут

    def get_filename_from_headers(self, response):
        """Витягує назву файлу (дублювання з io_handler, але логічно належить сюди)."""
        cd = response.headers.get('Content-Disposition')
        if cd:
            match = re.search(r'filename\*?=(?:utf-8\'\')?"?([^"]+)"?', cd, re.I)
            if match:
                return match.group(1).strip('"\' ')
        return os.path.basename(response.url.split('?')[0])
    
    def download_file(self, url, filename):
        """Виконує завантаження файлу."""
        io_handler.print_message(f"Розпочато скачування: {filename}")
        try:
            with self.scraper.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                file_path = os.path.join(config.DOWNLOAD_DIR, filename)
                
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                io_handler.print_message(f"Файл збережено до: {file_path}", color='GREEN')
        except Exception as e:
            io_handler.print_message(f"Не вдалося завантажити файл: {e}", color='RED')
