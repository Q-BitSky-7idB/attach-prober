# history.py

import re
from urllib.parse import urlparse
import io_handler

# Поки що треба, що воно вело історію хочаб в середині себе. Проте з можоивістю 
# екстракції. Постіний кравлінг файлових посилань може бути нетиповим і підозрілим 
# трафіком, тому добре було б зайвий раз не чіпати посилання які пройшли 
# Пізніше, добре було б синхронізувати отримані дані з іншими застосунками або системами
# через спільне API або конкретний формат кінцевих файлів

class HistoryEntry:
    """Структура для зберігання результату обробки одного ID."""
    def __init__(self, url, status_code, filename=None, length=None, is_cached=False):
        self.url = url
        self.status_code = status_code
        self.filename = filename
        self.content_length = length
        self.is_cached = is_cached # Чи було це завантажено з кешу/історії

class ScannerHistory:
    """Клас для зберігання історії сканування."""
    def __init__(self, url):
        self.successful_urls = []
        self.error_urls = []
        self.processed_results = {} # Новий словник: {id: HistoryEntry}
        self.last_checked_url = None
        parsed_url = urlparse(url)
        uri_path = parsed_url.path
        domain = parsed_url.netloc
        numbers = re.findall(r'\d+', uri_path)
        if numbers:
            # Перший знайдений числовий індекс
            first_index = int(numbers[0])
        else:
            first_index = -1
        io_handler.print_msg(f"[+] URL's history for [${domain}] started* from file index ${first_index}.")

    def add_success(self, url):
        """Додає успішно оброблений URL."""
        self.successful_urls.append(url)
        self.last_checked_url = url

    def add_error(self, url, status_code):
        """Додає URL, що викликав помилку."""
        self.error_urls.append((url, status_code))
        self.last_checked_url = url
        
    def add_result(self, id, url, status_code, filename=None, length=None, is_cached=False):
        """Додає або оновлює результат обробки для певного ID."""
        entry = HistoryEntry(url, status_code, filename, length, is_cached)
        self.processed_results[id] = entry
        
        if status_code == 200:
            if url not in self.successful_urls: # Уникаємо дублікатів при повторній обробці
                self.successful_urls.append(url)
        elif not status_code == 200:
             # Додаємо URL помилки, якщо це не 404
             if not any(item[0] == url for item in self.error_urls):
                self.error_urls.append((url, status_code)) 

        self.last_checked_url = url
        
    def get_result(self, id):
        """Повертає результат обробки для певного ID з історії, або None."""
        return self.processed_results.get(id)

    def get_last_successful(self):
        """Повертає останній успішний URL для буфера обміну."""
        return self.successful_urls[-1] if self.successful_urls else None
