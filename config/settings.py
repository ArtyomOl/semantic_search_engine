# Настройки системы семантического поиска

import os
from pathlib import Path

# Базовые пути
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
INDEX_DIR = BASE_DIR / "index"
LOG_DIR = BASE_DIR / "logs"

# Создание директорий если они не существуют
for directory in [DATA_DIR, INDEX_DIR, LOG_DIR]:
    directory.mkdir(exist_ok=True)

# Настройки обработки текста
TEXT_PROCESSING = {
    "min_word_length": 2,
    "max_word_length": 50,
    "remove_stop_words": True,
    "lemmatize": True,
    "normalize_case": True
}

# Настройки поиска
SEARCH_SETTINGS = {
    "default_results_count": 10,
    "max_results_count": 100,
    "relevance_threshold": 0.1,
    "enable_fuzzy_search": True,
    "enable_semantic_search": True
}

# Настройки логгирования
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": LOG_DIR / "search_engine.log"
}

