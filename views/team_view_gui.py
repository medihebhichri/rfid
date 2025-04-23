from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QFormLayout, QLineEdit,
    QMessageBox, QDialog, QTextEdit, QHeaderView
)
from PyQt6.QtCore import Qt


class TeamDialog(QDialog):
    def __init__(self, db_manager, team=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.team = team

        self.setWindowTitle("Add Team" if not team else "Edit Team")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Create form
        form_layout = QFormLayout()

        # Team Name
        self.name_input = QLineEdit()
        if team:
            self.name_input.setText(team[1])  # nom_equipe
        form_layout.addRow("Team Name:", self.name_input)

        # Team Leader
        self.leader_input = QLineEdit()
        if team:
            self.leader_input.setText(team[3])  # chef_equipe
        form_layout.addRow("Team Leader:", self.leader_input)

        # Description
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        if team:
            self.description_input.setText(team[2])  # description
        form_layout.addRow("Description:", self.description_input)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_team)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

    def save_team(self):
        # Validate inputs
        if not self.name_input.text():
            QMessageBox.warning(self, "Validation Error", "Team Name is a required field")
            return

        try:
            nom_equipe = self.name_input.text()
            description = self.description_input.toPlainText()
            chef_equipe = self.leader_input.text()

            if not self.team:  # Add new team
                self.db_manager.cursor.execute('''
                    INSERT INTO Equipe (nom_equipe, description, chef_equipe)
                    VALUES (?, ?, ?)
                ''', (nom_equipe, description, chef_equipe))
            else:  # Update existing team
                self.db_manager.cursor.execute('''
                    UPDATE Equipe
                    SET nom_equipe = ?, description = ?, chef_equipe = ?
                    WHERE equipe_id = ?
                ''', (nom_equipe, description, chef_equipe, self.team[0]))

            self.db_manager.conn.commit()
            self.accept()  # Close dialog with success
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving team: {str(e)}")


