# Script to import train data from trains_list.csv into the MySQL TRAINS table.

import mysql.connector
import csv
import os

# --- 1. Database Configuration (Must match railway_system.py) ---
# !!! IMPORTANT: ENSURE THESE DETAILS ARE CORRECT !!!
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Ram@123', # <-- CHANGE THIS
    'database': 'railway_db'
}

def import_train_data(csv_filepath="trains_list.csv", total_seats=500):
    """
    Reads train data from a CSV file and inserts it into the TRAINS table.

    Args:
        csv_filepath (str): The path to the CSV file.
        total_seats (int): The default total capacity to assign to each train.
    """
    try:
        # Establish database connection
        db_connection = mysql.connector.connect(**DB_CONFIG)
        cursor = db_connection.cursor()
        print("--- Database connection successful. ---")
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        print("Please check DB_CONFIG in this file and ensure your MySQL server is running.")
        return

    # SQL statement for inserting data
    insert_query = """
    INSERT INTO TRAINS 
        (train_number, train_name, source, destination, total_seats, available_seats)
    VALUES 
        (%s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE 
        train_name = VALUES(train_name),
        source = VALUES(source),
        destination = VALUES(destination),
        total_seats = VALUES(total_seats),
        available_seats = VALUES(available_seats);
    """
    # The ON DUPLICATE KEY UPDATE clause is important. If a train_number 
    # already exists (it's the PRIMARY KEY), it updates the record instead of failing.
    
    records_processed = 0
    records_inserted = 0
    
    try:
        with open(csv_filepath, mode='r', encoding='utf-8') as file:
            # Use csv.reader for files without column names or csv.DictReader if the first row is a header.
            # Assuming your CSV has a header row:
            reader = csv.DictReader(file) 
            
            print(f"Reading data from '{csv_filepath}'...")
            
            for row in reader:
                records_processed += 1
                
                # Based on the snippet, mapping is:
                # CSV 'Train no.' -> DB train_number
                # CSV 'Train name' -> DB train_name
                # CSV 'Starts' -> DB source
                # CSV 'Ends' -> DB destination
                
                # Sanitize and prepare data
                try:
                    train_number = str(row['Train no.']).strip()
                    train_name = row['Train name'].strip()
                    source = row['Starts'].strip()
                    destination = row['Ends'].strip()
                except KeyError as e:
                    print(f"\n[ERROR] Missing expected column in CSV: {e}. Row skipped: {row}")
                    continue

                # Data for the SQL query
                # available_seats is set equal to total_seats initially
                train_data = (
                    train_number,
                    train_name,
                    source,
                    destination,
                    total_seats,
                    total_seats 
                )
                
                # Execute the insertion
                cursor.execute(insert_query, train_data)
                records_inserted += 1
        
        # Commit the transaction after all rows are successfully processed
        db_connection.commit()
        
        print("\n==============================================")
        print("DATA IMPORT COMPLETE")
        print("==============================================")
        print(f"Total rows read from CSV: {records_processed}")
        print(f"Total trains added/updated in database: {records_inserted}")
        print(f"Default seats per train: {total_seats}")
        
    except FileNotFoundError:
        print(f"\n[ERROR] CSV file not found at path: {csv_filepath}")
    except mysql.connector.Error as err:
        print(f"\n[ERROR] Database Transaction Failed: {err}")
        db_connection.rollback()
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        
    finally:
        # Close connection
        if db_connection and db_connection.is_connected():
            cursor.close()
            db_connection.close()
            print("--- Database connection closed. ---")

# --- Execution Block ---
if __name__ == "__main__":
    # You can change the default_seats value here if you need more or less capacity.
    default_seats = 500 
    
    print("Starting data import...")
    # NOTE: The CSV file MUST be in the same directory as this script.
    import_train_data(csv_filepath="trains_list.csv", total_seats=default_seats)