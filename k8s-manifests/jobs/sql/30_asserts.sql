DO $$
DECLARE
  v_count int;
BEGIN
  -- vehicle_states: expected types
  SELECT count(*) INTO v_count FROM information_schema.columns
  WHERE table_schema='public' AND table_name='vehicle_states' AND (
    (column_name='id'                 AND data_type <> 'bigint') OR
    (column_name='battery_percentage' AND data_type <> 'double precision') OR
    (column_name='velocity'           AND data_type <> 'double precision') OR
    (column_name='timestamp'          AND data_type <> 'timestamp without time zone') OR
    (column_name='in_charge'          AND data_type <> 'boolean') OR
    (column_name='efficiency'         AND data_type <> 'text') OR
    (column_name='charges_count'      AND data_type <> 'bigint') OR
    (column_name='km_tot'             AND data_type <> 'double precision') OR
    (column_name='kwh_charged'        AND data_type <> 'double precision') OR
    (column_name='vehicle'            AND data_type <> 'bigint')
  );

  IF v_count > 0 THEN
    RAISE EXCEPTION 'Type assertions failed for public.vehicle_states (% rows mismatched)', v_count;
  END IF;

END $$;
