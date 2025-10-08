-- Simple database initialization script for PostgreSQL
\echo 'Running initial database bootstrap'

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

\echo 'Database initialization complete'
