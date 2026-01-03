-- Newsletter AI Database Setup Script
-- Run this with: mysql -u root -p < setup_database.sql

-- Drop and recreate database to ensure clean state
DROP DATABASE IF EXISTS newsletter_db;
CREATE DATABASE newsletter_db;

-- Use the database
USE newsletter_db;

-- Show success message
SELECT 'Database newsletter_db created successfully!' AS Status;

-- Show all databases to confirm
SHOW DATABASES;
