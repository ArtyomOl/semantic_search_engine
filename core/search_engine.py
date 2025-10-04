"""
Основной поисковый движок для семантического поиска
"""

from typing import List, Dict, Any, Optional, Tuple
from utils.document_manager import DocumentManager, Document
from core.document_indexer import DocumentIndex
from core.text_processor import TextProcessor


class SearchResult:
    """Класс для представления результата поиска"""
    
    def __init__(self, document: Document, score: float, matched_keywords: List[str]):
        self.document = document
        self.score = score
        self.matched_keywords = matched_keywords
        self.snippet = self._generate_snippet()
    
    def _generate_snippet(self, max_length: int = 200) -> str:
        """Генерация краткого описания документа"""
        content = self.document.content
        
        if len(content) <= max_length:
            return content
        
        # Находим первое вхождение ключевого слова
        content_lower = content.lower()
        for keyword in self.matched_keywords:
            keyword_lower = keyword.lower()
            pos = content_lower.find(keyword_lower)
            if pos != -1:
                # Берем текст вокруг найденного ключевого слова
                start = max(0, pos - max_length // 2)
                end = min(len(content), start + max_length)
                
                snippet = content[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(content):
                    snippet = snippet + "..."
                
                return snippet
        
        # Если ключевые слова не найдены, берем начало документа
        return content[:max_length] + "..."
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование результата в словарь"""
        return {
            'doc_id': self.document.doc_id,
            'title': self.document.title,
            'score': self.score,
            'snippet': self.snippet,
            'matched_keywords': self.matched_keywords,
            'file_path': self.document.file_path,
            'metadata': self.document.metadata
        }


class SearchEngine:
    """Основной поисковый движок"""
    
    def __init__(self, data_dir: str = "data"):
        self.document_manager = DocumentManager(data_dir)
        self.index = DocumentIndex()
        self.text_processor = TextProcessor()
        
        # Переиндексация существующих документов
        self._reindex_documents()
    
    def _reindex_documents(self):
        """Переиндексация всех документов"""
        documents = self.document_manager.get_all_documents()
        for doc in documents:
            self.index.add_document(doc.doc_id, doc.content)
            # Обновляем обработанное содержимое в документе
            processed_content = self.text_processor.preprocess_text(doc.content)
            self.document_manager.update_document_content(doc.doc_id, processed_content)
        
        print(f"Переиндексировано {len(documents)} документов")
    
    def add_document(self, title: str, content: str, 
                    file_path: Optional[str] = None, 
                    metadata: Optional[Dict] = None) -> str:
        """Добавление нового документа"""
        # Добавляем документ в менеджер
        doc_id = self.document_manager.add_document(title, content, file_path, metadata)
        
        # Добавляем в индекс
        self.index.add_document(doc_id, content)
        
        # Обновляем обработанное содержимое
        processed_content = self.text_processor.preprocess_text(content)
        self.document_manager.update_document_content(doc_id, processed_content)
        
        return doc_id
    
    def remove_document(self, doc_id: str) -> bool:
        """Удаление документа"""
        success = self.document_manager.delete_document(doc_id)
        if success:
            self.index.remove_document(doc_id)
        return success
    
    def search(self, query: str, top_k: int = 10, 
              min_score: float = 0.01) -> List[SearchResult]:
        """
        Поиск документов по запросу
        
        Args:
            query: Поисковый запрос
            top_k: Количество результатов
            min_score: Минимальный балл релевантности
        
        Returns:
            Список результатов поиска
        """
        if not query.strip():
            return []
        
        # Выполняем поиск в индексе
        search_results = self.index.search(query, top_k * 2)  # Берем больше для фильтрации
        
        results = []
        processed_query = self.text_processor.preprocess_text(query)
        query_keywords = processed_query.split() if processed_query else []
        
        for doc_id, score in search_results:
            # Фильтруем по минимальному баллу
            if score < min_score:
                continue
            
            # Получаем документ
            document = self.document_manager.get_document(doc_id)
            if not document:
                continue
            
            # Определяем совпавшие ключевые слова
            matched_keywords = self._find_matched_keywords(
                document.processed_content, query_keywords
            )
            
            # Создаем результат поиска
            result = SearchResult(document, score, matched_keywords)
            results.append(result)
            
            if len(results) >= top_k:
                break
        
        return results
    
    def _find_matched_keywords(self, doc_content: str, query_keywords: List[str]) -> List[str]:
        """Поиск совпавших ключевых слов в документе"""
        matched = []
        doc_words = set(doc_content.split())
        
        for keyword in query_keywords:
            if keyword in doc_words:
                matched.append(keyword)
        
        return matched
    
    def search_by_title(self, query: str) -> List[Document]:
        """Поиск документов по заголовку"""
        return self.document_manager.search_by_title(query)
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """Получение документа по ID"""
        return self.document_manager.get_document(doc_id)
    
    def get_document_keywords(self, doc_id: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Получение ключевых слов документа"""
        return self.index.get_document_keywords(doc_id, top_k)
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики поисковой системы"""
        doc_stats = self.document_manager.get_stats()
        index_stats = self.index.get_stats()
        
        return {
            'documents': doc_stats,
            'index': index_stats,
            'total_documents': doc_stats['total_documents']
        }
    
    def rebuild_index(self):
        """Перестроение индекса"""
        print("Перестроение индекса...")
        
        # Очищаем индекс
        self.index = DocumentIndex()
        
        # Переиндексируем все документы
        self._reindex_documents()
        
        print("Индекс перестроен")
    
    def suggest_keywords(self, query: str, max_suggestions: int = 5) -> List[str]:
        """Предложение ключевых слов на основе запроса"""
        if not query.strip():
            return []
        
        # Обрабатываем запрос
        processed_query = self.text_processor.preprocess_text(query)
        if not processed_query:
            return []
        
        query_words = processed_query.split()
        suggestions = []
        
        # Ищем похожие слова в индексе
        for word in query_words:
            if word in self.index.inverted_index:
                # Берем слова, которые часто встречаются вместе с этим словом
                suggestions.append(word)
        
        return suggestions[:max_suggestions]

