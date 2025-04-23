import pyodbc
from datetime import datetime
import os
from typing import Optional

CONNECTION_STRING = (
    'DRIVER={ODBC Driver 18 for SQL Server};'
    'SERVER=IHEB;'
    'DATABASE=rfid;'
    'Trusted_Connection=Yes;'
    'Encrypt=no;'
)

class DatabaseManager:
    def __init__(self):
        self.conn = pyodbc.connect(CONNECTION_STRING)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.populate_date_table()

    def insert_date(self, date):
        self.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (date,))
        if not self.cursor.fetchone():
            jour = date.day
            mois = date.month
            annee = date.year
            jour_semaine = date.strftime("%A")
            est_jour_ferie = 0
            description_jour = ""
            self.cursor.execute('''
                INSERT INTO Date (date_complete, jour, mois, annee, jour_semaine, est_jour_ferie, description_jour)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (date, jour, mois, annee, jour_semaine, est_jour_ferie, description_jour))
            self.conn.commit()
    def create_tables(self):
        self.cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='Date')
            CREATE TABLE Date (
                date_id INT PRIMARY KEY IDENTITY(1,1),
                date_complete DATE,
                jour INT,
                mois INT,
                annee INT,
                jour_semaine VARCHAR(20),
                est_jour_ferie BIT,
                description_jour VARCHAR(255)
            )
        ''')



        self.cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='Equipe')
            CREATE TABLE Equipe (
                equipe_id INT PRIMARY KEY IDENTITY(1,1),
                nom_equipe VARCHAR(100),
                description VARCHAR(255),
                chef_equipe VARCHAR(100)
            )
        ''')

        self.cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='Poste_Competence')
            CREATE TABLE Poste_Competence (
                poste_id INT PRIMARY KEY IDENTITY(1,1),
                titre_poste VARCHAR(100),
                niveau_competence VARCHAR(50),
                description VARCHAR(255),
                requirements VARCHAR(255)
            )
        ''')



        self.cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='Employe')
            CREATE TABLE Employe (
                rfid VARCHAR(50) PRIMARY KEY,
                nom VARCHAR(100),
                prenom VARCHAR(100),
                date_naissance DATE,
                date_embauche DATE,
                email VARCHAR(100),
                telephone VARCHAR(20),
                adresse VARCHAR(255),
                equipe_id INT FOREIGN KEY REFERENCES Equipe(equipe_id),
                poste_id INT FOREIGN KEY REFERENCES Poste_Competence(poste_id),
                date_id INT FOREIGN KEY REFERENCES Date(date_id)
            )
        ''')




        self.cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='Alerte')
            CREATE TABLE Alerte (
                alerte_id INT PRIMARY KEY IDENTITY(1,1),
                type_alerte VARCHAR(50),
                description VARCHAR(255),
                date_alerte DATETIME,
                status VARCHAR(20),
                rfid VARCHAR(50) FOREIGN KEY REFERENCES Employe(rfid),
                date_id INT FOREIGN KEY REFERENCES Date(date_id)
            )
        ''')




        self.cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='Evenement')
            CREATE TABLE Evenement (
                evenement_id INT PRIMARY KEY IDENTITY(1,1),
                type_evenement VARCHAR(50),
                date_evenement DATETIME,
                description VARCHAR(255),
                rfid VARCHAR(50) FOREIGN KEY REFERENCES Employe(rfid),
                equipe_id INT FOREIGN KEY REFERENCES Equipe(equipe_id),
                poste_id INT FOREIGN KEY REFERENCES Poste_Competence(poste_id),
                alerte_id INT FOREIGN KEY REFERENCES Alerte(alerte_id),
                date_id INT FOREIGN KEY REFERENCES Date(date_id)
            )
        ''')

        # Ensure the date_id column exists in the Evenement table
        self.cursor.execute('''
            IF COL_LENGTH('Evenement', 'date_id') IS NULL
            ALTER TABLE Evenement ADD date_id INT FOREIGN KEY REFERENCES Date(date_id)
        ''')

        self.conn.commit()

    def populate_date_table(self):
        dates = set()

        self.cursor.execute("SELECT date_naissance, date_embauche FROM Employe")
        for row in self.cursor.fetchall():
            dates.add(row.date_naissance)
            dates.add(row.date_embauche)

        self.cursor.execute("SELECT date_alerte FROM Alerte")
        for row in self.cursor.fetchall():
            dates.add(row.date_alerte.date())

        self.cursor.execute("SELECT date_evenement FROM Evenement")
        for row in self.cursor.fetchall():
            dates.add(row.date_evenement.date())

        for date in dates:
            if date:
                date_complete = date
                jour = date.day
                mois = date.month
                annee = date.year
                jour_semaine = date.strftime("%A")
                est_jour_ferie = 0
                description_jour = ""

                self.cursor.execute('''
                    IF NOT EXISTS (SELECT * FROM Date WHERE date_complete = ?)
                    INSERT INTO Date (date_complete, jour, mois, annee, jour_semaine, est_jour_ferie, description_jour)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (date_complete, date_complete, jour, mois, annee, jour_semaine, est_jour_ferie, description_jour))

        self.conn.commit()




