-- init.sql

-- Create database (if running as superuser)
CREATE DATABASE vuokradb;

-- Connect to the database
\c vuokradb

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create application user
-- CREATE USER postgres WITH PASSWORD 'Vuokra2026';

-- -- -- Grant privileges
-- GRANT ALL PRIVILEGES ON DATABASE myapp_db TO myapp_user;
-- GRANT ALL ON SCHEMA public TO myapp_user;

-- Create tables
CREATE TABLE links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    link VARCHAR(255) UNIQUE NOT NULL,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
