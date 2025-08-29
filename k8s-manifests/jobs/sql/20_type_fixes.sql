DO $$
BEGIN
  -- vehicle_states.id -> bigint
  IF (SELECT data_type FROM information_schema.columns
      WHERE table_schema='public' AND table_name='vehicle_states' AND column_name='id') <> 'bigint' THEN
    EXECUTE 'ALTER TABLE public.vehicle_states ALTER COLUMN id TYPE bigint USING NULLIF(id,'''')::bigint';
  END IF;

  -- vehicle_states.battery_percentage -> double precision
  IF (SELECT data_type FROM information_schema.columns
      WHERE table_schema='public' AND table_name='vehicle_states' AND column_name='battery_percentage') NOT IN ('double precision') THEN
    EXECUTE 'ALTER TABLE public.vehicle_states ALTER COLUMN battery_percentage TYPE double precision USING NULLIF(battery_percentage,'''')::double precision';
  END IF;

  -- vehicle_states.velocity -> double precision
  IF (SELECT data_type FROM information_schema.columns
      WHERE table_schema='public' AND table_name='vehicle_states' AND column_name='velocity') NOT IN ('double precision') THEN
    EXECUTE 'ALTER TABLE public.vehicle_states ALTER COLUMN velocity TYPE double precision USING NULLIF(velocity,'''')::double precision';
  END IF;

  -- vehicle_states.timestamp -> timestamp without time zone (gestione ISO8601 con offset)
  IF (SELECT data_type FROM information_schema.columns
      WHERE table_schema='public' AND table_name='vehicle_states' AND column_name='timestamp') NOT IN ('timestamp without time zone') THEN
    EXECUTE $sql$
      ALTER TABLE public.vehicle_states
        ALTER COLUMN "timestamp" TYPE timestamp WITHOUT TIME ZONE
        USING (
          CASE
            WHEN "timestamp" ~ '^\d{4}-\d{2}-\d{2}T' THEN (("timestamp")::timestamptz AT TIME ZONE 'UTC')
            ELSE ("timestamp")::timestamp
          END
        )
    $sql$;
  END IF;

  -- vehicle_states.in_charge -> boolean (gestione 't','true','1','f','false','0')
  IF (SELECT data_type FROM information_schema.columns
      WHERE table_schema='public' AND table_name='vehicle_states' AND column_name='in_charge') <> 'boolean' THEN
    EXECUTE $sql$
      ALTER TABLE public.vehicle_states
        ALTER COLUMN in_charge TYPE boolean USING
          CASE
            WHEN lower(in_charge) IN ('t','true','1') THEN true
            WHEN lower(in_charge) IN ('f','false','0') THEN false
            ELSE NULL
          END
    $sql$;
  END IF;

  -- vehicle_states.efficiency -> text
  IF (SELECT data_type FROM information_schema.columns
      WHERE table_schema='public' AND table_name='vehicle_states' AND column_name='efficiency') <> 'text' THEN
    EXECUTE 'ALTER TABLE public.vehicle_states ALTER COLUMN efficiency TYPE text USING efficiency::text';
  END IF;

  -- vehicle_states.charges_count -> bigint
  IF (SELECT data_type FROM information_schema.columns
      WHERE table_schema='public' AND table_name='vehicle_states' AND column_name='charges_count') <> 'bigint' THEN
    EXECUTE 'ALTER TABLE public.vehicle_states ALTER COLUMN charges_count TYPE bigint USING NULLIF(charges_count,'''')::bigint';
  END IF;

  -- vehicle_states.km_tot -> double precision
  IF (SELECT data_type FROM information_schema.columns
      WHERE table_schema='public' AND table_name='vehicle_states' AND column_name='km_tot') NOT IN ('double precision') THEN
    EXECUTE 'ALTER TABLE public.vehicle_states ALTER COLUMN km_tot TYPE double precision USING NULLIF(km_tot,'''')::double precision';
  END IF;

  -- vehicle_states.kwh_charged -> double precision
  IF (SELECT data_type FROM information_schema.columns
      WHERE table_schema='public' AND table_name='vehicle_states' AND column_name='kwh_charged') NOT IN ('double precision') THEN
    EXECUTE 'ALTER TABLE public.vehicle_states ALTER COLUMN kwh_charged TYPE double precision USING NULLIF(kwh_charged,'''')::double precision';
  END IF;

  -- vehicle_states.vehicle -> bigint
  IF (SELECT data_type FROM information_schema.columns
      WHERE table_schema='public' AND table_name='vehicle_states' AND column_name='vehicle') <> 'bigint' THEN
    EXECUTE 'ALTER TABLE public.vehicle_states ALTER COLUMN vehicle TYPE bigint USING NULLIF(vehicle,'''')::bigint';
  END IF;
END $$;

DO $$
BEGIN
  -- w4_calc.timestamp -> timestamp without time zone
  IF EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema='public' AND table_name='w4_calc' AND column_name='timestamp'
        AND data_type <> 'timestamp without time zone'
  ) THEN
    EXECUTE $sql$
      ALTER TABLE public.w4_calc
        ALTER COLUMN "timestamp" TYPE timestamp WITHOUT TIME ZONE
        USING (
          CASE
            WHEN "timestamp" ~ '^\d{4}-\d{2}-\d{2}T' THEN (("timestamp")::timestamptz AT TIME ZONE 'UTC')
            ELSE ("timestamp")::timestamp
          END
        )
    $sql$;
  END IF;

  -- w4_calc.w4_production -> double precision
  IF EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema='public' AND table_name='w4_calc' AND column_name='w4_production'
        AND data_type <> 'double precision'
  ) THEN
    EXECUTE 'ALTER TABLE public.w4_calc ALTER COLUMN w4_production TYPE double precision USING NULLIF(w4_production,'''')::double precision';
  END IF;

  -- w4_calc.w4_building_consumption -> double precision
  IF EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema='public' AND table_name='w4_calc' AND column_name='w4_building_consumption'
        AND data_type <> 'double precision'
  ) THEN
    EXECUTE 'ALTER TABLE public.w4_calc ALTER COLUMN w4_building_consumption TYPE double precision USING NULLIF(w4_building_consumption,'''')::double precision';
  END IF;
END $$;
