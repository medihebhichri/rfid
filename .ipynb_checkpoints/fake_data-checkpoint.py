import pyodbc
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker(['fr_FR'])

CONNECTION_STRING = (
    'DRIVER={ODBC Driver 18 for SQL Server};'
    'SERVER=IHEB;'
    'DATABASE=rfid;'
    'Trusted_Connection=Yes;'
    'Encrypt=no;'
)


def generate_fake_data():
    conn = pyodbc.connect(CONNECTION_STRING)
    cursor = conn.cursor()


    check_and_update_schema(cursor, conn)

    print("Clearing all existing data...")
    clear_all_tables(cursor, conn)

    print("Generating dates...")
    date_ids = generate_dates(cursor)

    print("Generating teams...")
    team_ids = generate_teams(cursor)


    print("Generating positions...")
    position_ids = generate_positions(cursor)


    print("Generating employees...")
    employee_rfids = generate_employees(cursor, team_ids, position_ids, date_ids)

    print("Generating alerts...")
    alert_ids = generate_alerts(cursor, employee_rfids, date_ids)


    print("Generating events...")
    generate_events(cursor, employee_rfids, team_ids, position_ids, alert_ids, date_ids)

    conn.commit()
    print("Data generation complete!")

    print_summary(cursor)

    cursor.close()
    conn.close()


def check_and_update_schema(cursor, conn):
    print("Checking database schema...")

    cursor.execute("""
    SELECT COLUMN_NAME 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'Alerte' AND COLUMN_NAME = 'date_id'
    """)

    if cursor.fetchone() is None:
        print("Adding date_id column to Alerte table...")
        cursor.execute("""
        ALTER TABLE Alerte 
        ADD date_id INT FOREIGN KEY REFERENCES Date(date_id)
        """)
        conn.commit()

    cursor.execute("""
    SELECT COLUMN_NAME 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'Evenement' AND COLUMN_NAME = 'date_id'
    """)

    if cursor.fetchone() is None:
        print("Adding date_id column to Evenement table...")
        cursor.execute("""
        ALTER TABLE Evenement 
        ADD date_id INT FOREIGN KEY REFERENCES Date(date_id)
        """)
        conn.commit()


def clear_all_tables(cursor, conn):
    tables = ["Evenement", "Alerte", "Employe", "Poste_Competence", "Equipe", "Date"]

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"Found {count} records in {table} table")

    cursor.execute("EXEC sp_MSforeachtable 'ALTER TABLE ? NOCHECK CONSTRAINT ALL'")

    print("Deleting data from all tables...")
    cursor.execute("DELETE FROM Evenement")
    cursor.execute("DELETE FROM Alerte")
    cursor.execute("DELETE FROM Employe")
    cursor.execute("DELETE FROM Poste_Competence")
    cursor.execute("DELETE FROM Equipe")
    cursor.execute("DELETE FROM Date")

    cursor.execute("DBCC CHECKIDENT ('Date', RESEED, 0)")
    cursor.execute("DBCC CHECKIDENT ('Equipe', RESEED, 0)")
    cursor.execute("DBCC CHECKIDENT ('Poste_Competence', RESEED, 0)")
    cursor.execute("DBCC CHECKIDENT ('Alerte', RESEED, 0)")
    cursor.execute("DBCC CHECKIDENT ('Evenement', RESEED, 0)")

    cursor.execute("EXEC sp_MSforeachtable 'ALTER TABLE ? CHECK CONSTRAINT ALL'")

    conn.commit()
    print("All tables cleared successfully")


