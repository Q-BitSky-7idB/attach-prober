# system.py
import os
import shutil
import config
import console as io

def _get_next_copy_filename(directory: str, filename: str) -> str:
    """
    Генерує ім'я для копії: filename.ext -> filename.1.ext -> filename.2.ext
    Знаходить перший вільний індекс.
    """
    name, ext = os.path.splitext(filename)
    index = 1
    
    while True:
        new_filename = f"{name}.{index}{ext}"
        full_path = os.path.join(directory, new_filename)
        if not os.path.exists(full_path):
            return new_filename
        index += 1

def _handle_file_conflict(filename: str) -> str:
    """
    Обробляє ситуацію, коли файл вже існує.
    Повертає дію: 'COPY', 'REWRITE' або 'SKIP'.
    """
    msg = f"Warning: Файл існує [{filename}] : Copy or Rewrite, Skip? [C\\R\\S] "
    
    # Використовуємо overwrite для виводу в той самий рядок
    io.overwrite(msg, color='YELLOW')
    
    # Очікуємо дію від користувача, використовуючи спеціальний словник
    action = io.get_action_from_user("", acts_dict=config.ACTIONS_FILE_CONFLICT)
    
    return action

def save_stream_content(stream_iterator, filename: str, expected_size: int = 0) -> bool:
    """
    Приймає ітератор байтів (потік) і записує його у файл з логікою конфліктів.
    """
    directory = config.DOWNLOAD_DIR
    file_path = os.path.join(directory, filename)
    
    # --- ЛОГІКА ПЕРЕВІРКИ ---
    if os.path.exists(file_path):
        local_size = os.path.getsize(file_path)
        
        # Якщо файл існує І розмір збігається
        if local_size == expected_size:
            action = _handle_file_conflict(filename)
            
            if action == 'SKIP':
                io.printf(" -> Skipped", color='GREY') # Дописуємо статус в рядок
                return False # Вихід із модуля із False в network
                
            elif action == 'COPY':
                new_filename = _get_next_copy_filename(directory, filename)
                file_path = os.path.join(directory, new_filename)
                io.printf(f" -> Saving Copy: {new_filename}", color='CYAN')
                # Далі йдемо до блоку запису з новим file_path
                
            elif action == 'REWRITE':
                io.printf(" -> Rewriting...", color='YELLOW')
                # file_path залишається тим самим, файл перезапишеться
            
            else:
                # На випадок якщо action=None (невідома клавіша і т.д.), хоча цикл get_action має це обробити
                io.printf(" -> Cancelled", color='RED')
                return False
        else:
             # Якщо розмір не збігається - звичайний запис (перезапис) без питань
             pass

    # --- ЛОГІКА ЗАПИСУ ---
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'wb') as f:
            for chunk in stream_iterator:
                if chunk: 
                    f.write(chunk)
        
        # Якщо ми перезаписували або писали копію, виведемо фінальний статус
        # Але оскільки network.py може виводити свої повідомлення, тут можна бути лаконічним.
        # io.printf(f"Saved: {os.path.basename(file_path)}", color='GREEN') 
        return True

    except Exception as e:
        io.prints(f"Помилка запису файлу: {e}", color='RED')
        return False
        