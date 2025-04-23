from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QFormLayout, QLineEdit,
    QMessageBox, QDialog, QTextEdit, QComboBox, QHeaderView
)
from PyQt6.QtCore import Qt
from datetime import datetime


class AlertDialog(QDialog):
    def __init__(self, db_manager, alert=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.alert = alert

        self.setWindowTitle("Add Alert" if not alert else "Edit Alert")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Create form
        form_layout = QFormLayout()

        # Alert Type
        self.type_input = QLineEdit()
        if alert:
            self.type_input.setText(alert[1])  # type_alerte
        form_layout.addRow("Alert Type:", self.type_input)

        # Description
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        if alert:
            self.description_input.setText(alert[2])  # description
        form_layout.addRow("Description:", self.description_input)

        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Open", "In Progress", "Resolved", "Closed"])
        if alert:
            index = self.status_combo.findText(alert[3])
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
        form_layout.addRow("Status:", self.status_combo)

        # Employee
        self.employee_combo = QComboBox()
        self.employee_combo.addItem("None", None)
        try:
            self.db_manager.cursor.execute("SELECT rfid, nom, prenom FROM Employe")
            employees = self.db_manager.cursor.fetchall()
            for emp in employees:
                self.employee_combo.addItem(f"{emp[1]}, {emp[2]} ({emp[0]})", emp[0])

            if alert and alert[4]:  # rfid
                for i in range(self.employee_combo.count()):
                    if self.employee_combo.itemData(i) == alert[4]:
                        self.employee_combo.setCurrentIndex(i)
                        break
        except Exception as e:
            print(f"Error loading employees: {e}")
        form_layout.addRow("Employee:", self.employee_combo)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_alert)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

    def save_alert(self):
        # Validate inputs
        if not self.type_input.text():
            QMessageBox.warning(self, "Validation Error", "Alert Type is a required field")
            return

        try:
            type_alerte = self.type_input.text()
            description = self.description_input.toPlainText()
            status = self.status_combo.currentText()
            rfid = self.employee_combo.currentData()

            # Get current date
            current_date = datetime.now().date()

            # Check if date exists in Date table
            self.db_manager.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (current_date,))
            date_id = self.db_manager.cursor.fetchone()

            if not date_id:
                # Insert date into Date table
                self.db_manager.cursor.execute('''
                    INSERT INTO Date (date_complete, jour, mois, annee, jour_semaine, est_jour_ferie, description_jour)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (current_date, current_date.day, current_date.month, current_date.year,
                      current_date.strftime("%A"), 0, ""))
                self.db_manager.conn.commit()

                # Get the new date_id
                self.db_manager.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (current_date,))
                date_id = self.db_manager.cursor.fetchone()

            if not self.alert:  # Add new alert
                self.db_manager.cursor.execute('''
                    INSERT INTO Alerte (type_alerte, description, status, rfid, date_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (type_alerte, description, status, rfid, date_id[0]))
            else:  # Update existing alert
                self.db_manager.cursor.execute('''
                    UPDATE Alerte
                    SET type_alerte = ?, description = ?, status = ?, rfid = ?
                    WHERE alerte_id = ?
                ''', (type_alerte, description, status, rfid, self.alert[0]))

            self.db_manager.conn.commit()
            self.accept()  # Close dialog with success

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving alert: {str(e)}")


class AlertViewGUI(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.setup_ui()
        self.load_alerts()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header with search and filter
        header_layout = QHBoxLayout()

        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_alerts)
        self.search_input.setPlaceholderText("Enter alert type or description...")

        header_layout.addWidget(search_label)
        header_layout.addWidget(self.search_input, 1)

        status_label = QLabel("Status Filter:")
        self.status_filter = QComboBox()
        self.status_filter.addItem("All", None)
        self.status_filter.addItems(["Open", "In Progress", "Resolved", "Closed"])
        self.status_filter.currentIndexChanged.connect(self.filter_alerts)

        header_layout.addWidget(status_label)
        header_layout.addWidget(self.status_filter)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_alerts)
        header_layout.addWidget(self.refresh_button)

        layout.addLayout(header_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Type", "Description", "Status", "Employee", "Date"
        ])

        # Set table properties
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)

        layout.addWidget(self.table)

        # Action buttons
        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Alert")
        self.add_button.clicked.connect(self.add_alert)
        button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit Alert")
        self.edit_button.clicked.connect(self.edit_alert)
        button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Delete Alert")
        self.delete_button.clicked.connect(self.delete_alert)
        button_layout.addWidget(self.delete_button)

        layout.addLayout(button_layout)

    def load_alerts(self):
        try:
            self.db_manager.cursor.execute('''
                SELECT a.alerte_id, a.type_alerte, a.description, a.status, a.rfid, 
                       e.nom, e.prenom, d.date_complete
                FROM Alerte a
                LEFT JOIN Employe e ON a.rfid = e.rfid
                LEFT JOIN Date d ON a.date_id = d.date_id
            ''')
            alerts = self.db_manager.cursor.fetchall()

            self.table.setRowCount(0)  # Clear the table

            for row_num, alert in enumerate(alerts):
                self.table.insertRow(row_num)

                # ID
                self.table.setItem(row_num, 0, QTableWidgetItem(str(alert[0])))

                # Type
                self.table.setItem(row_num, 1, QTableWidgetItem(alert[1]))

                # Description (shortened if too long)
                description = alert[2]
                if description and len(description) > 50:
                    description = description[:47] + "..."
                self.table.setItem(row_num, 2, QTableWidgetItem(description))

                # Status
                self.table.setItem(row_num, 3, QTableWidgetItem(alert[3] or ""))

                # Employee
                employee_name = f"{alert[5]} {alert[6]}" if alert[5] and alert[6] else ""
                self.table.setItem(row_num, 4, QTableWidgetItem(employee_name))

                # Date
                self.table.setItem(row_num, 5, QTableWidgetItem(str(alert[7] or "")))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading alerts: {str(e)}")

    def filter_alerts(self):
        search_text = self.search_input.text().lower()
        status_filter = self.status_filter.currentText()

        for row in range(self.table.rowCount()):
            match_found = True

            # Check for search text match
            if search_text:
                row_match = False
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item and search_text in item.text().lower():
                        row_match = True
                        break
                match_found = row_match

            # Check for status match if filter is not "All"
            if match_found and status_filter != "All":
                status_item = self.table.item(row, 3)
                if not status_item or status_item.text() != status_filter:
                    match_found = False

            self.table.setRowHidden(row, not match_found)

    def add_alert(self):
        dialog = AlertDialog(self.db_manager, parent=self)
        if dialog.exec():
            self.load_alerts()
            QMessageBox.information(self, "Success", "Alert added successfully")

    def edit_alert(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Required", "Please select an alert to edit")
            return

        selected_row = selected_rows[0].row()
        alert_id = int(self.table.item(selected_row, 0).text())

        try:
            self.db_manager.cursor.execute('''
                SELECT alerte_id, type_alerte, description, status, rfid
                FROM Alerte
                WHERE alerte_id = ?
            ''', (alert_id,))
            alert = self.db_manager.cursor.fetchone()

            if alert:
                dialog = AlertDialog(self.db_manager, alert, parent=self)
                if dialog.exec():
                    self.load_alerts()
                    QMessageBox.information(self, "Success", "Alert updated successfully")
            else:
                QMessageBox.warning(self, "Error", "Alert not found")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error editing alert: {str(e)}")

    def delete_alert(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Required", "Please select an alert to delete")
            return

        selected_row = selected_rows[0].row()
        alert_id = int(self.table.item(selected_row, 0).text())
        alert_type = self.table.item(selected_row, 1).text()

        # Check if the alert is linked to any events
        try:
            self.db_manager.cursor.execute("SELECT COUNT(*) FROM Evenement WHERE alerte_id = ?", (alert_id,))
            event_count = self.db_manager.cursor.fetchone()[0]

            if event_count > 0:
                reply = QMessageBox.question(
                    self, 'Alert Has Events',
                    f'Alert "{alert_type}" is linked to {event_count} events. Deleting this alert may cause issues. Proceed?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error checking associated events: {str(e)}")
            return

        reply = QMessageBox.question(
            self, 'Confirm Deletion',
            f'Are you sure you want to delete alert "{alert_type}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db_manager.cursor.execute("DELETE FROM Alerte WHERE alerte_id = ?", (alert_id,))
                self.db_manager.conn.commit()
                self.load_alerts()
                QMessageBox.information(self, "Success", "Alert deleted successfully")
            except Exception as e:
                self.db_manager.conn.rollback()
                QMessageBox.critical(self, "Error", f"Error deleting alert: {str(e)}")