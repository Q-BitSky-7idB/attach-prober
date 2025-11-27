import config
import io_handler
import re

# Модуль для розбору вводу\воводу інформації яку треба обробляти

def parse_url_args(args):
    """Розбирає URL на префікс, ID та постікс."""
    match = re.search(config.URL_ID_PATTERN, args, re.I)
    if not match:
        raise ValueError("Не вдалося знайти шаблон 'id=[number]' у посиланні.")
    
    return match.group(1), int(match.group(2)), match.group(3)

def get_target_url(prefix, current_id, suffix):
    """Складає цільовий URL."""
    return f"{prefix}{current_id}{suffix}"

def print_history_in_preview(id, status, filename, length):
    if status==200:
        io_handler.print_msg(f"\n{config.URL_ID_SUFIX}{id} : {length: >11} : {filename}", color='CYANB')
    else:
        io_handler.print_msg(f"\n{config.URL_ID_SUFIX}{id} : Помилка ({status}) або з'єднання/таймаут.", color='REDB')
        
def print_result_in_queue(id, status, filename="[None]", length=0):
    #if not filename:
    #    filename = "[Denied]"
    if not length:
        length = 0
    if status == 200:
        clr = 'GREENB'
    else:
        clr = 'YELLOWB'
    io_handler.overwrite_msg(f"{config.URL_ID_SUFIX}{id} : {length: >11} : {filename}\n", color=clr)

def rewrite_output(id, status, filename, length, act):
    if act == 'DOWNLOAD':
        # case 'DOWNLOAD':
        io_handler.print_msg(f"\r\033M{config.URL_ID_SUFIX}{id} : {length: >11} : {filename} => Downloaded.", color='GREEN')
    
    else:
        # case _: (Використовуємо else для всіх інших випадків)
        if status == 200:
            io_handler.print_msg(f"\r\033M{config.URL_ID_SUFIX}{id} : {length: >11} : {filename}", color='GREEN')
        else:
            io_handler.print_msg(f"\r\033M{config.URL_ID_SUFIX}{id} : Помилка ({status}) : Файл не отримано!", color='RED')

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
