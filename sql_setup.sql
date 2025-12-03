-- 1. Create the database
CREATE DATABASE IF NOT EXISTS railway_db;

-- Use the newly created database
USE railway_db;

-- 2. Create the USERS table
-- This table stores user credentials. Username is the unique ID.
CREATE TABLE IF NOT EXISTS USERS (
    username VARCHAR(50) PRIMARY KEY,
    password_hash VARCHAR(128) NOT NULL, -- To store SHA-512 hash
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Create the TRAINS table (unchanged structure)
CREATE TABLE IF NOT EXISTS TRAINS (
    train_number VARCHAR(10) PRIMARY KEY,
    train_name VARCHAR(100) NOT NULL,
    source VARCHAR(50) NOT NULL,
    destination VARCHAR(50) NOT NULL,
    total_seats INT NOT NULL,
    available_seats INT NOT NULL
);

-- 4. Create the RESERVATIONS table (updated to link to the USERS table)
CREATE TABLE IF NOT EXISTS RESERVATIONS (
    pnr_number VARCHAR(20) PRIMARY KEY,
    train_number VARCHAR(10) NOT NULL,
    username VARCHAR(50) NOT NULL, -- New column: Link reservation to user
    passenger_name VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    seat_number INT UNIQUE NOT NULL,
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (train_number) REFERENCES TRAINS(train_number),
    FOREIGN KEY (username) REFERENCES USERS(username) -- New Foreign Key
);

-- 5. Data Clearing and Load (with Foreign Key Bypass)
SET FOREIGN_KEY_CHECKS = 0; -- Temporarily disable checks to allow TRUNCATE
TRUNCATE TABLE RESERVATIONS;
TRUNCATE TABLE TRAINS;
TRUNCATE TABLE USERS; -- Clear users table as well
SET FOREIGN_KEY_CHECKS = 1; -- Re-enable checks

SELECT 'Both RESERVATIONS, TRAINS, and USERS tables have been successfully emptied.' AS Status;

-- Insert your 20 sample train entries from trains_list.csv (using your provided data)
INSERT INTO TRAINS (train_number, train_name, source, destination, total_seats, available_seats) VALUES
('12723', 'Andhra Pradesh Express', 'Hyderabad Decan', 'New Delhi', 500, 500),
('22416', 'Andhra Pradesh Express', 'New Delhi', 'Vishakapatnam', 500, 500),
('12724', 'Andhra Pradesh Express', 'New Delhi', 'Hyderabad Decan', 500, 500),
('12707', 'Andhra Pradesh Sampark Kranti', 'Tirupati', 'H Nizamuddin', 500, 500),
('15909', 'Abadh Assam Express', 'New Tinsukia Junction', 'Darbhanga Junction', 500, 500),
('18242', 'Abkp Durg Passenger E', 'Ambikapur', 'Durg', 500, 500),
('11266', 'Abkp Jbp Express', 'Ambikapur', 'Jabalpur', 500, 500),
('58702', 'Abkp Sdl Passenger', 'Ambikapur', 'Shahdol', 500, 500),
('54703', 'Abs Ju Passengr', 'Abohar', 'Jodhpur Junction', 500, 500),
('7509', 'Adb Qln Special', 'Adilabad', 'Kollam Junction', 500, 500),
('9416', 'Adi Madgaon Special', 'Ahmedabad Junction', 'Madgaon', 500, 500),
('19417', 'Adi Ald Express', 'Ahmedabad Junction', 'Allahabad Junction', 500, 500),
('9427', 'Adi Ald Special', 'Ahmedabad Junction', 'Allahabad Junction', 500, 500),
('9018', 'Adi Bct Ac Special', 'Ahmedabad Junction', 'Mumbai Central', 500, 500),
('14804', 'Adi Bgkt Express', 'Ahmedabad Junction', 'Bhagat Ki Kothi', 500, 500),
('4804', 'Adi Bgkt Special', 'Ahmedabad Junction', 'Bhagat Ki Kothi', 500, 500),
('9421', 'Adi Bme Ac Special', 'Ahmedabad Junction', 'Barmer', 500, 500),
('19409', 'Adi Gkp Express', 'Ahmedabad Junction', 'Gorakhpur Junction', 500, 500),
('9425', 'Adi Gkp Special', 'Ahmedabad Junction', 'Gorakhpur Junction', 500, 500),
('19411', 'Adi Hwh Express', 'Ahmedabad Junction', 'Howrah Junction', 500, 500);

SELECT 'Database setup complete. Tables (USERS, TRAINS, RESERVATIONS) and train data loaded.' AS Status;