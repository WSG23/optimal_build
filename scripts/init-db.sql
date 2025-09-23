\echo 'Running initial database bootstrap'
\set ON_ERROR_STOP on

-- Read the desired database name and owner from the environment so the script
-- tracks docker-compose overrides. Fall back to the defaults that ship with the
-- repository when the variables are unset.
\getenv dbname POSTGRES_DB
\if :dbname = ''
  \set dbname building_compliance
\endif

\getenv dbowner POSTGRES_USER
\if :dbowner = ''
  \set dbowner postgres
\endif

\echo 'Ensuring database' :'dbname' 'exists with owner' :'dbowner'

-- Connect to the maintenance database so we can create the application database when needed.
\connect postgres

SELECT format('CREATE DATABASE %I OWNER %I', :'dbname', :'dbowner')
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = :'dbname')
\gexec

-- Switch to the application database for extension setup.
\connect :dbname

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
