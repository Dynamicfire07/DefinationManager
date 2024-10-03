import sys
import json
import random
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QHBoxLayout, QPushButton, QLineEdit, QTextEdit, QFileDialog, QMessageBox, QTableWidget,
    QTableWidgetItem, QLabel, QDialog, QInputDialog, QColorDialog, QGridLayout, QScrollArea
)
from PyQt6.QtWidgets import QStyle
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont, QColor

DATA_FILE = 'data.json'

# Data Models
class Definition:
    def __init__(self, phrase, meaning):
        self.phrase = phrase
        self.meaning = meaning

    def to_dict(self):
        return {'phrase': self.phrase, 'meaning': self.meaning}

    @staticmethod
    def from_dict(data):
        return Definition(data['phrase'], data['meaning'])


class Folder:
    def __init__(self, name, color=None):
        self.name = name
        self.color = color  # Store color as a hex string
        self.subfolders = []
        self.definitions = []

    def to_dict(self):
        return {
            'name': self.name,
            'color': self.color,
            'subfolders': [folder.to_dict() for folder in self.subfolders],
            'definitions': [definition.to_dict() for definition in self.definitions]
        }

    @staticmethod
    def from_dict(data):
        folder = Folder(data['name'], data.get('color'))
        folder.subfolders = [Folder.from_dict(sf) for sf in data.get('subfolders', [])]
        folder.definitions = [Definition.from_dict(d) for d in data.get('definitions', [])]
        return folder


# Definition Dialog
class DefinitionDialog(QDialog):
    def __init__(self, parent=None, definition=None):
        super().__init__(parent)
        self.setWindowTitle('Add Definition' if definition is None else 'Edit Definition')
        self.definition = definition
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.phrase_label = QLabel('Phrase:')
        self.phrase_input = QLineEdit()
        self.meaning_label = QLabel('Meaning:')
        self.meaning_input = QTextEdit()

        if self.definition:
            self.phrase_input.setText(self.definition.phrase)
            self.meaning_input.setText(self.definition.meaning)

        layout.addWidget(self.phrase_label)
        layout.addWidget(self.phrase_input)
        layout.addWidget(self.meaning_label)
        layout.addWidget(self.meaning_input)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton('Save')
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton('Cancel')
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)


# Search Dialog
class SearchDialog(QDialog):
    def __init__(self, parent, root_folder):
        super().__init__(parent)
        self.setWindowTitle('Search Definitions')
        self.root_folder = root_folder
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Search...')
        self.search_input.textChanged.connect(self.perform_search)
        layout.addWidget(self.search_input)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(['Phrase', 'Meaning', 'Folder'])
        self.result_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.result_table)

        self.setLayout(layout)
        self.definitions = self.collect_definitions(self.root_folder)
        self.perform_search()

    def collect_definitions(self, folder, path='Root'):
        defs = []
        current_path = f"{path}/{folder.name}" if folder != self.root_folder else path
        for definition in folder.definitions:
            defs.append((definition, current_path))
        for subfolder in folder.subfolders:
            defs.extend(self.collect_definitions(subfolder, current_path))
        return defs

    def perform_search(self):
        query = self.search_input.text().lower()
        results = []
        for definition, folder_path in self.definitions:
            if query in definition.phrase.lower() or query in definition.meaning.lower():
                results.append((definition, folder_path))
        self.result_table.setRowCount(len(results))
        for row, (definition, folder_path) in enumerate(results):
            phrase_item = QTableWidgetItem(definition.phrase)
            meaning_item = QTableWidgetItem(definition.meaning)
            folder_item = QTableWidgetItem(folder_path)
            self.result_table.setItem(row, 0, phrase_item)
            self.result_table.setItem(row, 1, meaning_item)
            self.result_table.setItem(row, 2, folder_item)


