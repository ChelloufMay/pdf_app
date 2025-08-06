-- init_schema.sql

-- 1) Create database
CREATE DATABASE IF NOT EXISTS pdf_app_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE pdf_app_db;

-- 2) (Optional) Create or update pdf_user
CREATE USER IF NOT EXISTS 'pdf_user'@'localhost'
  IDENTIFIED BY 'BrightSun!2025$';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON pdf_app_db.* TO 'pdf_user'@'localhost';
FLUSH PRIVILEGES;

-- 3) Create metadata table
CREATE TABLE IF NOT EXISTS pdf_files (
  id INT AUTO_INCREMENT PRIMARY KEY,
  filename VARCHAR(255) NOT NULL COMMENT 'Original PDF filename',
  url VARCHAR(255) NOT NULL COMMENT 'Relative URL path',
  size_kb INT NOT NULL COMMENT 'Size in KB',
  upload_time DATETIME NOT NULL
    DEFAULT CURRENT_TIMESTAMP COMMENT 'Upload timestamp'
) ENGINE=InnoDB;
