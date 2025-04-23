class TeamController:
    def __init__(self, db_manager):
        self.db = db_manager

    def clear_screen(self):
        import os
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_team_menu(self):
        print("\n=== Team Management ===")
        print("1. Add Team")
        print("2. View All Teams")
        print("3. Update Team")
        print("4. Delete Team")
        print("0. Back to Main Menu")

    def team_menu(self):
        while True:
            self.clear_screen()
            self.print_team_menu()
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
            else:
                input("\nInvalid choice. Press Enter to continue...")

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

    def update_team(self):
        print("\n=== Update Team ===")
        try:
            equipe_id = int(input("Enter Team ID to update: "))
            self.db.cursor.execute("SELECT * FROM Equipe WHERE equipe_id=?", (equipe_id,))
            team = self.db.cursor.fetchone()
            if not team:
                print("Team not found!")
                return

            print("Leave blank to keep current value.")
            nom_equipe = input(f"Enter new Team Name [{team.nom_equipe}]: ") or team.nom_equipe
            description = input(f"Enter new Description [{team.description}]: ") or team.description
            chef_equipe = input(f"Enter new Team Leader [{team.chef_equipe}]: ") or team.chef_equipe

            self.db.cursor.execute('''
                UPDATE Equipe
                SET nom_equipe=?, description=?, chef_equipe=?
                WHERE equipe_id=?''', (nom_equipe, description, chef_equipe, equipe_id))
            self.db.conn.commit()
            print("\nTeam updated successfully!")
        except Exception as e:
            print(f"\nError updating team: {str(e)}")
        input("\nPress Enter to continue...")

    def delete_team(self):
        print("\n=== Delete Team ===")
        try:
            equipe_id = int(input("Enter Team ID to delete: "))
            self.db.cursor.execute("SELECT * FROM Equipe WHERE equipe_id=?", (equipe_id,))
            team = self.db.cursor.fetchone()
            if not team:
                print("Team not found!")
                return

            self.db.cursor.execute("DELETE FROM Equipe WHERE equipe_id=?", (equipe_id,))
            self.db.conn.commit()
            print("\nTeam deleted successfully!")
        except Exception as e:
            print(f"\nError deleting team: {str(e)}")
        input("\nPress Enter to continue...")