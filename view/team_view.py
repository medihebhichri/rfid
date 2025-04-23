class TeamView:
    def print_teams(self, teams):
        for team in teams:
            print(f"ID: {team.equipe_id}")
            print(f"Name: {team.nom_equipe}")
            print(f"Leader: {team.chef_equipe}")
            print(f"Description: {team.description}")
            print("-" * 30)

    def success(self, message):
        print(f"\n{message}")

    def error(self, message):
        print(f"\nError: {message}")