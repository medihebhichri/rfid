from datetime import datetime

from models.database_manager import DatabaseManager
from models.alert import Alert
from view.AlertView import AlertView

class AlertController:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.view = AlertView()

    def add_alert(self):
        try:
            type_alerte = input("Enter Alert Type: ")
            description = input("Enter Description: ")
            status = input("Enter Status (e.g., Open, Closed): ")

            self.db.cursor.execute("SELECT rfid, nom, prenom FROM Employe")
            employees = self.db.cursor.fetchall()
            if employees:
                self.view.print_employees(employees)
                rfid = input("Enter Employee RFID: ")
            else:
                self.view.error("No employees available!")
                return

            current_date = datetime.now().date()
            self.db.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (current_date,))
            date_id = self.db.cursor.fetchone()
            if not date_id:
                self.db.cursor.execute('''
                    INSERT INTO Date (date_complete, jour, mois, annee, jour_semaine, est_jour_ferie, description_jour)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (current_date, current_date.day, current_date.month, current_date.year, current_date.strftime("%A"), 0, ""))
                self.db.conn.commit()
                self.db.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (current_date,))
                date_id = self.db.cursor.fetchone()

            self.db.cursor.execute('''
                INSERT INTO Alerte (type_alerte, description, date_alerte, status, r fid, date_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (type_alerte, description, status, rfid, date_id[0]))
            self.db.conn.commit()
            self.view.success("Alert added successfully!")
        except Exception as e:
            self.view.error(f"Error adding alert: {str(e)}")
        input("Press Enter to continue...")

    def view_alerts(self):
        try:
            self.db.cursor.execute('''
                SELECT a.*, e.nom, e.prenom, d.date_complete
                FROM Alerte a
                LEFT JOIN Employe e ON a.rfid = e.rfid
                LEFT JOIN Date d ON a.date_id = d.date_id
            ''')
            alerts = self.db.cursor.fetchall()
            if alerts:
                self.view.print_alerts(alerts)
            else:
                self.view.error("No alerts found.")
        except Exception as e:
            self.view.error(f"Error viewing alerts: {str(e)}")
        input("Press Enter to continue...")

    def update_alert(self):
        try:
            self.view.view_alerts()
            alerte_id = int(input("Enter Alert ID to update: "))
            self.db.cursor.execute("SELECT * FROM Alerte WHERE alerte_id=?", (alerte_id,))
            alert = self.db.cursor.fetchone()
            if not alert:
                self.view.error("Alert not found!")
                return

            new_status = input(f"Enter new Status (current: {alert.status}): ") or alert.status
            new_desc = input(f"Enter new Description (current: {alert.description}): ") or alert.description

            self.db.cursor.execute('''
                UPDATE Alerte
                SET status=?, description=?
                WHERE alerte_id=?
            ''', (new_status, new_desc, alerte_id))
            self.db.conn.commit()
            self.view.success("Alert updated successfully!")
        except Exception as e:
            self.view.error(f"Error updating alert: {str(e)}")
        input("Press Enter to continue...")

    def delete_alert(self):
        try:
            self.view.view_alerts()
            alerte_id = int(input("Enter Alert ID to delete: "))
            self.db.cursor.execute("DELETE FROM Alerte WHERE alerte_id=?", (alerte_id,))
            self.db.conn.commit()
            self.view.success("Alert deleted successfully!")
        except Exception as e:
            self.view.error(f"Error deleting alert: {str(e)}")
        input("Press Enter to continue...")

    def alert_menu(self):
        while True:
            print("\n=== Alert Management ===")
            print("1. Add Alert")
            print("2. View All Alerts")
            print("3. Update Alert")
            print("4. Delete Alert")
            print("0. Back to Main Menu")
            choice = input("Enter choice: ")

            if choice == "1":
                self.add_alert()
            elif choice == "2":
                self.view_alerts()
            elif choice == "3":
                self.update_alert()
            elif choice == "4":
                self.delete_alert()
            elif choice == "0":
                break
            else:
                self.view.error("Invalid choice!")