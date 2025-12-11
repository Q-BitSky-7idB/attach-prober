# context.py
import config
from config import get_meta_from_headers as read_headers
from urllib.parse import urlparse
import re

class DataBlock:
 #def __init__(self, cycle_id=0, index=-1):
 def __init__(self, index=-1):
   #self.cycle_id = cycle_id
   self._data = {}
   self._index = index
   self.State = False
   self.Size = 0
   self.FileName = ""
   self._body = None
   self._code = 0
   if LINK is not None:
       self.URL = f"{LINK.Base}{self.Index}{LINK.Remains}"
   else:
       # Обробка випадку, коли CURRENT ще не ініціалізовано
       # Можна передати initial_url як дефолтний
       pass
   self._next_block = self
 
 @property
 def Index(self):
   return self._index

 @Index.setter
 def Index(self, new_index):
   """
   Цей setter перехоплює зміну індексу та ініціює ЗАМІНУ ОБ'ЄКТА.
   """
   # Логіка зміни стану (наприклад, декремент)
   if new_index != self._index:
     # 1. Створюємо НОВИЙ екземпляр з оновленими даними.
     new_instance = DataBlock(index=new_index)
            
     # 2. ОНОВЛЮЄМО ВНУТРІШНЄ ПОСИЛАННЯ:
     # Поточний об'єкт (self) тепер вказує на НОВИЙ об'єкт.
     self._next_block = new_instance
     #print(f"[DEBUG]: Об'єкт {id(self)} створив і посилається на {id(new_instance)}")        
     # Увага: Поточний об'єкт "застарів".
     self._index = new_index
        
 @property
 def Status(self):
   return self._code
 
 @Status.setter
 def Status(self, status):
   if status == 200 and self.FileName != "Access Denied.":
     self.State = True
   self._code = status

 @property
 def Body(self):
   #return self._body
   return self._body.text
 
 @Body.setter
 def Body(self, response):
   self._body = str(response.text)
   self._ref = str(response)
   self.FileName, self.Size = read_headers(response)
   if not self.Size and self._code == 200:
     self.State = False
     self.FileName = "Access Denied."
     self.Status = 410
     
# 3. Метод "Витягування Посилання"
 def GetNext(self):
   """
   Метод, який цикл буде викликати, щоб отримати актуальне посилання.
   Це і є ваша 'доступна комірка'.
   """
   return self._next_block
        
class LinkDetailed:
 def __init__(self, url):
   """Розбирає URL на префікс, ID та постфікс.
      Призначений тримати занальну інформацію та бути базисом для CURRENT
      Не змінний. Одноразовий на всю сесію забігу по урлам.
   """
   self.Domain = None
   self.Base = None
   self.BeginIndex = -1
   self.Remains = None
   self.Origin = "–"
   if url:
     if url == ".":
       return
     match = re.search(config.URL_ID_PATTERN, url, re.I)
     if not match:
       raise ValueError("Не вдалося знайти шаблон '[id:number]' у посиланні.")
     parsed_url = urlparse(url)
     #uri_path = parsed_url.path
     self.Domain = parsed_url.netloc
     self.Base = match.group(1)
     self.BeginIndex = int(match.group(2))
     self.Remains = match.group(3)
     self.Origin = url
   else:
     raise ValueError("Спроба створити порожній об'єкт 'LinkDetailed'!")


CURRENT = None
LINK = None
#LINK = LinkDetailed(".")
