# Class 12 CS Project: Railway Reservation System
# Python code using mysql-connector-python for database interaction.

import mysql.connector
import os
import hashlib
from uuid import uuid4

# --- 1. Database Configuration ---
# !!! IMPORTANT: YOU MUST CHANGE THESE DETAILS TO MATCH YOUR LOCAL MYSQL SETUP !!!
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',        # e.g., 'root'
    'password': 'Ram@123', # e.g., 'password123'
    'database': 'railway_db'
}

# --- Global State for Logged-in User ---
CURRENT_USER = None 
SALT = "class12csrailway" # A fixed salt for security (for a real app, this should be unique per user)
ADMIN_SECRET_CODE = "ADMIN" # Secret command to access the new Admin menu
ADMIN_USERNAME = "admin" # The designated username for the administrator account.

class RailwayReservationSystem:
    """
    Manages the core logic and database operations for the railway reservation system.
    """
    def __init__(self):
        self.db_connection = None
        self.cursor = None

    # --- Utility Methods ---

    def _hash_password(self, password):
        """Hashes the password using SHA-512 with a fixed salt."""
        # Concatenate password and salt, then hash the result
        hashed_password = hashlib.sha512((password + SALT).encode('utf-8')).hexdigest()
        return hashed_password

    def connect(self):
        """Attempts to establish a connection to the MySQL database."""
        try:
            self.db_connection = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.db_connection.cursor()
            print("--- Database connection successful. ---")
            return True
        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}")
            print("Please ensure your MySQL server is running and configuration details (host, user, password) are correct.")
            return False

    def disconnect(self):
        """Closes the database connection."""
        if self.db_connection and self.db_connection.is_connected():
            self.cursor.close()
            self.db_connection.close()
            print("--- Database connection closed. ---")

    def _execute_query(self, query, params=None, fetch=False, commit=False):
        """
        Internal function to handle query execution and common errors.
        Returns result if fetch=True, otherwise None.
        """
        try:
            self.cursor.execute(query, params or ())
            if commit:
                self.db_connection.commit()
            if fetch:
                return self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            self.db_connection.rollback() # Rollback on error to prevent transaction leakage
        except Exception as e:
            print(f"An unexpected error occurred during query execution: {e}")
        return None

    # --- Admin Statistics Function ---
    def get_admin_stats(self):
        """Fetches key statistics for the admin dashboard."""
        
        stats = {}
        
        try:
            # 1. Total Users
            total_users_query = "SELECT COUNT(*) FROM USERS"
            stats['total_users'] = self._execute_query(total_users_query, fetch=True)[0][0] or 0
            
            # 2. Total Trains
            total_trains_query = "SELECT COUNT(*) FROM TRAINS"
            stats['total_trains'] = self._execute_query(total_trains_query, fetch=True)[0][0] or 0
            
            # 3. Total Reservations (Booked Seats)
            total_reservations_query = "SELECT COUNT(*) FROM RESERVATIONS"
            stats['total_reservations'] = self._execute_query(total_reservations_query, fetch=True)[0][0] or 0
            
            # 4. Total Seats & Occupancy (booked seats is total - available)
            total_seats_query = "SELECT SUM(total_seats), SUM(total_seats - available_seats) FROM TRAINS"
            seat_info = self._execute_query(total_seats_query, fetch=True)[0]
            stats['system_total_seats'] = seat_info[0] or 0
            stats['system_booked_seats'] = seat_info[1] or 0
            
            # Calculate Occupancy Percentage
            if stats['system_total_seats'] > 0:
                stats['occupancy_percent'] = (stats['system_booked_seats'] / stats['system_total_seats']) * 100
            else:
                stats['occupancy_percent'] = 0.0

            return stats

        except Exception as e:
            print(f"Error fetching admin stats: {e}")
            return None

    # --- User Authentication Functions ---

    def register_user(self, username, password):
        """Registers a new user by hashing the password and inserting into the USERS table."""
        if not username or not password:
            print("Registration Failed: Username and password cannot be empty.")
            return False

        try:
            # Check if user already exists
            self.cursor.execute("SELECT username FROM USERS WHERE username = %s", (username,))
            if self.cursor.fetchone():
                print(f"Registration Failed: Username '{username}' already taken.")
                return False

            password_hash = self._hash_password(password)
            
            insert_query = "INSERT INTO USERS (username, password_hash) VALUES (%s, %s)"
            self.cursor.execute(insert_query, (username, password_hash))
            self.db_connection.commit()
            print(f"\n[SUCCESS] User '{username}' registered successfully!")
            return True
            
        except mysql.connector.Error as err:
            print(f"Registration Error: {err}")
            self.db_connection.rollback()
            return False

    def login_user(self, username, password):
        """Authenticates a user by checking the hashed password and setting CURRENT_USER."""
        global CURRENT_USER 
        try:
            self.cursor.execute("SELECT password_hash FROM USERS WHERE username = %s", (username,))
            result = self.cursor.fetchone()

            if result:
                stored_hash = result[0]
                provided_hash = self._hash_password(password)
                
                if stored_hash == provided_hash:
                    # Modify the global variable, so 'global' is needed here.
                    CURRENT_USER = username 
                    return True
                else:
                    print("\nLogin Failed: Invalid username or password.")
                    return False
            else:
                print("\nLogin Failed: Invalid username or password.")
                return False
                
        except mysql.connector.Error as err:
            print(f"Login Error: {err}")
            return False

    # --- Core Reservation Functions ---

    def search_trains(self, source, destination):
        """Searches for available trains between the given source and destination."""
        query = """
            SELECT train_number, train_name, source, destination, available_seats
            FROM TRAINS
            WHERE source = %s AND destination = %s AND available_seats > 0
        """
        results = self._execute_query(query, (source, destination), fetch=True) 
        
        if results:
            print("\n--- Available Trains ---")
            print("{:<10} {:<30} {:<15} {:<15} {:<10}".format(
                "Number", "Name", "Source", "Destination", "Seats"
            ))
            print("-" * 80)
            for row in results:
                print("{:<10} {:<30} {:<15} {:<15} {:<10}".format(*row))
            return True
        else:
            print("\nNo direct trains found for this route, or seats are unavailable.")
            return False

    def book_ticket(self, train_number, name, age):
        """Books a ticket by assigning a PNR and seat, and updating available seats."""
        # CURRENT_USER is only read here, so no 'global' declaration is needed.
        if not CURRENT_USER:
            print("Booking Failed: You must be logged in to book a ticket.")
            return

        try:
            # 1. Fetch current seat availability and VALIDATE TRAIN NUMBER FIRST
            # We use FOR UPDATE to lock the row, but we defer the transaction start slightly.
            # However, because we need to lock the row, we must start the transaction here.
            
            # --- TRANSACTION PRE-CHECK & START ---
            if self.db_connection.in_transaction:
                print("[WARNING] An active transaction was found before starting a new one. Rolling back...")
                self.db_connection.rollback()
            
            self.db_connection.start_transaction()
            # -----------------------------------

            self.cursor.execute("SELECT available_seats, total_seats FROM TRAINS WHERE train_number = %s FOR UPDATE", (train_number,))
            train_info = self.cursor.fetchone()

            if not train_info:
                print("Booking Failed: Invalid Train Number.")
                self.db_connection.rollback() 
                return
            
            available_seats, total_seats = train_info
            
            if available_seats <= 0:
                print("Booking Failed: No available seats left on this train.")
                self.db_connection.rollback() 
                return

            # 2. Determine the next available seat number
            seat_number = total_seats - available_seats + 1
            
            # 3. Generate PNR
            pnr_number = str(uuid4())[:8].upper() 

            # 4. Insert Reservation Record (This is where 'username' is used)
            reservation_query = """
                INSERT INTO RESERVATIONS (pnr_number, train_number, username, passenger_name, age, seat_number)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            # CURRENT_USER must correspond to a valid user in the USERS table
            self.cursor.execute(reservation_query, (pnr_number, train_number, CURRENT_USER, name, age, seat_number))
            
            # 5. Update Available Seats in TRAINS table
            update_seats_query = "UPDATE TRAINS SET available_seats = available_seats - 1 WHERE train_number = %s"
            self.cursor.execute(update_seats_query, (train_number,))

            self.db_connection.commit() # Commit all changes
            print(f"\n--- BOOKING SUCCESSFUL! ---")
            print(f"PNR Number: {pnr_number}")
            print(f"Booked by: {CURRENT_USER}")
            print(f"Train: {train_number} - Seat: {seat_number}")
            print(f"Passenger: {name}, Age: {age}")
            
        except mysql.connector.Error as err:
            # Re-raise the error to show which specific DB error occurred
            print(f"Booking Error: {err}")
            self.db_connection.rollback() 
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            self.db_connection.rollback() 


    def cancel_ticket(self, pnr_number):
        """Cancels a ticket by deleting the reservation and updating available seats."""
        # CURRENT_USER is only read here, so no 'global' declaration is needed.
        if not CURRENT_USER:
            print("Cancellation Failed: You must be logged in to cancel a ticket.")
            return

        try:
            # FIX: Ensure any prior transactions are rolled back before starting a new one.
            if self.db_connection.in_transaction:
                print("Cancellation Failed: An active transaction was found. Rolling back the old one...")
                self.db_connection.rollback()
            
            self.db_connection.start_transaction()

            # 1. Retrieve the reservation details (train_number and check user) FOR UPDATE
            self.cursor.execute("SELECT train_number, username FROM RESERVATIONS WHERE pnr_number = %s FOR UPDATE", (pnr_number,))
            reservation = self.cursor.fetchone()

            if not reservation:
                print(f"Cancellation Failed: PNR Number {pnr_number} not found.")
                self.db_connection.rollback()
                return
            
            train_number, booking_user = reservation
            
            # Check if the logged-in user owns the reservation
            if booking_user != CURRENT_USER:
                print(f"Cancellation Failed: You are not authorized to cancel PNR {pnr_number}. It was booked by user '{booking_user}'.")
                self.db_connection.rollback()
                return
            
            # 2. Delete the reservation record
            delete_query = "DELETE FROM RESERVATIONS WHERE pnr_number = %s"
            self.cursor.execute(delete_query, (pnr_number,))
            
            # 3. Update Available Seats in TRAINS table (increase by 1)
            update_seats_query = "UPDATE TRAINS SET available_seats = available_seats + 1 WHERE train_number = %s"
            self.cursor.execute(update_seats_query, (train_number,))

            self.db_connection.commit()
            print(f"\n--- CANCELLATION SUCCESSFUL! ---")
            print(f"PNR {pnr_number} cancelled. Seat on Train {train_number} is now available.")

        except mysql.connector.Error as err:
            print(f"Cancellation Error: {err}")
            self.db_connection.rollback()
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            self.db_connection.rollback()

    def view_booking(self, pnr_number):
        """Displays the details of a specific reservation."""
        # CURRENT_USER is only read here, so no 'global' declaration is needed.
        if not CURRENT_USER:
            print("View Booking Failed: You must be logged in to view a ticket.")
            return
            
        query = """
            SELECT 
                r.pnr_number, 
                r.passenger_name, 
                r.age, 
                r.seat_number, 
                t.train_name, 
                t.train_number,
                t.source, 
                t.destination,
                r.booking_date,
                r.username -- Fetch the booking user
            FROM RESERVATIONS r
            JOIN TRAINS t ON r.train_number = t.train_number
            WHERE r.pnr_number = %s
        """
        result = self._execute_query(query, (pnr_number,), fetch=True)

        if result:
            (pnr, name, age, seat, t_name, t_num, src, dest, date, booking_user) = result[0]
            
            # Only allow viewing if the logged-in user is the one who booked it
            if booking_user != CURRENT_USER:
                 print(f"\nView Failed: PNR {pnr_number} was booked by user '{booking_user}'. You cannot view this detail.")
                 return
                 
            print("\n--- RESERVATION DETAILS ---")
            print(f"PNR Number: {pnr}")
            print(f"Booked By: {booking_user}")
            print(f"Train: {t_num} - {t_name}")
            print(f"Route: {src} to {dest}")
            print(f"Passenger: {name} (Age: {age})")
            print(f"Seat Number: {seat}")
            print(f"Booked On: {date.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"\nBooking not found for PNR Number: {pnr_number}")

    def reset_seats(self):
        """
        Resets the available_seats for all trains to their total_seats capacity,
        and clears all entries in the RESERVATIONS table.
        """
        # CURRENT_USER and ADMIN_USERNAME are only read here, so no 'global' declaration is needed.
        
        if CURRENT_USER is None or CURRENT_USER.lower() != ADMIN_USERNAME.lower(): 
            print("Access Denied: Only the 'admin' user can perform a full reset.")
            return

        print("\n--- Initiating System Reset (Seating and Reservations) ---")
        try:
            self.cursor.execute("TRUNCATE TABLE RESERVATIONS")
            update_query = "UPDATE TRAINS SET available_seats = total_seats"
            self.cursor.execute(update_query)
            self.db_connection.commit()
            
            print(f"[SUCCESS] Cleared {self.cursor.rowcount} reservations.")
            print(f"[SUCCESS] Reset available seats for all trains to full capacity.")
            
        except mysql.connector.Error as err:
            print(f"Reset Error: {err}")
            self.db_connection.rollback()
        except Exception as e:
            print(f"An unexpected error occurred during reset: {e}")

    def reset_users(self):
        """
        Clears the USERS table and re-registers the admin user.
        Requires clearing RESERVATIONS first due to Foreign Key constraint.
        """
        global CURRENT_USER
        # ADMIN_USERNAME is only read here, so no 'global' declaration is needed.

        if CURRENT_USER is None or CURRENT_USER.lower() != ADMIN_USERNAME.lower(): 
            print("Access Denied: Only the 'admin' user can perform a user reset.")
            return

        print("\n--- Initiating User Table Reset (All Users will be deleted) ---")
        
        # Get new password before starting the irreversible reset
        print("\nNOTE: After the reset, the 'admin' user must be re-registered.")
        new_admin_password = input(f"Enter NEW password for the '{ADMIN_USERNAME}' account: ").strip()
        
        if not new_admin_password:
            print("Reset Cancelled: New admin password cannot be empty.")
            return

        try:
            # 1. Temporarily disable foreign key checks
            self.cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            # 2. Clear dependent table (RESERVATIONS)
            self.cursor.execute("TRUNCATE TABLE RESERVATIONS")
            
            # 3. Clear the USERS table
            self.cursor.execute("TRUNCATE TABLE USERS")
            
            # 4. Re-enable foreign key checks
            self.cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            
            self.db_connection.commit()
            
            # 5. Re-register the admin user immediately
            if self.register_user(ADMIN_USERNAME, new_admin_password):
                print(f"[SUCCESS] Cleared all users and re-registered '{ADMIN_USERNAME}' with the new password.")
                # Modify the global variable, so 'global' is needed here.
                CURRENT_USER = None 
                print("[WARNING] ACTION REQUIRED: You have been logged out. Please log in again using the new admin password.")
            else:
                print("CRITICAL ERROR: Cleared users table but failed to re-register admin user.")
            
        except mysql.connector.Error as err:
            print(f"User Reset Error: {err}")
            self.db_connection.rollback()
        except Exception as e:
            print(f"An unexpected error occurred during user reset: {e}")

# --- 3. User Interface / Menu Logic ---

def clear_screen():
    """Clears the console screen for better readability."""
    os.system('cls' if os.name == 'nt' else 'clear')

def auth_menu(system):
    """Handles the initial Login/Register menu."""
    global CURRENT_USER 
    # ADMIN_SECRET_CODE and ADMIN_USERNAME are only read here, so no 'global' is needed.

    while True:
        clear_screen()
        print("==============================================")
        print("  RAILWAY RESERVATION SYSTEM (AUTH MENU)")
        print("==============================================")
        print("1. Login (Standard User)")
        print("2. Register (New User)")
        print("3. Exit Application")
        print("----------------------------------------------")
        
        choice = input(f"Enter your choice (1-3, or type '{ADMIN_SECRET_CODE}' for admin menu): ").strip().upper()
        
        if choice == '3':
            return False

        # --- ADMIN MENU CHECK ---
        if choice == ADMIN_SECRET_CODE:
            # Modify the global variable, so 'global' is needed here.
            CURRENT_USER = None 
            
            print("\n--- Admin Access Attempt ---")
            username = input("Enter Admin Username: ").strip()
            password = input("Enter Admin Password: ").strip()
            
            # Attempt to login. login_user will set CURRENT_USER on success.
            if system.login_user(username, password):
                # SUCCESS: Now check if the logged-in user is the designated admin.
                if CURRENT_USER and CURRENT_USER.lower() == ADMIN_USERNAME.lower():
                    print(f"\n[SUCCESS] Admin login successful! Welcome, {CURRENT_USER}.")
                    input("Press Enter to continue to admin dashboard...")
                    admin_menu(system)
                    # Modify the global variable, so 'global' is needed here.
                    CURRENT_USER = None 
                else:
                    print("\nAdmin Access Failed: Login successful, but user is not the designated 'admin' user.")
                    # Modify the global variable, so 'global' is needed here.
                    CURRENT_USER = None 
            
            input("\nPress Enter to continue...")
            continue # Loop back to the start of auth_menu
        # --- END ADMIN MENU CHECK ---

        # If choice is 1 or 2, proceed with standard authentication
        
        if choice in ('1', '2'):
            username = input("Enter Username: ").strip()
            password = input("Enter Password: ").strip()

            if choice == '1':
                # The login_user sets CURRENT_USER and returns bool.
                if system.login_user(username, password):
                    print(f"\n[SUCCESS] Login successful! Welcome, {CURRENT_USER}.")
                    input("Press Enter to continue to main menu...")
                    return True # Go to main_menu
            elif choice == '2':
                system.register_user(username, password)
            
            input("\nPress Enter to continue...")
        else:
             print("\nInvalid choice.")
             input("\nPress Enter to continue...")

def admin_menu(system):
    """Displays the admin menu with stats and handles admin actions."""
    # CURRENT_USER and ADMIN_USERNAME are only read here, so no 'global' is needed.
    
    # Use case-insensitive check against the official ADMIN_USERNAME
    if CURRENT_USER is None or CURRENT_USER.lower() != ADMIN_USERNAME.lower():
        print("\nADMIN ACCESS DENIED: Only the 'admin' user can access this menu.")
        input("Press Enter to return to the main menu...")
        return
        
    while True:
        clear_screen()
        print("==============================================")
        print("          ADMINISTRATION DASHBOARD")
        print("==============================================")
        
        stats = system.get_admin_stats()
        
        if stats:
            print("\n--- Current System Statistics ---")
            print(f"Total Registered Users: {stats['total_users']}")
            print(f"Total Trains in System: {stats['total_trains']}")
            print(f"Total Reservations Made: {stats['total_reservations']}")
            print(f"Total System Seat Capacity: {stats['system_total_seats']}")
            print(f"Total Seats Booked: {stats['system_booked_seats']}")
            print(f"System Occupancy Rate: {stats['occupancy_percent']:.2f}%")
            print("---------------------------------")
        else:
            print("Could not load system statistics.")
            
        print("\n--- Admin Actions ---")
        print("1. Reset All Seats & Clear Bookings (DANGER)")
        print("2. Reset All Users & Re-register Admin (DANGER)")
        print("3. Return to Main Menu")
        print("----------------------------------------------")
        
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == '1':
            confirm = input("DANGER: Are you absolutely sure you want to delete ALL reservations and reset seats? (Type 'YES' to confirm): ").strip().upper()
            if confirm == 'YES':
                system.reset_seats()
            else:
                print("Database reset cancelled.")
        elif choice == '2':
            confirm = input("DANGER: Are you absolutely sure you want to delete ALL users (including non-admin) and their associated data? (Type 'YES' to confirm): ").strip().upper()
            if confirm == 'YES':
                system.reset_users()
                # If reset_users succeeds, it will clear CURRENT_USER and the loop will return to auth_menu next.
                if CURRENT_USER is None:
                    return 
            else:
                print("User table reset cancelled.")
        elif choice == '3':
            return # Exit admin menu and return to auth_menu
        else:
            print("\nInvalid choice.")

        input("\nPress Enter to continue...")

def main_menu():
    """Displays the main menu and handles user input."""
    global CURRENT_USER 
    
    system = RailwayReservationSystem()

    if not system.connect():
        input("\nPress Enter to exit...")
        return
        
    # --- Start with Authentication ---
    if not auth_menu(system):
        print("\nThank you for using the Railway Reservation System. Goodbye!")
        system.disconnect()
        return

    # --- Main Application Loop ---
    while True:
        clear_screen()
        # Display logged-in status
        print("==============================================")
        print(f"  RAILWAY RESERVATION SYSTEM | User: {CURRENT_USER}")
        print("==============================================")
        print("1. Search & Book Train")
        print("2. View My Reservation Details (by PNR)")
        print("3. Cancel My Reservation (by PNR)")
        print("4. Logout / Exit")
        print("----------------------------------------------")
        
        choice = input("Enter your choice (1-4): ").strip().upper()

        if choice == '1':
            source = input("Enter Source Station: ").strip()
            destination = input("Enter Destination Station: ").strip()
            
            if system.search_trains(source, destination):
                train_num = input("\nEnter Train Number to book (or press Enter to return to menu): ").strip()
                if train_num:
                    name = input("Enter Passenger Name (Name on ticket): ").strip()
                    try:
                        age = int(input("Enter Passenger Age: "))
                        if age > 0:
                            system.book_ticket(train_num, name, age)
                        else:
                            print("Invalid age entered.")
                    except ValueError:
                        print("Invalid input for age.")
            
        elif choice == '2':
            pnr = input("Enter PNR Number to view: ").strip().upper()
            if pnr:
                system.view_booking(pnr)

        elif choice == '3':
            pnr = input("Enter PNR Number to cancel: ").strip().upper()
            if pnr:
                system.cancel_ticket(pnr)

        elif choice == '4':
            # Modify the global variable, so 'global' is needed here.
            CURRENT_USER = None
            print("\nLogged out successfully.")
            system.disconnect()
            return
        
        else:
            print("\nInvalid choice. Please enter a number between 1 and 4.")

        input("\nPress Enter to continue...")

# --- 4. Main Execution Block ---

if __name__ == "__main__":
    main_menu()