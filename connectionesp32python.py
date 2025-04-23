import sys
import pyodbc
import logging
from datetime import datetime
from flask import Flask, request
from threading import Thread
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem, QTabWidget,
                             QLineEdit, QComboBox, QFormLayout, QMessageBox, QGroupBox,
                             QTextEdit, QSplitter, QHeaderView)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QColor, QFont, QIcon

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='rfid_server.log',
    filemode='a'
)
logger = logging.getLogger('rfid_server')

# Console handler for debugging
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)

# Database connection string
CONNECTION_STRING = (
    'DRIVER={ODBC Driver 18 for SQL Server};'
    'SERVER=IHEB;'
    'DATABASE=rfid;'
    'Trusted_Connection=Yes;'
    'Encrypt=no;'
)

# Flask server setup
app = Flask(__name__)


# Custom signal class for communication between Flask and PyQt
class ServerSignals(QObject):
    new_access_event = pyqtSignal(str, str, str, str)
    log_message = pyqtSignal(str)


# Global signal instance
signals = ServerSignals()


class DatabaseManager:
    def __init__(self):
        try:
            self.conn = pyodbc.connect(CONNECTION_STRING)
            self.cursor = self.conn.cursor()
            logger.info("Database connection established")
            signals.log_message.emit("Database connection established")
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            signals.log_message.emit(f"Database error: {str(e)}")
            self.conn = None
            self.cursor = None

    def reconnect(self):
        try:
            if self.conn:
                self.conn.close()
            self.conn = pyodbc.connect(CONNECTION_STRING)
            self.cursor = self.conn.cursor()
            logger.info("Database reconnection successful")
            signals.log_message.emit("Database reconnection successful")
            return True
        except Exception as e:
            logger.error(f"Database reconnection error: {str(e)}")
            signals.log_message.emit(f"Database reconnection error: {str(e)}")
            self.conn = None
            self.cursor = None
            return False

    def verify_rfid(self, rfid_value):
        try:
            if not self.conn or not self.cursor:
                if not self.reconnect():
                    return False

            logger.debug(f"Verifying RFID: {rfid_value}")
            signals.log_message.emit(f"Verifying RFID: {rfid_value}")

            # Query to check if RFID exists in the Employe table
            query = "SELECT * FROM Employe WHERE rfid = ?"
            self.cursor.execute(query, (rfid_value,))
            result = self.cursor.fetchone()

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if result:
                employee_name = f"{result.prenom} {result.nom}"
                logger.info(f"RFID {rfid_value} authorized - Employee: {employee_name}")
                signals.log_message.emit(f"Access granted for {employee_name}")

                # Emit signal for UI update
                signals.new_access_event.emit(
                    current_time,
                    rfid_value,
                    employee_name,
                    "ACCESS GRANTED"
                )

                # Log access event
                self.record_access_event(rfid_value, "AUTHORIZED", "Door access granted")
                return True
            else:
                logger.warning(f"RFID {rfid_value} unauthorized - No matching employee")
                signals.log_message.emit(f"Access denied for RFID: {rfid_value}")

                # Emit signal for UI update
                signals.new_access_event.emit(
                    current_time,
                    rfid_value,
                    "Unknown",
                    "ACCESS DENIED"
                )

                # Log unauthorized attempt
                self.record_access_event(rfid_value, "UNAUTHORIZED", "Unauthorized access attempt")
                return False

        except Exception as e:
            logger.error(f"Database error during RFID verification: {str(e)}")
            signals.log_message.emit(f"Database error: {str(e)}")
            return False

    def record_access_event(self, rfid, event_type, description):
        try:
            if not self.conn or not self.cursor:
                if not self.reconnect():
                    return False

            # Get current date info for Date table
            current_date = datetime.now().date()
            current_day = current_date.day
            current_month = current_date.month
            current_year = current_date.year
            day_of_week = current_date.strftime("%A")

            # Check if date exists in Date table, if not, insert it
            self.cursor.execute('''
                IF NOT EXISTS (SELECT * FROM Date WHERE date_complete = ?)
                INSERT INTO Date (date_complete, jour, mois, annee, jour_semaine, est_jour_ferie, description_jour)
                VALUES (?, ?, ?, ?, ?, 0, '')
            ''', (current_date, current_date, current_day, current_month, current_year, day_of_week))

            # Get the date_id for the current date
            self.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (current_date,))
            date_row = self.cursor.fetchone()
            date_id = date_row.date_id if date_row else None

            # Record in Evenement table
            if rfid and date_id:
                # Check if this RFID exists in Employe table
                self.cursor.execute("SELECT * FROM Employe WHERE rfid = ?", (rfid,))
                employee = self.cursor.fetchone()

                if employee:
                    # Valid employee - record normal event
                    self.cursor.execute('''
                        INSERT INTO Evenement (
                            type_evenement, 
                            date_evenement, 
                            description, 
                            rfid, 
                            date_id
                        )
                        VALUES (?, ?, ?, ?, ?)
                    ''', (event_type, datetime.now(), description, rfid, date_id))
                else:
                    # Unknown RFID - create an alert
                    self.cursor.execute('''
                        INSERT INTO Alerte (
                            type_alerte,
                            description,
                            date_alerte,
                            status,
                            date_id
                        )
                        VALUES (?, ?, ?, ?, ?)
                    ''', ("SECURITY", f"Unknown RFID: {rfid}", datetime.now(), "NEW", date_id))

                    # Get the alert_id that was just created
                    self.cursor.execute("SELECT @@IDENTITY AS alert_id")
                    alert_row = self.cursor.fetchone()
                    alert_id = alert_row.alert_id if alert_row else None

                    # Create event linked to the alert
                    if alert_id:
                        self.cursor.execute('''
                            INSERT INTO Evenement (
                                type_evenement, 
                                date_evenement, 
                                description, 
                                alerte_id,
                                date_id
                            )
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                        "SECURITY_ALERT", datetime.now(), f"Unauthorized access with RFID: {rfid}", alert_id, date_id))

            self.conn.commit()
            logger.debug(f"Successfully recorded access event for RFID: {rfid}")

            return True

        except Exception as e:
            logger.error(f"Error recording access event: {str(e)}")
            signals.log_message.emit(f"Error recording event: {str(e)}")
            if self.conn:
                try:
                    self.conn.rollback()
                except:
                    pass
            return False

    def get_recent_events(self, limit=50):
        try:
            if not self.conn or not self.cursor:
                if not self.reconnect():
                    return []

            query = '''
                SELECT TOP (?) e.evenement_id, e.type_evenement, e.date_evenement, e.description, 
                       COALESCE(em.prenom + ' ' + em.nom, 'Unknown') as employee_name, 
                       COALESCE(em.rfid, '') as rfid
                FROM Evenement e
                LEFT JOIN Employe em ON e.rfid = em.rfid
                ORDER BY e.date_evenement DESC
            '''

            self.cursor.execute(query, (limit,))
            results = self.cursor.fetchall()
            events = []

            for row in results:
                events.append({
                    'id': row.evenement_id,
                    'type': row.type_evenement,
                    'date': row.date_evenement,
                    'description': row.description,
                    'employee': row.employee_name,
                    'rfid': row.rfid
                })

            return events

        except Exception as e:
            logger.error(f"Error fetching recent events: {str(e)}")
            signals.log_message.emit(f"Error fetching events: {str(e)}")
            return []

    def get_all_employees(self):
        try:
            if not self.conn or not self.cursor:
                if not self.reconnect():
                    return []

            query = '''
                SELECT e.rfid, e.nom, e.prenom, e.email, e.telephone,
                       eq.nom_equipe, pc.titre_poste
                FROM Employe e
                LEFT JOIN Equipe eq ON e.equipe_id = eq.equipe_id
                LEFT JOIN Poste_Competence pc ON e.poste_id = pc.poste_id
                ORDER BY e.nom, e.prenom
            '''

            self.cursor.execute(query)
            results = self.cursor.fetchall()
            employees = []

            for row in results:
                employees.append({
                    'rfid': row.rfid,
                    'name': f"{row.prenom} {row.nom}",
                    'email': row.email or '',
                    'phone': row.telephone or '',
                    'team': row.nom_equipe or '',
                    'position': row.titre_poste or ''
                })

            return employees

        except Exception as e:
            logger.error(f"Error fetching employees: {str(e)}")
            signals.log_message.emit(f"Error fetching employees: {str(e)}")
            return []

    def add_new_employee(self, rfid, first_name, last_name, email, phone, team_id=None, position_id=None):
        try:
            if not self.conn or not self.cursor:
                if not self.reconnect():
                    return False

            # Check if RFID already exists
            self.cursor.execute("SELECT COUNT(*) FROM Employe WHERE rfid = ?", (rfid,))
            count = self.cursor.fetchone()[0]

            if count > 0:
                logger.warning(f"RFID {rfid} already exists in database")
                signals.log_message.emit(f"RFID {rfid} already exists in database")
                return False

            # Current date for date_id reference
            current_date = datetime.now().date()
            self.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (current_date,))
            date_row = self.cursor.fetchone()

            if not date_row:
                # Insert current date if it doesn't exist
                current_day = current_date.day
                current_month = current_date.month
                current_year = current_date.year
                day_of_week = current_date.strftime("%A")

                self.cursor.execute('''
                    INSERT INTO Date (date_complete, jour, mois, annee, jour_semaine, est_jour_ferie, description_jour)
                    VALUES (?, ?, ?, ?, ?, 0, '')
                ''', (current_date, current_day, current_month, current_year, day_of_week))

                self.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (current_date,))
                date_row = self.cursor.fetchone()

            date_id = date_row.date_id if date_row else None

            # Insert new employee
            query = '''
                INSERT INTO Employe (rfid, nom, prenom, email, telephone, date_embauche, equipe_id, poste_id, date_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''

            self.cursor.execute(query, (
                rfid, last_name, first_name, email, phone, current_date,
                team_id, position_id, date_id
            ))

            self.conn.commit()
            logger.info(f"Added new employee with RFID {rfid}: {first_name} {last_name}")
            signals.log_message.emit(f"Added new employee: {first_name} {last_name}")
            return True

        except Exception as e:
            logger.error(f"Error adding new employee: {str(e)}")
            signals.log_message.emit(f"Error adding employee: {str(e)}")
            if self.conn:
                try:
                    self.conn.rollback()
                except:
                    pass
            return False

    def get_teams(self):
        try:
            if not self.conn or not self.cursor:
                if not self.reconnect():
                    return []

            self.cursor.execute("SELECT equipe_id, nom_equipe FROM Equipe ORDER BY nom_equipe")
            results = self.cursor.fetchall()
            teams = []

            for row in results:
                teams.append({
                    'id': row.equipe_id,
                    'name': row.nom_equipe
                })

            return teams

        except Exception as e:
            logger.error(f"Error fetching teams: {str(e)}")
            return []

    def get_positions(self):
        try:
            if not self.conn or not self.cursor:
                if not self.reconnect():
                    return []

            self.cursor.execute("SELECT poste_id, titre_poste FROM Poste_Competence ORDER BY titre_poste")
            results = self.cursor.fetchall()
            positions = []

            for row in results:
                positions.append({
                    'id': row.poste_id,
                    'title': row.titre_poste
                })

            return positions

        except Exception as e:
            logger.error(f"Error fetching positions: {str(e)}")
            return []

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


# Flask routes
@app.route('/verify', methods=['GET'])
def verify():
    rfid = request.args.get('rfid')

    if not rfid:
        logger.warning("Verification request received without RFID parameter")
        return "error: missing rfid parameter", 400

    logger.info(f"Verification request received for RFID: {rfid}")

    db_manager = DatabaseManager()
    if db_manager.verify_rfid(rfid):
        db_manager.close()
        return "authorized"
    else:
        db_manager.close()
        return "unauthorized"


@app.route('/status', methods=['GET'])
def status():
    return "running", 200


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.db_manager = DatabaseManager()

        # Connect to signal
        signals.new_access_event.connect(self.add_access_log_entry)
        signals.log_message.connect(self.add_debug_log)

        # Setup refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds

        # Initial data load
        self.refresh_data()

    def initUI(self):
        self.setWindowTitle('RFID Access Control System')
        self.setGeometry(100, 100, 1200, 800)

        # Create central widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        # Status bar at top
        self.status_bar = QHBoxLayout()
        self.server_status_label = QLabel("Server Status: Starting...")
        self.server_status_label.setStyleSheet("font-weight: bold;")
        self.db_status_label = QLabel("Database: Connecting...")
        self.db_status_label.setStyleSheet("font-weight: bold;")

        self.status_bar.addWidget(self.server_status_label)
        self.status_bar.addStretch(1)
        self.status_bar.addWidget(self.db_status_label)

        main_layout.addLayout(self.status_bar)

        # Create tab widget
        self.tabs = QTabWidget()

        # Dashboard tab
        self.dashboard_tab = QWidget()
        dashboard_layout = QVBoxLayout(self.dashboard_tab)

        # Split dashboard for access log and debug log
        dashboard_splitter = QSplitter(Qt.Orientation.Vertical)

        # Access log group
        access_log_group = QGroupBox("Access Log")
        access_log_layout = QVBoxLayout(access_log_group)

        self.access_log_table = QTableWidget()
        self.access_log_table.setColumnCount(5)
        self.access_log_table.setHorizontalHeaderLabels(["Time", "RFID", "Employee", "Status", "Details"])
        self.access_log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.access_log_table.verticalHeader().setVisible(False)

        access_log_layout.addWidget(self.access_log_table)
        dashboard_splitter.addWidget(access_log_group)

        # Debug log group
        debug_log_group = QGroupBox("System Log")
        debug_log_layout = QVBoxLayout(debug_log_group)

        self.debug_log = QTextEdit()
        self.debug_log.setReadOnly(True)

        debug_log_layout.addWidget(self.debug_log)
        dashboard_splitter.addWidget(debug_log_group)

        # Add splitter to dashboard
        dashboard_layout.addWidget(dashboard_splitter)

        # Employees tab
        self.employees_tab = QWidget()
        employees_layout = QVBoxLayout(self.employees_tab)

        # Employees table
        self.employees_table = QTableWidget()
        self.employees_table.setColumnCount(6)
        self.employees_table.setHorizontalHeaderLabels(["RFID", "Name", "Email", "Phone", "Team", "Position"])
        self.employees_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.employees_table.verticalHeader().setVisible(False)

        employees_layout.addWidget(self.employees_table)

        # Add employee form
        add_employee_group = QGroupBox("Add New Employee")
        add_employee_layout = QFormLayout(add_employee_group)

        self.rfid_input = QLineEdit()
        self.rfid_input.setPlaceholderText("RFID Card Number")

        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("First Name")

        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Last Name")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email Address")

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone Number")

        self.team_combo = QComboBox()
        self.team_combo.addItem("Select Team", None)

        self.position_combo = QComboBox()
        self.position_combo.addItem("Select Position", None)

        add_employee_layout.addRow("RFID:", self.rfid_input)
        add_employee_layout.addRow("First Name:", self.first_name_input)
        add_employee_layout.addRow("Last Name:", self.last_name_input)
        add_employee_layout.addRow("Email:", self.email_input)
        add_employee_layout.addRow("Phone:", self.phone_input)
        add_employee_layout.addRow("Team:", self.team_combo)
        add_employee_layout.addRow("Position:", self.position_combo)

        add_employee_buttons = QHBoxLayout()
        self.add_employee_btn = QPushButton("Add Employee")
        self.add_employee_btn.clicked.connect(self.add_employee)
        self.clear_form_btn = QPushButton("Clear Form")
        self.clear_form_btn.clicked.connect(self.clear_employee_form)

        add_employee_buttons.addWidget(self.add_employee_btn)
        add_employee_buttons.addWidget(self.clear_form_btn)

        add_employee_layout.addRow("", add_employee_buttons)
        employees_layout.addWidget(add_employee_group)

        # Settings tab
        self.settings_tab = QWidget()
        settings_layout = QVBoxLayout(self.settings_tab)

        server_settings_group = QGroupBox("Server Settings")
        server_settings_layout = QFormLayout(server_settings_group)

        self.host_input = QLineEdit("0.0.0.0")
        self.port_input = QLineEdit("3000")

        server_settings_layout.addRow("Host:", self.host_input)
        server_settings_layout.addRow("Port:", self.port_input)

        # Database settings group
        db_settings_group = QGroupBox("Database Settings")
        db_settings_layout = QFormLayout(db_settings_group)

        self.server_input = QLineEdit("IHEB")
        self.db_name_input = QLineEdit("rfid")

        db_settings_layout.addRow("SQL Server:", self.server_input)
        db_settings_layout.addRow("Database:", self.db_name_input)

        settings_layout.addWidget(server_settings_group)
        settings_layout.addWidget(db_settings_group)
        settings_layout.addStretch(1)

        # Add tabs to tab widget
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.employees_tab, "Employees")
        self.tabs.addTab(self.settings_tab, "Settings")

        main_layout.addWidget(self.tabs)

        # Add control buttons
        self.control_buttons = QHBoxLayout()

        self.refresh_btn = QPushButton("Refresh Data")
        self.refresh_btn.clicked.connect(self.refresh_data)

        self.restart_server_btn = QPushButton("Restart Server")
        self.restart_server_btn.clicked.connect(self.restart_server)

        self.control_buttons.addWidget(self.refresh_btn)
        self.control_buttons.addWidget(self.restart_server_btn)

        main_layout.addLayout(self.control_buttons)

        self.setCentralWidget(central_widget)
        self.show()

        # Add initial debug log
        self.add_debug_log("Application started")
        self.add_debug_log("Initializing server...")

    def add_access_log_entry(self, timestamp, rfid, employee, status):
        row_position = self.access_log_table.rowCount()
        self.access_log_table.insertRow(row_position)

        self.access_log_table.setItem(row_position, 0, QTableWidgetItem(timestamp))
        self.access_log_table.setItem(row_position, 1, QTableWidgetItem(rfid))
        self.access_log_table.setItem(row_position, 2, QTableWidgetItem(employee))

        status_item = QTableWidgetItem(status)
        if status == "ACCESS GRANTED":
            status_item.setBackground(QColor(200, 255, 200))  # Light green
        else:
            status_item.setBackground(QColor(255, 200, 200))  # Light red

        self.access_log_table.setItem(row_position, 3, status_item)

        if status == "ACCESS GRANTED":
            self.access_log_table.setItem(row_position, 4, QTableWidgetItem("Door opened"))
        else:
            self.access_log_table.setItem(row_position, 4, QTableWidgetItem("Access denied"))

        # Scroll to the new row
        self.access_log_table.scrollToBottom()

    def add_debug_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.debug_log.append(f"[{timestamp}] {message}")
        # Scroll to bottom
        scrollbar = self.debug_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def refresh_data(self):
        self.add_debug_log("Refreshing data...")

        # Update server status
        self.server_status_label.setText("Server Status: Running")
        self.server_status_label.setStyleSheet("font-weight: bold; color: green;")

        # Update database status
        if self.db_manager.conn:
            self.db_status_label.setText("Database: Connected")
            self.db_status_label.setStyleSheet("font-weight: bold; color: green;")
        else:
            self.db_status_label.setText("Database: Disconnected")
            self.db_status_label.setStyleSheet("font-weight: bold; color: red;")

        # Load recent events
        self.load_recent_events()

        # Load employees
        self.load_employees()

        # Load teams and positions
        self.load_teams_and_positions()

        self.add_debug_log("Data refresh complete")

    def load_recent_events(self):
        events = self.db_manager.get_recent_events(50)

        # Clear existing table
        self.access_log_table.setRowCount(0)

        # Add events to table
        for event in events:
            row_position = self.access_log_table.rowCount()
            self.access_log_table.insertRow(row_position)

            timestamp = event['date'].strftime("%Y-%m-%d %H:%M:%S")
            self.access_log_table.setItem(row_position, 0, QTableWidgetItem(timestamp))
            self.access_log_table.setItem(row_position, 1, QTableWidgetItem(event['rfid']))
            self.access_log_table.setItem(row_position, 2, QTableWidgetItem(event['employee']))

            status_item = QTableWidgetItem("ACCESS GRANTED" if event['type'] == "AUTHORIZED" else "ACCESS DENIED")
            if event['type'] == "AUTHORIZED":
                status_item.setBackground(QColor(200, 255, 200))  # Light green
            else:
                status_item.setBackground(QColor(255, 200, 200))  # Light red

            self.access_log_table.setItem(row_position, 3, status_item)
            self.access_log_table.setItem(row_position, 4, QTableWidgetItem(event['description']))

    def load_employees(self):
        employees = self.db_manager.get_all_employees()

        # Clear existing table
        self.employees_table.setRowCount(0)

        # Add employees to table
        for employee in employees:
            row_position = self.employees_table.rowCount()
            self.employees_table.insertRow(row_position)

            self.employees_table.setItem(row_position, 0, QTableWidgetItem(employee['rfid']))
            self.employees_table.setItem(row_position, 1, QTableWidgetItem(employee['name']))
            self.employees_table.setItem(row_position, 2, QTableWidgetItem(employee['email']))
            self.employees_table.setItem(row_position, 3, QTableWidgetItem(employee['phone']))
            self.employees_table.setItem(row_position, 4, QTableWidgetItem(employee['team']))
            self.employees_table.setItem(row_position, 5, QTableWidgetItem(employee['position']))

    def load_teams_and_positions(self):
        # Save current selections
        current_team = self.team_combo.currentData()
        current_position = self.position_combo.currentData()

        # Clear and reload teams
        self.team_combo.clear()
        self.team_combo.addItem("Select Team", None)

        teams = self.db_manager.get_teams()
        for team in teams:
            self.team_combo.addItem(team['name'], team['id'])

        # Clear and reload positions
        self.position_combo.clear()
        self.position_combo.addItem("Select Position", None)

        positions = self.db_manager.get_positions()
        for position in positions:
            self.position_combo.addItem(position['title'], position['id'])

        # Restore selections if possible
        if current_team:
            index = self.team_combo.findData(current_team)
            if index >= 0:
                self.team_combo.setCurrentIndex(index)

        if current_position:
            index = self.position_combo.findData(current_position)
            if index >= 0:
                self.position_combo.setCurrentIndex(index)

    def add_employee(self):
        rfid = self.rfid_input.text().strip()
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()
        team_id = self.team_combo.currentData()
        position_id = self.position_combo.currentData()

        # Validate inputs
        if not rfid:
            QMessageBox.warning(self, "Input Error", "RFID is required")
            return

        if not first_name or not last_name:
            QMessageBox.warning(self, "Input Error", "First name and last name are required")
            return

        # Attempt to add employee
        success = self.db_manager.add_new_employee(
            rfid, first_name, last_name, email, phone, team_id, position_id
        )

        if success:
            QMessageBox.information(self, "Success", f"Employee {first_name} {last_name} added successfully")
            self.clear_employee_form()
            self.load_employees()
        else:
            QMessageBox.critical(self, "Error", "Failed to add employee. Check logs for details.")

    def clear_employee_form(self):
        self.rfid_input.clear()
        self.first_name_input.clear()
        self.last_name_input.clear()
        self.email_input.clear()
        self.phone_input.clear()
        self.team_combo.setCurrentIndex(0)
        self.position_combo.setCurrentIndex(0)

    def restart_server(self):
        reply = QMessageBox.question(
            self, "Restart Server",
            "Are you sure you want to restart the server?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.add_debug_log("Restarting server...")
            # In a real implementation, you would restart the Flask server here
            self.add_debug_log("Server restarted")

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "Exit",
            "Are you sure you want to exit? This will stop the RFID server.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.db_manager.close()
            event.accept()
        else:
            event.ignore()


def start_flask_server():
    app.run(host='0.0.0.0', port=3000, debug=False, threaded=True)


if __name__ == '__main__':
    logger.info("Starting RFID Access Control Server")

    # Test database connection on startup
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        row = cursor.fetchone()
        logger.info(f"Connected to database: {row[0]}")
        conn.close()
    except Exception as e:
        logger.error(f"Failed to connect to database on startup: {str(e)}")

    # Start Flask server in a separate thread
    flask_thread = Thread(target=start_flask_server)
    flask_thread.daemon = True
    flask_thread.start()

    # Start PyQt application
    app_instance = QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app_instance.exec())