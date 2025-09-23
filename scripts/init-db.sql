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

-- Normalise the PostGIS feature flag into an "on"/"off" token so we can
-- selectively install the extension when the environment requests it.
\getenv postgis_request_raw BUILDABLE_USE_POSTGIS
SELECT CASE
         WHEN :'postgis_request_raw' ~* '^(1|true|yes|on)$' THEN 'on'
         ELSE 'off'
       END AS enable_postgis_request
\gset

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

\if :enable_postgis_request = 'on'
  SELECT EXISTS (
           SELECT 1
           FROM pg_available_extensions
           WHERE name = 'postgis'
         ) AS postgis_available
  \gset

  \if :postgis_available = 't'
    CREATE EXTENSION IF NOT EXISTS postgis;
  \else
    \echo 'PostGIS requested but the extension is not available; skipping installation.'
  \endif
\endif
