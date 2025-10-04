#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Примеры использования системы семантического поиска
"""

from core.search_engine import SearchEngine


def example_basic_search():
    """Базовый пример поиска"""
    print("=== БАЗОВЫЙ ПОИСК ===")
    
    # Создаем поисковую систему
    engine = SearchEngine()
    
    # Добавляем документы
    engine.add_document(
        "Машинное обучение", 
        "Машинное обучение - это метод анализа данных, который автоматизирует построение аналитических моделей."
    )
    
    engine.add_document(
        "Искусственный интеллект", 
        "Искусственный интеллект - это имитация человеческого интеллекта в машинах."
    )
    
    # Выполняем поиск
    results = engine.search("машинное обучение")
    
    print(f"Найдено результатов: {len(results)}")
    for result in results:
        print(f"- {result.document.title} (релевантность: {result.score:.3f})")


def example_advanced_search():
    """Продвинутый пример с фильтрацией"""
    print("\n=== ПРОДВИНУТЫЙ ПОИСК ===")
    
    engine = SearchEngine()
    
    # Добавляем больше документов
    documents = [
        ("Python программирование", "Python - популярный язык программирования для веб-разработки и анализа данных."),
        ("Базы данных", "Базы данных используются для хранения и управления структурированными данными."),
        ("Веб-разработка", "Веб-разработка включает создание веб-сайтов и веб-приложений."),
        ("Анализ данных", "Анализ данных помогает извлекать полезную информацию из больших объемов данных.")
    ]
    
    for title, content in documents:
        engine.add_document(title, content)
    
    # Поиск с минимальным порогом релевантности
    results = engine.search("Python данные", top_k=3, min_score=0.05)
    
    print("Результаты поиска 'Python данные':")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.document.title}")
        print(f"   Релевантность: {result.score:.4f}")
        print(f"   Фрагмент: {result.snippet[:80]}...")
        print()


def example_document_management():
    """Пример управления документами"""
    print("=== УПРАВЛЕНИЕ ДОКУМЕНТАМИ ===")
    
    engine = SearchEngine()
    
    # Добавляем документ
    doc_id = engine.add_document(
        "Тест документ", 
        "Это тестовый документ для демонстрации управления."
    )
    
    print(f"Добавлен документ с ID: {doc_id}")
    
    # Получаем документ
    doc = engine.get_document(doc_id)
    if doc:
        print(f"Заголовок: {doc.title}")
        print(f"Содержимое: {doc.content[:50]}...")
    
    # Получаем ключевые слова
    keywords = engine.get_document_keywords(doc_id, top_k=5)
    print("Ключевые слова:")
    for word, weight in keywords:
        print(f"  {word}: {weight:.4f}")
    
    # Статистика
    stats = engine.get_stats()
    print(f"\nСтатистика системы:")
    print(f"  Документов: {stats['total_documents']}")
    print(f"  Уникальных слов: {stats['index']['unique_words']}")


def example_search_variations():
    """Пример различных типов поиска"""
    print("\n=== РАЗЛИЧНЫЕ ТИПЫ ПОИСКА ===")
    
    engine = SearchEngine()
    
    # Добавляем документы
    engine.add_document("Программирование на Python", "Python - отличный язык для начинающих программистов.")
    engine.add_document("Изучение Python", "Python можно изучать самостоятельно или на курсах.")
    engine.add_document("Python в веб-разработке", "Django и Flask - популярные фреймворки Python для веб-разработки.")
    
    # Поиск по содержимому
    print("1. Поиск по содержимому:")
    results = engine.search("Python программирование")
    for result in results[:2]:
        print(f"   - {result.document.title}")
    
    # Поиск по заголовку
    print("\n2. Поиск по заголовку:")
    title_results = engine.search_by_title("Python")
    for doc in title_results:
        print(f"   - {doc.title}")


if __name__ == "__main__":
    example_basic_search()
    example_advanced_search()
    example_document_management()
    example_search_variations()
    
    print("\n=== ВСЕ ПРИМЕРЫ ЗАВЕРШЕНЫ ===")

