import requests
import json
import time
from datetime import datetime
import sys


class ESP32RFIDClient:
    def __init__(self, esp32_ip):
        self.base_url = f"http://{esp32_ip}"
        self.check_connection()

    def check_connection(self):
        try:
            response = requests.get(f"{self.base_url}/status", timeout=5)
            if response.status_code == 200:
                print(f"Successfully connected to ESP32 at {self.base_url}")
                system_info = response.json()
                print(f"System info: {json.dumps(system_info, indent=2)}")
                return True
            else:
                print(f"Error: Received status code {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to ESP32: {e}")
            return False

    def get_status(self):
        try:
            response = requests.get(f"{self.base_url}/status")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting status: {e}")
            return None

    def unlock_door(self):
        try:
            payload = {"unlock": True}
            response = requests.post(f"{self.base_url}/control", json=payload)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error unlocking door: {e}")
            return None

    def lock_door(self):
        try:
            payload = {"lock": True}
            response = requests.post(f"{self.base_url}/control", json=payload)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error locking door: {e}")
            return None

    def get_authorized_cards(self):
        try:
            response = requests.get(f"{self.base_url}/authorized-cards")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting authorized cards: {e}")
            return None

    def add_authorized_card(self, card_id):
        try:
            payload = {"cardId": card_id}
            response = requests.post(f"{self.base_url}/add-card", json=payload)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error adding card: {e}")
            return None

    def monitor_card_events(self, interval=1, duration=None):

        print("Starting card event monitoring. Press Ctrl+C to stop.")
        start_time = time.time()
        last_card_id = None

        try:
            while True:
                if duration and (time.time() - start_time) > duration:
                    break

                status = self.get_status()
                if status and status.get("cardDetected"):
                    current_card = status.get("lastCardId")
                    if current_card != last_card_id:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        auth_status = "Authorized" if status.get("isAuthorized") else "Unauthorized"
                        print(f"[{timestamp}] Card detected: {current_card} - {auth_status}")
                        last_card_id = current_card

                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user.")


def main():
    if len(sys.argv) < 2:
        print("Usage: python rfid_client.py <esp32_ip_address>")
        sys.exit(1)

    esp32_ip = sys.argv[1]
    client = ESP32RFIDClient(esp32_ip)

    while True:
        print("\nESP32 RFID Door Lock System")
        print("1. Get system status")
        print("2. Unlock door")
        print("3. Lock door")
        print("4. List authorized cards")
        print("5. Add new authorized card")
        print("6. Monitor card events")
        print("7. Exit")

        choice = input("Enter your choice (1-7): ")

        if choice == "1":
            status = client.get_status()
            if status:
                print(json.dumps(status, indent=2))

        elif choice == "2":
            result = client.unlock_door()
            if result:
                print(f"Result: {result}")

        elif choice == "3":
            result = client.lock_door()
            if result:
                print(f"Result: {result}")

        elif choice == "4":
            cards = client.get_authorized_cards()
            if cards:
                print(f"Authorized cards: {json.dumps(cards, indent=2)}")

        elif choice == "5":
            card_id = input("Enter card ID (in hex format without spaces): ")
            result = client.add_authorized_card(card_id)
            if result:
                print(f"Result: {result}")

        elif choice == "6":
            try:
                interval = float(input("Check interval in seconds (default 1): ") or 1)
                client.monitor_card_events(interval=interval)
            except ValueError:
                print("Invalid interval. Using default of 1 second.")
                client.monitor_card_events()

        elif choice == "7":
            print("Exiting program.")
            break

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()