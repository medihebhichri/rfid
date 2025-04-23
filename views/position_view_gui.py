from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QFormLayout, QLineEdit,
    QMessageBox, QDialog, QTextEdit, QComboBox, QHeaderView
)
from PyQt6.QtCore import Qt


class PositionDialog(QDialog):
    def __init__(self, db_manager, position=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.position = position

        self.setWindowTitle("Add Position" if not position else "Edit Position")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Create form
        form_layout = QFormLayout()

        # Position Title
        self.title_input = QLineEdit()
        if position:
            self.title_input.setText(position[1])  # titre_poste
        form_layout.addRow("Position Title:", self.title_input)

        # Competence Level
        self.level_input = QComboBox()
        self.level_input.addItems(["Junior", "Intermediate", "Senior", "Expert"])
        if position and position[2]:
            index = self.level_input.findText(position[2])
            if index >= 0:
                self.level_input.setCurrentIndex(index)
        form_layout.addRow("Competence Level:", self.level_input)

        # Description
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        if position and position[3]:
            self.description_input.setText(position[3])
        form_layout.addRow("Description:", self.description_input)

        # Requirements
        self.requirements_input = QTextEdit()
        self.requirements_input.setMaximumHeight(100)
        if position and position[4]:
            self.requirements_input.setText(position[4])
        form_layout.addRow("Requirements:", self.requirements_input)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_position)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

    def save_position(self):
        # Validate inputs
        if not self.title_input.text():
            QMessageBox.warning(self, "Validation Error", "Position Title is a required field")
            return

        try:
            titre_poste = self.title_input.text()
            niveau_competence = self.level_input.currentText()
            description = self.description_input.toPlainText()
            requirements = self.requirements_input.toPlainText()

            if not self.position:  # Add new position
                self.db_manager.cursor.execute('''
                    INSERT INTO Poste_Competence (titre_poste, niveau_competence, description, requirements)
                    VALUES (?, ?, ?, ?)
                ''', (titre_poste, niveau_competence, description, requirements))
            else:  # Update existing position
                self.db_manager.cursor.execute('''
                    UPDATE Poste_Competence
                    SET titre_poste = ?, niveau_competence = ?, description = ?, requirements = ?
                    WHERE poste_id = ?
                ''', (titre_poste, niveau_competence, description, requirements, self.position[0]))

            self.db_manager.conn.commit()
            self.accept()  # Close dialog with success
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving position: {str(e)}")