# All Definitions Dialog
class AllDefinitionsDialog(QDialog):
    def __init__(self, parent, root_folder):
        super().__init__(parent)
        self.setWindowTitle('All Words and Definitions')
        self.root_folder = root_folder
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Filter input
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText('Filter by phrase, meaning, or folder...')
        self.filter_input.textChanged.connect(self.update_table)
        layout.addWidget(self.filter_input)

        # Table to display definitions
        self.def_table = QTableWidget()
        self.def_table.setColumnCount(3)
        self.def_table.setHorizontalHeaderLabels(['Phrase', 'Meaning', 'Folder'])
        self.def_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.def_table)

        self.setLayout(layout)
        self.definitions = self.collect_definitions(self.root_folder)
        self.update_table()

    def collect_definitions(self, folder, path='Root'):
        defs = []
        current_path = f"{path}/{folder.name}" if folder != self.root_folder else path
        for definition in folder.definitions:
            defs.append((definition, current_path))
        for subfolder in folder.subfolders:
            defs.extend(self.collect_definitions(subfolder, current_path))
        return defs

    def update_table(self):
        query = self.filter_input.text().lower()
        filtered_defs = []
        for definition, folder_path in self.definitions:
            if (query in definition.phrase.lower() or
                query in definition.meaning.lower() or
                query in folder_path.lower()):
                filtered_defs.append((definition, folder_path))
        self.def_table.setRowCount(len(filtered_defs))
        for row, (definition, folder_path) in enumerate(filtered_defs):
            phrase_item = QTableWidgetItem(definition.phrase)
            meaning_item = QTableWidgetItem(definition.meaning)
            folder_item = QTableWidgetItem(folder_path)
            self.def_table.setItem(row, 0, phrase_item)
            self.def_table.setItem(row, 1, meaning_item)
            self.def_table.setItem(row, 2, folder_item)


