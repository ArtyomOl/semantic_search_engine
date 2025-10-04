#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главное окно приложения семантического поиска
"""

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QListWidget, QListWidgetItem, QTabWidget,
                             QGroupBox, QGridLayout, QSpinBox, QDoubleSpinBox,
                             QFileDialog, QMessageBox, QSplitter, QFrame,
                             QProgressBar, QStatusBar, QMenuBar, QAction,
                             QDialog, QDialogButtonBox, QFormLayout, QComboBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPalette, QColor

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.search_engine import SearchEngine, SearchResult
from core.text_processor import TextProcessor


class SearchWorker(QThread):
    """Поток для выполнения поиска в фоновом режиме"""
    
    search_completed = pyqtSignal(list)
    search_error = pyqtSignal(str)
    
    def __init__(self, search_engine, query, top_k, min_score):
        super().__init__()
        self.search_engine = search_engine
        self.query = query
        self.top_k = top_k
        self.min_score = min_score
    
    def run(self):
        try:
            results = self.search_engine.search(self.query, self.top_k, self.min_score)
            self.search_completed.emit(results)
        except Exception as e:
            self.search_error.emit(str(e))


class DocumentDialog(QDialog):
    """Диалог для добавления/редактирования документа"""
    
    def __init__(self, parent=None, document=None):
        super().__init__(parent)
        self.document = document
        self.setup_ui()
        
        if document:
            self.load_document()
    
    def setup_ui(self):
        self.setWindowTitle("Добавить документ" if not self.document else "Редактировать документ")
        self.setModal(True)
        self.resize(600, 400)
        
        layout = QFormLayout()
        
        # Заголовок
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Введите заголовок документа...")
        layout.addRow("Заголовок:", self.title_edit)
        
        # Содержимое
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("Введите содержимое документа...")
        self.content_edit.setMinimumHeight(200)
        layout.addRow("Содержимое:", self.content_edit)
        
        # Файл (опционально)
        file_layout = QHBoxLayout()
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("Путь к файлу (опционально)")
        self.file_edit.setReadOnly(True)
        
        browse_btn = QPushButton("Обзор...")
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.file_edit)
        file_layout.addWidget(browse_btn)
        
        file_widget = QWidget()
        file_widget.setLayout(file_layout)
        layout.addRow("Файл:", file_widget)
        
        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл", "", 
            "Текстовые файлы (*.txt);;Все файлы (*)"
        )
        if file_path:
            self.file_edit.setText(file_path)
            # Автоматически загружаем содержимое файла
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.content_edit.setPlainText(content)
                    # Устанавливаем заголовок из имени файла
                    if not self.title_edit.text():
                        filename = os.path.basename(file_path)
                        self.title_edit.setText(filename)
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось прочитать файл: {e}")
    
    def load_document(self):
        if self.document:
            self.title_edit.setText(self.document.title)
            self.content_edit.setPlainText(self.document.content)
            if self.document.file_path:
                self.file_edit.setText(self.document.file_path)
    
    def get_document_data(self):
        return {
            'title': self.title_edit.text().strip(),
            'content': self.content_edit.toPlainText().strip(),
            'file_path': self.file_edit.text().strip() if self.file_edit.text().strip() else None
        }


class SearchResultsWidget(QWidget):
    """Виджет для отображения результатов поиска"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Заголовок
        header_label = QLabel("Результаты поиска")
        header_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(header_label)
        
        # Список результатов
        self.results_list = QListWidget()
        self.results_list.setAlternatingRowColors(True)
        self.results_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.results_list)
        
        # Область для отображения содержимого документа
        self.content_area = QTextEdit()
        self.content_area.setReadOnly(True)
        self.content_area.setMaximumHeight(200)
        layout.addWidget(self.content_area)
        
        self.setLayout(layout)
        
        # Хранилище результатов
        self.search_results = []
    
    def display_results(self, results):
        """Отображение результатов поиска"""
        self.search_results = results
        self.results_list.clear()
        self.content_area.clear()
        
        if not results:
            item = QListWidgetItem("Результаты не найдены")
            item.setData(Qt.UserRole, None)
            self.results_list.addItem(item)
            return
        
        for i, result in enumerate(results, 1):
            # Создаем текст для элемента списка
            text = f"{i}. {result.document.title}\n"
            text += f"   Релевантность: {result.score:.4f}\n"
            text += f"   Ключевые слова: {', '.join(result.matched_keywords)}"
            
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, result)
            self.results_list.addItem(item)
    
    def on_item_double_clicked(self, item):
        """Обработка двойного клика по результату"""
        result = item.data(Qt.UserRole)
        if result:
            self.content_area.setPlainText(result.snippet)
    
    def get_selected_result(self):
        """Получение выбранного результата"""
        current_item = self.results_list.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole)
        return None


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        self.search_engine = SearchEngine()
        self.search_worker = None
        
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()
        
        # Обновляем статистику
        self.update_statistics()
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.setWindowTitle("Система семантического поиска")
        self.setGeometry(100, 100, 1200, 800)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QHBoxLayout(central_widget)
        
        # Создаем разделитель
        splitter = QSplitter(Qt.Horizontal)
        
        # Левая панель - поиск и настройки
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Правая панель - результаты
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Устанавливаем пропорции
        splitter.setSizes([400, 800])
        
        main_layout.addWidget(splitter)
        
        # Применяем стили
        self.apply_styles()
    
    def create_left_panel(self):
        """Создание левой панели с поиском и настройками"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Поиск
        search_group = QGroupBox("Поиск")
        search_layout = QVBoxLayout(search_group)
        
        # Поле поиска
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите поисковый запрос...")
        self.search_input.returnPressed.connect(self.perform_search)
        search_layout.addWidget(self.search_input)
        
        # Кнопки поиска
        button_layout = QHBoxLayout()
        
        self.search_button = QPushButton("Поиск")
        self.search_button.clicked.connect(self.perform_search)
        button_layout.addWidget(self.search_button)
        
        self.clear_button = QPushButton("Очистить")
        self.clear_button.clicked.connect(self.clear_search)
        button_layout.addWidget(self.clear_button)
        
        search_layout.addLayout(button_layout)
        
        # Настройки поиска
        settings_layout = QGridLayout()
        
        settings_layout.addWidget(QLabel("Количество результатов:"), 0, 0)
        self.top_k_spinbox = QSpinBox()
        self.top_k_spinbox.setRange(1, 100)
        self.top_k_spinbox.setValue(10)
        settings_layout.addWidget(self.top_k_spinbox, 0, 1)
        
        settings_layout.addWidget(QLabel("Минимальная релевантность:"), 1, 0)
        self.min_score_spinbox = QDoubleSpinBox()
        self.min_score_spinbox.setRange(0.0, 1.0)
        self.min_score_spinbox.setSingleStep(0.01)
        self.min_score_spinbox.setValue(0.01)
        settings_layout.addWidget(self.min_score_spinbox, 1, 1)
        
        search_layout.addLayout(settings_layout)
        layout.addWidget(search_group)
        
        # Управление документами
        docs_group = QGroupBox("Управление документами")
        docs_layout = QVBoxLayout(docs_group)
        
        # Кнопки управления
        docs_button_layout = QVBoxLayout()
        
        self.add_doc_button = QPushButton("Добавить документ")
        self.add_doc_button.clicked.connect(self.add_document)
        docs_button_layout.addWidget(self.add_doc_button)
        
        self.delete_doc_button = QPushButton("Удалить документ")
        self.delete_doc_button.clicked.connect(self.delete_document)
        docs_button_layout.addWidget(self.delete_doc_button)
        
        self.rebuild_index_button = QPushButton("Перестроить индекс")
        self.rebuild_index_button.clicked.connect(self.rebuild_index)
        docs_button_layout.addWidget(self.rebuild_index_button)
        
        docs_layout.addLayout(docs_button_layout)
        layout.addWidget(docs_group)
        
        # Статистика
        stats_group = QGroupBox("Статистика")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_label = QLabel("Загрузка статистики...")
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)
        
        layout.addWidget(stats_group)
        
        # Растягивающийся элемент
        layout.addStretch()
        
        return panel
    
    def create_right_panel(self):
        """Создание правой панели с результатами"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Вкладки
        self.tab_widget = QTabWidget()
        
        # Вкладка поиска
        self.search_results_widget = SearchResultsWidget()
        self.tab_widget.addTab(self.search_results_widget, "Результаты поиска")
        
        # Вкладка документов
        self.documents_widget = self.create_documents_widget()
        self.tab_widget.addTab(self.documents_widget, "Все документы")
        
        layout.addWidget(self.tab_widget)
        
        return panel
    
    def create_documents_widget(self):
        """Создание виджета для отображения всех документов"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Заголовок
        header_label = QLabel("Все документы в системе")
        header_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(header_label)
        
        # Список документов
        self.documents_list = QListWidget()
        self.documents_list.setAlternatingRowColors(True)
        self.documents_list.itemDoubleClicked.connect(self.on_document_double_clicked)
        layout.addWidget(self.documents_list)
        
        # Обновляем список документов
        self.update_documents_list()
        
        return widget
    
    def setup_menu(self):
        """Настройка меню"""
        menubar = self.menuBar()
        
        # Меню "Файл"
        file_menu = menubar.addMenu('Файл')
        
        add_action = QAction('Добавить документ', self)
        add_action.triggered.connect(self.add_document)
        file_menu.addAction(add_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Выход', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню "Инструменты"
        tools_menu = menubar.addMenu('Инструменты')
        
        rebuild_action = QAction('Перестроить индекс', self)
        rebuild_action.triggered.connect(self.rebuild_index)
        tools_menu.addAction(rebuild_action)
        
        # Меню "Справка"
        help_menu = menubar.addMenu('Справка')
        
        about_action = QAction('О программе', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self):
        """Настройка строки состояния"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Прогресс-бар для поиска
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        self.status_bar.showMessage("Готов к работе")
    
    def apply_styles(self):
        """Применение стилей к интерфейсу"""
        style = """
        QMainWindow {
            background-color: #f0f0f0;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        QPushButton {
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 8px 16px;
            text-align: center;
            font-size: 14px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QPushButton:pressed {
            background-color: #3d8b40;
        }
        QLineEdit, QTextEdit {
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 5px;
        }
        QLineEdit:focus, QTextEdit:focus {
            border: 2px solid #4CAF50;
        }
        QListWidget {
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: white;
        }
        QListWidget::item {
            padding: 5px;
            border-bottom: 1px solid #eee;
        }
        QListWidget::item:selected {
            background-color: #4CAF50;
            color: white;
        }
        QListWidget::item:hover {
            background-color: #f0f8ff;
        }
        """
        self.setStyleSheet(style)
    
    def perform_search(self):
        """Выполнение поиска"""
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Предупреждение", "Введите поисковый запрос")
            return
        
        # Показываем прогресс
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Неопределенный прогресс
        self.search_button.setEnabled(False)
        self.status_bar.showMessage("Выполняется поиск...")
        
        # Запускаем поиск в отдельном потоке
        self.search_worker = SearchWorker(
            self.search_engine,
            query,
            self.top_k_spinbox.value(),
            self.min_score_spinbox.value()
        )
        self.search_worker.search_completed.connect(self.on_search_completed)
        self.search_worker.search_error.connect(self.on_search_error)
        self.search_worker.start()
    
    def on_search_completed(self, results):
        """Обработка завершения поиска"""
        self.progress_bar.setVisible(False)
        self.search_button.setEnabled(True)
        
        if results:
            self.search_results_widget.display_results(results)
            self.tab_widget.setCurrentIndex(0)  # Переключаемся на вкладку результатов
            self.status_bar.showMessage(f"Найдено {len(results)} результатов")
        else:
            self.search_results_widget.display_results([])
            self.status_bar.showMessage("Результаты не найдены")
    
    def on_search_error(self, error_message):
        """Обработка ошибки поиска"""
        self.progress_bar.setVisible(False)
        self.search_button.setEnabled(True)
        QMessageBox.critical(self, "Ошибка поиска", f"Произошла ошибка: {error_message}")
        self.status_bar.showMessage("Ошибка при выполнении поиска")
    
    def clear_search(self):
        """Очистка поиска"""
        self.search_input.clear()
        self.search_results_widget.display_results([])
        self.status_bar.showMessage("Поиск очищен")
    
    def add_document(self):
        """Добавление нового документа"""
        dialog = DocumentDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_document_data()
            if data['title'] and data['content']:
                try:
                    doc_id = self.search_engine.add_document(
                        title=data['title'],
                        content=data['content'],
                        file_path=data['file_path']
                    )
                    QMessageBox.information(self, "Успех", f"Документ добавлен с ID: {doc_id}")
                    self.update_statistics()
                    self.update_documents_list()
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось добавить документ: {e}")
            else:
                QMessageBox.warning(self, "Предупреждение", "Заполните заголовок и содержимое")
    
    def delete_document(self):
        """Удаление документа"""
        current_item = self.documents_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Предупреждение", "Выберите документ для удаления")
            return
        
        doc_id = current_item.data(Qt.UserRole)
        if doc_id:
            reply = QMessageBox.question(
                self, "Подтверждение", 
                f"Удалить документ '{self.search_engine.get_document(doc_id).title}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    success = self.search_engine.remove_document(doc_id)
                    if success:
                        QMessageBox.information(self, "Успех", "Документ удален")
                        self.update_statistics()
                        self.update_documents_list()
                    else:
                        QMessageBox.warning(self, "Предупреждение", "Не удалось удалить документ")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении: {e}")
    
    def rebuild_index(self):
        """Перестроение индекса"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Перестроить индекс? Это может занять некоторое время.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.search_engine.rebuild_index()
                QMessageBox.information(self, "Успех", "Индекс перестроен")
                self.update_statistics()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при перестроении индекса: {e}")
    
    def update_statistics(self):
        """Обновление статистики"""
        try:
            stats = self.search_engine.get_stats()
            doc_stats = stats['documents']
            index_stats = stats['index']
            
            stats_text = f"""
Документов: {doc_stats['total_documents']}
Уникальных слов: {index_stats['unique_words']}
Среднее слов в документе: {index_stats['average_words_per_document']:.1f}
Общий размер: {doc_stats['total_characters']} символов
            """.strip()
            
            self.stats_label.setText(stats_text)
        except Exception as e:
            self.stats_label.setText(f"Ошибка загрузки статистики: {e}")
    
    def update_documents_list(self):
        """Обновление списка документов"""
        self.documents_list.clear()
        
        try:
            documents = self.search_engine.document_manager.get_all_documents()
            for doc in documents:
                item_text = f"{doc.title}\nID: {doc.doc_id}\nСимволов: {len(doc.content)}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, doc.doc_id)
                self.documents_list.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить документы: {e}")
    
    def on_document_double_clicked(self, item):
        """Обработка двойного клика по документу"""
        doc_id = item.data(Qt.UserRole)
        if doc_id:
            doc = self.search_engine.get_document(doc_id)
            if doc:
                # Показываем содержимое документа в диалоге
                dialog = QDialog(self)
                dialog.setWindowTitle(f"Документ: {doc.title}")
                dialog.resize(800, 600)
                
                layout = QVBoxLayout(dialog)
                
                # Заголовок
                title_label = QLabel(doc.title)
                title_label.setFont(QFont("Arial", 14, QFont.Bold))
                layout.addWidget(title_label)
                
                # Содержимое
                content_text = QTextEdit()
                content_text.setPlainText(doc.content)
                content_text.setReadOnly(True)
                layout.addWidget(content_text)
                
                # Кнопки
                buttons = QDialogButtonBox(QDialogButtonBox.Close)
                buttons.rejected.connect(dialog.reject)
                layout.addWidget(buttons)
                
                dialog.exec_()
    
    def show_about(self):
        """Показ информации о программе"""
        QMessageBox.about(self, "О программе", 
                         "Система семантического поиска v1.0\n\n"
                         "Разработано для поиска по документам на русском языке\n"
                         "с использованием TF-IDF алгоритма.\n\n"
                         "Возможности:\n"
                         "• Семантический поиск\n"
                         "• Управление документами\n"
                         "• Обработка русского языка\n"
                         "• Современный интерфейс")


def main():
    """Главная функция"""
    app = QApplication(sys.argv)
    app.setApplicationName("Система семантического поиска")
    app.setApplicationVersion("1.0")
    
    # Создаем главное окно
    window = MainWindow()
    window.show()
    
    # Запускаем приложение
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