class PositionViewGUI(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.setup_ui()
        self.load_positions()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header with search
        header_layout = QHBoxLayout()

        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_positions)
        self.search_input.setPlaceholderText("Enter position title or competence level...")

        header_layout.addWidget(search_label)
        header_layout.addWidget(self.search_input, 1)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_positions)
        header_layout.addWidget(self.refresh_button)

        layout.addLayout(header_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID", "Position Title", "Competence Level", "Description", "Requirements"
        ])

        # Set table properties
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)

        layout.addWidget(self.table)

        # Action buttons
        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Position")
        self.add_button.clicked.connect(self.add_position)
        button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit Position")
        self.edit_button.clicked.connect(self.edit_position)
        button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Delete Position")
        self.delete_button.clicked.connect(self.delete_position)
        button_layout.addWidget(self.delete_button)

        # Add employee count button
        self.view_employees_button = QPushButton("View Position Employees")
        self.view_employees_button.clicked.connect(self.view_position_employees)
        button_layout.addWidget(self.view_employees_button)

        layout.addLayout(button_layout)

    def load_positions(self):
        try:
            self.db_manager.cursor.execute('SELECT * FROM Poste_Competence')
            positions = self.db_manager.cursor.fetchall()

            self.table.setRowCount(0)  # Clear the table

            for row_num, pos in enumerate(positions):
                self.table.insertRow(row_num)

                # ID
                self.table.setItem(row_num, 0, QTableWidgetItem(str(pos[0])))

                # Position Title
                self.table.setItem(row_num, 1, QTableWidgetItem(pos[1]))

                # Competence Level
                self.table.setItem(row_num, 2, QTableWidgetItem(pos[2] or ""))

                # Description
                self.table.setItem(row_num, 3, QTableWidgetItem(pos[3] or ""))

                # Requirements
                self.table.setItem(row_num, 4, QTableWidgetItem(pos[4] or ""))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading positions: {str(e)}")

    def filter_positions(self):
        search_text = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            match_found = False

            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    match_found = True
                    break

            self.table.setRowHidden(row, not match_found)

    def add_position(self):
        dialog = PositionDialog(self.db_manager, parent=self)
        if dialog.exec():
            self.load_positions()
            QMessageBox.information(self, "Success", "Position added successfully")

    def edit_position(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Required", "Please select a position to edit")
            return

        selected_row = selected_rows[0].row()
        position_id = int(self.table.item(selected_row, 0).text())

        try:
            self.db_manager.cursor.execute("SELECT * FROM Poste_Competence WHERE poste_id = ?", (position_id,))
            position = self.db_manager.cursor.fetchone()

            if position:
                dialog = PositionDialog(self.db_manager, position, parent=self)
                if dialog.exec():
                    self.load_positions()
                    QMessageBox.information(self, "Success", "Position updated successfully")
            else:
                QMessageBox.warning(self, "Error", "Position not found")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error editing position: {str(e)}")

    def delete_position(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Required", "Please select a position to delete")
            return

        selected_row = selected_rows[0].row()
        position_id = int(self.table.item(selected_row, 0).text())
        position_title = self.table.item(selected_row, 1).text()

        # Check if the position has employees
        try:
            self.db_manager.cursor.execute("SELECT COUNT(*) FROM Employe WHERE poste_id = ?", (position_id,))
            employee_count = self.db_manager.cursor.fetchone()[0]

            if employee_count > 0:
                QMessageBox.warning(
                    self, 'Cannot Delete Position',
                    f'Position {position_title} has {employee_count} employees assigned to it. Cannot delete.'
                )
                return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error checking position employees: {str(e)}")
            return

        reply = QMessageBox.question(
            self, 'Confirm Deletion',
            f'Are you sure you want to delete position {position_title}?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db_manager.cursor.execute("DELETE FROM Poste_Competence WHERE poste_id = ?", (position_id,))
                self.db_manager.conn.commit()
                self.load_positions()
                QMessageBox.information(self, "Success", "Position deleted successfully")
            except Exception as e:
                self.db_manager.conn.rollback()
                QMessageBox.critical(self, "Error", f"Error deleting position: {str(e)}")

    def view_position_employees(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Required", "Please select a position to view employees")
            return

        selected_row = selected_rows[0].row()
        position_id = int(self.table.item(selected_row, 0).text())
        position_title = self.table.item(selected_row, 1).text()

        try:
            self.db_manager.cursor.execute('''
                SELECT e.rfid, e.nom, e.prenom, eq.nom_equipe
                FROM Employe e
                LEFT JOIN Equipe eq ON e.equipe_id = eq.equipe_id
                WHERE e.poste_id = ?
            ''', (position_id,))

            employees = self.db_manager.cursor.fetchall()

            if not employees:
                QMessageBox.information(self, "Position Employees", f"Position {position_title} has no employees")
                return

            # Create a simple dialog to display position employees
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Position Employees - {position_title}")
            dialog.setMinimumWidth(500)

            layout = QVBoxLayout(dialog)

            # Create table for employees
            employee_table = QTableWidget()
            employee_table.setColumnCount(4)
            employee_table.setHorizontalHeaderLabels(["RFID", "Last Name", "First Name", "Team"])
            employee_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            employee_table.setAlternatingRowColors(True)

            # Populate table
            for row_num, emp in enumerate(employees):
                employee_table.insertRow(row_num)
                employee_table.setItem(row_num, 0, QTableWidgetItem(str(emp[0])))
                employee_table.setItem(row_num, 1, QTableWidgetItem(str(emp[1])))
                employee_table.setItem(row_num, 2, QTableWidgetItem(str(emp[2])))
                employee_table.setItem(row_num, 3, QTableWidgetItem(str(emp[3] or "")))

            layout.addWidget(employee_table)

            # Close button
            close_button = QPushButton("Close")
            close_button.clicked.connect(dialog.accept)

            button_layout = QHBoxLayout()
            button_layout.addStretch()
            button_layout.addWidget(close_button)

            layout.addLayout(button_layout)

            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading position employees: {str(e)}")