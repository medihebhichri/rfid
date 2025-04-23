from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QFormLayout, QLineEdit,
    QDateEdit, QMessageBox, QDialog, QComboBox, QHeaderView
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime


class EmployeeDialog(QDialog):
    def __init__(self, db_manager, employee=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.employee = employee

        self.setWindowTitle("Add Employee" if not employee else "Edit Employee")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Create form
        form_layout = QFormLayout()

        # RFID
        self.rfid_input = QLineEdit()
        if employee:
            self.rfid_input.setText(employee[0])  # rfid
            self.rfid_input.setReadOnly(True)  # RFID cannot be changed when editing
        form_layout.addRow("RFID:", self.rfid_input)

        # Last Name
        self.lastname_input = QLineEdit()
        if employee:
            self.lastname_input.setText(employee[1])  # nom
        form_layout.addRow("Last Name:", self.lastname_input)

        # First Name
        self.firstname_input = QLineEdit()
        if employee:
            self.firstname_input.setText(employee[2])  # prenom
        form_layout.addRow("First Name:", self.firstname_input)

        # Birth Date
        self.birth_date_input = QDateEdit()
        self.birth_date_input.setDisplayFormat("yyyy-MM-dd")
        self.birth_date_input.setCalendarPopup(True)
        if employee and employee[3]:  # date_naissance
            self.birth_date_input.setDate(QDate.fromString(str(employee[3]), "yyyy-MM-dd"))
        else:
            self.birth_date_input.setDate(QDate.currentDate())
        form_layout.addRow("Birth Date:", self.birth_date_input)

        # Hire Date
        self.hire_date_input = QDateEdit()
        self.hire_date_input.setDisplayFormat("yyyy-MM-dd")
        self.hire_date_input.setCalendarPopup(True)
        if employee and employee[4]:  # date_embauche
            self.hire_date_input.setDate(QDate.fromString(str(employee[4]), "yyyy-MM-dd"))
        else:
            self.hire_date_input.setDate(QDate.currentDate())
        form_layout.addRow("Hire Date:", self.hire_date_input)

        # Email
        self.email_input = QLineEdit()
        if employee:
            self.email_input.setText(employee[5])  # email
        form_layout.addRow("Email:", self.email_input)

        # Phone
        self.phone_input = QLineEdit()
        if employee:
            self.phone_input.setText(employee[6])  # telephone
        form_layout.addRow("Phone:", self.phone_input)

        # Address
        self.address_input = QLineEdit()
        if employee:
            self.address_input.setText(employee[7])  # adresse
        form_layout.addRow("Address:", self.address_input)

        # Team dropdown
        self.team_combo = QComboBox()
        try:
            self.db_manager.cursor.execute("SELECT equipe_id, nom_equipe FROM Equipe")
            teams = self.db_manager.cursor.fetchall()
            for team in teams:
                self.team_combo.addItem(f"{team[1]}", team[0])
            if employee and employee[8]:  # equipe_id
                index = self.team_combo.findData(employee[8])
                if index >= 0:
                    self.team_combo.setCurrentIndex(index)
        except Exception as e:
            print(f"Error loading teams: {e}")
        form_layout.addRow("Team:", self.team_combo)

        # Position dropdown
        self.position_combo = QComboBox()
        try:
            self.db_manager.cursor.execute("SELECT poste_id, titre_poste FROM Poste_Competence")
            positions = self.db_manager.cursor.fetchall()
            for position in positions:
                self.position_combo.addItem(f"{position[1]}", position[0])
            if employee and employee[9]:  # poste_id
                index = self.position_combo.findData(employee[9])
                if index >= 0:
                    self.position_combo.setCurrentIndex(index)
        except Exception as e:
            print(f"Error loading positions: {e}")
        form_layout.addRow("Position:", self.position_combo)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_employee)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

    def save_employee(self):
        # Validate inputs
        if not self.rfid_input.text() or not self.lastname_input.text() or not self.firstname_input.text():
            QMessageBox.warning(self, "Validation Error", "RFID, Last Name, and First Name are required fields")
            return

        try:
            rfid = self.rfid_input.text()
            nom = self.lastname_input.text()
            prenom = self.firstname_input.text()
            date_naissance = self.birth_date_input.date().toString("yyyy-MM-dd")
            date_embauche = self.hire_date_input.date().toString("yyyy-MM-dd")
            email = self.email_input.text()
            telephone = self.phone_input.text()
            adresse = self.address_input.text()
            equipe_id = self.team_combo.currentData()
            poste_id = self.position_combo.currentData()

            # Insert birth date into Date table if it doesn't exist
            self.db_manager.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (date_naissance,))
            date_naissance_id = self.db_manager.cursor.fetchone()
            if not date_naissance_id:
                date_obj = datetime.strptime(date_naissance, "%Y-%m-%d").date()
                self.db_manager.cursor.execute('''
                    INSERT INTO Date (date_complete, jour, mois, annee, jour_semaine, est_jour_ferie, description_jour)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (date_naissance, date_obj.day, date_obj.month, date_obj.year,
                      date_obj.strftime("%A"), 0, ""))
                self.db_manager.conn.commit()
                self.db_manager.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (date_naissance,))
                date_naissance_id = self.db_manager.cursor.fetchone()

            # Insert hire date into Date table if it doesn't exist
            self.db_manager.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (date_embauche,))
            date_embauche_id = self.db_manager.cursor.fetchone()
            if not date_embauche_id:
                date_obj = datetime.strptime(date_embauche, "%Y-%m-%d").date()
                self.db_manager.cursor.execute('''
                    INSERT INTO Date (date_complete, jour, mois, annee, jour_semaine, est_jour_ferie, description_jour)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (date_embauche, date_obj.day, date_obj.month, date_obj.year, date_obj.strftime("%A"),
                      0, ""))
                self.db_manager.conn.commit()
                self.db_manager.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (date_embauche,))
                date_embauche_id = self.db_manager.cursor.fetchone()

            if not self.employee:  # Add new employee
                # Check if RFID already exists
                self.db_manager.cursor.execute("SELECT rfid FROM Employe WHERE rfid = ?", (rfid,))
                if self.db_manager.cursor.fetchone():
                    QMessageBox.warning(self, "Duplicate RFID", f"RFID {rfid} already exists")
                    return

                self.db_manager.cursor.execute('''
                    INSERT INTO Employe (rfid, nom, prenom, date_naissance, date_embauche, email, telephone, adresse, equipe_id, poste_id, date_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (rfid, nom, prenom, date_naissance, date_embauche, email, telephone, adresse, equipe_id, poste_id,
                      date_naissance_id[0]))
            else:  # Update existing employee
                self.db_manager.cursor.execute('''
                    UPDATE Employe
                    SET nom = ?, prenom = ?, date_naissance = ?, date_embauche = ?, email = ?, telephone = ?, adresse = ?, equipe_id = ?, poste_id = ?, date_id = ?
                    WHERE rfid = ?
                ''', (nom, prenom, date_naissance, date_embauche, email, telephone, adresse, equipe_id, poste_id,
                      date_embauche_id[0], rfid))

            self.db_manager.conn.commit()
            self.accept()  # Close dialog with success
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving employee: {str(e)}")


class EmployeeViewGUI(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.setup_ui()
        self.load_employees()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header with search
        header_layout = QHBoxLayout()

        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_employees)
        self.search_input.setPlaceholderText("Enter name, team or position...")

        header_layout.addWidget(search_label)
        header_layout.addWidget(self.search_input, 1)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_employees)
        header_layout.addWidget(self.refresh_button)

        layout.addLayout(header_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "RFID", "Name", "Email", "Phone",
            "Team", "Position", "Birth Date", "Hire Date", "Address"
        ])

        # Set table properties
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)

        layout.addWidget(self.table)

        # Action buttons
        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Employee")
        self.add_button.clicked.connect(self.add_employee)
        button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit Employee")
        self.edit_button.clicked.connect(self.edit_employee)
        button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Delete Employee")
        self.delete_button.clicked.connect(self.delete_employee)
        button_layout.addWidget(self.delete_button)

        layout.addLayout(button_layout)

    def load_employees(self):
        try:
            self.db_manager.cursor.execute('''
                SELECT e.rfid, e.nom, e.prenom, e.date_naissance, e.date_embauche, e.email, e.telephone, e.adresse, 
                       e.equipe_id, e.poste_id, eq.nom_equipe, pc.titre_poste
                FROM Employe e
                LEFT JOIN Equipe eq ON e.equipe_id = eq.equipe_id
                LEFT JOIN Poste_Competence pc ON e.poste_id = pc.poste_id
            ''')
            employees = self.db_manager.cursor.fetchall()

            self.table.setRowCount(0)  # Clear the table

            for row_num, emp in enumerate(employees):
                self.table.insertRow(row_num)

                # RFID
                self.table.setItem(row_num, 0, QTableWidgetItem(str(emp[0])))

                # Name (Last, First)
                self.table.setItem(row_num, 1, QTableWidgetItem(f"{emp[1]}, {emp[2]}"))

                # Email
                self.table.setItem(row_num, 2, QTableWidgetItem(str(emp[5])))

                # Phone
                self.table.setItem(row_num, 3, QTableWidgetItem(str(emp[6])))

                # Team
                self.table.setItem(row_num, 4, QTableWidgetItem(str(emp[10] or "")))

                # Position
                self.table.setItem(row_num, 5, QTableWidgetItem(str(emp[11] or "")))

                # Birth Date
                self.table.setItem(row_num, 6, QTableWidgetItem(str(emp[3])))

                # Hire Date
                self.table.setItem(row_num, 7, QTableWidgetItem(str(emp[4])))

                # Address
                self.table.setItem(row_num, 8, QTableWidgetItem(str(emp[7])))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading employees: {str(e)}")

    def filter_employees(self):
        search_text = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            match_found = False

            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    match_found = True
                    break

            self.table.setRowHidden(row, not match_found)

    def add_employee(self):
        dialog = EmployeeDialog(self.db_manager, parent=self)
        if dialog.exec():
            self.load_employees()
            QMessageBox.information(self, "Success", "Employee added successfully")

    def edit_employee(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Required", "Please select an employee to edit")
            return

        selected_row = selected_rows[0].row()
        rfid = self.table.item(selected_row, 0).text()

        try:
            self.db_manager.cursor.execute('''
                SELECT e.rfid, e.nom, e.prenom, e.date_naissance, e.date_embauche, e.email, e.telephone, 
                       e.adresse, e.equipe_id, e.poste_id
                FROM Employe e
                WHERE e.rfid = ?
            ''', (rfid,))
            employee = self.db_manager.cursor.fetchone()

            if employee:
                dialog = EmployeeDialog(self.db_manager, employee, parent=self)
                if dialog.exec():
                    self.load_employees()
                    QMessageBox.information(self, "Success", "Employee updated successfully")
            else:
                QMessageBox.warning(self, "Error", "Employee not found")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error editing employee: {str(e)}")

    def delete_employee(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Required", "Please select an employee to delete")
            return

        selected_row = selected_rows[0].row()
        rfid = self.table.item(selected_row, 0).text()
        name = self.table.item(selected_row, 1).text()

        reply = QMessageBox.question(
            self, 'Confirm Deletion',
            f'Are you sure you want to delete employee {name} ({rfid})?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db_manager.cursor.execute("DELETE FROM Employe WHERE rfid = ?", (rfid,))
                self.db_manager.conn.commit()
                self.load_employees()
                QMessageBox.information(self, "Success", "Employee deleted successfully")
            except Exception as e:
                self.db_manager.conn.rollback()
                QMessageBox.critical(self, "Error", f"Error deleting employee: {str(e)}")