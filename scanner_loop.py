# scanner_loop.py

import sys
import pyperclip
import re
#import history
import config
import network
import console as io
import transformer as tf
import context

def final(history):
    last_url = history.get_last_successful()
    if last_url:
        pyperclip.copy(last_url)
        io.prints(f"[>] Повернення останнього успішного URL '{last_url}' до буфера обміну.\nВихід.")

def run_scanner(initial_url):
    """Основний цикл сканування та взаємодії з користувачем."""
    global LINK
    global CURRENT
    cycle = 1
    
    # Ініціалізація
    try:
        #io.prints(f"[·] Спроба отримати елементи URL...", color='YELLOW')
        LINK = LinkDetailed(initial_url)
    except ValueError as e:
        io.prints(f"[!] Помилка:", color='EDB')
        io.prints(f"{e}", color='REDB')
        return
        
    CURRENT = DataBlock(cycle, LINK.BeginIndex)
    session = network.FileScannerSession()	# Have 1 shadow call of CURRENT.URL
    #history_tracker = history.ScannerHistory(initial_url)
    
    io.prints(f"Базове посилання: {LINK.Base}")
    io.prints(f"Поточний ID: [{LINK.BeginIndex}]")
    if LINK.Remains:
        io.prints(f"Закінчення URI: '{LINK.Remains}'")
    io.printf("Папка завантажень: ")
    io.prints(f"{config.DOWNLOAD_DIR}", color='CYAN')

    # Початкова перевірка сесії
    io.prints("[+] Сесія ініціалізована успішно!\n")

    while True:
        if CURRENT.Index < 0:
            break
        
        #history_tracker.last_checked_url = target_url # Оновлюємо останній перевірений

        # --- НОВА ЛОГІКА: Перевірка Історії спершу ---
        #history_entry = history_tracker.get_result(current_id)
        
        # --- ВИКОНАННЯ ЗАПИТУ ---
        response, status_code = session.check_url_head(CURRENT.URL)
        
        #if history_entry:
            # Якщо результат знайдено в історії, відтворюємо його
        #    response, status_code = None, history_entry.status_code
        #    filename = history_entry.filename
        #    c_length = history_entry.content_length
        #    is_cached = True
            
            # Виводимо повідомлення, що це дані з історії
            # TODO: Вивід має регулюватися dt-transform, тут лише виклик кінцевого формату
        #    if status_code in (200, 404):
        #        data_transformer.print_history_in_preview(current_id, status_code, filename, c_length)
        #    else:
        #        is_cached = False
        #        io.printf(f"\n{config.URL_ID_SUFIX}{current_id} : {filename} : Перевірка {target_url}... (Last code={status_code})", color='CYAN')
        #        response, status_code = session.check_url_head(target_url)
            
        #else:
            # Якщо результату немає в історії, виконуємо запит
        #    is_cached = False
        #    io.printf(f"\n{config.URL_ID_SUFIX}{current_id} : Перевірка {target_url}...", color='YELLOW')
        #    response, status_code = session.check_url_head(target_url)

        #history_tracker.last_checked_url = target_url # Оновлюємо останній перевірений
        
        # --- ОБРОБКА КОДІВ ---
        if CURRENT.State:
            io.prints()
        if status_code == 200:
          if not CURRENT.Length:
            status_code = 410
            
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

            #io.print_msg(f"\nID-{current_id} : Файл знайдено : {filename}", color='GREENB')
            
            options_str = data_transformer.get_options('act_normal') 
            action = io.get_action_from_user(options_str)

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
                io.print_msg("[!] Процес зупинено користувачем.")
                break
            elif action == 'EXIT':
                final(history_tracker)
                break

        elif status_code == 403:
            if not is_cached:
                # Зберігаємо результат у історії
                history_tracker.add_result(current_id, target_url, status_code)
            history_tracker.add_error(target_url, status_code)
            
            #action = io.handle_403_prompt(current_id)
            io.overwrite_msg(f"\r{config.URL_ID_SUFIX}{current_id}: Доступ заборонено (403)! Опції: ", color='RED')
            options_str = data_transformer.get_options('act_error')
            action = io.get_action_from_user(options_str)
            
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
                io.print_msg("Процес зупинено.")
                break
                
        # Обробка інших помилок
        elif status_code == 404:
            io.print_msg(f"ID-{current_id} : Файл не знайдено (404)", color='YELLOW')
            history_tracker.add_error(target_url, status_code)
            if action == 'INCREMENT':
                current_id += 1
            elif action == 'DECREMENT':
                current_id -= 1
        elif status_code == -1:
            io.print_msg(f">({status_code}) : Unexpected Error:!", color='RED')
        else: 
            io.print_msg(f"ID-{current_id} : Помилка ({status_code}) або з'єднання/таймаут.", color='RED')
            history_tracker.add_error(target_url, status_code)
            current_id += 1
