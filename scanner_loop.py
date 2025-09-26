# scanner_loop.py

import sys
import pyperclip
from . import io_handler
from . import history
from . import session_manager
from . import config

def parse_url_args(url):
    """Розбирає URL на префікс, ID та суфікс."""
    match = re.search(config.URL_ID_PATTERN, url, re.I)
    if not match:
        raise ValueError("Не вдалося знайти шаблон 'id=[number]' у посиланні.")
    
    return match.group(1), int(match.group(2)), match.group(3)

def get_target_url(prefix, current_id, suffix):
    """Складає цільовий URL."""
    return f"{prefix}{current_id}{suffix}"

def run_scanner_loop(initial_url):
    """Основний цикл сканування та взаємодії з користувачем."""
    
    # Ініціалізація
    try:
        base_url_prefix, current_id, base_url_suffix = parse_url_args(initial_url)
    except ValueError as e:
        io_handler.print_message(f"Помилка: {e}", color='RED')
        return

    session = session_manager.FileScannerSession()
    history_tracker = history.ScannerHistory()
    
    io_handler.print_message(f"Базове посилання: {base_url_prefix}**[ID]**{base_url_suffix}")
    io_handler.print_message(f"Папка завантажень: {config.DOWNLOAD_DIR}")

    # Початкова перевірка сесії
    try:
        session.check_url_head(get_target_url(base_url_prefix, current_id, base_url_suffix))
        io_handler.print_message("Сесія ініціалізована.")
    except Exception:
        io_handler.print_message("Початкова перевірка не пройшла. Спробуйте 't' (обхід) пізніше.", color='YELLOW')


    while True:
        if current_id < 0:
            break
            
        target_url = get_target_url(base_url_prefix, current_id, base_url_suffix)
        history_tracker.last_checked_url = target_url # Оновлюємо останній перевірений
        
        # --- ВИКОНАННЯ ЗАПИТУ ---
        response, status_code = session.check_url_head(target_url)

        # --- ОБРОБКА КОДІВ ---
        if status_code == 200:
            filename = session.get_filename_from_headers(response)
            history_tracker.add_success(target_url)

            io_handler.print_message(f"\nID-{current_id} : Файл знайдено: {filename}", color='GREEN')
            
            options_str = f"Оберіть дію (c/r: продовжити, d: скачати, s/q: вийти) [ID: {current_id}]: "
            action = io_handler.get_action_from_user(options_str)

            if action == 'DECREMENT':
                current_id -= 1
            elif action == 'INCREMENT':
                current_id += 1
            elif action == 'DOWNLOAD':
                session.download_file(target_url, filename)
                current_id += 1 
            elif action == 'EXIT_SOFT':
                io_handler.print_message("Процес зупинено користувачем.")
                break
            elif action == 'EXIT_CLIPBOARD':
                last_url = history_tracker.get_last_successful()
                if last_url:
                    pyperclip.copy(last_url)
                    io_handler.print_message(f"Повернення останнього успішного URL '{last_url}' до буфера обміну. Вихід.")
                break

        elif status_code == 403:
            history_tracker.add_error(target_url, status_code)
            
            action = io_handler.handle_403_prompt(current_id)
            
            if action == 'TRY_BYPASS':
                if session.renew_session(target_url):
                    continue # Повторна перевірка ТОГО Ж ID з новим скрепером
            elif action == 'DECREMENT':
                current_id -= 1
            elif action == 'INCREMENT':
                current_id += 1
            elif action in ('EXIT_SOFT', 'EXIT_CLIPBOARD'):
                if action == 'EXIT_CLIPBOARD':
                    last_url = history_tracker.get_last_successful()
                    if last_url:
                        pyperclip.copy(last_url)
                        io_handler.print_message(f"Повернення останнього успішного URL '{last_url}' до буфера обміну. Вихід.")
                io_handler.print_message("Процес зупинено користувачем.")
                break
        
        # Обробка інших помилок
        elif status_code == 404:
            io_handler.print_message(f"ID-{current_id} : Файл не знайдено (404)", color='YELLOW')
            history_tracker.add_error(target_url, status_code)
            current_id += 1
        else: 
            io_handler.print_message(f"ID-{current_id} : Помилка ({status_code}) або з'єднання/таймаут.", color='RED')
            history_tracker.add_error(target_url, status_code)
            current_id += 1
