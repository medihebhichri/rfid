import pyodbc
from datetime import datetime

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