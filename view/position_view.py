class PositionView:
    def print_positions(self, positions):
        for pos in positions:
            print(f"ID: {pos.poste_id}")
            print(f"Title: {pos.titre_poste}")
            print(f"Level: {pos.niveau_competence}")
            print(f"Description: {pos.description}")
            print(f"Requirements: {pos.requirements}")
            print("-" * 30)

    def success(self, message):
        print(f"\n{message}")

    def error(self, message):
        print(f"\nError: {message}")