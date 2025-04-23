from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QFormLayout, QLineEdit,
    QMessageBox, QDialog, QTextEdit, QComboBox, QHeaderView,
    QDateTimeEdit
)
from PyQt6.QtCore import Qt, QDateTime
from datetime import datetime


class EventDialog(QDialog):
    def __init__(self, db_manager, event=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.event = event

        self.setWindowTitle("Add Event" if not event else "Edit Event")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Create form
        form_layout = QFormLayout()

        # Event Type
        self.type_input = QLineEdit()
        if event:
            self.type_input.setText(event[1])  # type_evenement
        form_layout.addRow("Event Type:", self.type_input)

        # Event Date
        self.date_input = QDateTimeEdit()
        self.date_input.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.date_input.setCalendarPopup(True)
        self.date_input.setDateTime(QDateTime.currentDateTime())
        if event and event[2]:  # date_evenement
            try:
                event_date = QDateTime.fromString(str(event[2]), "yyyy-MM-dd HH:mm:ss")
                if event_date.isValid():
                    self.date_input.setDateTime(event_date)
            except Exception:
                pass
        form_layout.addRow("Event Date:", self.date_input)

        # Description
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        if event:
            self.description_input.setText(event[3])  # description
        form_layout.addRow("Description:", self.description_input)

        # Employee
        self.employee_combo = QComboBox()
        self.employee_combo.addItem("None", None)
        try:
            self.db_manager.cursor.execute("SELECT rfid, nom, prenom FROM Employe")
            employees = self.db_manager.cursor.fetchall()
            for emp in employees:
                self.employee_combo.addItem(f"{emp[1]}, {emp[2]} ({emp[0]})", emp[0])

            if event and event[4]:  # rfid
                for i in range(self.employee_combo.count()):
                    if self.employee_combo.itemData(i) == event[4]:
                        self.employee_combo.setCurrentIndex(i)
                        break
        except Exception as e:
            print(f"Error loading employees: {e}")
        form_layout.addRow("Employee:", self.employee_combo)

        # Team
        self.team_combo = QComboBox()
        self.team_combo.addItem("None", None)
        try:
            self.db_manager.cursor.execute("SELECT equipe_id, nom_equipe FROM Equipe")
            teams = self.db_manager.cursor.fetchall()
            for team in teams:
                self.team_combo.addItem(f"{team[1]}", team[0])

            if event and event[5]:  # equipe_id
                for i in range(self.team_combo.count()):
                    if self.team_combo.itemData(i) == event[5]:
                        self.team_combo.setCurrentIndex(i)
                        break
        except Exception as e:
            print(f"Error loading teams: {e}")
        form_layout.addRow("Team:", self.team_combo)

        # Position
        self.position_combo = QComboBox()
        self.position_combo.addItem("None", None)
        try:
            self.db_manager.cursor.execute("SELECT poste_id, titre_poste FROM Poste_Competence")
            positions = self.db_manager.cursor.fetchall()
            for pos in positions:
                self.position_combo.addItem(f"{pos[1]}", pos[0])

            if event and event[6]:  # poste_id
                for i in range(self.position_combo.count()):
                    if self.position_combo.itemData(i) == event[6]:
                        self.position_combo.setCurrentIndex(i)
                        break
        except Exception as e:
            print(f"Error loading positions: {e}")
        form_layout.addRow("Position:", self.position_combo)

        # Alert
        self.alert_combo = QComboBox()
        self.alert_combo.addItem("None", None)
        try:
            self.db_manager.cursor.execute("SELECT alerte_id, type_alerte FROM Alerte")
            alerts = self.db_manager.cursor.fetchall()
            for alert in alerts:
                self.alert_combo.addItem(f"{alert[1]} (ID: {alert[0]})", alert[0])

            if event and event[7]:  # alerte_id
                for i in range(self.alert_combo.count()):
                    if self.alert_combo.itemData(i) == event[7]:
                        self.alert_combo.setCurrentIndex(i)
                        break
        except Exception as e:
            print(f"Error loading alerts: {e}")
        form_layout.addRow("Related Alert:", self.alert_combo)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_event)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

    def save_event(self):
        # Validate inputs
        if not self.type_input.text():
            QMessageBox.warning(self, "Validation Error", "Event Type is a required field")
            return

        try:
            type_evenement = self.type_input.text()
            date_evenement = self.date_input.dateTime().toString("yyyy-MM-dd HH:mm:ss")
            description = self.description_input.toPlainText()
            rfid = self.employee_combo.currentData()
            equipe_id = self.team_combo.currentData()
            poste_id = self.position_combo.currentData()
            alerte_id = self.alert_combo.currentData()

            # Get date part only for Date table
            date_evenement_date = self.date_input.date().toString("yyyy-MM-dd")

            # Check if date exists in Date table
            self.db_manager.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (date_evenement_date,))
            date_id = self.db_manager.cursor.fetchone()

            if not date_id:
                # Insert date into Date table
                date_obj = datetime.strptime(date_evenement_date, "%Y-%m-%d").date()
                self.db_manager.cursor.execute('''
                    INSERT INTO Date (date_complete, jour, mois, annee, jour_semaine, est_jour_ferie, description_jour)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (date_evenement_date, date_obj.day, date_obj.month, date_obj.year,
                      date_obj.strftime("%A"), 0, ""))
                self.db_manager.conn.commit()

                # Get the new date_id
                self.db_manager.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?",
                                               (date_evenement_date,))
                date_id = self.db_manager.cursor.fetchone()

            if not self.event:  # Add new event
                self.db_manager.cursor.execute('''
                    INSERT INTO Evenement (type_evenement, date_evenement, description, rfid, equipe_id, poste_id, alerte_id, date_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (type_evenement, date_evenement, description, rfid, equipe_id, poste_id, alerte_id, date_id[0]))
            else:  # Update existing event
                self.db_manager.cursor.execute('''
                    UPDATE Evenement
                    SET type_evenement = ?, date_evenement = ?, description = ?, rfid = ?, equipe_id = ?, poste_id = ?, alerte_id = ?, date_id = ?
                    WHERE evenement_id = ?
                ''', (type_evenement, date_evenement, description, rfid, equipe_id, poste_id, alerte_id, date_id[0],
                      self.event[0]))

            self.db_manager.conn.commit()
            self.accept()  # Close dialog with success

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving event: {str(e)}")


class EventViewGUI(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.setup_ui()
        self.load_events()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header with search
        header_layout = QHBoxLayout()

        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_events)
        self.search_input.setPlaceholderText("Enter event type or description...")

        header_layout.addWidget(search_label)
        header_layout.addWidget(self.search_input, 1)

        self.event_type_filter = QComboBox()
        self.event_type_filter.addItem("All Types", None)
        try:
            self.db_manager.cursor.execute("SELECT DISTINCT type_evenement FROM Evenement")
            types = self.db_manager.cursor.fetchall()
            for type_item in types:
                if type_item[0]:  # Avoid None types
                    self.event_type_filter.addItem(type_item[0], type_item[0])
        except Exception as e:
            print(f"Error loading event types: {e}")
        self.event_type_filter.currentIndexChanged.connect(self.filter_events)

        header_layout.addWidget(QLabel("Type:"))
        header_layout.addWidget(self.event_type_filter)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_events)
        header_layout.addWidget(self.refresh_button)

        layout.addLayout(header_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Type", "Date", "Description", "Employee", "Team", "Position"
        ])

        # Set table properties
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)

        layout.addWidget(self.table)

        # Action buttons
        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Event")
        self.add_button.clicked.connect(self.add_event)
        button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit Event")
        self.edit_button.clicked.connect(self.edit_event)
        button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Delete Event")
        self.delete_button.clicked.connect(self.delete_event)
        button_layout.addWidget(self.delete_button)

        # View details button
        self.view_details_button = QPushButton("View Details")
        self.view_details_button.clicked.connect(self.view_event_details)
        button_layout.addWidget(self.view_details_button)

        layout.addLayout(button_layout)

    def load_events(self):
        try:
            self.db_manager.cursor.execute('''
                SELECT e.evenement_id, e.type_evenement, e.date_evenement, e.description, 
                       e.rfid, e.equipe_id, e.poste_id, e.alerte_id,
                       emp.nom, emp.prenom, eq.nom_equipe, pc.titre_poste
                FROM Evenement e
                LEFT JOIN Employe emp ON e.rfid = emp.rfid
                LEFT JOIN Equipe eq ON e.equipe_id = eq.equipe_id
                LEFT JOIN Poste_Competence pc ON e.poste_id = pc.poste_id
                ORDER BY e.date_evenement DESC
            ''')
            events = self.db_manager.cursor.fetchall()

            self.table.setRowCount(0)  # Clear the table

            for row_num, event in enumerate(events):
                self.table.insertRow(row_num)

                # ID
                self.table.setItem(row_num, 0, QTableWidgetItem(str(event[0])))

                # Type
                self.table.setItem(row_num, 1, QTableWidgetItem(event[1]))

                # Date
                self.table.setItem(row_num, 2, QTableWidgetItem(str(event[2])))

                # Description (shortened if too long)
                description = event[3]
                if description and len(description) > 50:
                    description = description[:47] + "..."
                self.table.setItem(row_num, 3, QTableWidgetItem(description))

                # Employee
                employee_name = f"{event[8]} {event[9]}" if event[8] and event[9] else ""
                self.table.setItem(row_num, 4, QTableWidgetItem(employee_name))

                # Team
                self.table.setItem(row_num, 5, QTableWidgetItem(str(event[10] or "")))

                # Position
                self.table.setItem(row_num, 6, QTableWidgetItem(str(event[11] or "")))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading events: {str(e)}")

    def filter_events(self):
        search_text = self.search_input.text().lower()
        event_type = self.event_type_filter.currentData()

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

            # Check for event type match if filter is active
            if match_found and event_type:
                type_item = self.table.item(row, 1)
                if not type_item or type_item.text() != event_type:
                    match_found = False

            self.table.setRowHidden(row, not match_found)

    def add_event(self):
        dialog = EventDialog(self.db_manager, parent=self)
        if dialog.exec():
            self.load_events()
            QMessageBox.information(self, "Success", "Event added successfully")

    def edit_event(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Required", "Please select an event to edit")
            return

        selected_row = selected_rows[0].row()
        event_id = int(self.table.item(selected_row, 0).text())

        try:
            self.db_manager.cursor.execute('''
                SELECT evenement_id, type_evenement, date_evenement, description, 
                       rfid, equipe_id, poste_id, alerte_id
                FROM Evenement
                WHERE evenement_id = ?
            ''', (event_id,))
            event = self.db_manager.cursor.fetchone()

            if event:
                dialog = EventDialog(self.db_manager, event, parent=self)
                if dialog.exec():
                    self.load_events()
                    QMessageBox.information(self, "Success", "Event updated successfully")
            else:
                QMessageBox.warning(self, "Error", "Event not found")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error editing event: {str(e)}")

    def delete_event(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Required", "Please select an event to delete")
            return

        selected_row = selected_rows[0].row()
        event_id = int(self.table.item(selected_row, 0).text())
        event_type = self.table.item(selected_row, 1).text()

        reply = QMessageBox.question(
            self, 'Confirm Deletion',
            f'Are you sure you want to delete event "{event_type}" (ID: {event_id})?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db_manager.cursor.execute("DELETE FROM Evenement WHERE evenement_id = ?", (event_id,))
                self.db_manager.conn.commit()
                self.load_events()
                QMessageBox.information(self, "Success", "Event deleted successfully")
            except Exception as e:
                self.db_manager.conn.rollback()
                QMessageBox.critical(self, "Error", f"Error deleting event: {str(e)}")

    def view_event_details(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Required", "Please select an event to view details")
            return

        selected_row = selected_rows[0].row()
        event_id = int(self.table.item(selected_row, 0).text())

        try:
            self.db_manager.cursor.execute('''
                SELECT e.evenement_id, e.type_evenement, e.date_evenement, e.description, 
                       emp.rfid, emp.nom, emp.prenom, eq.nom_equipe, pc.titre_poste, 
                       a.type_alerte, a.description as alert_description,
                       d.date_complete
                FROM Evenement e
                LEFT JOIN Employe emp ON e.rfid = emp.rfid
                LEFT JOIN Equipe eq ON e.equipe_id = eq.equipe_id
                LEFT JOIN Poste_Competence pc ON e.poste_id = pc.poste_id
                LEFT JOIN Alerte a ON e.alerte_id = a.alerte_id
                LEFT JOIN Date d ON e.date_id = d.date_id
                WHERE e.evenement_id = ?
            ''', (event_id,))

            event = self.db_manager.cursor.fetchone()

            if not event:
                QMessageBox.warning(self, "Error", "Event not found")
                return

            # Create a dialog to display event details
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Event Details - {event[1]}")
            dialog.setMinimumWidth(500)

            layout = QVBoxLayout(dialog)

            # Create details layout
            details_layout = QFormLayout()

            details_layout.addRow("Event ID:", QLabel(str(event[0])))
            details_layout.addRow("Type:", QLabel(event[1]))
            details_layout.addRow("Date:", QLabel(str(event[2])))
            details_layout.addRow("Description:", QLabel(event[3] or ""))

            if event[4]:  # Employee
                details_layout.addRow("Employee:", QLabel(f"{event[5]} {event[6]} ({event[4]})"))
            else:
                details_layout.addRow("Employee:", QLabel("None"))

            details_layout.addRow("Team:", QLabel(event[7] or "None"))
            details_layout.addRow("Position:", QLabel(event[8] or "None"))

            if event[9]:  # Alert
                details_layout.addRow("Related Alert:", QLabel(f"{event[9]}"))
                details_layout.addRow("Alert Description:", QLabel(event[10] or ""))
            else:
                details_layout.addRow("Related Alert:", QLabel("None"))

            details_layout.addRow("Date Record:", QLabel(str(event[11])))

            layout.addLayout(details_layout)

            # Close button
            close_button = QPushButton("Close")
            close_button.clicked.connect(dialog.accept)

            button_layout = QHBoxLayout()
            button_layout.addStretch()
            button_layout.addWidget(close_button)

            layout.addLayout(button_layout)

            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading event details: {str(e)}")