def generate_dates(cursor):
    date_ids = {}

    start_date = datetime.now() - timedelta(days=365 * 2)
    end_date = datetime.now() + timedelta(days=365)

    holidays = {
        "01-01": "Jour de l'An",
        "05-01": "Fête du Travail",
        "05-08": "Victoire 1945",
        "07-14": "Fête Nationale",
        "08-15": "Assomption",
        "11-01": "Toussaint",
        "11-11": "Armistice 1918",
        "12-25": "Noël"
    }

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        jour = current_date.day
        mois = current_date.month
        annee = current_date.year
        jour_semaine = current_date.strftime("%A")

        date_key = f"{mois:02d}-{jour:02d}"
        est_jour_ferie = 1 if date_key in holidays else 0
        description_jour = holidays.get(date_key, "")

        cursor.execute('''
            INSERT INTO Date (date_complete, jour, mois, annee, jour_semaine, est_jour_ferie, description_jour)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (date_str, jour, mois, annee, jour_semaine, est_jour_ferie, description_jour))

        cursor.execute("SELECT @@IDENTITY AS date_id")
        date_id = cursor.fetchone()[0]
        date_ids[date_str] = date_id

        current_date += timedelta(days=1)

    return date_ids


def generate_teams(cursor):
    teams = [
        ("Équipe Production", "Responsable de la production et fabrication", "Jean Dupont"),
        ("Équipe Maintenance", "Maintenance des équipements et installations", "Marie Lambert"),
        ("Équipe Logistique", "Gestion des stocks et expéditions", "Philippe Martin"),
        ("Équipe Qualité", "Contrôle et assurance qualité", "Sophie Bernard"),
        ("Équipe R&D", "Recherche et développement", "Thomas Petit"),
        ("Équipe Administrative", "Gestion administrative et RH", "Claire Dubois"),
        ("Équipe Informatique", "Support IT et développement", "Lucas Moreau")
    ]

    team_ids = []
    for team_name, description, chef in teams:
        cursor.execute('''
            INSERT INTO Equipe (nom_equipe, description, chef_equipe)
            VALUES (?, ?, ?)
        ''', (team_name, description, chef))

        cursor.execute("SELECT @@IDENTITY AS team_id")
        team_id = cursor.fetchone()[0]
        team_ids.append(team_id)

    return team_ids


def generate_positions(cursor):
    positions = [
        ("Opérateur", "Débutant", "Opération des machines de base", "Formation technique de base"),
        ("Opérateur", "Intermédiaire", "Opération des machines complexes", "1 an d'expérience minimum"),
        ("Opérateur", "Expert", "Opération et réglage de toutes les machines", "3 ans d'expérience minimum"),
        ("Technicien", "Débutant", "Maintenance préventive", "Formation technique"),
        ("Technicien", "Intermédiaire", "Réparations et maintenance", "2 ans d'expérience minimum"),
        ("Technicien", "Expert", "Dépannage complexe et améliorations", "5 ans d'expérience minimum"),
        ("Ingénieur", "Junior", "Support technique et analyses", "Diplôme d'ingénieur"),
        ("Ingénieur", "Senior", "Conception et amélioration des process", "3 ans d'expérience en ingénierie"),
        ("Manager", "Intermédiaire", "Gestion d'équipe et planification", "Expérience en management"),
        ("Manager", "Senior", "Direction stratégique", "5 ans d'expérience en management"),
        ("Administratif", "Junior", "Tâches administratives de base", "Formation administrative"),
        ("Administratif", "Senior", "Coordination administrative", "3 ans d'expérience minimum")
    ]

    position_ids = []
    for titre, niveau, description, requirements in positions:
        cursor.execute('''
            INSERT INTO Poste_Competence (titre_poste, niveau_competence, description, requirements)
            VALUES (?, ?, ?, ?)
        ''', (titre, niveau, description, requirements))

        cursor.execute("SELECT @@IDENTITY AS position_id")
        position_id = cursor.fetchone()[0]
        position_ids.append(position_id)

    return position_ids


def generate_employees(cursor, team_ids, position_ids, date_ids):

    num_employees = 100

    employee_rfids = []

    for _ in range(num_employees):
        rfid = ''.join(random.choice('0123456789ABCDEF') for _ in range(8))

        nom = fake.last_name()
        prenom = fake.first_name()

        age = random.randint(21, 65)
        date_naissance = (datetime.now() - timedelta(days=365 * age)).strftime("%Y-%m-%d")

        years_employed = random.randint(0, 10)
        date_embauche = (datetime.now() - timedelta(days=365 * years_employed)).strftime("%Y-%m-%d")

        email = f"{prenom.lower()}.{nom.lower()}@company.com"
        telephone = fake.phone_number()
        adresse = fake.address().replace('\n', ', ')

        equipe_id = random.choice(team_ids)
        poste_id = random.choice(position_ids)


        date_id = date_ids.get(date_embauche)


        cursor.execute('''
            INSERT INTO Employe (rfid, nom, prenom, date_naissance, date_embauche, email, telephone, adresse, equipe_id, poste_id, date_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
        rfid, nom, prenom, date_naissance, date_embauche, email, telephone, adresse, equipe_id, poste_id, date_id))

        employee_rfids.append(rfid)

    return employee_rfids


def generate_alerts(cursor, employee_rfids, date_ids):
    alert_types = [
        "Retard",
        "Absence",
        "Accès non autorisé",
        "Badge oublié",
        "Maintenance requise",
        "Formation à planifier",
        "Certificat expiré",
        "Accès après heures"
    ]

    statuses = ["Nouveau", "En cours", "Résolu", "Fermé", "En attente"]

    alert_ids = []

    for _ in range(200):
        type_alerte = random.choice(alert_types)
        description = f"Alerte: {type_alerte} - {fake.sentence()}"

        days_ago = random.randint(0, 365)
        date_alerte = (datetime.now() - timedelta(days=days_ago))
        date_alerte_str = date_alerte.strftime("%Y-%m-%d")

        status = random.choice(statuses)
        rfid = random.choice(employee_rfids)

        date_id = date_ids.get(date_alerte_str)

        cursor.execute('''
            INSERT INTO Alerte (type_alerte, description, date_alerte, status, rfid, date_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (type_alerte, description, date_alerte, status, rfid, date_id))

        cursor.execute("SELECT @@IDENTITY AS alert_id")
        alert_id = cursor.fetchone()[0]
        alert_ids.append(alert_id)

    return alert_ids


def generate_events(cursor, employee_rfids, team_ids, position_ids, alert_ids, date_ids):
    event_types = [
        "Entrée",
        "Sortie",
        "Pause début",
        "Pause fin",
        "Réunion",
        "Formation",
        "Maintenance",
        "Incident",
        "Visite client"
    ]

    for _ in range(1000):
        type_evenement = random.choice(event_types)

        days_ago = random.randint(0, 365)
        date_evenement = (datetime.now() - timedelta(days=days_ago))
        date_evenement_str = date_evenement.strftime("%Y-%m-%d")

        description = f"Événement: {type_evenement} - {fake.sentence()}"
        rfid = random.choice(employee_rfids)
        equipe_id = random.choice(team_ids)
        poste_id = random.choice(position_ids)


        alerte_id = random.choice(alert_ids) if random.random() < 0.2 else None


        date_id = date_ids.get(date_evenement_str)


        cursor.execute('''
            INSERT INTO Evenement (type_evenement, date_evenement, description, rfid, equipe_id, poste_id, alerte_id, date_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (type_evenement, date_evenement, description, rfid, equipe_id, poste_id, alerte_id, date_id))


def print_summary(cursor):

    tables = ["Date", "Equipe", "Poste_Competence", "Employe", "Alerte", "Evenement"]

    print("\nData Generation Summary:")
    print("-----------------------")

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table}: {count} records")


if __name__ == "__main__":
    generate_fake_data()