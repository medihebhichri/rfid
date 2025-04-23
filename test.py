import pyodbc
import serial
import threading
import time
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='access_control.log'
)

class DatabaseManager:
    def __init__(self):
        self.conn_str = (
            'DRIVER={ODBC Driver 18 for SQL Server};'
            'SERVER=IHEB;'
            'DATABASE=rfid;'
            'Trusted_Connection=Yes;'
            'Encrypt=no'
        )
        self.create_tables()

    def create_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='employees' AND xtype='U')
                CREATE TABLE employees (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    qr_code VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    department VARCHAR(255),
                    card_expiry DATE,
                    authorized_access VARCHAR(255),
                    status VARCHAR(10) DEFAULT 'ACTIVE'
                )
            """)
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='access_logs' AND xtype='U')
                CREATE TABLE access_logs (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    qr_code VARCHAR(255),
                    access_time DATETIME DEFAULT GETDATE(),
                    access_granted BIT,
                    reason VARCHAR(255)
                )
            """)
            conn.commit()

    def get_connection(self):
        return pyodbc.connect(self.conn_str)

    def log_access_attempt(self, qr_code, granted, reason=""):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO access_logs (qr_code, access_granted, reason)
                    VALUES (?, ?, ?)
                """, (qr_code, granted, reason))
                conn.commit()
        except Exception as e:
            logging.error(f"Error logging access attempt: {str(e)}")

    def check_access(self, qr_code):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name, status, card_expiry 
                    FROM employees 
                    WHERE qr_code = ?
                """, (qr_code,))

                employee = cursor.fetchone()

                if not employee:
                    self.log_access_attempt(qr_code, False, "Card not registered")
                    return "DENY"

                name, status, expiry = employee

                if expiry and expiry < datetime.now().date():
                    self.log_access_attempt(qr_code, False, "Card expired")
                    return "DENY"

                if status != 'ACTIVE':
                    self.log_access_attempt(qr_code, False, f"Card status: {status}")
                    return "DENY"

                self.log_access_attempt(qr_code, True, "Access granted")
                return f"GRANT,{name}"

        except Exception as e:
            logging.error(f"Error checking access: {str(e)}")
            return "DENY"

class SerialHandler:
    def __init__(self, port, baud_rate):
        self.ser = serial.Serial(port, baud_rate, timeout=1)
        time.sleep(2)
        self.db = DatabaseManager()
        self.waiting_for_card = False
        self.card_callback = None
        logging.info(f"Serial connection established on {port}")

    def listen(self):
        while True:
            try:
                if self.ser.in_waiting > 0:
                    qr_code = self.ser.readline().decode().strip()
                    logging.info(f"Received UID: {qr_code}")

                    if self.waiting_for_card and self.card_callback:
                        self.card_callback(qr_code)
                        self.waiting_for_card = False
                    else:
                        response = self.db.check_access(qr_code)
                        logging.info(f"Sending response: {response}")
                        self.ser.write(f"{response}\n".encode())
                        self.ser.flush()
                        time.sleep(0.1)  # Ensure data is sent

            except Exception as e:
                logging.error(f"Serial error: {str(e)}")
                time.sleep(1)

    def wait_for_card(self, callback):
        self.waiting_for_card = True
        self.card_callback = callback

def main():
    try:
        ser_handler = SerialHandler('COM3', 115200)
        thread = threading.Thread(target=ser_handler.listen, daemon=True)
        thread.start()
        admin_menu(ser_handler)

    except Exception as e:
        logging.error(f"Main error: {str(e)}")
        print(f"Error: {str(e)}")


