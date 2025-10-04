"""
Менеджер для работы с документами
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class Document:
    """Класс для представления документа"""
    
    def __init__(self, doc_id: str, title: str, content: str, 
                 file_path: Optional[str] = None, metadata: Optional[Dict] = None):
        self.doc_id = doc_id
        self.title = title
        self.content = content
        self.file_path = file_path
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat()
        self.processed_content = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование документа в словарь"""
        return {
            'doc_id': self.doc_id,
            'title': self.title,
            'content': self.content,
            'file_path': self.file_path,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'processed_content': self.processed_content
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """Создание документа из словаря"""
        doc = cls(
            doc_id=data['doc_id'],
            title=data['title'],
            content=data['content'],
            file_path=data.get('file_path'),
            metadata=data.get('metadata', {})
        )
        doc.created_at = data.get('created_at', datetime.now().isoformat())
        doc.processed_content = data.get('processed_content', "")
        return doc


class DocumentManager:
    """Менеджер для работы с документами"""
    
    def __init__(self, data_dir: str = "data", index_file: str = "documents.json"):
        self.data_dir = Path(data_dir)
        self.index_file = self.data_dir / index_file
        self.documents: Dict[str, Document] = {}
        self._ensure_data_dir()
        self._load_documents()
    
    def _ensure_data_dir(self):
        """Создание директории для данных если она не существует"""
        self.data_dir.mkdir(exist_ok=True)
    
    def _load_documents(self):
        """Загрузка документов из файла индекса"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for doc_data in data.get('documents', []):
                        doc = Document.from_dict(doc_data)
                        self.documents[doc.doc_id] = doc
                print(f"Загружено {len(self.documents)} документов")
            except Exception as e:
                print(f"Ошибка при загрузке документов: {e}")
                self.documents = {}
    
    def _save_documents(self):
        """Сохранение документов в файл индекса"""
        try:
            data = {
                'documents': [doc.to_dict() for doc in self.documents.values()],
                'last_updated': datetime.now().isoformat()
            }
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка при сохранении документов: {e}")
    
    def add_document(self, title: str, content: str, 
                    file_path: Optional[str] = None, 
                    metadata: Optional[Dict] = None) -> str:
        """Добавление нового документа"""
        doc_id = f"doc_{len(self.documents) + 1}_{hash(content) % 10000}"
        
        # Проверяем, не существует ли уже такой документ
        for existing_doc in self.documents.values():
            if existing_doc.content == content:
                print(f"Документ с таким содержимым уже существует: {existing_doc.doc_id}")
                return existing_doc.doc_id
        
        doc = Document(
            doc_id=doc_id,
            title=title,
            content=content,
            file_path=file_path,
            metadata=metadata
        )
        
        self.documents[doc_id] = doc
        self._save_documents()
        print(f"Добавлен документ: {doc_id}")
        return doc_id
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """Получение документа по ID"""
        return self.documents.get(doc_id)
    
    def get_all_documents(self) -> List[Document]:
        """Получение всех документов"""
        return list(self.documents.values())
    
    def update_document_content(self, doc_id: str, processed_content: str):
        """Обновление обработанного содержимого документа"""
        if doc_id in self.documents:
            self.documents[doc_id].processed_content = processed_content
            self._save_documents()
    
    def delete_document(self, doc_id: str) -> bool:
        """Удаление документа"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            self._save_documents()
            print(f"Документ {doc_id} удален")
            return True
        return False
    
    def search_by_title(self, query: str) -> List[Document]:
        """Поиск документов по заголовку"""
        query_lower = query.lower()
        results = []
        for doc in self.documents.values():
            if query_lower in doc.title.lower():
                results.append(doc)
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики по документам"""
        total_docs = len(self.documents)
        total_chars = sum(len(doc.content) for doc in self.documents.values())
        avg_chars = total_chars / total_docs if total_docs > 0 else 0
        
        return {
            'total_documents': total_docs,
            'total_characters': total_chars,
            'average_characters_per_document': avg_chars,
            'index_file_size': self.index_file.stat().st_size if self.index_file.exists() else 0
        }

