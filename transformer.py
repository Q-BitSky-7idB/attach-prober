import config
import console as io
import re

# Модуль для розбору вводу\воводу інформації яку треба обробляти

def get_meta_from_headers(response):
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
        match = re.search(config.FILENAME_PATTERN, cd, re.I)
        if match:
            filename = match.group(1).strip('"\' ')
        
        # Якщо назва не знайдена в Content-Disposition, беремо її з URL
        if not filename:
            filename = os.path.basename(response.url.split('?')[0])

    # 3. Повернення обох значень
    return filename, content_length

def print_history_in_preview(id, status, filename, length):
    if status==200:
        io_handler.print_msg(f"\n{config.URL_SUFIX}{id} : {length: >11} : {filename}", color='CYANB')
    else:
        io_handler.print_msg(f"\n{config.URL_SUFIX}{id} : Помилка ({status}) або з'єднання/таймаут.", color='REDB')
        
def print_result_in_queue(id, status, filename="[None]", length=0):
    #if not filename:
    #    filename = "[Denied]"
    if not length:
        length = 0
    if status == 200:
        clr = 'GREENB'
    else:
        clr = 'YELLOWB'
    io_handler.overwrite_msg(f"{config.URL_SUFIX}{id} : {length: >11} : {filename}\n", color=clr)

def rewrite_output(id, status, filename, length, act):
    if act == 'DOWNLOAD':
        # case 'DOWNLOAD':
        io_handler.print_msg(f"\r\033M{config.URL_SUFIX}{id} : {length: >11} : {filename} => Downloaded.", color='GREEN')
    
    else:
        # case _: (Використовуємо else для всіх інших випадків)
        if status == 200:
            io_handler.print_msg(f"\r\033M{config.URL_SUFIX}{id} : {length: >11} : {filename}", color='GREEN')
        else:
            io_handler.print_msg(f"\r\033M{config.URL_SUFIX}{id} : Помилка ({status}) : Файл не отримано!", color='RED')

# Примітка: Додаємо current_id як аргумент
def get_options(mode, current_id=None):
    """
    Повертає рядок з опціями дій для користувача залежно від поточного режиму.
    """
    
    if mode == 'act_normal':
        # act_normal: знайдено файл (200 OK)
        if current_id is not None:
            return f"Оберіть дію (E/D: продовжити, G: скачати, C/Q: вийти) [ID: {current_id}]: "
        else:
            return "Оберіть дію (E/D: продовжити, G: скачати, C/Q: вийти): "
            
    elif mode == 'act_after':
        # act_after: (режим після завантаження або іншої дії, що вимагає тиші)
        return f""
        
    elif mode == 'act_error':
        # act_error: помилка 403, таймаут (-1)
        return f"[T/Е] - Обхід, [D/В] - Декремент, [E/У] - Інкремент, [C/Q] - Вийти: "
        
    else:
        # _: (Інші випадки)
        return "PRESS_ANY: "
