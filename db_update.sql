-- Check if the column already exists before adding it to avoid errors on re-run
-- NOTE: This syntax is for MySQL 8.0+. If you are using an older version, you might need to run the simple ALTER TABLE command below.

-- 1. Add the missing 'username' column
ALTER TABLE RESERVATIONS
ADD COLUMN username VARCHAR(50) NOT NULL AFTER train_number;

-- 2. Add the Foreign Key constraint to link reservations to users
-- This assumes your USERS table has 'username' as the primary key or a unique index.
ALTER TABLE RESERVATIONS
ADD CONSTRAINT fk_user_reservation
FOREIGN KEY (username)
REFERENCES USERS (username)
ON DELETE CASCADE;

-- If the above batch commands give errors, run this simple command first:
-- ALTER TABLE RESERVATIONS ADD COLUMN username VARCHAR(50) NOT NULL AFTER train_number;