# Flashcard Dialog
class FlashcardDialog(QDialog):
    def __init__(self, parent, definitions):
        super().__init__(parent)
        self.setWindowTitle('Flashcards')
        self.definitions = definitions
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.phrase_label = QLabel('')
        self.phrase_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.phrase_label.setStyleSheet('font-size: 24px;')
        layout.addWidget(self.phrase_label)

        self.meaning_label = QLabel('')
        self.meaning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.meaning_label.setStyleSheet('font-size: 18px; color: gray;')
        layout.addWidget(self.meaning_label)

        btn_layout = QHBoxLayout()
        self.show_meaning_btn = QPushButton('Show Meaning')
        self.show_meaning_btn.clicked.connect(self.show_meaning)
        self.next_btn = QPushButton('Next')
        self.next_btn.clicked.connect(self.next_flashcard)
        btn_layout.addWidget(self.show_meaning_btn)
        btn_layout.addWidget(self.next_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        random.shuffle(self.definitions)
        self.current_index = -1
        self.next_flashcard()

    def show_meaning(self):
        if 0 <= self.current_index < len(self.definitions):
            meaning = self.definitions[self.current_index].meaning
            self.meaning_label.setText(meaning)

    def next_flashcard(self):
        self.current_index += 1
        if self.current_index >= len(self.definitions):
            QMessageBox.information(self, 'Info', 'No more flashcards.')
            self.close()
            return
        phrase = self.definitions[self.current_index].phrase
        self.phrase_label.setText(phrase)
        self.meaning_label.setText('')


# Main Application Window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Definition Manager')
        self.resize(1000, 700)

        self.root_folder = Folder('Root')
        self.current_folder = self.root_folder
        self.folder_stack = [self.root_folder]  # To keep track of navigation

        self.load_data()
        self.init_ui()

    def init_ui(self):
        # Main layout
        main_layout = QHBoxLayout()

        # Sidebar
        self.sidebar = QVBoxLayout()

        self.back_btn = QPushButton('◀ Back')
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setEnabled(False)
        self.sidebar.addWidget(self.back_btn)

        self.add_folder_btn = QPushButton('Add Folder')
        self.add_folder_btn.clicked.connect(self.add_folder)
        self.sidebar.addWidget(self.add_folder_btn)

        self.add_def_btn = QPushButton('Add Definition')
        self.add_def_btn.clicked.connect(self.add_definition)
        self.sidebar.addWidget(self.add_def_btn)

        self.change_color_btn = QPushButton('Change Folder Color')
        self.change_color_btn.clicked.connect(self.change_folder_color)
        self.sidebar.addWidget(self.change_color_btn)

        self.import_btn = QPushButton('Import')
        self.import_btn.clicked.connect(self.import_data)
        self.sidebar.addWidget(self.import_btn)

        self.export_btn = QPushButton('Export')
        self.export_btn.clicked.connect(self.export_data)
        self.sidebar.addWidget(self.export_btn)

        self.save_btn = QPushButton('Save Data')
        self.save_btn.clicked.connect(self.save_data)
        self.sidebar.addWidget(self.save_btn)

        self.search_btn = QPushButton('Search')
        self.search_btn.clicked.connect(self.open_search)
        self.sidebar.addWidget(self.search_btn)

        self.all_defs_btn = QPushButton('All Words and Definitions')
        self.all_defs_btn.clicked.connect(self.open_all_definitions)
        self.sidebar.addWidget(self.all_defs_btn)

        self.flashcard_btn = QPushButton('Flashcards')
        self.flashcard_btn.clicked.connect(self.open_flashcards)
        self.sidebar.addWidget(self.flashcard_btn)

        self.sidebar.addStretch()

        # Styling buttons
        button_style = """
        QPushButton {
            background-color: #2E8B57;
            color: white;
            border-radius: 5px;
            padding: 10px 20px;
            margin: 5px;
            font-size: 14px;
        }
        QPushButton:hover {
            background-color: #3CB371;
        }
        """
        for btn in [self.back_btn, self.add_folder_btn, self.add_def_btn, self.change_color_btn,
                    self.import_btn, self.export_btn, self.save_btn, self.search_btn, self.all_defs_btn, self.flashcard_btn]:
            btn.setStyleSheet(button_style)

        # Content Area
        self.content_layout = QVBoxLayout()

        # Folder path label
        self.path_label = QLabel('Root')
        font = QFont()
        font.setPointSize(14)
        self.path_label.setFont(font)
        self.content_layout.addWidget(self.path_label)

        # Scroll area for content
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.content_layout.addWidget(self.scroll_area)

        # Set layouts
        main_layout.addLayout(self.sidebar)
        main_layout.addLayout(self.content_layout)

        # Set main widget
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.update_content()

    def update_content(self):
        self.path_label.setText(' / '.join([folder.name for folder in self.folder_stack]))

        # Determine if current folder contains subfolders or definitions
        has_subfolders = len(self.current_folder.subfolders) > 0
        has_definitions = len(self.current_folder.definitions) > 0

        if has_subfolders and has_definitions:
            QMessageBox.warning(self, 'Error', 'A folder cannot contain both subfolders and definitions.')
            self.current_folder.definitions.clear()
            self.save_data()

        if has_subfolders:
            # Display subfolders in grid view
            widget = QWidget()
            grid_layout = QGridLayout()
            widget.setLayout(grid_layout)
            row = 0
            col = 0
            for idx, folder in enumerate(self.current_folder.subfolders):
                button = QPushButton(folder.name)
                folder_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
                button.setIcon(folder_icon)
                button.setIconSize(QSize(64, 64))
                button.setMinimumSize(150, 150)
                button.setStyleSheet(f"background-color: transparent; border: none;")
                button.clicked.connect(lambda checked, f=folder: self.enter_folder(f))
                grid_layout.addWidget(button, row, col)
                col += 1
                if col >= 4:
                    col = 0
                    row += 1
            self.scroll_area.setWidget(widget)
        elif has_definitions:
            # Display definitions in a table
            widget = QWidget()
            v_layout = QVBoxLayout()
            widget.setLayout(v_layout)

            table = QTableWidget()
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(['Phrase', 'Meaning'])
            table.horizontalHeader().setStretchLastSection(True)
            table.setRowCount(len(self.current_folder.definitions))
            for row, definition in enumerate(self.current_folder.definitions):
                phrase_item = QTableWidgetItem(definition.phrase)
                meaning_item = QTableWidgetItem(definition.meaning)
                table.setItem(row, 0, phrase_item)
                table.setItem(row, 1, meaning_item)
            v_layout.addWidget(table)
            self.scroll_area.setWidget(widget)
        else:
            # Empty folder
            widget = QWidget()
            v_layout = QVBoxLayout()
            v_layout.addWidget(QLabel('This folder is empty.'))
            widget.setLayout(v_layout)
            self.scroll_area.setWidget(widget)

        self.back_btn.setEnabled(len(self.folder_stack) > 1)

    def enter_folder(self, folder):
        self.folder_stack.append(folder)
        self.current_folder = folder
        self.update_content()

    def go_back(self):
        if len(self.folder_stack) > 1:
            self.folder_stack.pop()
            self.current_folder = self.folder_stack[-1]
            self.update_content()

    def add_folder(self):
        if self.current_folder.definitions:
            QMessageBox.warning(self, 'Error', 'Cannot add a folder here. This folder contains definitions.')
            return
        name, ok = QInputDialog.getText(self, 'Add Folder', 'Folder Name:')
        if ok and name:
            new_folder = Folder(name)
            self.current_folder.subfolders.append(new_folder)
            self.update_content()
            self.save_data()

    def add_definition(self):
        if self.current_folder.subfolders:
            QMessageBox.warning(self, 'Error', 'Cannot add definitions here. This folder contains subfolders.')
            return
        def_dialog = DefinitionDialog(self)
        if def_dialog.exec():
            phrase = def_dialog.phrase_input.text()
            meaning = def_dialog.meaning_input.toPlainText()
            if phrase and meaning:
                new_def = Definition(phrase, meaning)
                self.current_folder.definitions.append(new_def)
                self.update_content()
                self.save_data()

    def change_folder_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_folder.color = color.name()
            self.update_content()
            self.save_data()

    def import_data(self):
        options = QFileDialog.Option.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(
            self, 'Import Data', '', 'All Supported Files (*.json *.csv *.xlsx);;JSON Files (*.json);;CSV Files (*.csv);;Excel Files (*.xlsx)', options=options)
        if file_name:
            file_extension = file_name.split('.')[-1].lower()
            if file_extension == 'json':
                self.import_json(file_name)
            elif file_extension in ['csv', 'xlsx']:
                self.import_tabular_data(file_name, file_extension)
            else:
                QMessageBox.warning(self, 'Error', 'Unsupported file type.')

    def import_json(self, file_name):
        try:
            with open(file_name, 'r') as f:
                data = json.load(f)
                new_data = Folder.from_dict(data)
                # Ensure that the current folder can accept the imported data
                if self.current_folder.subfolders:
                    if new_data.subfolders or new_data.definitions:
                        QMessageBox.warning(self, 'Error', 'Cannot import data here. This folder contains subfolders.')
                        return
                elif self.current_folder.definitions:
                    if new_data.subfolders or new_data.definitions:
                        QMessageBox.warning(self, 'Error', 'Cannot import data here. This folder contains definitions.')
                        return
                self.current_folder.subfolders.extend(new_data.subfolders)
                self.current_folder.definitions.extend(new_data.definitions)
                self.update_content()
                self.save_data()
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to import data: {e}')

    def import_tabular_data(self, file_name, file_type):
        try:
            if self.current_folder.subfolders:
                QMessageBox.warning(self, 'Error', 'Cannot import definitions here. This folder contains subfolders.')
                return
            if file_type == 'csv':
                df = pd.read_csv(file_name)
            elif file_type == 'xlsx':
                df = pd.read_excel(file_name)
            else:
                QMessageBox.warning(self, 'Error', 'Unsupported file type.')
                return

            # Check required columns
            if 'Phrase' not in df.columns or 'Meaning' not in df.columns:
                QMessageBox.warning(
                    self, 'Error', 'CSV/XLSX file must contain "Phrase" and "Meaning" columns.')
                return

            # Add definitions to the current folder
            for index, row in df.iterrows():
                phrase = str(row['Phrase'])
                meaning = str(row['Meaning'])
                new_def = Definition(phrase, meaning)
                self.current_folder.definitions.append(new_def)

            self.update_content()
            self.save_data()
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to import data: {e}')

    def export_data(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self, 'Export Data', '', 'JSON Files (*.json)')
        if file_name:
            try:
                with open(file_name, 'w') as f:
                    json.dump(self.root_folder.to_dict(), f, indent=4)
            except Exception as e:
                QMessageBox.warning(self, 'Error', f'Failed to export data: {e}')

    def open_search(self):
        search_dialog = SearchDialog(self, self.root_folder)
        search_dialog.exec()

    def open_all_definitions(self):
        all_defs_dialog = AllDefinitionsDialog(self, self.root_folder)
        all_defs_dialog.exec()

    def open_flashcards(self):
        definitions = self.collect_definitions(self.current_folder)
        if definitions:
            flashcard_dialog = FlashcardDialog(self, definitions)
            flashcard_dialog.exec()
        else:
            QMessageBox.information(self, 'Info', 'No definitions available for flashcards.')

    def collect_definitions(self, folder):
        defs = folder.definitions.copy()
        for subfolder in folder.subfolders:
            defs.extend(self.collect_definitions(subfolder))
        return defs

    def save_data(self):
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(self.root_folder.to_dict(), f, indent=4)
            QMessageBox.information(self, 'Info', 'Data saved successfully.')
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to save data: {e}')

    def load_data(self):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                self.root_folder = Folder.from_dict(data)
                self.current_folder = self.root_folder
                self.folder_stack = [self.root_folder]
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Failed to load data: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
