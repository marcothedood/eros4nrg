-- Schema base (safe se esiste già)
CREATE SCHEMA IF NOT EXISTS public;

-- Crea vehicle_states se non esiste, già coi tipi giusti
CREATE TABLE IF NOT EXISTS public.vehicle_states (
    id                 bigint,
    battery_percentage double precision,
    velocity           double precision,
    "timestamp"        timestamp without time zone,
    in_charge          boolean,
    efficiency         text,
    charges_count      bigint,
    km_tot             double precision,
    kwh_charged        double precision,
    vehicle            bigint
);

-- Se la tabella esiste ma con tipi sbagliati (es. text), li correggiamo.
DO $$
BEGIN
    -- id
    IF (SELECT data_type FROM information_schema.columns 
        WHERE table_schema='public' AND table_name='vehicle_states' AND column_name='id') <> 'bigint' THEN
        ALTER TABLE public.vehicle_states
          ALTER COLUMN id TYPE bigint USING NULLIF(id,'')::bigint;
    END IF;

    -- battery_percentage
    IF (SELECT data_type FROM information_schema.columns 
        WHERE table_schema='public' AND table_name='vehicle_states' AND column_name='battery_percentage') NOT IN ('double precision') THEN
        ALTER TABLE public.vehicle_states
          ALTER COLUMN battery_percentage TYPE double precision USING NULLIF(battery_percentage,'')::double precision;
    END IF;

    -- velocity
    IF (SELECT data_type FROM information_schema.columns 
        WHERE table_schema='public' AND table_name='vehicle_states' AND column_name='velocity') NOT IN ('double precision') THEN
        ALTER TABLE public.vehicle_states
          ALTER COLUMN velocity TYPE double precision USING NULLIF(velocity,'')::double precision;
    END IF;

    -- timestamp (stringhe tipo 2019-01-08T08:58:55+01:00 -> timestamptz -> AT TIME ZONE 'UTC')
    IF (SELECT data_type FROM information_schema.columns 
        WHERE table_schema='public' AND table_name='vehicle_states' AND column_name='timestamp') NOT IN ('timestamp without time zone') THEN
        ALTER TABLE public.vehicle_states
          ALTER COLUMN "timestamp" TYPE timestamp WITHOUT TIME ZONE
          USING (
            CASE
              WHEN "timestamp" ~ '^\d{4}-\d{2}-\d{2}T' THEN (("timestamp")::timestamptz AT TIME ZONE 'UTC')
              ELSE ("timestamp")::timestamp
            END
          );
    END IF;

    -- in_charge (gestione true/false/1/0)
    IF (SELECT data_type FROM information_schema.columns 
        WHERE table_schema='public' AND table_name='vehicle_states' AND column_name='in_charge') <> 'boolean' THEN
        ALTER TABLE public.vehicle_states
          ALTER COLUMN in_charge TYPE boolean USING
            CASE
              WHEN lower(in_charge) IN ('t','true','1') THEN true
              WHEN lower(in_charge) IN ('f','false','0') THEN false
              ELSE NULL
            END;
    END IF;

    -- efficiency deve rimanere TEXT (accetta "charging")
    IF (SELECT data_type FROM information_schema.columns 
        WHERE table_schema='public' AND table_name='vehicle_states' AND column_name='efficiency') <> 'text' THEN
        ALTER TABLE public.vehicle_states
          ALTER COLUMN efficiency TYPE text USING efficiency::text;
    END IF;

    -- charges_count
    IF (SELECT data_type FROM information_schema.columns 
        WHERE table_schema='public' AND table_name='vehicle_states' AND column_name='charges_count') <> 'bigint' THEN
        ALTER TABLE public.vehicle_states
          ALTER COLUMN charges_count TYPE bigint USING NULLIF(charges_count,'')::bigint;
    END IF;

    -- km_tot
    IF (SELECT data_type FROM information_schema.columns 
        WHERE table_schema='public' AND table_name='vehicle_states' AND column_name='km_tot') NOT IN ('double precision') THEN
        ALTER TABLE public.vehicle_states
          ALTER COLUMN km_tot TYPE double precision USING NULLIF(km_tot,'')::double precision;
    END IF;

    -- kwh_charged
    IF (SELECT data_type FROM information_schema.columns 
        WHERE table_schema='public' AND table_name='vehicle_states' AND column_name='kwh_charged') NOT IN ('double precision') THEN
        ALTER TABLE public.vehicle_states
          ALTER COLUMN kwh_charged TYPE double precision USING NULLIF(kwh_charged,'')::double precision;
    END IF;

    -- vehicle
    IF (SELECT data_type FROM information_schema.columns 
        WHERE table_schema='public' AND table_name='vehicle_states' AND column_name='vehicle') <> 'bigint' THEN
        ALTER TABLE public.vehicle_states
          ALTER COLUMN vehicle TYPE bigint USING NULLIF(vehicle,'')::bigint;
    END IF;

    -- Piccolo registro di migrazioni
    CREATE SCHEMA IF NOT EXISTS bootstrap;
    CREATE TABLE IF NOT EXISTS bootstrap.migrations (
      id text primary key,
      applied_at timestamptz default now()
    );
    INSERT INTO bootstrap.migrations(id) VALUES ('schema-vehicle-states-typed-001')
      ON CONFLICT DO NOTHING;
END $$;