def admin_menu(ser_handler):
    db = ser_handler.db

    while True:
        print("\nAdmin Menu:")
        print("1. Add Employee")
        print("2. Update Employee")
        print("3. Delete Employee")
        print("4. Check Status")
        print("5. View Access Logs")
        print("6. Exit")

        choice = input("Choose option: ")

        if choice == '1':
            print("Scan the employee's card...")

            def card_scanned(qr_code):
                try:
                    name = input("Enter name: ")
                    department = input("Enter department: ")
                    card_expiry = input("Enter expiry (YYYY-MM-DD): ")
                    areas = input("Enter authorized areas (comma-separated): ")

                    with db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO employees 
                            (qr_code, name, department, card_expiry, authorized_access)
                            VALUES (?, ?, ?, ?, ?)
                        """, (qr_code, name, department, card_expiry, areas))
                        conn.commit()
                        print("Employee added successfully!")
                        logging.info(f"New employee added: {name} ({qr_code})")

                except Exception as e:
                    print(f"Error: {e}")
                    logging.error(f"Error adding employee: {str(e)}")

            ser_handler.wait_for_card(card_scanned)
            while ser_handler.waiting_for_card:
                time.sleep(0.1)

        elif choice == '2':
            qr_code = input("Enter employee QR code: ")
            try:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM employees WHERE qr_code = ?", (qr_code,))
                    employee = cursor.fetchone()

                    if employee:
                        print("\nCurrent employee details:")
                        print(f"Name: {employee.name}")
                        print(f"Department: {employee.department}")
                        print(f"Status: {employee.status}")

                        new_status = input("Enter new status (ACTIVE/INACTIVE) or press Enter to skip: ")
                        if new_status:
                            cursor.execute("""
                                UPDATE employees 
                                SET status = ? 
                                WHERE qr_code = ?
                            """, (new_status, qr_code))
                            conn.commit()
                            print("Employee status updated!")
                            logging.info(f"Employee status updated: {qr_code} -> {new_status}")
                    else:
                        print("Employee not found!")

            except Exception as e:
                print(f"Error: {e}")
                logging.error(f"Error updating employee: {str(e)}")

        elif choice == '3':
            qr_code = input("Enter employee QR code to delete: ")
            try:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM employees WHERE qr_code = ?", (qr_code,))
                    if cursor.rowcount > 0:
                        conn.commit()
                        print("Employee deleted successfully!")
                        logging.info(f"Employee deleted: {qr_code}")
                    else:
                        print("Employee not found!")
            except Exception as e:
                print(f"Error: {e}")
                logging.error(f"Error deleting employee: {str(e)}")

        elif choice == '4':
            print("Scan card to check status...")

            def status_check(qr_code):
                try:
                    with db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT name, department, status, card_expiry, authorized_access 
                            FROM employees 
                            WHERE qr_code = ?
                        """, (qr_code,))
                        employee = cursor.fetchone()

                        if employee:
                            print("\nEmployee Details:")
                            print(f"Name: {employee.name}")
                            print(f"Department: {employee.department}")
                            print(f"Status: {employee.status}")
                            print(f"Card Expiry: {employee.card_expiry}")
                            print(f"Authorized Areas: {employee.authorized_access}")
                        else:
                            print("Card not registered in system")

                except Exception as e:
                    print(f"Error: {e}")
                    logging.error(f"Error checking status: {str(e)}")

            ser_handler.wait_for_card(status_check)
            while ser_handler.waiting_for_card:
                time.sleep(0.1)

        elif choice == '5':
            try:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT TOP 10 
                            l.access_time,
                            l.qr_code,
                            e.name,
                            l.access_granted,
                            l.reason
                        FROM access_logs l
                        LEFT JOIN employees e ON l.qr_code = e.qr_code
                        ORDER BY l.access_time DESC
                    """)
                    logs = cursor.fetchall()

                    print("\nRecent Access Logs:")
                    for log in logs:
                        status = "GRANTED" if log.access_granted else "DENIED"
                        name = log.name if log.name else "Unknown"
                        print(f"Time: {log.access_time}, Name: {name}, Status: {status}, Reason: {log.reason}")

            except Exception as e:
                print(f"Error: {e}")
                logging.error(f"Error viewing access logs: {str(e)}")

        elif choice == '6':
            print("Exiting admin menu...")
            break


if __name__ == "__main__":
    main()