class TeamViewGUI(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.setup_ui()
        self.load_teams()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header with search
        header_layout = QHBoxLayout()

        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_teams)
        self.search_input.setPlaceholderText("Enter team name or leader...")

        header_layout.addWidget(search_label)
        header_layout.addWidget(self.search_input, 1)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_teams)
        header_layout.addWidget(self.refresh_button)

        layout.addLayout(header_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "ID", "Team Name", "Team Leader", "Description"
        ])

        # Set table properties
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)

        layout.addWidget(self.table)

        # Action buttons
        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Team")
        self.add_button.clicked.connect(self.add_team)
        button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit Team")
        self.edit_button.clicked.connect(self.edit_team)
        button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Delete Team")
        self.delete_button.clicked.connect(self.delete_team)
        button_layout.addWidget(self.delete_button)

        # Add employee count button
        self.view_members_button = QPushButton("View Team Members")
        self.view_members_button.clicked.connect(self.view_team_members)
        button_layout.addWidget(self.view_members_button)

        layout.addLayout(button_layout)

    def load_teams(self):
        try:
            self.db_manager.cursor.execute('SELECT * FROM Equipe')
            teams = self.db_manager.cursor.fetchall()

            self.table.setRowCount(0)  # Clear the table

            for row_num, team in enumerate(teams):
                self.table.insertRow(row_num)

                # ID
                self.table.setItem(row_num, 0, QTableWidgetItem(str(team[0])))

                # Team Name
                self.table.setItem(row_num, 1, QTableWidgetItem(team[1]))

                # Team Leader
                self.table.setItem(row_num, 2, QTableWidgetItem(team[3] or ""))

                # Description
                self.table.setItem(row_num, 3, QTableWidgetItem(team[2] or ""))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading teams: {str(e)}")

    def filter_teams(self):
        search_text = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            match_found = False

            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    match_found = True
                    break

            self.table.setRowHidden(row, not match_found)

    def add_team(self):
        dialog = TeamDialog(self.db_manager, parent=self)
        if dialog.exec():
            self.load_teams()
            QMessageBox.information(self, "Success", "Team added successfully")

    def edit_team(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Required", "Please select a team to edit")
            return

        selected_row = selected_rows[0].row()
        team_id = int(self.table.item(selected_row, 0).text())

        try:
            self.db_manager.cursor.execute("SELECT * FROM Equipe WHERE equipe_id = ?", (team_id,))
            team = self.db_manager.cursor.fetchone()

            if team:
                dialog = TeamDialog(self.db_manager, team, parent=self)
                if dialog.exec():
                    self.load_teams()
                    QMessageBox.information(self, "Success", "Team updated successfully")
            else:
                QMessageBox.warning(self, "Error", "Team not found")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error editing team: {str(e)}")

    def delete_team(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Required", "Please select a team to delete")
            return

        selected_row = selected_rows[0].row()
        team_id = int(self.table.item(selected_row, 0).text())
        team_name = self.table.item(selected_row, 1).text()

        # Check if the team has employees
        try:
            self.db_manager.cursor.execute("SELECT COUNT(*) FROM Employe WHERE equipe_id = ?", (team_id,))
            employee_count = self.db_manager.cursor.fetchone()[0]

            if employee_count > 0:
                reply = QMessageBox.question(
                    self, 'Team Has Employees',
                    f'Team {team_name} has {employee_count} employees assigned to it. Deleting this team may cause issues. Proceed?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error checking team employees: {str(e)}")
            return

        reply = QMessageBox.question(
            self, 'Confirm Deletion',
            f'Are you sure you want to delete team {team_name}?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db_manager.cursor.execute("DELETE FROM Equipe WHERE equipe_id = ?", (team_id,))
                self.db_manager.conn.commit()
                self.load_teams()
                QMessageBox.information(self, "Success", "Team deleted successfully")
            except Exception as e:
                self.db_manager.conn.rollback()
                QMessageBox.critical(self, "Error", f"Error deleting team: {str(e)}")

    def view_team_members(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Required", "Please select a team to view members")
            return

        selected_row = selected_rows[0].row()
        team_id = int(self.table.item(selected_row, 0).text())
        team_name = self.table.item(selected_row, 1).text()

        try:
            self.db_manager.cursor.execute('''
                SELECT e.rfid, e.nom, e.prenom, pc.titre_poste
                FROM Employe e
                LEFT JOIN Poste_Competence pc ON e.poste_id = pc.poste_id
                WHERE e.equipe_id = ?
            ''', (team_id,))

            employees = self.db_manager.cursor.fetchall()

            if not employees:
                QMessageBox.information(self, "Team Members", f"Team {team_name} has no members")
                return

            # Create a simple dialog to display team members
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Team Members - {team_name}")
            dialog.setMinimumWidth(500)

            layout = QVBoxLayout(dialog)

            # Create table for members
            member_table = QTableWidget()
            member_table.setColumnCount(4)
            member_table.setHorizontalHeaderLabels(["RFID", "Last Name", "First Name", "Position"])
            member_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            member_table.setAlternatingRowColors(True)

            # Populate table
            for row_num, emp in enumerate(employees):
                member_table.insertRow(row_num)
                member_table.setItem(row_num, 0, QTableWidgetItem(str(emp[0])))
                member_table.setItem(row_num, 1, QTableWidgetItem(str(emp[1])))
                member_table.setItem(row_num, 2, QTableWidgetItem(str(emp[2])))
                member_table.setItem(row_num, 3, QTableWidgetItem(str(emp[3] or "")))

            layout.addWidget(member_table)

            # Close button
            close_button = QPushButton("Close")
            close_button.clicked.connect(dialog.accept)

            button_layout = QHBoxLayout()
            button_layout.addStretch()
            button_layout.addWidget(close_button)

            layout.addLayout(button_layout)

            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading team members: {str(e)}")