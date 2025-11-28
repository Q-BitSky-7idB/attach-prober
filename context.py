# context.py
import config
from urllib.parse import urlparse
from transformer import get_meta_from_headers as read_headers
import re

CURRENT = None
LINK = None

class DataBlock:
 def __init__(self, cycle_id=0, index=-1):
   self.cycle_id = cycle_id
   self._data = {}
   self.Index = index
   self.URL = f"{LINK.Base}{self.Index}{LINK.Remains}"
   self.State = False
   self.Size = 0
   self.FileName = ""
   self._body = None
   self._code = 0
 
 @property
 def Code(self):
   return self._code
 
 @Code.setter
 def Code(self, status):
   if status == 200:
     self.State = True
   self._code = status

 @property
 def Body(self):
   return self._body
 
 @Body.setter
 def Body(self, response):
   self._body = response
   self.FileName, self.Size = read_headers(response)
   if not self.Size:
     self.State = False
     self.FileName = "Access Denied."
     self.Status = 410

class LinkDetailed:
 def __init__(self, url):
   """Розбирає URL на префікс, ID та постфікс."""
   self.Domain = None
   self.Base = None
   self.BeginIndex = -1
   self.Remains = None
   self.Origin = "–"
   if url:
     match = re.search(config.URL_ID_PATTERN, args, re.I)
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
     