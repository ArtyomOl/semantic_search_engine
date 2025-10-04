#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Запуск графического интерфейса системы семантического поиска
"""

import sys
import os
from PyQt5.QtWidgets import QApplication

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gui.main_window import main
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что установлен PyQt5: pip install PyQt5")
    sys.exit(1)

if __name__ == "__main__":
    main()

