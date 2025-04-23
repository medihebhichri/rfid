from datetime import datetime

from models.database_manager import DatabaseManager
from models.employee import Employee
from view.employee_view import EmployeeView

class EmployeeController:
    def __init__(self, db_manager):
        self.db = db_manager

    def clear_screen(self):
        import os
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_employee_menu(self):
        print("\n=== Employee Management ===")
        print("1. Add Employee")
        print("2. View All Employees")
        print("3. Search Employee")
        print("4. Update Employee")
        print("5. Delete Employee")
        print("0. Back to Main Menu")

    def employee_menu(self):
        while True:
            self.clear_screen()
            self.print_employee_menu()
            choice = input("Enter choice: ")

            if choice == "1":
                self.add_employee()
            elif choice == "2":
                self.view_all_employees()
            elif choice == "3":
                self.search_employee()
            elif choice == "4":
                self.update_employee()
            elif choice == "5":
                self.delete_employee()
            elif choice == "0":
                break
            else:
                input("\nInvalid choice. Press Enter to continue...")

    def add_employee(self):
        print("\n=== Add New Employee ===")
        try:
            rfid = input("Enter RFID: ")
            nom = input("Enter Last Name: ")
            prenom = input("Enter First Name: ")
            date_naissance = input("Enter Birth Date (YYYY-MM-DD): ")
            date_embauche = input("Enter Hire Date (YYYY-MM-DD): ")
            email = input("Enter Email: ")
            telephone = input("Enter Phone: ")
            adresse = input("Enter Address: ")

            # Convert date strings to datetime objects
            date_naissance = datetime.strptime(date_naissance, "%Y-%m-%d").date()
            date_embauche = datetime.strptime(date_embauche, "%Y-%m-%d").date()

            # Check if RFID already exists
            self.db.cursor.execute("SELECT rfid FROM Employe WHERE rfid = ?", (rfid,))
            existing_rfid = self.db.cursor.fetchone()
            if existing_rfid:
                print(f"\nError: RFID {rfid} already exists. Please enter a unique RFID.")
                input("\nPress Enter to continue...")
                return

            self.db.cursor.execute("SELECT equipe_id, nom_equipe FROM Equipe")
            teams = self.db.cursor.fetchall()
            print("\nAvailable Teams:")
            for team in teams:
                print(f"{team.equipe_id}: {team.nom_equipe}")
            equipe_id = int(input("Enter Team ID: "))

            self.db.cursor.execute("SELECT poste_id, titre_poste FROM Poste_Competence")
            positions = self.db.cursor.fetchall()
            print("\nAvailable Positions:")
            for pos in positions:
                print(f"{pos.poste_id}: {pos.titre_poste}")
            poste_id = int(input("Enter Position ID: "))

            # Insert birth date into Date table if it doesn't exist
            self.db.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (date_naissance,))
            date_naissance_id = self.db.cursor.fetchone()
            if not date_naissance_id:
                self.db.cursor.execute('''
                    INSERT INTO Date (date_complete, jour, mois, annee, jour_semaine, est_jour_ferie, description_jour)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (date_naissance, date_naissance.day, date_naissance.month, date_naissance.year,
                      date_naissance.strftime("%A"), 0, ""))
                self.db.conn.commit()
                self.db.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (date_naissance,))
                date_naissance_id = self.db.cursor.fetchone()

            # Insert hire date into Date table if it doesn't exist
            self.db.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (date_embauche,))
            date_embauche_id = self.db.cursor.fetchone()
            if not date_embauche_id:
                self.db.cursor.execute('''
                    INSERT INTO Date (date_complete, jour, mois, annee, jour_semaine, est_jour_ferie, description_jour)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (date_embauche, date_embauche.day, date_embauche.month, date_embauche.year, date_embauche.strftime("%A"),
                      0, ""))
                self.db.conn.commit()
                self.db.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (date_embauche,))
                date_embauche_id = self.db.cursor.fetchone()

            self.db.cursor.execute('''
                INSERT INTO Employe (rfid, nom, prenom, date_naissance, date_embauche, email, telephone, adresse, equipe_id, poste_id, date_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (rfid, nom, prenom, date_naissance, date_embauche, email, telephone, adresse, equipe_id, poste_id,
                  date_naissance_id[0]))
            self.db.conn.commit()
            print("\nEmployee added successfully!")
        except Exception as e:
            print(f"\nError adding employee: {str(e)}")
        input("\nPress Enter to continue...")

    def view_all_employees(self):
        print("\n=== All Employees ===")
        try:
            self.db.cursor.execute('''
                SELECT e.*, eq.nom_equipe, pc.titre_poste, d.date_complete
                FROM Employe e
                LEFT JOIN Equipe eq ON e.equipe_id = eq.equipe_id
                LEFT JOIN Poste_Competence pc ON e.poste_id = pc.poste_id
                LEFT JOIN Date d ON e.date_id = d.date_id
            ''')
            employees = self.db.cursor.fetchall()
            if employees:
                for emp in employees:
                    print(f"\nRFID: {emp.rfid}")
                    print(f"Name: {emp.nom} {emp.prenom}")
                    print(f"Email: {emp.email}")
                    print(f"Phone: {emp.telephone}")
                    print(f"Team: {emp.nom_equipe}")
                    print(f"Position: {emp.titre_poste}")
                    print(f"Date of Birth: {emp.date_naissance}")
                    print(f"Date of Hire: {emp.date_embauche}")
                    print("-" * 30)
            else:
                print("\nNo employees found.")
        except Exception as e:
            print(f"\nError viewing employees: {str(e)}")
        input("\nPress Enter to continue...")

    def search_employee(self):
        print("\n=== Search Employee ===")
        print("1. Search by RFID")
        print("2. Search by Name")
        print("3. Search by Team")
        choice = input("Enter choice: ")

        try:
            if choice == "1":
                rfid = input("Enter RFID: ")
                query = '''
                    SELECT e.*, eq.nom_equipe, pc.titre_poste, d.date_complete
                    FROM Employe e
                    LEFT JOIN Equipe eq ON e.equipe_id = eq.equipe_id
                    LEFT JOIN Poste_Competence pc ON e.poste_id = pc.poste_id
                    LEFT JOIN Date d ON e.date_id = d.date_id
                    WHERE e.rfid = ?
                '''
                params = (rfid,)
            elif choice == "2":
                name = input("Enter Name: ")
                query = '''
                    SELECT e.*, eq.nom_equipe, pc.titre_poste, d.date_complete
                    FROM Employe e
                    LEFT JOIN Equipe eq ON e.equipe_id = eq.equipe_id
                    LEFT JOIN Poste_Competence pc ON e.poste_id = pc.poste_id
                    LEFT JOIN Date d ON e.date_id = d.date_id
                    WHERE e.nom LIKE ? OR e.prenom LIKE ?
                '''
                params = (f'%{name}%', f'%{name}%')
            elif choice == "3":
                team = input("Enter Team Name: ")
                query = '''
                    SELECT e.*, eq.nom_equipe, pc.titre_poste, d.date_complete
                    FROM Employe e
                    LEFT JOIN Equipe eq ON e.equipe_id = eq.equipe_id
                    LEFT JOIN Poste_Competence pc ON e.poste_id = pc.poste_id
                    LEFT JOIN Date d ON e.date_id = d.date_id
                    WHERE eq.nom_equipe LIKE ?
                '''
                params = (f'%{team}%',)
            else:
                print("Invalid choice!")
                return

            self.db.cursor.execute(query, params)
            employees = self.db.cursor.fetchall()

            if employees:
                for emp in employees:
                    print("\nEmployee Details:")
                    print(f"RFID: {emp.rfid}")
                    print(f"Name: {emp.nom} {emp.prenom}")
                    print(f"Email: {emp.email}")
                    print(f"Phone: {emp.telephone}")
                    print(f"Team: {emp.nom_equipe}")
                    print(f"Position: {emp.titre_poste}")
                    print(f"Date of Birth: {emp.date_naissance}")
                    print(f"Date of Hire: {emp.date_embauche}")
                    print("-" * 30)
            else:
                print("\nNo employees found.")
        except Exception as e:
            print(f"\nError searching employee: {str(e)}")
        input("\nPress Enter to continue...")

    def update_employee(self):
        print("\n=== Update Employee ===")
        try:
            rfid = input("Enter RFID of the employee to update: ")
            self.db.cursor.execute("SELECT * FROM Employe WHERE rfid = ?", (rfid,))
            emp = self.db.cursor.fetchone()
            if not emp:
                print("Employee not found!")
                return

            print("Leave blank to keep current value.")
            nom = input(f"Enter new Last Name [{emp.nom}]: ") or emp.nom
            prenom = input(f"Enter new First Name [{emp.prenom}]: ") or emp.prenom
            date_naissance = input(f"Enter new Birth Date (YYYY-MM-DD) [{emp.date_naissance}]: ") or emp.date_naissance
            date_embauche = input(f"Enter new Hire Date (YYYY-MM-DD) [{emp.date_embauche}]: ") or emp.date_embauche
            email = input(f"Enter new Email [{emp.email}]: ") or emp.email
            telephone = input(f"Enter new Phone [{emp.telephone}]: ") or emp.telephone
            adresse = input(f"Enter new Address [{emp.adresse}]: ") or emp.adresse

            # Convert date strings to datetime objects if provided
            if date_naissance:
                date_naissance = datetime.strptime(date_naissance, "%Y-%m-%d").date()
            else:
                date_naissance = emp.date_naissance

            if date_embauche:
                date_embauche = datetime.strptime(date_embauche, "%Y-%m-%d").date()
            else:
                date_embauche = emp.date_embauche

            # Insert birth date into Date table if it doesn't exist
            self.db.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (date_naissance,))
            date_naissance_id = self.db.cursor.fetchone()
            if not date_naissance_id:
                self.db.cursor.execute('''
                    INSERT INTO Date (date_complete, jour, mois, annee, jour_semaine, est_jour_ferie, description_jour)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (date_naissance, date_naissance.day, date_naissance.month, date_naissance.year,
                      date_naissance.strftime("%A"), 0, ""))
                self.db.conn.commit()
                self.db.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (date_naissance,))
                date_naissance_id = self.db.cursor.fetchone()

            # Insert hire date into Date table if it doesn't exist
            self.db.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (date_embauche,))
            date_embauche_id = self.db.cursor.fetchone()
            if not date_embauche_id:
                self.db.cursor.execute('''
                    INSERT INTO Date (date_complete, jour, mois, annee, jour_semaine, est_jour_ferie, description_jour)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (date_embauche, date_embauche.day, date_embauche.month, date_embauche.year, date_embauche.strftime("%A"),
                      0, ""))
                self.db.conn.commit()
                self.db.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (date_embauche,))
                date_embauche_id = self.db.cursor.fetchone()

            self.db.cursor.execute('''
                UPDATE Employe
                SET nom = ?, prenom = ?, date_naissance = ?, date_embauche = ?, email = ?, telephone = ?, adresse = ?, equipe_id = ?, poste_id = ?, date_id = ?
                WHERE rfid = ?
            ''', (nom, prenom, date_naissance, date_embauche, email, telephone, adresse, emp.equipe_id, emp.poste_id, date_embauche_id[0], rfid))
            self.db.conn.commit()
            print("\nEmployee updated successfully!")
        except Exception as e:
            print(f"\nError updating employee: {str(e)}")
        input("\nPress Enter to continue...")

    def delete_employee(self):
        print("\n=== Delete Employee ===")
        try:
            rfid = input("Enter RFID of the employee to delete: ")
            self.db.cursor.execute("SELECT * FROM Employe WHERE rfid = ?", (rfid,))
            emp = self.db.cursor.fetchone()
            if not emp:
                print("Employee not found!")
                return

            self.db.cursor.execute("DELETE FROM Employe WHERE rfid = ?", (rfid,))
            self.db.conn.commit()
            print("\nEmployee deleted successfully!")
        except Exception as e:
            print(f"\nError deleting employee: {str(e)}")
        input("\nPress Enter to continue...")