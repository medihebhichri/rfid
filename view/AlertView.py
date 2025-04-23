class AlertView:
    def print_alerts(self, alerts):
        for alert in alerts:
            print(f"ID: {alert.alerte_id}")
            print(f"Type: {alert.type_alerte}")
            print(f"Description: {alert.description}")
            print(f"Date: {alert.date_alerte}")
            print(f"Status: {alert.status}")
            print(f"Employee: {alert.nom} {alert.prenom}" if alert.nom else "No employee linked")
            print(f"Date: {alert.date_complete}")
            print("-" * 30)

    def print_employees(self, employees):
        for emp in employees:
            print(f"RFID: {emp.rfid}, Name: {emp.nom} {emp.prenom}")

    def success(self, message):
        print(f"\n{message}")

    def error(self, message):
        print(f"\nError: {message}")