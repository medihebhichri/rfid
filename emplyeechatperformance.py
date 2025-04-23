import sys
import pyodbc
import requests
import json
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
                             QLineEdit, QTextEdit, QLabel, QComboBox, QMessageBox, QStatusBar,
                             QProgressBar, QDialog, QFrame, QSplitter, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette

CONNECTION_STRING = (
    'DRIVER={ODBC Driver 18 for SQL Server};'
    'SERVER=IHEB;'
    'DATABASE=rfid;'
    'Trusted_Connection=Yes;'
    'Encrypt=no;'
)


class DatabaseManager:
    def __init__(self):
        self.conn = pyodbc.connect(CONNECTION_STRING)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.populate_date_table()

    def create_tables(self):
        self.cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='Date')
            CREATE TABLE Date (
                Date_id INT PRIMARY KEY IDENTITY(1,1),
                date_complete DATE,
                jour INT,
                mois INT,
                annee INT,
                jour_semaine VARCHAR(20),
                est_jour_ferie BIT,
                description_jour VARCHAR(255)
            )
        ''')

        self.cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='Equipe')
            CREATE TABLE Equipe (
                equipe_id INT PRIMARY KEY IDENTITY(1,1),
                nom_equipe VARCHAR(100),
                description VARCHAR(255),
                chef_equipe VARCHAR(100)
            )
        ''')

        self.cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='Poste_Competence')
            CREATE TABLE Poste_Competence (
                poste_id INT PRIMARY KEY IDENTITY(1,1),
                titre_poste VARCHAR(100),
                niveau_competence VARCHAR(50),
                description VARCHAR(255),
                requirements VARCHAR(255)
            )
        ''')

        self.cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='Employe')
            CREATE TABLE Employe (
                rfid VARCHAR(50) PRIMARY KEY,
                nom VARCHAR(100),
                prenom VARCHAR(100),
                date_naissance DATE,
                date_embauche DATE,
                email VARCHAR(100),
                telephone VARCHAR(20),
                adresse VARCHAR(255),
                equipe_id INT FOREIGN KEY REFERENCES Equipe(equipe_id),
                poste_id INT FOREIGN KEY REFERENCES Poste_Competence(poste_id),
                date_id INT FOREIGN KEY REFERENCES Date(date_id)
            )
        ''')

        self.cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='Alerte')
            CREATE TABLE Alerte (
                alerte_id INT PRIMARY KEY IDENTITY(1,1),
                type_alerte VARCHAR(50),
                description VARCHAR(255),
                date_alerte DATETIME,
                status VARCHAR(20),
                rfid VARCHAR(50) FOREIGN KEY REFERENCES Employe(rfid),
                date_id INT FOREIGN KEY REFERENCES Date(date_id)
            )
        ''')

        self.cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='Evenement')
            CREATE TABLE Evenement (
                evenement_id INT PRIMARY KEY IDENTITY(1,1),
                type_evenement VARCHAR(50),
                date_evenement DATETIME,
                description VARCHAR(255),
                rfid VARCHAR(50) FOREIGN KEY REFERENCES Employe(rfid),
                equipe_id INT FOREIGN KEY REFERENCES Equipe(equipe_id),
                poste_id INT FOREIGN KEY REFERENCES Poste_Competence(poste_id),
                alerte_id INT FOREIGN KEY REFERENCES Alerte(alerte_id),
                date_id INT FOREIGN KEY REFERENCES Date(date_id)
            )
        ''')

        self.cursor.execute('''
            IF COL_LENGTH('Evenement', 'date_id') IS NULL
            ALTER TABLE Evenement ADD date_id INT FOREIGN KEY REFERENCES Date(date_id)
        ''')

        self.conn.commit()

    def populate_date_table(self):
        dates = set()

        self.cursor.execute("SELECT date_naissance, date_embauche FROM Employe")
        for row in self.cursor.fetchall():
            if row.date_naissance:
                dates.add(row.date_naissance)
            if row.date_embauche:
                dates.add(row.date_embauche)

        self.cursor.execute("SELECT date_alerte FROM Alerte")
        for row in self.cursor.fetchall():
            if row.date_alerte:
                dates.add(row.date_alerte.date())

        self.cursor.execute("SELECT date_evenement FROM Evenement")
        for row in self.cursor.fetchall():
            if row.date_evenement:
                dates.add(row.date_evenement.date())

        for date in dates:
            if date:
                date_complete = date
                jour = date.day
                mois = date.month
                annee = date.year
                jour_semaine = date.strftime("%A")
                est_jour_ferie = 0
                description_jour = ""

                self.cursor.execute('''
                    IF NOT EXISTS (SELECT * FROM Date WHERE date_complete = ?)
                    INSERT INTO Date (date_complete, jour, mois, annee, jour_semaine, est_jour_ferie, description_jour)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (date_complete, date_complete, jour, mois, annee, jour_semaine, est_jour_ferie, description_jour))

        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()


def get_employee_data(employee_name=None, rfid=None):
    if not employee_name and not rfid:
        return None

    db = DatabaseManager()

    search_condition = ""
    if rfid:
        search_condition = f"WHERE rfid = '{rfid}'"
    elif employee_name:
        name_parts = employee_name.split()
        if len(name_parts) == 1:
            search_condition = f"WHERE nom LIKE '%{name_parts[0]}%' OR prenom LIKE '%{name_parts[0]}%'"
        else:
            search_condition = f"WHERE (nom LIKE '%{name_parts[0]}%' AND prenom LIKE '%{name_parts[1]}%') OR (nom LIKE '%{name_parts[1]}%' AND prenom LIKE '%{name_parts[0]}%')"

    query = f"""
        SELECT 
            rfid, nom, prenom, date_naissance, date_embauche, 
            email, telephone, adresse,
            nom_equipe, chef_equipe,
            titre_poste, niveau_competence
        FROM Employe e
        LEFT JOIN Equipe eq ON e.equipe_id = eq.equipe_id
        LEFT JOIN Poste_Competence pc ON e.poste_id = pc.poste_id
        {search_condition}
    """

    db.cursor.execute(query)
    employee = db.cursor.fetchone()

    if not employee:
        db.close()
        return None

    basic_info = {
        "rfid": employee.rfid,
        "nom": employee.nom,
        "prenom": employee.prenom,
        "nom_complet": f"{employee.prenom} {employee.nom}",
        "date_naissance": employee.date_naissance.strftime("%Y-%m-%d") if employee.date_naissance else None,
        "date_embauche": employee.date_embauche.strftime("%Y-%m-%d") if employee.date_embauche else None,
        "email": employee.email,
        "telephone": employee.telephone,
        "adresse": employee.adresse,
        "equipe": employee.nom_equipe,
        "chef_equipe": employee.chef_equipe,
        "poste": employee.titre_poste,
        "niveau_competence": employee.niveau_competence
    }

    query = f"""
        SELECT 
            type_alerte, description, date_alerte, status
        FROM Alerte
        WHERE rfid = '{employee.rfid}'
        ORDER BY date_alerte DESC
    """

    db.cursor.execute(query)
    alerts = []
    for row in db.cursor.fetchall():
        alerts.append({
            "type": row.type_alerte,
            "description": row.description,
            "date": row.date_alerte.strftime("%Y-%m-%d") if row.date_alerte else None,
            "status": row.status
        })

    query = f"""
        SELECT 
            type_evenement, date_evenement, description
        FROM Evenement
        WHERE rfid = '{employee.rfid}'
        ORDER BY date_evenement DESC
    """

    db.cursor.execute(query)
    events = []
    for row in db.cursor.fetchall():
        events.append({
            "type": row.type_evenement,
            "date": row.date_evenement.strftime("%Y-%m-%d") if row.date_evenement else None,
            "description": row.description
        })

    tenure = 0
    if employee.date_embauche:
        hire_date = employee.date_embauche
        tenure = (datetime.now().date() - hire_date).days // 365

    recent_alerts = 0
    if alerts:
        for a in alerts:
            if a["date"]:
                alert_date = datetime.strptime(a["date"], "%Y-%m-%d").date()
                if (datetime.now().date() - alert_date).days <= 90:
                    recent_alerts += 1

    employee_data = {
        "basic_info": basic_info,
        "alerts": alerts,
        "events": events,
        "tenure": tenure,
        "alert_count": len(alerts),
        "recent_alerts": recent_alerts
    }

    db.close()
    return employee_data


def generate_employee_report(employee_data, llm_endpoint="http://localhost:1234/v1/chat/completions",
                             model_name="llama3"):
    if not employee_data:
        return "Employee not found in database."

    alerts_json = json.dumps([a for a in employee_data['alerts'] if a.get("date") and
                              (datetime.now().date() - datetime.strptime(a["date"], "%Y-%m-%d").date()).days <= 365],
                             indent=2)

    events_json = json.dumps([e for e in employee_data['events'] if e.get("date") and
                              (datetime.now().date() - datetime.strptime(e["date"], "%Y-%m-%d").date()).days <= 365],
                             indent=2)

    prompt = f"""
    Generate a comprehensive employee performance report based on the following data:

    EMPLOYEE INFORMATION:
    Name: {employee_data['basic_info']['nom_complet']}
    Position: {employee_data['basic_info']['poste'] or 'Not specified'}
    Competence Level: {employee_data['basic_info']['niveau_competence'] or 'Not specified'}
    Team: {employee_data['basic_info']['equipe'] or 'Not assigned'}
    Team Leader: {employee_data['basic_info']['chef_equipe'] or 'Not specified'}
    Hire Date: {employee_data['basic_info']['date_embauche'] or 'Not specified'}
    Years at Company: {employee_data['tenure']}

    ALERT HISTORY (Last 12 months):
    Total Alerts: {employee_data['alert_count']}
    Recent Alerts (last 90 days): {employee_data['recent_alerts']}

    DETAILED ALERTS:
    {alerts_json}

    RECENT EVENTS AND ACTIVITIES:
    {events_json}

    Based on this information, provide:
    1. A summary of the employee's profile
    2. Analysis of their performance based on alerts and events
    3. Key strengths and areas for improvement
    4. Recommendations for HR

    Format the report professionally for an HR manager.
    """

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system",
             "content": "You are an HR assistant that analyzes employee data and generates insightful performance reports."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(llm_endpoint, headers=headers, json=payload)
        response_data = response.json()
        return response_data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error generating report: {str(e)}\n\nMake sure LM Studio is running with API server enabled and the model is loaded."


def generate_chatbot_response(query, employee_data, llm_endpoint="http://localhost:1234/v1/chat/completions",
                              model_name="llama3"):
    if not employee_data:
        return "I don't have information about this employee in my database."

    employee_info = json.dumps(employee_data["basic_info"], indent=2)
    alerts_info = json.dumps(employee_data["alerts"], indent=2)
    events_info = json.dumps(employee_data["events"], indent=2)

    prompt = f"""
    You are an HR assistant chatbot. Answer the following question about an employee based on their data:

    QUESTION: {query}

    EMPLOYEE DATA:
    Basic Information: {employee_info}
    Tenure: {employee_data['tenure']} years
    Alert Count: {employee_data['alert_count']} (Recent: {employee_data['recent_alerts']})

    Alerts: {alerts_info}

    Events: {events_info}

    Provide a concise, helpful response directly answering the question. If the question can't be answered from the provided data, politely say so.
    """

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system",
             "content": "You are an HR assistant chatbot that answers questions about employees based on their data."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 1000
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(llm_endpoint, headers=headers, json=payload)
        response_data = response.json()
        return response_data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error generating response: {str(e)}\n\nMake sure LM Studio is running with API server enabled and the model is loaded."


class ReportGeneratorThread(QThread):
    report_generated = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, employee_data, llm_endpoint, model_name):
        super().__init__()
        self.employee_data = employee_data
        self.llm_endpoint = llm_endpoint
        self.model_name = model_name

    def run(self):
        report = generate_employee_report(self.employee_data, self.llm_endpoint, self.model_name)
        if "Error generating report" in report:
            self.error_occurred.emit(report)
        else:
            self.report_generated.emit(report)


class ChatbotResponseThread(QThread):
    response_generated = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, query, employee_data, llm_endpoint, model_name):
        super().__init__()
        self.query = query
        self.employee_data = employee_data
        self.llm_endpoint = llm_endpoint
        self.model_name = model_name

    def run(self):
        response = generate_chatbot_response(self.query, self.employee_data, self.llm_endpoint, self.model_name)
        if "Error generating response" in response:
            self.error_occurred.emit(response)
        else:
            self.response_generated.emit(response)


class Message:
    def __init__(self, text, is_user=True):
        self.text = text
        self.is_user = is_user
        self.timestamp = datetime.now()


class CustomMessageItem(QListWidgetItem):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.message = message
        self.setSizeHint(QSize(0, 50))  # Will be adjusted based on content


class MessageWidget(QWidget):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.message = message

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        # Message text
        self.text_label = QLabel(message.text)
        self.text_label.setWordWrap(True)
        self.text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # Style based on sender
        if message.is_user:
            self.text_label.setStyleSheet("""
                background-color: #DCF8C6;
                border-radius: 10px;
                padding: 10px;
                color: #000000;
            """)
            layout.setAlignment(Qt.AlignRight)
        else:
            self.text_label.setStyleSheet("""
                background-color: #F0F0F0;
                border-radius: 10px;
                padding: 10px;
                color: #000000;
            """)
            layout.setAlignment(Qt.AlignLeft)

        layout.addWidget(self.text_label)

        # Time stamp
        time_label = QLabel(message.timestamp.strftime("%H:%M"))
        time_label.setStyleSheet("color: #888888; font-size: 10px;")

        if message.is_user:
            layout.setAlignment(time_label, Qt.AlignRight)
        else:
            layout.setAlignment(time_label, Qt.AlignLeft)

        layout.addWidget(time_label)
        self.setLayout(layout)


class ModernEmployeeChatbot(QMainWindow):
    def __init__(self):
        super().__init__()
        self.load_settings()
        self.current_employee_data = None
        self.conversation_history = []
        self.initUI()

    def load_settings(self):
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                self.llm_endpoint = settings.get("llm_endpoint", "http://localhost:1234/v1/chat/completions")
                self.model_name = settings.get("model_name", "llama3")
        except:
            self.llm_endpoint = "http://localhost:1234/v1/chat/completions"
            self.model_name = "llama3"

    def initUI(self):
        self.setWindowTitle('HR Assistant')
        self.setGeometry(100, 100, 1000, 700)

        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F5F5F5;
            }
            QLabel {
                font-size: 14px;
            }
            QLineEdit, QTextEdit {
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                padding: 8px;
                background-color: white;
                font-size: 14px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QTabWidget::pane {
                border: 1px solid #CCCCCC;
                background-color: white;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #E0E0E0;
                border: 1px solid #CCCCCC;
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                min-width: 100px;
                padding: 8px 15px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: none;
            }
            QProgressBar {
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                background-color: #F0F0F0;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 5px;
            }
        """)

        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Left panel (employee search and selection)
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.StyledPanel)
        left_panel.setMaximumWidth(300)
        left_panel_layout = QVBoxLayout()
        left_panel.setLayout(left_panel_layout)

        title_label = QLabel('HR Assistant')
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333333; margin-bottom: 20px;")
        title_label.setAlignment(Qt.AlignCenter)
        left_panel_layout.addWidget(title_label)

        left_panel_layout.addWidget(QLabel('Employee Name or RFID:'))

        employee_search_layout = QHBoxLayout()
        self.employee_input = QLineEdit()
        self.employee_input.setPlaceholderText("Enter name or RFID...")
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_employee)

        employee_search_layout.addWidget(self.employee_input)
        employee_search_layout.addWidget(self.search_button)
        left_panel_layout.addLayout(employee_search_layout)

        left_panel_layout.addSpacing(20)

        # Employee info panel (shown after search)
        self.employee_info_panel = QFrame()
        self.employee_info_panel.setFrameShape(QFrame.StyledPanel)
        self.employee_info_panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 10px;
            }
        """)

        employee_info_layout = QVBoxLayout()
        self.employee_info_panel.setLayout(employee_info_layout)

        self.employee_name_label = QLabel("No Employee Selected")
        self.employee_name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.employee_position_label = QLabel("")
        self.employee_team_label = QLabel("")
        self.employee_tenure_label = QLabel("")

        employee_info_layout.addWidget(self.employee_name_label)
        employee_info_layout.addWidget(self.employee_position_label)
        employee_info_layout.addWidget(self.employee_team_label)
        employee_info_layout.addWidget(self.employee_tenure_label)

        left_panel_layout.addWidget(self.employee_info_panel)
        left_panel_layout.addStretch()

        # Settings button
        self.settings_button = QPushButton("Settings")
        self.settings_button.setStyleSheet("""
            background-color: #607D8B;
        """)
        self.settings_button.clicked.connect(self.open_settings)
        left_panel_layout.addWidget(self.settings_button)

        # Right panel with tabs
        right_panel = QFrame()
        right_panel_layout = QVBoxLayout()
        right_panel.setLayout(right_panel_layout)

        # Chatbot interface
        chat_frame = QFrame()
        chat_frame.setFrameShape(QFrame.StyledPanel)
        chat_layout = QVBoxLayout()
        chat_frame.setLayout(chat_layout)

        # Chat history
        self.chat_list = QListWidget()
        self.chat_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #CCCCCC;
                border-radius: 5px;
            }
        """)
        chat_layout.addWidget(self.chat_list)

        # Input area
        input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask about the selected employee...")
        self.chat_input.returnPressed.connect(self.send_message)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)

        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(self.send_button)
        chat_layout.addLayout(input_layout)

        report_frame = QFrame()
        report_frame.setFrameShape(QFrame.StyledPanel)
        report_layout = QVBoxLayout()
        report_frame.setLayout(report_layout)

        report_header = QLabel("Employee Performance Report")
        report_header.setStyleSheet("font-size: 18px; font-weight: bold;")
        report_header.setAlignment(Qt.AlignCenter)
        report_layout.addWidget(report_header)

        self.report_output = QTextEdit()
        self.report_output.setReadOnly(True)
        report_layout.addWidget(self.report_output)

        self.generate_report_button = QPushButton("Generate Full Report")
        self.generate_report_button.clicked.connect(self.generate_report)
        report_layout.addWidget(self.generate_report_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        report_layout.addWidget(self.progress_bar)

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(chat_frame)
        splitter.addWidget(report_frame)
        splitter.setSizes([400, 300])

        right_panel_layout.addWidget(splitter)

        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.chat_input.setEnabled(False)
        self.send_button.setEnabled(False)
        self.generate_report_button.setEnabled(False)

        welcome_message = Message("Welcome to HR Assistant! Please search for an employee to begin.", is_user=False)
        self.add_message_to_chat(welcome_message)

    def search_employee(self):
        employee_name = self.employee_input.text().strip()
        if not employee_name:
            QMessageBox.warning(self, 'Input Error', 'Please enter an employee name or RFID.')
            return

        self.status_bar.showMessage('Searching for employee...')
        self.current_employee_data = get_employee_data(employee_name=employee_name)

        if not self.current_employee_data:
            self.status_bar.showMessage('Employee not found.')
            QMessageBox.warning(self, 'Not Found', f"Employee '{employee_name}' not found in database.")
            return

        self.update_employee_info()

        self.chat_input.setEnabled(True)
        self.send_button.setEnabled(True)
        self.generate_report_button.setEnabled(True)

        # Clear previous conversation
        self.chat_list.clear()
        self.conversation_history = []

        # Add welcome message for the selected employee
        welcome_message = Message(
            f"Employee found! I can answer questions about {self.current_employee_data['basic_info']['nom_complet']}. What would you like to know?",
            is_user=False
        )
        self.add_message_to_chat(welcome_message)

        self.status_bar.showMessage('Employee loaded successfully.')

    def update_employee_info(self):
        if not self.current_employee_data:
            return

        basic_info = self.current_employee_data['basic_info']
        self.employee_name_label.setText(basic_info['nom_complet'])
        self.employee_position_label.setText(f"Position: {basic_info['poste'] or 'Not specified'}")
        self.employee_team_label.setText(f"Team: {basic_info['equipe'] or 'Not assigned'}")
        self.employee_tenure_label.setText(f"Tenure: {self.current_employee_data['tenure']} years")

    def send_message(self):
        if not self.current_employee_data:
            QMessageBox.warning(self, 'No Employee Selected', 'Please search for an employee first.')
            return

        query = self.chat_input.text().strip()
        if not query:
            return

        # Add user message to chat
        user_message = Message(query, is_user=True)
        self.add_message_to_chat(user_message)
        self.conversation_history.append(user_message)

        # Clear input field
        self.chat_input.clear()

        # Add typing indicator
        typing_message = Message("Thinking...", is_user=False)
        typing_item = self.add_message_to_chat(typing_message)

        self.chatbot_response_thread = ChatbotResponseThread(
            query,
            self.current_employee_data,
            self.llm_endpoint,
            self.model_name
        )
        self.chatbot_response_thread.response_generated.connect(
            lambda response: self.handle_chatbot_response(response, typing_item)
        )
        self.chatbot_response_thread.error_occurred.connect(
            lambda error: self.handle_chatbot_error(error, typing_item)
        )
        self.chatbot_response_thread.start()

    def handle_chatbot_response(self, response, typing_item):
        self.chat_list.takeItem(self.chat_list.row(typing_item))

        bot_message = Message(response, is_user=False)
        self.add_message_to_chat(bot_message)
        self.conversation_history.append(bot_message)

    def handle_chatbot_error(self, error, typing_item):
        self.chat_list.takeItem(self.chat_list.row(typing_item))

        error_message = Message(f"Error: {error}", is_user=False)
        self.add_message_to_chat(error_message)
        self.status_bar.showMessage('Error generating response.')

    def add_message_to_chat(self, message):
        item = CustomMessageItem(message)
        self.chat_list.addItem(item)

        widget = MessageWidget(message)
        self.chat_list.setItemWidget(item, widget)

        text_height = widget.text_label.sizeHint().height()
        item.setSizeHint(QSize(self.chat_list.width(), text_height + 50))

        self.chat_list.scrollToBottom()
        return item

    def generate_report(self):
        if not self.current_employee_data:
            QMessageBox.warning(self, 'No Employee Selected', 'Please search for an employee first.')
            return

        self.progress_bar.setValue(20)
        self.report_output.setPlainText("Generating report, please wait...")
        self.generate_report_button.setEnabled(False)

        self.report_generator_thread = ReportGeneratorThread(
            self.current_employee_data,
            self.llm_endpoint,
            self.model_name
        )
        self.report_generator_thread.report_generated.connect(self.handle_report_generated)
        self.report_generator_thread.error_occurred.connect(self.handle_report_error)
        self.report_generator_thread.start()

        self.progress_bar.setValue(50)

    def handle_report_generated(self, report):
        self.report_output.setPlainText(report)
        self.progress_bar.setValue(100)
        self.generate_report_button.setEnabled(True)
        self.status_bar.showMessage('Report generated successfully.')

    def handle_report_error(self, error):
        self.report_output.setPlainText(f"Error: {error}")
        self.progress_bar.setValue(0)
        self.generate_report_button.setEnabled(True)
        self.status_bar.showMessage('Error generating report.')

    def open_settings(self):
        settings_dialog = QDialog(self)
        settings_dialog.setWindowTitle('Settings')
        settings_dialog.setMinimumWidth(400)

        layout = QVBoxLayout()

        layout.addWidget(QLabel('LLM API Endpoint:'))
        endpoint_input = QLineEdit(self.llm_endpoint)
        layout.addWidget(endpoint_input)

        layout.addWidget(QLabel('Model Name:'))
        model_input = QLineEdit(self.model_name)
        layout.addWidget(model_input)

        button_layout = QHBoxLayout()
        save_button = QPushButton('Save')
        cancel_button = QPushButton('Cancel')

        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        settings_dialog.setLayout(layout)

        save_button.clicked.connect(
            lambda: self.save_settings(endpoint_input.text(), model_input.text(), settings_dialog))
        cancel_button.clicked.connect(settings_dialog.reject)

        settings_dialog.exec_()

    def save_settings(self, endpoint, model, dialog):
        if not endpoint or not model:
            QMessageBox.warning(self, 'Input Error', 'Please fill in all fields.')
            return

        self.llm_endpoint = endpoint
        self.model_name = model

        settings = {
            "llm_endpoint": endpoint,
            "model_name": model
        }

        try:
            with open('settings.json', 'w') as f:
                json.dump(settings, f)
            self.status_bar.showMessage('Settings saved successfully.')
            dialog.accept()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to save settings: {str(e)}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ModernEmployeeChatbot()
    window.show()
    sys.exit(app.exec_())