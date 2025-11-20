# history.py

# Поки що треба, що воно вело історію хочаб в середині себе. Проте з можоивістю 
# екстракції. Постіний кравлінг файлових посилань може бути нетиповим і підозрілим 
# трафіком, тому добре було б зайвий раз не чіпати посилання які пройшли 
# Пізніше, добре було б синхронізувати отримані дані з іншими застосунками або системами
# через спільне API або конкретний формат кінцевих файлів

class ScannerHistory:
    """Клас для зберігання історії сканування."""
    def __init__(self):
        self.successful_urls = []
        self.error_urls = []
        self.last_checked_url = None

    def add_success(self, url):
        """Додає успішно оброблений URL."""
        self.successful_urls.append(url)
        self.last_checked_url = url

    def add_error(self, url, status_code):
        """Додає URL, що викликав помилку."""
        self.error_urls.append((url, status_code))
        self.last_checked_url = url
        
    def get_last_successful(self):
        """Повертає останній успішний URL для буфера обміну."""
        return self.successful_urls[-1] if self.successful_urls else None
