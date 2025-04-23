import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QVBoxLayout,
    QHBoxLayout, QWidget, QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from models.database_manager import DatabaseManager
from views.employee_view_gui import EmployeeViewGUI
from views.team_view_gui import TeamViewGUI
from views.position_view_gui import PositionViewGUI
from views.event_view_gui import EventViewGUI
from views.alert_view_gui import AlertViewGUI


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up the database manager
        self.db_manager = DatabaseManager()

        # Set up the main window
        self.setWindowTitle("Employee Management System")
        self.setMinimumSize(1000, 600)

        # Create the central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create header
        header_layout = QHBoxLayout()
        logo_label = QLabel("EMS")
        logo_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        header_layout.addWidget(logo_label)

        title_label = QLabel("Employee Management System")
        title_label.setFont(QFont("Arial", 16))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label, 1)

        # Add the header to the main layout
        main_layout.addLayout(header_layout)

        # Create tab widget
        self.tabs = QTabWidget()

        # Create tabs for each module
        self.employee_tab = EmployeeViewGUI(self.db_manager)
        self.team_tab = TeamViewGUI(self.db_manager)
        self.position_tab = PositionViewGUI(self.db_manager)
        self.event_tab = EventViewGUI(self.db_manager)
        self.alert_tab = AlertViewGUI(self.db_manager)

        # Add tabs to the tab widget
        self.tabs.addTab(self.employee_tab, "Employees")
        self.tabs.addTab(self.team_tab, "Teams")
        self.tabs.addTab(self.position_tab, "Positions")
        self.tabs.addTab(self.event_tab, "Events")
        self.tabs.addTab(self.alert_tab, "Alerts")

        # Add the tab widget to the main layout
        main_layout.addWidget(self.tabs)

        # Create footer with exit button
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        exit_button = QPushButton("Exit")
        exit_button.setMinimumSize(100, 30)
        exit_button.clicked.connect(self.close)
        footer_layout.addWidget(exit_button)

        # Add the footer to the main layout
        main_layout.addLayout(footer_layout)

    def closeEvent(self, event):
        """Handle window close event to properly shut down the application"""
        reply = QMessageBox.question(
            self, 'Exit',
            'Are you sure you want to exit?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Close database connection
            self.db_manager.conn.close()
            event.accept()
        else:
            event.ignore()