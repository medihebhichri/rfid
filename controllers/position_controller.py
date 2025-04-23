from models.database_manager import DatabaseManager
from models.position import Position
from view.position_view import PositionView

class PositionController:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.view = PositionView()

    def add_position(self):
        try:
            titre_poste = input("Enter Position Title: ")
            niveau_competence = input("Enter Competence Level: ")
            description = input("Enter Description: ")
            requirements = input("Enter Requirements: ")

            self.db.cursor.execute('''
                INSERT INTO Poste_Competence (titre_poste, niveau_competence, description, requirements)
                VALUES (?, ?, ?, ?)
            ''', (titre_poste, niveau_competence, description, requirements))
            self.db.conn.commit()
            self.view.success("Position added successfully!")
        except Exception as e:
            self.view.error(f"Error adding position: {str(e)}")
        input("Press Enter to continue...")

    def view_positions(self):
        try:
            self.db.cursor.execute("SELECT * FROM Poste_Competence")
            positions = self.db.cursor.fetchall()
            if positions:
                self.view.print_positions(positions)
            else:
                self.view.error("No positions found.")
        except Exception as e:
            self.view.error(f"Error viewing positions: {str(e)}")
        input("Press Enter to continue...")

    def update_position(self):
        try:
            self.view.view_positions()
            poste_id = int(input("Enter Position ID to update: "))
            self.db.cursor.execute("SELECT * FROM Poste_Competence WHERE poste_id=?", (poste_id,))
            pos = self.db.cursor.fetchone()
            if not pos:
                self.view.error("Position not found!")
                return

            print("Leave blank to keep current value.")
            titre_poste = input(f"Enter new Title [{pos.titre_poste}]: ") or pos.titre_poste
            niveau_competence = input(f"Enter new Level [{pos.niveau_competence}]: ") or pos.niveau_competence
            description = input(f"Enter new Description [{pos.description}]: ") or pos.description
            requirements = input(f"Enter new Requirements [{pos.requirements}]: ") or pos.requirements

            self.db.cursor.execute('''
                UPDATE Poste_Competence
                SET titre_poste=?, niveau_competence=?, description=?, requirements=?
                WHERE poste_id=?
            ''', (titre_poste, niveau_competence, description, requirements, poste_id))
            self.db.conn.commit()
            self.view.success("Position updated successfully!")
        except Exception as e:
            self.view.error(f"Error updating position: {str(e)}")
        input("Press Enter to continue...")

    def delete_position(self):
        try:
            self.view.view_positions()
            poste_id = int(input("Enter Position ID to delete: "))
            self.db.cursor.execute("SELECT COUNT(*) FROM Employe WHERE poste_id=?", (poste_id,))
            count = self.db.cursor.fetchone()[0]
            if count > 0:
                self.view.error("Cannot delete position. Employees are assigned to it.")
                return

            self.db.cursor.execute("DELETE FROM Poste_Competence WHERE poste_id=?", (poste_id,))
            self.db.conn.commit()
            self.view.success("Position deleted successfully!")
        except Exception as e:
            self.view.error(f"Error deleting position: {str(e)}")
        input("Press Enter to continue...")

    def position_menu(self):
        while True:
            print("\n=== Position Management ===")
            print("1. Add Position")
            print("2. View All Positions")
            print("3. Update Position")
            print("4. Delete Position")
            print("0. Back to Main Menu")
            choice = input("Enter choice: ")

            if choice == "1":
                self.add_position()
            elif choice == "2":
                self.view_positions()
            elif choice == "3":
                self.update_position()
            elif choice == "4":
                self.delete_position()
            elif choice == "0":
                break
            else:
                self.view.error("Invalid choice!")