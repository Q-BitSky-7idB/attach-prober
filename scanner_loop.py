# scanner_loop.py

import sys
import pyperclip
import re
#import history
import config
import network
import console as io
import context as ct

def final(history):
    last_url = history.get_last_successful()
    if last_url:
        pyperclip.copy(last_url)
        io.prints(f"[>] Повернення останнього успішного URL '{last_url}' до буфера обміну.\nВихід.")

def run_scanner(initial_url):
    """Основний цикл сканування та взаємодії з користувачем."""
    #cycle = 1
    
    # Ініціалізація
    try:
        #io.prints(f"[·] Спроба десереалізувати рядок URL...", color='YELLOW')
        ct.LINK = ct.LinkDetailed(initial_url)
    except ValueError as e:
        io.prints(f"[!] Помилка:", color='RED')
        io.prints(f"{e}", color='REDB')
        return

    ct.CURRENT = ct.DataBlock(ct.LINK.BeginIndex)
    session = network.FileScannerSession()	# Have 1 shadow call of CURRENT.URL
    #history_tracker = history.ScannerHistory(initial_url)
    
    io.prints(f"Базове посилання: {ct.LINK.Base}")
    io.prints(f"Поточний ID: [{ct.LINK.BeginIndex}]")
    if ct.LINK.Remains:
        io.prints(f"Закінчення URI: '{ct.LINK.Remains}'")
    io.printf("Папка завантажень: ")
    io.prints(f"{config.DOWNLOAD_DIR}", color='CYAN')

    # Початкова перевірка сесії
    while True:
        if ct.CURRENT.Index < 0:
            break
        # 1. CURRENT.GetNext() повертає посилання, що зберігається всередині CURRENT.
        # 2. CURRENT = ... ПЕРЕПРИСВОЮЄ мітку CURRENT на нове (або старе) посилання.
        ct.CURRENT = ct.CURRENT.GetNext()
        
        #history_tracker.last_checked_url = target_url # Оновлюємо останній перевірений

        # --- НОВА ЛОГІКА: Перевірка Історії спершу ---
        #history_entry = history_tracker.get_result(current_id)
        
        # --- ВИКОНАННЯ ЗАПИТУ ---
        #response, status_code = session.check_url_head(CURRENT.URL)
        session.check_url_head()
        
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
        
        io.printf(f"\n{config.URL_SUFIX}{ct.CURRENT.Index} : Перевірка {ct.CURRENT.URL}...", color='YELLOW')
        
        # --- ОБРОБКА КОДІВ ---
        if ct.CURRENT.State:
            io.overwrite(f"{config.URL_SUFIX}{ct.CURRENT.Index} : {ct.CURRENT.Size: >11} : {ct.CURRENT.FileName}", color='GREENB')
        else:
            if ct.CURRENT.Status == 403:
                io.overwrite(f"{config.URL_SUFIX}{ct.CURRENT.Index} : Доступ заборонено (403)! Опції: ", color='REDB')
            elif ct.CURRENT.Status > 403 and ct.CURRENT.Status < 500:
                io.overwrite(f"{config.URL_SUFIX}{ct.CURRENT.Index} : Помилка - ({ct.CURRENT.Status}) : Файл не отримано!", color='YELLOWB')
            else:
                io.overwrite(f"{config.URL_SUFIX}{ct.CURRENT.Index} : Помилка - ({ct.CURRENT.Status}) : Неочікувана відповідь! ", color='REDB')

        options_msg, options_scope = config.OPTIONS_STRATEGY.get(ct.CURRENT.Status)
        action = io.get_action_from_user(options_msg, options_scope)
        #io.overwrite(config.PASSIVE_MSGS.get(action, config.PASSIVE_MSGS['DEFAULT'])(ct.CURRENT))
        io.overwrite(*config.PASSIVE_MSGS.get(action, config.PASSIVE_MSGS['DEFAULT'])(ct.CURRENT))
        
        # Тут ми вже змінюємо основний об'єкт(не валідний index), тому перемальовувати треба рдразу
        if action == 'RETURN':
            ct.CURRENT.Index += 1
        elif action == 'DECREMENT':
            ct.CURRENT.Index -= 1
        elif action == 'INCREMENT':
            ct.CURRENT.Index += 1
        elif action == 'TRY_BYPASS':
            if session.renew_session():
                continue # Повторна перевірка ТОГО Ж ID з новим скрепером
        elif action == 'DOWNLOAD':
            if session.download_file():
                # Треба враховувати напрямок дії. а не просто (де)інкрементувати кожен раз.
                io.overwrite(*config.PASSIVE_MSGS.get('DOWNLOADED')(ct.CURRENT))
                ct.CURRENT.Index -= 1
                continue
        elif action == 'QUICK_EXIT':
            io.prints("\n[!] Процес зупинено користувачем.", color = 'GREEN')
            break
        elif action == 'EXIT':
            #final(history_tracker)
            io.prints("\nВихід!", color = 'GREEN')
            break
        elif action == 'DEBUG':
            io.prints("\n"+str(vars(ct.CURRENT)))
            io.get_action_from_user()
            continue
            
        #io.overwrite(config.PASSIVE_MSGS.get(action, 0))

#########################################################################################
