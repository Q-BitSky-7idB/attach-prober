# main.py

#    Project Name: Attach-Prober.
#    A simple interactive tool that allows you iteratively exploring
#    through a website's files using the initial direct link based 
#    on its numerical index.
#
#    Copyright (C) 2025 Kubitskyi Bohdan
#
#    This project (including all associated source code files but excluding documentation)
#    is free software: you can redistribute it and/or modify it under 
#    the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This project is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this project.  If not, see <https://www.gnu.org/licenses/>.
#
# ---------------------------------------------------------------------------
#    Contact Information:
#    Email:   kurl0xe3z.tw0yb+github-public-support@gmail.com
#    GitHub:  https://github.com/Q-BitSky-7idB/attach-prober

import sys
import argparse
import os

# Додаємо поточну папку до шляху для імпорту локальних модулів
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scanner_loop import run_scanner

def main():
    """Основна функція для парсингу аргументів та запуску сканера."""
    parser = argparse.ArgumentParser(description="• Інтерактивний сканер файлів із змінним ID.")
    parser.add_argument('url', type=str, help='– Початкове посилання, що містить змінний ID (наприклад, base?id=123)')
    args = parser.parse_args()
    
    run_scanner(args.url)

if __name__ == '__main__':
    main()