class EmployeeSystem:
    def __init__(self):
        self.db = DatabaseManager()

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_main_menu(self):
        print("\n=== Employee Management System ===")
        print("1. Employee Management")
        print("2. Team Management")
        print("3. Position Management")
        print("4. Event Management")
        print("5. Alert Management")
        print("0. Exit")
        print("===============================")

    def employee_menu(self):
        while True:
            print("\n=== Employee Management ===")
            print("1. Add Employee")
            print("2. View All Employees")
            print("3. Search Employee")
            print("4. Update Employee")
            print("5. Delete Employee")
            print("0. Back to Main Menu")

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
            date_naissance = input(f"Enter new Birth Date (YYYY-MM-DD) [{emp.date_naissance}]: ")
            date_embauche = input(f"Enter new Hire Date (YYYY-MM-DD) [{emp.date_embauche}]: ")
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
                ''', (
                date_embauche, date_embauche.day, date_embauche.month, date_embauche.year, date_embauche.strftime("%A"),
                0, ""))
                self.db.conn.commit()
                self.db.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (date_embauche,))
                date_embauche_id = self.db.cursor.fetchone()

            self.db.cursor.execute('''
                UPDATE Employe
                SET nom = ?, prenom = ?, date_naissance = ?, date_embauche = ?, email = ?, telephone = ?, adresse = ?, equipe_id = ?, poste_id = ?, date_id = ?
                WHERE rfid = ?
            ''', (nom, prenom, date_naissance, date_embauche, email, telephone, adresse, emp.equipe_id, emp.poste_id,
                  date_embauche_id[0], rfid))
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

    def team_menu(self):
        while True:
            print("\n=== Team Management ===")
            print("1. Add Team")
            print("2. View All Teams")
            print("3. Update Team")
            print("4. Delete Team")
            print("0. Back to Main Menu")

            choice = input("Enter choice: ")

            if choice == "1":
                self.add_team()
            elif choice == "2":
                self.view_teams()
            elif choice == "3":
                self.update_team()
            elif choice == "4":
                self.delete_team()
            elif choice == "0":
                break

    def add_team(self):
        print("\n=== Add New Team ===")
        try:
            nom_equipe = input("Enter Team Name: ")
            description = input("Enter Description: ")
            chef_equipe = input("Enter Team Leader: ")

            self.db.cursor.execute('''
                INSERT INTO Equipe (nom_equipe, description, chef_equipe)
                VALUES (?, ?, ?)
            ''', (nom_equipe, description, chef_equipe))
            self.db.conn.commit()
            print("\nTeam added successfully!")
        except Exception as e:
            print(f"\nError adding team: {str(e)}")
        input("\nPress Enter to continue...")

    def view_teams(self):
        print("\n=== All Teams ===")
        try:
            self.db.cursor.execute("SELECT * FROM Equipe")
            teams = self.db.cursor.fetchall()
            if teams:
                for team in teams:
                    print(f"\nID: {team.equipe_id}")
                    print(f"Name: {team.nom_equipe}")
                    print(f"Leader: {team.chef_equipe}")
                    print(f"Description: {team.description}")
                    print("-" * 30)
            else:
                print("\nNo teams found.")
        except Exception as e:
            print(f"\nError viewing teams: {str(e)}")
        input("\nPress Enter to continue...")

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
                print("Invalid choice!")

    def add_position(self):
        print("\n=== Add New Position ===")
        try:
            titre = input("Enter Position Title: ")
            niveau = input("Enter Competence Level: ")
            desc = input("Enter Description: ")
            reqs = input("Enter Requirements: ")

            self.db.cursor.execute('''
                    INSERT INTO Poste_Competence (titre_poste, niveau_competence, description, requirements)
                    VALUES (?, ?, ?, ?)
                ''', (titre, niveau, desc, reqs))
            self.db.conn.commit()
            print("\nPosition added successfully!")
        except Exception as e:
            print(f"\nError adding position: {str(e)}")
        input("\nPress Enter to continue...")

    def view_positions(self):
        print("\n=== All Positions ===")
        try:
            self.db.cursor.execute("SELECT * FROM Poste_Competence")
            positions = self.db.cursor.fetchall()
            if positions:
                for pos in positions:
                    print(f"\nID: {pos.poste_id}")
                    print(f"Title: {pos.titre_poste}")
                    print(f"Level: {pos.niveau_competence}")
                    print(f"Description: {pos.description}")
                    print(f"Requirements: {pos.requirements}")
                    print("-" * 30)
            else:
                print("\nNo positions found.")
        except Exception as e:
            print(f"\nError viewing positions: {str(e)}")
        input("\nPress Enter to continue...")



    def update_position(self):
        print("\n=== Update Position ===")
        self.view_positions()
        try:
            poste_id = int(input("Enter Position ID to update: "))
            self.db.cursor.execute("SELECT * FROM Poste_Competence WHERE poste_id=?", (poste_id,))
            pos = self.db.cursor.fetchone()
            if not pos:
                print("Position not found!")
                return

            print("Leave blank to keep current value.")
            titre = input(f"Enter new Title [{pos.titre_poste}]: ") or pos.titre_poste
            niveau = input(f"Enter new Level [{pos.niveau_competence}]: ") or pos.niveau_competence
            desc = input(f"Enter new Description [{pos.description}]: ") or pos.description
            reqs = input(f"Enter new Requirements [{pos.requirements}]: ") or pos.requirements

            self.db.cursor.execute('''
                    UPDATE Poste_Competence 
                    SET titre_poste=?, niveau_competence=?, description=?, requirements=?
                    WHERE poste_id=?
                ''', (titre, niveau, desc, reqs, poste_id))
            self.db.conn.commit()
            print("\nPosition updated successfully!")
        except Exception as e:
            print(f"\nError updating position: {str(e)}")
        input("\nPress Enter to continue...")



    def delete_position(self):
        print("\n=== Delete Position ===")
        self.view_positions()
        try:
            poste_id = int(input("Enter Position ID to delete: "))
            self.db.cursor.execute("SELECT COUNT(*) FROM Employe WHERE poste_id=?", (poste_id,))
            count = self.db.cursor.fetchone()[0]
            if count > 0:
                print("Cannot delete position. Employees are assigned to it.")
                return

            self.db.cursor.execute("DELETE FROM Poste_Competence WHERE poste_id=?", (poste_id,))
            self.db.conn.commit()
            print("\nPosition deleted successfully!")
        except Exception as e:
            print(f"\nError deleting position: {str(e)}")
        input("\nPress Enter to continue...")



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
                print("Invalid choice!")

    def add_event(self):
        print("\n=== Add New Event ===")
        try:
            type_event = input("Enter Event Type: ")
            date_event = input("Enter Event Date (YYYY-MM-DD HH:MM:SS): ")
            description = input("Enter Description: ")

            self.db.cursor.execute("SELECT rfid, nom, prenom FROM Employe")
            employees = self.db.cursor.fetchall()
            rfid = None
            if employees:
                print("\nAvailable Employees:")
                for emp in employees:
                    print(f"RFID: {emp.rfid}, Name: {emp.nom} {emp.prenom}")
                rfid_input = input("Enter RFID (leave blank if none): ")
                rfid = rfid_input if rfid_input.strip() else None

            self.db.cursor.execute("SELECT equipe_id, nom_equipe FROM Equipe")
            teams = self.db.cursor.fetchall()
            equipe_id = None
            if teams:
                print("\nAvailable Teams:")
                for team in teams:
                    print(f"ID: {team.equipe_id}, Name: {team.nom_equipe}")
                equipe_input = input("Enter Team ID (leave blank if none): ")
                equipe_id = int(equipe_input) if equipe_input.strip() else None

            self.db.cursor.execute("SELECT poste_id, titre_poste FROM Poste_Competence")
            positions = self.db.cursor.fetchall()
            poste_id = None
            if positions:
                print("\nAvailable Positions:")
                for pos in positions:
                    print(f"ID: {pos.poste_id}, Title: {pos.titre_poste}")
                poste_input = input("Enter Position ID (leave blank if none): ")
                poste_id = int(poste_input) if poste_input.strip() else None

            self.db.cursor.execute("SELECT alerte_id, type_alerte FROM Alerte")
            alerts = self.db.cursor.fetchall()
            alerte_id = None
            if alerts:
                print("\nAvailable Alerts:")
                for alert in alerts:
                    print(f"ID: {alert.alerte_id}, Type: {alert.type_alerte}")
                alerte_input = input("Enter Alert ID (leave blank if none): ")
                alerte_id = int(alerte_input) if alerte_input.strip() else None

            date_event_date = datetime.strptime(date_event, "%Y-%m-%d %H:%M:%S").date()
            self.db.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (date_event_date,))
            date_id = self.db.cursor.fetchone()
            if not date_id:
                self.db.cursor.execute('''
                    INSERT INTO Date (date_complete, jour, mois, annee, jour_semaine, est_jour_ferie, description_jour)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (date_event_date, date_event_date.day, date_event_date.month, date_event_date.year, date_event_date.strftime("%A"), 0, ""))
                self.db.conn.commit()
                self.db.cursor.execute("SELECT date_id FROM Date WHERE date_complete = ?", (date_event_date,))
                date_id = self.db.cursor.fetchone()

            self.db.cursor.execute('''
                    INSERT INTO Evenement 
                    (type_evenement, date_evenement, description, rfid, equipe_id, poste_id, alerte_id, date_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (type_event, date_event, description, rfid, equipe_id, poste_id, alerte_id, date_id[0]))
            self.db.conn.commit()
            print("\nEvent added successfully!")
        except Exception as e:
            print(f"\nError adding event: {str(e)}")
        input("\nPress Enter to continue...")




    def view_events(self):
        print("\n=== All Events ===")
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
                for event in events:
                    print(f"\nEvent ID: {event.evenement_id}")
                    print(f"Type: {event.type_evenement}")
                    print(f"Date: {event.date_evenement}")
                    print(f"Description: {event.description}")
                    print(f"Employee: {event.nom} {event.prenom}" if event.nom else "No employee linked")
                    print(f"Team: {event.nom_equipe}" if event.nom_equipe else "No team linked")
                    print(f"Position: {event.titre_poste}" if event.titre_poste else "No position linked")
                    print(f"Alert: {event.type_alerte}" if event.type_alerte else "No alert linked")
                    print(f"Date: {event.date_complete}")
                    print("-" * 30)
            else:
                print("\nNo events found.")
        except Exception as e:
            print(f"\nError viewing events: {str(e)}")
        input("\nPress Enter to continue...")




    def update_event(self):
        print("\n=== Update Event ===")
        self.view_events()
        try:
            event_id = int(input("Enter Event ID to update: "))
            self.db.cursor.execute("SELECT * FROM Evenement WHERE evenement_id=?", (event_id,))
            event = self.db.cursor.fetchone()
            if not event:
                print("Event not found!")
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
                ''', (new_type, new_date, new_desc, date_id[0], event_id))
            self.db.conn.commit()
            print("\nEvent updated successfully!")
        except Exception as e:
            print(f"\nError updating event: {str(e)}")
        input("\nPress Enter to continue...")

    def delete_event(self):
        print("\n=== Delete Event ===")
        self.view_events()
        try:
            event_id = int(input("Enter Event ID to delete: "))
            self.db.cursor.execute("DELETE FROM Evenement WHERE evenement_id=?", (event_id,))
            self.db.conn.commit()
            print("\nEvent deleted successfully!")
        except Exception as e:
            print(f"\nError deleting event: {str(e)}")
        input("\nPress Enter to continue...")

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
                print("Invalid choice!")





    def add_alert(self):
        print("\n=== Add New Alert ===")
        try:
            type_alerte = input("Enter Alert Type: ")
            description = input("Enter Description: ")
            status = input("Enter Status (e.g., Open, Closed): ")

            self.db.cursor.execute("SELECT rfid, nom, prenom FROM Employe")
            employees = self.db.cursor.fetchall()
            if employees:
                print("\nAvailable Employees:")
                for emp in employees:
                    print(f"RFID: {emp.rfid}, Name: {emp.nom} {emp.prenom}")
                rfid = input("Enter Employee RFID: ")
            else:
                print("No employees available!")
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
                    INSERT INTO Alerte (type_alerte, description, date_alerte, status, rfid, date_id)
                    VALUES (?, ?, GETDATE(), ?, ?, ?)
                ''', (type_alerte, description, status, rfid, date_id[0]))
            self.db.conn.commit()
            print("\nAlert added successfully!")
        except Exception as e:
            print(f"\nError adding alert: {str(e)}")
        input("\nPress Enter to continue...")

    def view_alerts(self):
        print("\n=== All Alerts ===")
        try:
            self.db.cursor.execute('''
                    SELECT a.*, e.nom, e.prenom, d.date_complete
                    FROM Alerte a
                    LEFT JOIN Employe e ON a.rfid = e.rfid
                    LEFT JOIN Date d ON a.date_id = d.date_id
                ''')
            alerts = self.db.cursor.fetchall()
            if alerts:
                for alert in alerts:
                    print(f"\nID: {alert.alerte_id}")
                    print(f"Type: {alert.type_alerte}")
                    print(f"Description: {alert.description}")
                    print(f"Date: {alert.date_alerte}")
                    print(f"Status: {alert.status}")
                    print(f"Employee: {alert.nom} {alert.prenom}" if alert.nom else "No employee linked")
                    print(f"Date: {alert.date_complete}")
                    print("-" * 30)
            else:
                print("\nNo alerts found.")
        except Exception as e:
            print(f"\nError viewing alerts: {str(e)}")
        input("\nPress Enter to continue...")

    def update_alert(self):
        print("\n=== Update Alert ===")
        self.view_alerts()
        try:
            alerte_id = int(input("Enter Alert ID to update: "))
            self.db.cursor.execute("SELECT * FROM Alerte WHERE alerte_id=?", (alerte_id,))
            alert = self.db.cursor.fetchone()
            if not alert:
                print("Alert not found!")
                return

            new_status = input(f"Enter new Status (current: {alert.status}): ") or alert.status
            new_desc = input(f"Enter new Description (current: {alert.description}): ") or alert.description

            self.db.cursor.execute('''
                    UPDATE Alerte 
                    SET status=?, description=?
                    WHERE alerte_id=?
                ''', (new_status, new_desc, alerte_id))
            self.db.conn.commit()
            print("\nAlert updated successfully!")
        except Exception as e:
            print(f"\nError updating alert: {str(e)}")
        input("\nPress Enter to continue...")

    def delete_alert(self):
        print("\n=== Delete Alert ===")
        self.view_alerts()
        try:
            alerte_id = int(input("Enter Alert ID to delete: "))
            self.db.cursor.execute("DELETE FROM Alerte WHERE alerte_id=?", (alerte_id,))
            self.db.conn.commit()
            print("\nAlert deleted successfully!")
        except Exception as e:
            print(f"\nError deleting alert: {str(e)}")
        input("\nPress Enter to continue...")

    def run(self):
        while True:
            self.clear_screen()
            self.print_main_menu()
            choice = input("Enter your choice (0-5): ")

            if choice == "1":
                self.employee_menu()
            elif choice == "2":
                self.team_menu()
            elif choice == "3":
                self.position_menu()
            elif choice == "4":
                self.event_menu()
            elif choice == "5":
                self.alert_menu()
            elif choice == "0":
                print("\nThank you for using Employee Management System!")
                break
            else:
                input("\nInvalid choice. Press Enter to continue...")

if __name__ == "__main__":
    system = EmployeeSystem()
    system.run()

