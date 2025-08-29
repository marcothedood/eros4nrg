-- bootstrap.migrations
CREATE TABLE IF NOT EXISTS bootstrap.migrations (
    id text NOT NULL,
    applied_at timestamptz DEFAULT now()
);

-- public.predicted_battery_percentage_cat
CREATE TABLE IF NOT EXISTS public.predicted_battery_percentage_cat (
    battery_percentage double precision,
    "timestamp" timestamp without time zone,
    vehicle bigint
);

-- public.predicted_w4_building_consumption_cat
CREATE TABLE IF NOT EXISTS public.predicted_w4_building_consumption_cat (
    w4_building_consumption double precision,
    "timestamp" timestamp without time zone
);

-- public.predicted_w4_production_cat
CREATE TABLE IF NOT EXISTS public.predicted_w4_production_cat (
    w4_production double precision,
    "timestamp" timestamp without time zone
);

-- public.prophet_forecast_w4_building_consumption
CREATE TABLE IF NOT EXISTS public.prophet_forecast_w4_building_consumption (
    "timestamp" timestamp without time zone,
    w4_building_consumption double precision,
    trend double precision,
    daily double precision,
    hourly double precision,
    weekly double precision
);

-- public.tower
CREATE TABLE IF NOT EXISTS public.tower (
    tower bigint,
    charge_id integer[]
);

-- public.tower_states
CREATE TABLE IF NOT EXISTS public.tower_states (
    id bigint,
    plugs_state text,
    "timestamp" timestamp without time zone,
    ac_max_current double precision,
    dc_modules_number text,
    dc_min_voltage text,
    dc_max_voltage text,
    dc_max_current text,
    tower bigint
);

-- public.vehicle
CREATE TABLE IF NOT EXISTS public.vehicle (
    vehicle bigint,
    charge_id integer[]
);

-- public.vehicle_states
CREATE TABLE IF NOT EXISTS public.vehicle_states (
    id bigint,
    battery_percentage double precision,
    velocity double precision,
    "timestamp" timestamp without time zone,
    in_charge boolean,
    efficiency text,
    charges_count bigint,
    km_tot double precision,
    kwh_charged double precision,
    vehicle bigint
);

-- public.w4_calc
CREATE TABLE IF NOT EXISTS public.w4_calc (
    "timestamp" text,
    w4_production text,
    w4_building_consumption text
);