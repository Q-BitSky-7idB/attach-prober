# scanner_loop.py

import sys
import pyperclip
import io_handler
import history
import session_manager
import config
import re

def run_scanner(initial_url):
    """Основний цикл сканування та взаємодії з користувачем."""
    
    # Ініціалізація
    try:
        #io_handler.print_message(f"[.] Спроба отримати елементи URL...", color='YELLOW')
        base_url_prefix, current_id, base_url_suffix = parse_url_args(initial_url)
    except ValueError as e:
        io_handler.print_message(f"[!] Помилка: {e}", color='RED')
        return

    session = session_manager.FileScannerSession(initial_url)
    history_tracker = history.ScannerHistory()
    
    #io_handler.print_message(f"// Базове посилання: {base_url_prefix}**[ID]**{base_url_suffix}")
    io_handler.print_message(f"// Базове посилання: {base_url_prefix}")
    io_handler.print_message(f"// Поточний ID: [{current_id}]")
    if base_url_suffix:
	io_handler.print_message(f"[+] Закінчення URI: '{base_url_suffix}'")
    io_handler.printf_message("// Папка завантажень: ")
    io_handler.print_message(f"{config.DOWNLOAD_DIR}", color='CYAN')

    # Початкова перевірка сесії
    try:
        session.check_url_head(get_target_url(base_url_prefix, current_id, base_url_suffix))
        io_handler.print_message("[+] Сесія ініціалізована успішно!")
    except Exception:
        io_handler.print_message("[!] Початкова перевірка не пройшла. Спробуйте 't' (обхід) пізніше.", color='YELLOW')


    while True:
        if current_id < 0:
            break
        
        target_url = get_target_url(base_url_prefix, current_id, base_url_suffix)
        #history_tracker.last_checked_url = target_url # Оновлюємо останній перевірений

        # --- НОВА ЛОГІКА: Перевірка Історії спершу ---
        history_entry = history_tracker.get_result(current_id)
        
        # --- ВИКОНАННЯ ЗАПИТУ ---
        #response, status_code = session.check_url_head(target_url)
        
        if history_entry:
            # Якщо результат знайдено в історії, відтворюємо його
            response, status_code = None, history_entry.status_code
            filename = history_entry.filename
            c_length = history_entry.content_length
            is_cached = True
            
            # Виводимо повідомлення, що це дані з історії
            # TODO: Вивід має регулюватися dt-transform, тут лише виклик кінцевого формату
            data_transformer.print_history_in_preview(current_id, status_code, filename, c_length)
            
        else:
            # Якщо результату немає в історії, виконуємо запит
            is_cached = False
            io_handler.printf_message(f"\n{URL_ID_SUFIX}{current_id} : Перевірка {target_url}...", color='YELLOW')
            response, status_code = session.check_url_head(target_url)

        history_tracker.last_checked_url = target_url # Оновлюємо останній перевірений
        
        # --- ОБРОБКА КОДІВ ---
        if status_code == 200:
	    if not is_cached:
                # Отримуємо ім'я файлу лише якщо це новий запит
                filename, c_length = session.get_meta_from_headers(response)
                # Зберігаємо результат у історії
                history_tracker.add_result(current_id, target_url, status_code, filename=filename, length=c_length)
                data_transformer.print_result_in_queue(current_id, status_code, filename, c_length)
            
            history_tracker.add_success(target_url)

            #io_handler.print_message(f"\nID-{current_id} : Файл знайдено : {filename}", color='GREENB')
            
            options_str = f"Оберіть дію (E/D: продовжити, G: скачати, C/Q: вийти) [ID: {current_id}]: "
            action = io_handler.get_action_from_user(options_str)

            if action == 'RETURN':
            elif action == 'DECREMENT':
                current_id -= 1
            elif action == 'INCREMENT':
                current_id += 1
            elif action == 'DOWNLOAD':
                session.download_file(target_url, filename)
                current_id += 1 
            elif action == 'EXIT_SOFT':
                io_handler.print_message("[!] Процес зупинено користувачем.")
                break
            elif action == 'EXIT_CLIPBOARD':
                last_url = history_tracker.get_last_successful()
                if last_url:
                    pyperclip.copy(last_url)
                    io_handler.print_message(f"[.] Повернення останнього успішного URL '{last_url}' до буфера обміну. Вихід.")
                break

        #elif status_code == 403:
        elif status_code == 403:
            if not is_cached:
                # Зберігаємо результат у історії
                history_tracker.add_result(current_id, target_url, status_code)
            history_tracker.add_error(target_url, status_code)
            
            #action = io_handler.handle_403_prompt(current_id)
            io_handler.overwrite_message(f"\r{URL_ID_SUFIX}{current_id}: Доступ заборонено (403)! Опції: ", color='RED')
            options_str = f"[T/Е] - Обхід, [D/В] - Декремент, [E/К] - Інкремент, [C/Q] - Вийти: "
            action = io_handler.get_action_from_user(options_str)
            
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
        elif status_code == -1:
        else: 
            io_handler.print_message(f"ID-{current_id} : Помилка ({status_code}) або з'єднання/таймаут.", color='RED')
            history_tracker.add_error(target_url, status_code)
            current_id += 1
