import cloudscraper

scraper = cloudscraper.create_scraper() # Створюємо інстанс, який обходить CF
file_url = "https://itorrents-igruha.org/engine/download.php?id=90881"

# Виконуємо запит HEAD для отримання лише заголовків
response = scraper.head(file_url, allow_redirects=True)

if response.status_code == 200:
    # Отримання назви файлу із заголовка Content-Disposition
    filename = response.headers.get('Content-Disposition')
    print(f"Статус: Успішно (200)")
    print(f"Content-Disposition: {filename}")
else:
    print(f"Помилка: {response.status_code}. Не вдалося обійти Cloudflare.")