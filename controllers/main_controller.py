from controllers.employee_controller import EmployeeController
from controllers.team_controller import TeamController
from controllers.position_controller import PositionController
from controllers.EventController import EventController
from controllers.AlertController import AlertController
from models.database_manager import DatabaseManager
from view.main_view import MainView

class MainController:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.main_view = MainView()
        self.employee_controller = EmployeeController(self.db_manager)
        self.team_controller = TeamController(self.db_manager)
        self.position_controller = PositionController(self.db_manager)
        self.event_controller = EventController(self.db_manager)
        self.alert_controller = AlertController(self.db_manager)

    def run(self):
        while True:
            self.main_view.print_main_menu()
            choice = input("Enter your choice (0-5): ")

            if choice == "1":
                self.employee_controller.employee_menu()
            elif choice == "2":
                self.team_controller.team_menu()
            elif choice == "3":
                self.position_controller.position_menu()
            elif choice == "4":
                self.event_controller.event_menu()
            elif choice == "5":
                self.alert_controller.alert_menu()
            elif choice == "0":
                print("\nThank you for using Employee Management System!")
                break
            else:
                input("\nInvalid choice. Press Enter to continue...")