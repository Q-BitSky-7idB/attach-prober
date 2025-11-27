# scanner_loop.py

import sys
import pyperclip
import io_handler
import history
import session_manager
import data_transformer
import config
import re

def final(history):
    last_url = history.get_last_successful()
    if last_url:
        pyperclip.copy(last_url)
        io_handler.print_msg(f"[>] Повернення останнього успішного URL '{last_url}' до буфера обміну.\nВихід.")

INIT_URL = None

def run_scanner(initial_url):
    """Основний цикл сканування та взаємодії з користувачем."""
    
    # Ініціалізація
    try:
        #io_handler.print_msg(f"[.] Спроба отримати елементи URL...", color='YELLOW')
        base_url_prefix, current_id, base_url_postfix = data_transformer.parse_url_args(initial_url)
    except ValueError as e:
        io_handler.print_msg(f"[!] Помилка: {e}", color='RED')
        return

    session = session_manager.FileScannerSession(initial_url)
    history_tracker = history.ScannerHistory(initial_url)
    
    #io_handler.print_msg(f"// Базове посилання: {base_url_prefix}**[ID]**{base_url_postfix}")
    io_handler.print_msg(f"// Базове посилання: {base_url_prefix}")
    io_handler.print_msg(f"// Поточний ID: [{current_id}]")
    if base_url_postfix:
        io_handler.print_msg(f"[+] Закінчення URI: '{base_url_postfix}'")
    io_handler.printf_msg("// Папка завантажень: ")
    io_handler.print_msg(f"{config.DOWNLOAD_DIR}", color='CYAN')

    # Початкова перевірка сесії
    try:
        i_response, i_status = session.check_url_head(get_target_url(base_url_prefix, current_id, base_url_postfix))
        io_handler.print_msg("[+] Сесія ініціалізована успішно!\n")
        #io_handler.begin_listener()
    except Exception:
        io_handler.print_msg("[!] Початкова перевірка не пройшла. Спробуйте 't' (обхід) пізніше.", color='YELLOW')

    while True:
        if current_id < 0:
            break
        
        target_url = data_transformer.get_target_url(base_url_prefix, current_id, base_url_postfix)
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
            if status_code in (200, 404):
                data_transformer.print_history_in_preview(current_id, status_code, filename, c_length)
            else:
                is_cached = False
                io_handler.printf_msg(f"\n{config.URL_ID_SUFIX}{current_id} : {filename} : Перевірка {target_url}... (Last code={status_code})", color='CYAN')
                response, status_code = session.check_url_head(target_url)
            
        else:
            # Якщо результату немає в історії, виконуємо запит
            is_cached = False
            io_handler.printf_msg(f"\n{config.URL_ID_SUFIX}{current_id} : Перевірка {target_url}...", color='YELLOW')
            response, status_code = session.check_url_head(target_url)

        history_tracker.last_checked_url = target_url # Оновлюємо останній перевірений
        
        # --- ОБРОБКА КОДІВ ---
        if status_code == 200:
            if not is_cached:
                # Отримуємо ім'я файлу лише якщо це новий запит
                filename, c_length = session.get_meta_from_headers(response)
                # Зберігаємо результат у історії
                history_tracker.add_result(current_id, target_url, status_code, filename=filename, length=c_length)
                if not c_length:
                    c_length = 0
                    filename = "Access Denied."
                    status_code = 410
                
                data_transformer.print_result_in_queue(current_id, status_code, filename, c_length)
            
            history_tracker.add_success(target_url)

            #io_handler.print_msg(f"\nID-{current_id} : Файл знайдено : {filename}", color='GREENB')
            
            options_str = data_transformer.get_options('act_normal') 
            action = io_handler.get_action_from_user(options_str)

            if action == 'RETURN':
                current_id -= 1
                # return-function
            
            if action == 'DECREMENT':
                data_transformer.rewrite_output(current_id, status_code, filename, c_length, action)
                current_id -= 1
            elif action == 'INCREMENT':
                data_transformer.rewrite_output(current_id, status_code, filename, c_length, action)
                current_id += 1
            elif action == 'DOWNLOAD':
                data_transformer.rewrite_output(current_id, status_code, filename, c_length, action)
                session.download_file(target_url, filename)
                current_id += 1 
            elif action == 'QUICK_EXIT':
                io_handler.print_msg("[!] Процес зупинено користувачем.")
                break
            elif action == 'EXIT':
                final(history_tracker)
                break

        elif status_code == 403:
            if not is_cached:
                # Зберігаємо результат у історії
                history_tracker.add_result(current_id, target_url, status_code)
            history_tracker.add_error(target_url, status_code)
            
            #action = io_handler.handle_403_prompt(current_id)
            io_handler.overwrite_msg(f"\r{config.URL_ID_SUFIX}{current_id}: Доступ заборонено (403)! Опції: ", color='RED')
            options_str = data_transformer.get_options('act_error')
            action = io_handler.get_action_from_user(options_str)
            
            if action == 'TRY_BYPASS':
                if session.renew_session(target_url):
                    continue # Повторна перевірка ТОГО Ж ID з новим скрепером
            elif action == 'DECREMENT':
                if current_id < 1:
                    current_id -= 1
                data_transformer.rewrite_output(current_id, status_code, filename, c_length, action)
                session.renew_session(get_target_url(base_url_prefix, current_id, base_url_postfix))
            elif action == 'INCREMENT':
                current_id += 1
                data_transformer.rewrite_output(current_id, status_code, filename, c_length, action)
                session.renew_session(get_target_url(base_url_prefix, current_id, base_url_postfix))
            elif action in ('QUICK_EXIT', 'EXIT'):
                if action == 'EXIT':
                    final(history_tracker)
                    break
                io_handler.print_msg("Процес зупинено.")
                break
                
        # Обробка інших помилок
        elif status_code == 404:
            io_handler.print_msg(f"ID-{current_id} : Файл не знайдено (404)", color='YELLOW')
            history_tracker.add_error(target_url, status_code)
            if action == 'INCREMENT':
                current_id += 1
            elif action == 'DECREMENT':
                current_id -= 1
        elif status_code == -1:
            io_handler.print_msg(f">({status_code}) : Unexpected Error:!", color='RED')
        else: 
            io_handler.print_msg(f"ID-{current_id} : Помилка ({status_code}) або з'єднання/таймаут.", color='RED')
            history_tracker.add_error(target_url, status_code)
            current_id += 1
