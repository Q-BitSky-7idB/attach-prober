import config
import re

# Модуль для розбору вводу\воводу інформації яку треба обробляти

def parse_url_from_args(args):
    """Розбирає URL на префікс, ID та суфікс."""
    match = re.search(config.URL_ID_PATTERN, args, re.I)
    if not match:
        raise ValueError("Не вдалося знайти шаблон 'id=[number]' у посиланні.")
    
    return match.group(1), int(match.group(2)), match.group(3)

def get_target_url(prefix, current_id, suffix):
    """Складає цільовий URL."""
    return f"{prefix}{current_id}{suffix}"
