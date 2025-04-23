import datetime

from models.database_manager import DatabaseManager
from models.event import Event
from view.EventView import EventView

class EventController:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.view = EventView()

    def add_event(self):
        try:
            type_evenement = input("Enter Event Type: ")
            date_evenement = input("Enter Event Date (YYYY-MM-DD HH:MM:SS): ")
            description = input("Enter Description: ")

            self.db.cursor.execute("SELECT rfid, nom, prenom FROM Employe")
            employees = self.db.cursor.fetchall()
            rfid = None
            if employees:
                self.view.print_employees(employees)
                rfid_input = input("Enter RFID (leave blank if none): ")
                rfid = rfid_input if rfid_input.strip() else None

            self.db.cursor.execute("SELECT equipe_id, nom_equipe FROM Equipe")
            teams = self.db.cursor.fetchall()
            equipe_id = None
            if teams:
                self.view.print_teams(teams)
                equipe_input = input("Enter Team ID (leave blank if none): ")
                equipe_id = int(equipe_input) if equipe_input.strip() else None

            self.db.cursor.execute("SELECT poste_id, titre_poste FROM Poste_Competence")
            positions = self.db.cursor.fetchall()
            poste_id = None
            if positions:
                self.view.print_positions(positions)
                poste_input = input("Enter Position ID (leave blank if none): ")
                poste_id = int(poste_input) if poste_input.strip() else None

            self.db.cursor.execute("SELECT alerte_id, type_alerte FROM Alerte")
            alerts = self.db.cursor.fetchall()
            alerte_id = None
            if alerts:
                self.view.print_alerts(alerts)
                alerte_input = input("Enter Alert ID (leave blank if none): ")
                alerte_id = int(alerte_input) if alerte_input.strip() else None

            date_evenement_date = datetime.strptime(date_evenement, "%Y-%m-%d %H:%M:%S").date()
            self.db.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (date_evenement_date,))
            date_id = self.db.cursor.fetchone()
            if not date_id:
                self.db.cursor.execute('''
                    INSERT INTO Date (date_complete, jour, mois, annee, jour_semaine, est_jour_ferie, description_jour)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (date_evenement_date, date_evenement_date.day, date_evenement_date.month, date_evenement_date.year, date_evenement_date.strftime("%A"), 0, ""))
                self.db.conn.commit()
                self.db.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (date_evenement_date,))
                date_id = self.db.cursor.fetchone()

            self.db.cursor.execute('''
                INSERT INTO Evenement (type_evenement, date_evenement, description, rfid, equipe_id, poste_id, alerte_id, date_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (type_evenement, date_evenement, description, rfid, equipe_id, poste_id, alerte_id, date_id[0]))
            self.db.conn.commit()
            self.view.success("Event added successfully!")
        except Exception as e:
            self.view.error(f"Error adding event: {str(e)}")
        input("Press Enter to continue...")

    def view_events(self):
        try:
            self.db.cursor.execute('''
                SELECT e.*, emp.nom, emp.prenom, eq.nom_equipe, pc.titre_poste, a.type_alerte, d.date_complete
                FROM Evenement e
                LEFT JOIN Employe emp ON e.rfid = emp.rfid
                LEFT JOIN Equipe eq ON e.equipe_id = eq.equipe_id
                LEFT JOIN Poste_Competence pc ON e.poste_id = pc.poste_id
                LEFT JOIN Alerte a ON e.alerte_id = a.alerte_id
                LEFT JOIN Date d ON e.date_id = d.date_id
            ''')
            events = self.db.cursor.fetchall()
            if events:
                self.view.print_events(events)
            else:
                self.view.error("No events found.")
        except Exception as e:
            self.view.error(f"Error viewing events: {str(e)}")
        input("Press Enter to continue...")

    def update_event(self):
        try:
            self.view.view_events()
            evenement_id = int(input("Enter Event ID to update: "))
            self.db.cursor.execute("SELECT * FROM Evenement WHERE evenement_id=?", (evenement_id,))
            event = self.db.cursor.fetchone()
            if not event:
                self.view.error("Event not found!")
                return

            new_type = input(f"Enter new Type [{event.type_evenement}]: ") or event.type_evenement
            new_date = input(f"Enter new Date (YYYY-MM-DD HH:MM:SS) [{event.date_evenement}]: ") or event.date_evenement
            new_desc = input(f"Enter new Description [{event.description}]: ") or event.description

            new_date_date = datetime.strptime(new_date, "%Y-%m-%d %H:%M:%S").date()
            self.db.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (new_date_date,))
            date_id = self.db.cursor.fetchone()
            if not date_id:
                self.db.cursor.execute('''
                    INSERT INTO Date (date_complete, jour, mois, annee, jour_semaine, est_jour_ferie, description_jour)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (new_date_date, new_date_date.day, new_date_date.month, new_date_date.year, new_date_date.strftime("%A"), 0, ""))
                self.db.conn.commit()
                self.db.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (new_date_date,))
                date_id = self.db.cursor.fetchone()

            self.db.cursor.execute('''
                UPDATE Evenement
                SET type_evenement=?, date_evenement=?, description=?, date_id=?
                WHERE evenement_id=?
            ''', (new_type, new_date, new_desc, date_id[0], evenement_id))
            self.db.conn.commit()
            self.view.success("Event updated successfully!")
        except Exception as e:
            self.view.error(f"Error updating event: {str(e)}")
        input("Press Enter to continue...")

    def delete_event(self):
        try:
            self.view.view_events()
            evenement_id = int(input("Enter Event ID to delete: "))
            self.db.cursor.execute("DELETE FROM Evenement WHERE evenement_id=?", (evenement_id,))
            self.db.conn.commit()
            self.view.success("Event deleted successfully!")
        except Exception as e:
            self.view.error(f"Error deleting event: {str(e)}")
        input("Press Enter to continue...")

    def event_menu(self):
        while True:
            print("\n=== Event Management ===")
            print("1. Add Event")
            print("2. View All Events")
            print("3. Update Event")
            print("4. Delete Event")
            print("0. Back to Main Menu")
            choice = input("Enter choice: ")

            if choice == "1":
                self.add_event()
            elif choice == "2":
                self.view_events()
            elif choice == "3":
                self.update_event()
            elif choice == "4":
                self.delete_event()
            elif choice == "0":
                break
            else:
                self.view.error("Invalid choice!")