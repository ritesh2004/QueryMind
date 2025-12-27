from nt import error
import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QScrollArea, QTabWidget, QFrame, 
                             QGridLayout, QSpacerItem, QSizePolicy, QMessageBox, QComboBox)
from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtGui import QFont, QIcon, QColor, QPalette
from PySide6 import QtGui

from agent import OllamaAgent
from dbManager import DatabaseManager
import subprocess
import json
import re
from datetime import datetime
import os

# Custom CSS for modern look
STYLE_SHEET = """
QMainWindow {
    background-color: #ffffff;
}

QTabWidget::pane {
    border-top: 1px solid #e5e7eb;
    background: white;
}

QTabBar::tab {
    background: transparent;
    padding: 10px 20px;
    font-size: 14px;
    color: #6b7280;
    border-bottom: 2px solid transparent;
}

QTabBar::tab:selected {
    color: #111827;
    font-weight: bold;
    border-bottom: 2px solid #3b82f6;
}

/* Common Header Styles */
.Title {
    font-size: 20px;
    font-weight: bold;
    color: #111827;
}

.SubTitle {
    font-size: 13px;
    color: #6b7280;
}

/* Input Styles */
QLineEdit, QTextEdit {
    background-color: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 8px;
    color: #111827;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #3b82f6;
}

QPushButton#PrimaryButton {
    background-color: #111827;
    color: white;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
}

QPushButton#PrimaryButton:hover {
    background-color: #374151;
}

QPushButton#IconButton {
    border: none;
    background: transparent;
}
"""
DBManager = None
global model_name_global

basedir = os.path.dirname(__file__)

class ChatInput(QTextEdit):
    """Custom text edit to handle Enter vs Shift+Enter."""
    returnPressed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self.setPlaceholderText("Ask me anything about your database... (e.g., 'Show me all users who signed up last month')")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.modifiers() & Qt.ShiftModifier:
                super().keyPressEvent(event)
            else:
                self.returnPressed.emit()
        else:
            super().keyPressEvent(event)

