# strategy.py

import config
import context

def get_options():
  if CURRENT.Status == 403:
    return f"[T/Е] - Обхід, [D/В] - Декремент, [E/У] - Інкремент, [C/Q] - Вийти: "