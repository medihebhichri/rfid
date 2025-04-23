class EventView:
    def print_events(self, events):
        for event in events:
            print(f"Event ID: {event.evenement_id}")
            print(f"Type: {event.type_evenement}")
            print(f"Date: {event.date_evenement}")
            print(f"Description: {event.description}")
            print(f"Employee: {event.nom} {event.prenom}" if event.nom else "No employee linked")
            print(f"Team: {event.nom_equipe}" if event.nom_equipe else "No team linked")
            print(f"Position: {event.titre_poste}" if event.titre_poste else "No position linked")
            print(f"Alert: {event.type_alerte}" if event.type_alerte else "No alert linked")
            print(f"Date: {event.date_complete}")
            print("-" * 30)

    def print_employees(self, employees):
        for emp in employees:
            print(f"RFID: {emp.rfid}, Name: {emp.nom} {emp.prenom}")

    def print_teams(self, teams):
        for team in teams:
            print(f"ID: {team.equipe_id}, Name: {team.nom_equipe}")

    def print_positions(self, positions):
        for pos in positions:
            print(f"ID: {pos.poste_id}, Title: {pos.titre_poste}")

    def print_alerts(self, alerts):
        for alert in alerts:
            print(f"ID: {alert.alerte_id}, Type: {alert.type_alerte}")

    def success(self, message):
        print(f"\n{message}")

    def error(self, message):
        print(f"\nError: {message}")