class ChatMessage(QFrame):
    """A widget representing a single message bubble."""
    def __init__(self, text, is_assistant=True, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        # In a real app, you'd style bubbles differently for User vs Assistant
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {'#f3f4f6' if is_assistant else '#eff6ff'};
                border-radius: 12px;
                margin: 5px;
            }}
        """)
        
        msg_label = QLabel(text)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("color: #111827; background: transparent; border: none;")
        
        time = datetime.now()
        time_label = QLabel(time.strftime("%I:%M %p")) # Placeholder timestamp
        time_label.setStyleSheet("color: #9ca3af; font-size: 10px; background: transparent; border: none;")
        time_label.setAlignment(Qt.AlignRight)
        
        layout.addWidget(msg_label)
        layout.addWidget(time_label)

class ChatTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QVBoxLayout()
        title = QLabel("Database Chat Assistant")
        title.setProperty("class", "Title")
        sub = QLabel("Query your database using natural language")
        sub.setProperty("class", "SubTitle")
        header_layout.addWidget(title)
        header_layout.addWidget(sub)
        layout.addLayout(header_layout)

        # Chat Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setMinimumHeight(400)  # Set minimum height
        self.scroll_content = QWidget()
        self.chat_layout = QVBoxLayout(self.scroll_content)
        self.chat_layout.addStretch()
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll, 1)  # Add with stretch factor to take available space
        
        # self.model_name = model_name_global

        # Welcome Message
        welcome = ChatMessage("Hello! I'm your database assistant. Ask me anything about your data in natural language, and I'll convert it to SQL and retrieve the results for you.")
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, welcome)

        # Input Area
        input_container = QVBoxLayout()
        self.text_input = ChatInput()
        self.text_input.returnPressed.connect(self.send_message)
        
        instruction = QLabel("Press Enter to send, Shift+Enter for new line")
        instruction.setStyleSheet("color: #9ca3af; font-size: 11px;")
        
        input_row = QHBoxLayout()
        input_row.addWidget(self.text_input)
        
        send_btn = QPushButton("➤") # Unicode placeholder for icon
        send_btn.setFixedSize(40, 40)
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.clicked.connect(self.send_message)
        send_btn.setStyleSheet("background-color: #111827; color: white; border-radius: 20px; font-size: 18px;")
        
        input_row.addWidget(send_btn)
        
        input_container.addLayout(input_row)
        input_container.addWidget(instruction)
        layout.addLayout(input_container)

    def scroll_to_bottom(self):
        QTimer.singleShot(100, lambda: self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum()))

    def send_message(self):
        text = self.text_input.toPlainText().strip()
        if not text:
            return
            
        # Add user message
        user_msg = ChatMessage(text, is_assistant=False)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, user_msg)
        self.text_input.clear()
        self.scroll_to_bottom()
        
        # Show typing indicator
        self.typing_indicator = QLabel("Assistant is thinking...")
        self.typing_indicator.setStyleSheet("color: #6b7280; font-style: italic;")
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, self.typing_indicator)
        self.scroll_to_bottom()
        
        try:
            if not DBManager:
                self.show_error("Database not connected")
                return
                
            tables = DBManager.extract_all_tables()
            schemas = DBManager.describe_all_tables()
            
            schema_str = ""
            for table, columns in schemas.items():
                schema_str += f"\nTable: {table}\n"
                for col in columns:
                    schema_str += f"- {col[0]} ({col[1]})\n"
            print(model_name_global)
            self.agent = OllamaAgent(
                query=text,
                model_name=model_name_global,
                db_schema=schema_str,
                db_tables=tables
            )
            
            self.agent.response_received.connect(self.handle_agent_response)
            self.agent.error_occurred.connect(self.handle_agent_error)
            self.agent.start()
            
        except Exception as e:
            self.show_error(f"Error: {str(e)}")
            self.remove_typing_indicator()
            
        
    def handle_agent_response(self, response_type: str, content: str):
        if response_type == "sql":
            extracted_content = re.sub(r"```sql|```", "", content).strip()
            self.remove_typing_indicator()
            if self.is_sql_query(extracted_content):
                sql_msg = ChatMessage(extracted_content, is_assistant=True)
                self.chat_layout.insertWidget(self.chat_layout.count() - 1, sql_msg)
                self.scroll_to_bottom()
                
                container = QWidget()
                layout = QHBoxLayout(container)
                
                execute_btn = QPushButton("Execute Query")
                execute_btn.clicked.connect(lambda: self.execute_sql_query(extracted_content))
                
                copy_btn = QPushButton("Copy SQL")
                copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(extracted_content))
                
                layout.addWidget(execute_btn)
                layout.addWidget(copy_btn)
                
                self.chat_layout.insertWidget(self.chat_layout.count() - 1, container)
                self.scroll_to_bottom()
            else:
                error_message = ChatMessage("Please ask about the database", is_assistant=True)
                self.chat_layout.insertWidget(self.chat_layout.count() - 1, error_message)
                self.scroll_to_bottom()
                
    def handle_agent_error(self, error_message: str):
        self.show_error(f"Agent error: {error_message}")
        
    def execute_sql_query(self, query: str):
        try:
            if not DBManager.connect():
                raise Exception("Not connected to database")
                
            # Show executing message
            executing_msg = ChatMessage("Executing query...", is_assistant=True)
            self.chat_layout.insertWidget(self.chat_layout.count() - 1, executing_msg)
            self.scroll_to_bottom()
            
            sql = re.sub(r"```sql|```", "", query).strip() # Extract query
            results = DBManager.query_database(sql)
            
            # Display results
            if isinstance(results, str):  # Error message
                result_msg = ChatMessage(f"❌ Error: {results}", is_assistant=True)
            else:
                if not results:
                    result_text = "No results found."
                else:
                    columns = DBManager.get_last_columns()
                    
                    table_rows = []
                    if columns:
                        table_rows.append("| " + " | ".join(columns) + " |")
                        table_rows.append("|" + "|".join(["---"] * len(columns)) + "|")
                    
                    for row in results:
                        table_rows.append("| " + " | ".join(str(cell) for cell in row) + " |")
                    
                    result_text = "\n".join(table_rows)
                
                result_msg = ChatMessage(f"✅ Query executed successfully:\n\n{result_text}", is_assistant=True)
            
            self.chat_layout.insertWidget(self.chat_layout.count() - 1, result_msg)
            self.scroll_to_bottom()
            
        except Exception as e:
            error_msg = ChatMessage(f"❌ Error executing query: {str(e)}", is_assistant=True)
            self.chat_layout.insertWidget(self.chat_layout.count() - 1, error_msg)
            self.scroll_to_bottom()
        finally:
            pass
        
    def is_sql_query(self, query: str) -> bool:
        if not query:
            return False

        sql_keywords = (
            "select", "insert", "update", "delete",
            "create", "drop", "alter", "truncate",
            "with", "show", "describe", "explain"
        )

        query = query.strip().lower()
        return query.startswith(sql_keywords)

    def remove_typing_indicator(self):
        if hasattr(self, 'typing_indicator'):
            self.typing_indicator.deleteLater()
            del self.typing_indicator
            
    def show_error(self, message: str):
        error_msg = ChatMessage(f"❌ {message}", is_assistant=True)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, error_msg)
        self.remove_typing_indicator()
        
    def update_status(self, status: str):
        if hasattr(self, 'status_bar'):
            self.status_bar.showMessage(status)
                        
            

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(25)
        
        self.is_db_connected = False
        self.model = None
        self.config = {}
        
        self.load_settings()
        self.setup_ui()
        self.load_settings_to_ui()
        
        global model_name_global
        model_name_global = self.config["model"]["name"]

        # Header
        header_layout = QVBoxLayout()
        title = QLabel("Settings & Configuration")
        title.setProperty("class", "Title")
        sub = QLabel("Configure your database connection and LLM model preferences")
        sub.setProperty("class", "SubTitle")
        header_layout.addWidget(title)
        header_layout.addWidget(sub)
        layout.addLayout(header_layout)

        # Database Section
        db_group = QWidget()
        db_layout = QVBoxLayout(db_group)
        db_layout.setContentsMargins(0, 0, 0, 0)
        
        db_title = QLabel("Database Configuration")
        db_title.setStyleSheet("font-weight: bold; font-size: 15px; color: #111827;")
        db_sub = QLabel("Enter your database connection details")
        db_sub.setProperty("class", "SubTitle")
        
        db_layout.addWidget(db_title)
        db_layout.addWidget(db_sub)
        db_layout.addSpacing(10)

        form = QGridLayout()
        form.setSpacing(15)
        
        # Form Fields
        fields = [
            ("db_type", "Database Type", "postgresql/mysql"),
            ("db_name", "Database Name", "my_database"),    
            ("host", "Host", "localhost"),
            ("port", "Port", "5432"),
            ("username", "Username", "username")
        ]
        
        db_type_lbl = QLabel("Database Type")
        db_type_lbl.setStyleSheet("color: #374151; font-weight: 500;")
        self.db_type_input.setPlaceholderText("postgresql/mysql")
        
        db_name_lbl = QLabel("Database Name")
        db_name_lbl.setStyleSheet("color: #374151; font-weight: 500;")
        self.db_name_input.setPlaceholderText("my_database")
        
        host_lbl = QLabel("Host")
        host_lbl.setStyleSheet("color: #374151; font-weight: 500;")
        self.host_input.setPlaceholderText("localhost")
        
        port_lbl = QLabel("Port")
        port_lbl.setStyleSheet("color: #374151; font-weight: 500;")
        self.port_input.setPlaceholderText("3306")
        
        username_lbl = QLabel("Username")
        username_lbl.setStyleSheet("color: #374151; font-weight: 500;")
        self.username_input.setPlaceholderText("root")
        
        password_lbl = QLabel("Password")
        password_lbl.setStyleSheet("color: #374151; font-weight: 500;")
        self.password_input.setPlaceholderText("Enter Password")
        
        form.addWidget(db_type_lbl, 0, 0)
        form.addWidget(self.db_type_input, 0, 1)
        form.addWidget(db_name_lbl, 1, 0)
        form.addWidget(self.db_name_input, 1, 1)
        form.addWidget(host_lbl, 2, 0)
        form.addWidget(self.host_input, 2, 1)
        form.addWidget(port_lbl, 3, 0)
        form.addWidget(self.port_input, 3, 1)
        form.addWidget(username_lbl, 4, 0)
        form.addWidget(self.username_input, 4, 1)
        form.addWidget(password_lbl, 5, 0)
        form.addWidget(self.password_input, 5, 1)

        db_layout.addLayout(form)
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setObjectName("PrimaryButton")
        self.connect_btn.setFixedWidth(150)
        
        self.connect_btn.clicked.connect(self.connect_db)
        
        db_layout.addSpacing(10)
        db_layout.addWidget(self.connect_btn)
        
        layout.addWidget(db_group)

        # LLM Section Placeholder
        llm_group = QWidget()
        llm_layout = QVBoxLayout(llm_group)
        llm_layout.setContentsMargins(0, 0, 0, 0)
        
        llm_title = QLabel("LLM Model Configuration")
        llm_title.setStyleSheet("font-weight: bold; font-size: 15px; color: #111827;")
        llm_sub = QLabel("Configure your LLM model preferences")
        llm_sub.setProperty("class", "SubTitle")
        
        llm_layout.addWidget(llm_title)
        llm_layout.addWidget(llm_sub)
        llm_layout.addSpacing(10)
        
        form_llm = QGridLayout()
        form_llm.setSpacing(15)
        
        ollama_installed_lbl = QLabel("Check Ollama Installed or not: ")
        ollama_installed_lbl.setStyleSheet("color: #374151; font-weight: 500;")
        ollama_test_btn = QPushButton("Check")
        ollama_test_btn.setObjectName("PrimaryButton")
        ollama_test_btn.clicked.connect(self.check_ollama_installed)
        
        info_lbl = QLabel("Note: Ensure Ollama is installed and running locally.")
        info_lbl.setStyleSheet("color: #9ca3af; font-size: 11px;")
        
        choose_model_lbl = QLabel("Choose Model: ")
        choose_model_lbl.setStyleSheet("color: #374151; font-weight: 500;")
        
        models = ["Select Model"]
        models.extend(self.list_ollama_models())
        
        self.choose_model_edit.addItems(models)
        self.choose_model_edit.currentIndexChanged.connect(lambda: self.update_model(self.choose_model_edit.currentText()))
        
        
        pull_models_ins = QLabel("Pull models using 'ollama pull <model_name>' command in terminal.")
        pull_models_ins.setStyleSheet("color: #9ca3af; font-size: 11px;")
        
        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("PrimaryButton")
        save_btn.clicked.connect(self.save_settings)

        form_llm.addWidget(ollama_installed_lbl, 0, 0)
        form_llm.addWidget(ollama_test_btn, 0, 1)
        form_llm.addWidget(info_lbl, 1, 0, 1, 2)
        form_llm.addWidget(choose_model_lbl, 2, 0)
        form_llm.addWidget(self.choose_model_edit, 2, 1)
        form_llm.addWidget(pull_models_ins, 3, 0, 1, 2)

        llm_layout.addLayout(form_llm)

        layout.addWidget(llm_group)
        layout.addWidget(save_btn)
        layout.addStretch()
        
        
    def update_model(self, model_name):
        global model_name_global
        model_name_global = model_name
    
    def setup_ui(self):
        self.db_type_input = QLineEdit()
        self.db_name_input = QLineEdit()
        self.host_input = QLineEdit()
        self.port_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.choose_model_edit = QComboBox()
        self.choose_model_edit.setStyleSheet("background-color: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 6px; color: #111827;")

    def load_settings_to_ui(self):
        self.db_type_input.setText(self.config["database"]["type"])
        self.db_name_input.setText(self.config["database"]["name"])
        self.host_input.setText(self.config["database"]["host"])
        self.port_input.setText(str(self.config["database"]["port"]))
        self.username_input.setText(self.config["database"]["username"])
        self.password_input.setText(self.config["database"]["password"])
        self.choose_model_edit.setCurrentText(self.config["model"]["name"])
    
    def connect_db(self):
        print("Connecting to DB...")
        global DBManager
        DBManager = DatabaseManager(
            db_type=self.db_type_input.text().strip(),
            db_name=self.db_name_input.text().strip(),
            host=self.host_input.text().strip(),
            port=self.port_input.text().strip(),
            username=self.username_input.text().strip(),
            password=self.password_input.text().strip()
        )
        flag = DBManager.connect()
        if flag:
            self.is_db_connected = True
            self.connect_btn.setText("Connected")
            self.connect_btn.setEnabled(False)
            self.connect_btn.setStyleSheet("background-color:gray;")
            QMessageBox.information(self, "Database Connection", "Database connected successfully")
        else:
            QMessageBox.information(self, "Database Connection", "Failed to connect with database")
    
    def check_ollama_installed(self):
        try:
            result = subprocess.run(["cmd", "/c", "ollama", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print("Ollama is installed:", result.stdout)
                QMessageBox.information(self, "Ollama Check", "Ollama is installed:\n" + result.stdout)
            else:
                print("Ollama is not installed.")
        except FileNotFoundError:
            print("Ollama command not found. Please install Ollama.")
    
    def list_ollama_models(self) -> list[str]:
        try:
            result = subprocess.run(["cmd", "/c", "ollama", "list"], capture_output=True, text=True)
            if result.returncode == 0:
                print("Available Ollama models:\n", extract_model_names(result.stdout))
                
                return extract_model_names(result.stdout)
            else:
                print("Failed to list Ollama models.")
                return ["Failed to list models"]
        except FileNotFoundError:
            print("Ollama command not found. Please install Ollama.")
            return ["Ollama not found"]
        
    def save_settings(self):
        try:
            self.model = self.choose_model_edit.currentText().strip()
            settings_path = resource_path("settings.json")
            with open(settings_path, "w") as f:
                config = {
                    "database" : {
                        "type" : self.db_type_input.text().strip(),
                        "name" : self.db_name_input.text().strip(),
                        "host" : self.host_input.text().strip(),
                        "port" : self.port_input.text().strip(),
                        "username" : self.username_input.text().strip(),
                        "password" : self.password_input.text().strip()
                    },
                    "model" : {
                        "name" : self.model
                    }
                }
                json.dump(config, f, indent=4)
            QMessageBox.information(self, "Save Settings", "Configurations saved successfully")
            return None
        except:
          print('An exception occurred')
          return None
        
    def load_settings(self):
        settings_path = resource_path("settings.json")
        with open(settings_path, "r") as f:
            self.config = json.load(f)
        
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QueryMind")
        self.resize(800, 800)
        
        # Tabs
        self.tabs = QTabWidget()
        # self.chat_tab = ChatTab(model_name="gemma3:1b")
        # self.tabs.addTab(self.chat_tab, "Chat")
        self.tabs.addTab(ChatTab(), "Chat")
        self.tabs.addTab(SettingsTab(), "Settings")
        
        self.setCentralWidget(self.tabs)
        self.setStyleSheet(STYLE_SHEET)

def extract_model_names(output: str):
    lines = output.strip().splitlines()
    models = []

    for line in lines[1:]:  # skip header
        parts = line.split()
        if parts:
            models.append(parts[0])

    return models

def resource_path(path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, path)
    return os.path.join(os.path.abspath("."), path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(os.path.join(basedir, 'logo.ico')))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())