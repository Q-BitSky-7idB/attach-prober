# system.py
import os
import shutil
import console as io # Припускаємо, що get_actions_from_user тут
import config

class FileSystem:
    """
    Клас для роботи з файловою системою, щоб розвантажити network/session модулі.
    """

    @staticmethod
    def _get_next_copy_filename(directory: str, filename: str) -> str:
        """
        Генерує ім'я для копії: filename.ext -> filename.1.ext -> filename.2.ext
        Знаходить перший вільний індекс.
        """
        name, ext = os.path.splitext(filename)
        index = 1
        
        while True:
            # Формуємо нове ім'я: name.N.ext
            new_filename = f"{name}.{index}{ext}"
            full_path = os.path.join(directory, new_filename)
            
            if not os.path.exists(full_path):
                return new_filename
            index += 1

    @staticmethod
    def save_stream_content(stream_iterator, filename: str, expected_size: int = 0) -> bool:
        """
        Приймає ітератор байтів (потік) і записує його у файл з логікою конфліктів.
        
        :param stream_iterator: генератор r.iter_content(...)
        :param filename: оригінальне ім'я файлу
        :param expected_size: розмір файлу з context.CURRENT.Size для звірки
        """
        directory = config.DOWNLOAD_DIR
        file_path = os.path.join(directory, filename)
        
        # --- ЛОГІКА ПЕРЕВІРКИ ---
        if os.path.exists(file_path):
            local_size = os.path.getsize(file_path)
            
            # Якщо файл існує І розмір збігається
            if local_size == 			:
                msg = f"Файл '{filename}' (Size: {local_size}) вже існує."
                
                # Викликаємо меню вибору (припускаємо, що повертає ключ або індекс)
                # Потрібно адаптувати під реальний інтерфейс get_actions_from_user
                choice = io.get_actions_from_user(
                    msg, 
                    options=["Overwrite (Перезаписати)", "Save as Copy (Зберегти копію)"]
                )
                
                if choice == 0: # Overwrite
                    io.printf("Перезапис файлу...", color='YELLOW')
                    # file_path залишається тим самим
                    
                elif choice == 1: # Copy
                    new_filename = FileSystem._get_next_copy_filename(directory, filename)
                    file_path = os.path.join(directory, new_filename)
                    io.printf(f"Збереження як копія: {new_filename}", color='CYAN')
                    
                else:
                    # Якщо користувач скасував або щось пішло не так
                    io.prints("Завантаження скасовано користувачем.", color='GREY')
                    return False
            else:
                # Якщо файл існує, але розмір різний - зазвичай просто перезаписуємо 
                # або додаємо .part, але за вашим ТЗ (якщо немає збігу - звичайний запис)
                # тож просто пишемо поверх (Overwrite).
                pass

        # --- ЛОГІКА ЗАПИСУ ---
        try:
            # Створення директорії, якщо її немає
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'wb') as f:
                # Транслюємо чанки з мережі прямо на диск
                for chunk in stream_iterator:
                    if chunk: 
                        f.write(chunk)
            
            io.printf(f"Файл збережено: {os.path.basename(file_path)}", color='GREEN')
            return True

        except Exception as e:
            io.prints(f"Помилка запису файлу: {e}", color='RED')
            return False

# Створюємо екземпляр або використовуємо як статику, залежно від архітектури
fs = FileSystem()
