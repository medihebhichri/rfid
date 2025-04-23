class EmployeeView:
    def print_employees(self, employees):
        for emp in employees:
            print(f"RFID: {emp.rfid}")
            print(f"Name: {emp.nom} {emp.prenom}")
            print(f"Email: {emp.email}")
            print(f"Phone: {emp.telephone}")
            print(f"Team: {emp.nom_equipe}")
            print(f"Position: {emp.titre_poste}")
            print(f"Date of Birth: {emp.date_naissance}")
            print(f"Date of Hire: {emp.date_embauche}")
            print("-" * 30)

    def print_teams(self, teams):
        for team in teams:
            print(f"ID: {team.equipe_id}, Name: {team.nom_equipe}")

    def print_positions(self, positions):
        for pos in positions:
            print(f"ID: {pos.poste_id}, Title: {pos.titre_poste}")

    def success(self, message):
        print(f"\n{message}")

    def error(self, message):
        print(f"\nError: {message}")