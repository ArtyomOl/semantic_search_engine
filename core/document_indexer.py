"""
Система индексации документов для поиска
"""

from typing import Dict, List, Set, Tuple
from collections import defaultdict, Counter
import math
from core.text_processor import TextProcessor


class DocumentIndex:
    """Класс для индексации документов"""
    
    def __init__(self):
        self.text_processor = TextProcessor()
        
        # Инвертированный индекс: слово -> {doc_id: tf}
        self.inverted_index: Dict[str, Dict[str, int]] = defaultdict(dict)
        
        # Прямой индекс: doc_id -> {слово: tf}
        self.forward_index: Dict[str, Dict[str, int]] = defaultdict(dict)
        
        # Общее количество документов
        self.total_documents = 0
        
        # Общее количество слов в каждом документе
        self.document_lengths: Dict[str, int] = {}
        
        # TF-IDF веса для каждого слова в каждом документе
        self.tf_idf_weights: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Кэш для IDF значений
        self.idf_cache: Dict[str, float] = {}
    
    def add_document(self, doc_id: str, content: str):
        """Добавление документа в индекс"""
        # Обрабатываем текст
        processed_text = self.text_processor.preprocess_text(content)
        
        if not processed_text:
            return
        
        # Разбиваем на слова
        words = processed_text.split()
        
        # Подсчитываем частоту слов в документе
        word_counts = Counter(words)
        
        # Обновляем индексы
        for word, count in word_counts.items():
            # Обновляем инвертированный индекс
            self.inverted_index[word][doc_id] = count
            
            # Обновляем прямой индекс
            self.forward_index[doc_id][word] = count
        
        # Обновляем длину документа
        self.document_lengths[doc_id] = sum(word_counts.values())
        
        # Инвалидируем кэш IDF
        self.idf_cache.clear()
        
        # Обновляем общее количество документов
        self.total_documents = len(self.forward_index)
    
    def remove_document(self, doc_id: str):
        """Удаление документа из индекса"""
        if doc_id not in self.forward_index:
            return
        
        # Удаляем из прямого индекса
        words = list(self.forward_index[doc_id].keys())
        del self.forward_index[doc_id]
        
        # Удаляем из инвертированного индекса
        for word in words:
            if doc_id in self.inverted_index[word]:
                del self.inverted_index[word][doc_id]
                # Если слово больше не встречается ни в одном документе, удаляем его
                if not self.inverted_index[word]:
                    del self.inverted_index[word]
        
        # Удаляем длину документа
        if doc_id in self.document_lengths:
            del self.document_lengths[doc_id]
        
        # Удаляем TF-IDF веса
        if doc_id in self.tf_idf_weights:
            del self.tf_idf_weights[doc_id]
        
        # Инвалидируем кэш IDF
        self.idf_cache.clear()
        
        # Обновляем общее количество документов
        self.total_documents = len(self.forward_index)
    
    def calculate_tf(self, word: str, doc_id: str) -> float:
        """Вычисление TF (Term Frequency)"""
        if doc_id not in self.forward_index or word not in self.forward_index[doc_id]:
            return 0.0
        
        word_count = self.forward_index[doc_id][word]
        doc_length = self.document_lengths.get(doc_id, 1)
        
        # Нормализованный TF
        return word_count / doc_length
    
    def calculate_idf(self, word: str) -> float:
        """Вычисление IDF (Inverse Document Frequency)"""
        if word in self.idf_cache:
            return self.idf_cache[word]
        
        if word not in self.inverted_index:
            return 0.0
        
        # Количество документов, содержащих это слово
        doc_frequency = len(self.inverted_index[word])
        
        # IDF = log(total_documents / doc_frequency)
        if doc_frequency == 0:
            idf = 0.0
        else:
            idf = math.log(self.total_documents / doc_frequency)
        
        self.idf_cache[word] = idf
        return idf
    
    def calculate_tf_idf(self, word: str, doc_id: str) -> float:
        """Вычисление TF-IDF"""
        tf = self.calculate_tf(word, doc_id)
        idf = self.calculate_idf(word)
        return tf * idf
    
    def get_document_vector(self, doc_id: str) -> Dict[str, float]:
        """Получение вектора документа (TF-IDF веса для всех слов)"""
        if doc_id not in self.forward_index:
            return {}
        
        vector = {}
        for word in self.forward_index[doc_id]:
            vector[word] = self.calculate_tf_idf(word, doc_id)
        
        return vector
    
    def get_query_vector(self, query: str) -> Dict[str, float]:
        """Получение вектора запроса"""
        processed_query = self.text_processor.preprocess_text(query)
        if not processed_query:
            return {}
        
        words = processed_query.split()
        word_counts = Counter(words)
        
        vector = {}
        for word, count in word_counts.items():
            # Для запроса используем простую частоту (не нормализованную)
            tf = count
            idf = self.calculate_idf(word)
            vector[word] = tf * idf
        
        return vector
    
    def calculate_cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """Вычисление косинусного сходства между векторами"""
        # Находим общие слова
        common_words = set(vec1.keys()) & set(vec2.keys())
        
        if not common_words:
            return 0.0
        
        # Вычисляем скалярное произведение
        dot_product = sum(vec1[word] * vec2[word] for word in common_words)
        
        # Вычисляем нормы векторов
        norm1 = math.sqrt(sum(vec1[word] ** 2 for word in vec1))
        norm2 = math.sqrt(sum(vec2[word] ** 2 for word in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Поиск документов по запросу"""
        if not query or self.total_documents == 0:
            return []
        
        # Получаем вектор запроса
        query_vector = self.get_query_vector(query)
        
        if not query_vector:
            return []
        
        # Вычисляем сходство с каждым документом
        similarities = []
        for doc_id in self.forward_index:
            doc_vector = self.get_document_vector(doc_id)
            similarity = self.calculate_cosine_similarity(query_vector, doc_vector)
            
            if similarity > 0:
                similarities.append((doc_id, similarity))
        
        # Сортируем по убыванию сходства
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def get_document_keywords(self, doc_id: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Получение ключевых слов документа с их TF-IDF весами"""
        if doc_id not in self.forward_index:
            return []
        
        vector = self.get_document_vector(doc_id)
        keywords = [(word, weight) for word, weight in vector.items()]
        keywords.sort(key=lambda x: x[1], reverse=True)
        
        return keywords[:top_k]
    
    def get_stats(self) -> Dict[str, any]:
        """Получение статистики индекса"""
        total_words = sum(len(doc_words) for doc_words in self.forward_index.values())
        unique_words = len(self.inverted_index)
        
        return {
            'total_documents': self.total_documents,
            'total_words': total_words,
            'unique_words': unique_words,
            'average_words_per_document': total_words / self.total_documents if self.total_documents > 0 else 0
        }

