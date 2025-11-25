import config
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
        io_handler.print_msg(f"\n{URL_ID_SUFIX}{id} : {length: >11} : {filename}", color='CYANB')
    else:
        io_handler.print_msg(f"\n{URL_ID_SUFIX}{id} : Помилка ({status}) або з'єднання/таймаут.", color='REDB')
        
def print_result_in_queue(id, status, filename, length):
    io_handler.overwrite_msg(f"{URL_ID_SUFIX}{id} : {length: >11} : {filename}\n", color='GREENB')

def rewrite_output(id, status, filename, length, act):
    match act:
        case 'DOWNLOAD':
            io_handler.print_msg(f"\r\033M{URL_ID_SUFIX}{id} : {length: >11} : {filename} => Downloaded.\n", color='GREEN')
        case _:
            if status == 200:
                io_handler.print_msg(f"\r\033M{URL_ID_SUFIX}{id} : {length: >11} : {filename}\n", color='GREEN')
            else:
                io_handler.print_msg(f"\r\033M{URL_ID_SUFIX}{id} : Помилка ({status}) : Файл не отримано!\n", color='RED')

def get_options(mode):
    match mode:
        case 'act_normal':
            return f"Оберіть дію (E/D: продовжити, G: скачати, C/Q: вийти) [ID: {current_id}]: "
        case 'act_after':
            return f""
        case 'act_error':
            return f"[T/Е] - Обхід, [D/В] - Декремент, [E/К] - Інкремент, [C/Q] - Вийти: "
        case _:
            return "PRESS_ANY: "