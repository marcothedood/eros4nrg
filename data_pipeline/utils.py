import pandas as pd
import numpy as np
import sqlalchemy as sa
from sqlalchemy import text as sqltext
from sqlalchemy.dialects.postgresql import (
    JSONB, ARRAY, INTEGER, BIGINT, DOUBLE_PRECISION, TIMESTAMP, BOOLEAN, TEXT
)

from config.settings import (
    BUCKET_NAME,
    POSTGRES_DB,
    POSTGRES_PASSWORD,
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_USER,
)
from clients.minio.minio_client import MinioClient

# ---------------- MinIO & DB engine ----------------
micl = MinioClient()

engine = sa.create_engine(
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

TABLE_DTYPES = {
    "vehicle_states": {
        "id": BIGINT(),
        "battery_percentage": DOUBLE_PRECISION(),
        "velocity": DOUBLE_PRECISION(),
        "timestamp": TIMESTAMP(timezone=False),
        "in_charge": BOOLEAN(),
        "efficiency": TEXT(),
        "charges_count": BIGINT(),
        "km_tot": DOUBLE_PRECISION(),
        "kwh_charged": DOUBLE_PRECISION(),
        "vehicle": BIGINT(),
    },
    "tower_states": {
        "id": BIGINT(),
        "plugs_state": JSONB(),
        "timestamp": TIMESTAMP(timezone=False),
        "ac_max_current": DOUBLE_PRECISION(),
        "dc_modules_number": TEXT(),
        "dc_min_voltage": TEXT(),
        "dc_max_voltage": TEXT(),
        "dc_max_current": TEXT(),
        "tower": BIGINT(),
    },
    "w4_calc": {
        "timestamp": TIMESTAMP(timezone=False),
        "w4_production": DOUBLE_PRECISION(),
        "w4_building_consumption": DOUBLE_PRECISION(),
    },
    "vehicle": {"vehicle": BIGINT(), "charge_id": ARRAY(INTEGER())},
    "tower":   {"tower":   BIGINT(), "charge_id": ARRAY(INTEGER())},

    "predicted_battery_percentage_cat": {
        "battery_percentage": DOUBLE_PRECISION(),
        "timestamp": TIMESTAMP(timezone=False),
        "vehicle": BIGINT(),
    },
    "predicted_w4_building_consumption_cat": {
        "w4_building_consumption": DOUBLE_PRECISION(),
        "timestamp": TIMESTAMP(timezone=False),
    },
    "predicted_w4_production_cat": {
        "w4_production": DOUBLE_PRECISION(),
        "timestamp": TIMESTAMP(timezone=False),
    },
    "prophet_forecast_w4_building_consumption": {
        "timestamp": TIMESTAMP(timezone=False),
        "w4_building_consumption": DOUBLE_PRECISION(),
        "trend": DOUBLE_PRECISION(),
        "daily": DOUBLE_PRECISION(),
        "hourly": DOUBLE_PRECISION(),
        "weekly": DOUBLE_PRECISION(),
    },
}

def get_dtype(table_name: str):
    return TABLE_DTYPES.get(table_name)

W4_EXPECTED = {
    "timestamp": "timestamp without time zone",
    "w4_production": "double precision",
    "w4_building_consumption": "double precision",
}

def _w4_schema_is_ok(conn) -> bool:
    q = """
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema='public' AND table_name='w4_calc'
    ORDER BY ordinal_position
    """
    df = pd.read_sql(q, conn)
    if df.empty:
        return False
    got = dict(zip(df["column_name"], df["data_type"]))
    return all(got.get(k) == v for k, v in W4_EXPECTED.items())

def ensure_w4_schema():
    with engine.begin() as conn:
        exists_df = pd.read_sql("SELECT to_regclass('public.w4_calc') is not null AS exists", conn)
        exists = bool(exists_df["exists"].iloc[0]) if not exists_df.empty else False
        if not exists:
            return
        if not _w4_schema_is_ok(conn):
            conn.execute(sqltext("DROP TABLE public.w4_calc"))

# ---------------- DB helpers ----------------
def get_all_tables():
    sql_query = "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    try:
        return pd.read_sql(sql=sql_query, con=engine)
    except Exception:
        return pd.DataFrame(columns=["table_name"])

def get_table(columns=None, table_name="vehicle", clause=""):
    if columns is None:
        columns = "*"
    joined_columns = ",".join(columns) if isinstance(columns, (list, tuple)) else columns
    sql_query = f'SELECT {joined_columns} FROM {table_name} {clause}'
    try:
        return pd.read_sql(sql=sql_query, con=engine)
    except Exception:
        return pd.DataFrame()

def get_existing_metadata(table_name):
    sql_query = f"SELECT * FROM {table_name}"
    existing_ids, existing_table = [], pd.DataFrame()
    try:
        existing_table = pd.read_sql(sql=sql_query, con=engine)
        if not existing_table.empty and table_name in existing_table.columns:
            existing_ids = existing_table[table_name].tolist()
        return existing_ids, existing_table
    except Exception:
        return existing_ids, existing_table

def clean_db():
    tables_df = get_all_tables()
    if tables_df.empty or "table_name" not in tables_df.columns:
        return

    existing = set(tables_df["table_name"].tolist())

    if "vehicle_states" in existing:
        with engine.begin() as conn:
            conn.execute(sqltext("""
                DELETE FROM vehicle_states a
                USING vehicle_states b
                WHERE a.ctid < b.ctid
                  AND a.id = b.id
                  AND a."timestamp" = b."timestamp";
            """))

    if "tower_states" in existing:
        with engine.begin() as conn:
            conn.execute(sqltext("""
                DELETE FROM tower_states a
                USING tower_states b
                WHERE a.ctid < b.ctid
                  AND a.id = b.id
                  AND a."timestamp" = b."timestamp";
            """))

    if "w4_calc" in existing:
        with engine.begin() as conn:
            conn.execute(sqltext("""
                DELETE FROM w4_calc a
                USING w4_calc b
                WHERE a.ctid < b.ctid
                  AND a."timestamp" = b."timestamp";
            """))

def save_df_to_db(df, table_name, if_exists="append", ind_bool=False, dtype=None):
    effective_dtype = dtype if dtype is not None else get_dtype(table_name)
    df.to_sql(
        table_name,
        engine,
        if_exists=if_exists,
        index=ind_bool,
        dtype=effective_dtype,
        method="multi",
        chunksize=1000,
    )

def calculate_w4(asm_w4_df, asm_w6_df):
    w4_calc = pd.DataFrame()
    asm_w4_df["DateTime"] = pd.to_datetime(asm_w4_df["DateTime"])
    asm_w6_df["DateTime"] = pd.to_datetime(asm_w6_df["DateTime"])

    asm_w4_df.set_index("DateTime", inplace=True)
    asm_w6_df.set_index("DateTime", inplace=True)

    asm_w4_df = asm_w4_df.resample("5s").ffill()
    asm_w6_df = asm_w6_df.resample("5s").ffill()

    w4_calc["timestamp"] = asm_w4_df.index[:len(asm_w6_df)]

    w4_production = pd.to_numeric(asm_w6_df["Value"], errors="coerce") * (60 / 185)
    w4_production = w4_production.fillna(0)
    w4_calc["w4_production"] = w4_production.values

    w4_building = (
        pd.to_numeric(asm_w4_df["Value"][:len(asm_w6_df)], errors="coerce").fillna(0)
        + w4_calc["w4_production"]
    )
    w4_calc["w4_building_consumption"] = w4_building.values

    save_df_to_db(
        w4_calc,
        "w4_calc",
        if_exists="replace",
    )

# ---------------- MinIO helpers ----------------
def get_df(folder_name, drct_file):
    return micl.file_to_df(
        bucket_name=BUCKET_NAME, file_name=drct_file, directory=folder_name
    )

def get_new_and_existing_dfs(df, existing_ids, metadata_name):
    new_dfs = df.loc[~df[metadata_name].isin(existing_ids)]
    existing_dfs = df.loc[df[metadata_name].isin(existing_ids)]
    return new_dfs, existing_dfs

def _to_python_int_list_series(series: pd.Series) -> pd.Series:
    def fix_list(lst):
        if not isinstance(lst, (list, tuple)):
            return lst
        out = []
        for x in lst:
            if x is None or (isinstance(x, float) and pd.isna(x)):
                out.append(None)
                continue
            try:
                out.append(int(x))
            except Exception:
                try:
                    out.append(int(pd.to_numeric(x, errors="coerce")))
                except Exception:
                    out.append(None)
        return out
    return series.apply(fix_list)

# ---------------- Metadata merge & upsert ----------------
def merge_metadata(existing_metadata, grouped_df, metadata_name):
    if metadata_name not in existing_metadata.keys():
        existing_metadata = existing_metadata.reset_index()

    for metadata_id in existing_metadata[metadata_name]:
        relevant_list = existing_metadata.loc[
            existing_metadata[metadata_name] == metadata_id
        ]["charge_id"].values[0]
        if metadata_id in grouped_df["charge_id"].keys():
            existing_metadata.at[
                existing_metadata[
                    existing_metadata[metadata_name] == metadata_id
                ].index[0],
                "charge_id",
            ] = list(set(relevant_list + grouped_df["charge_id"][metadata_id]))
        else:
            existing_metadata.at[
                existing_metadata[
                    existing_metadata[metadata_name] == metadata_id
                ].index[0],
                "charge_id",
            ] = relevant_list


    if "charge_id" in existing_metadata.columns:
        existing_metadata["charge_id"] = _to_python_int_list_series(existing_metadata["charge_id"])
    return existing_metadata

def update_or_create_metadata(transformed_df, metadata_name):
    existing_ids, existing_metadata_from_table = get_existing_metadata(metadata_name)
    new_dfs_from_source, existing_dfs_from_source = get_new_and_existing_dfs(
        transformed_df, existing_ids, metadata_name
    )

    grouped_new = (
        new_dfs_from_source.rename(columns={"id": "charge_id"})
        .groupby(metadata_name)["charge_id"].apply(list).to_frame()
    )
    grouped_existing = (
        existing_dfs_from_source.rename(columns={"id": "charge_id"})
        .groupby(metadata_name)["charge_id"].apply(list).to_frame()
    )

    if not grouped_new.empty:
        grouped_new["charge_id"] = _to_python_int_list_series(grouped_new["charge_id"])
    if not grouped_existing.empty:
        grouped_existing["charge_id"] = _to_python_int_list_series(grouped_existing["charge_id"])

    if not grouped_new.empty and not existing_metadata_from_table.empty:
        existing_metadata_from_table = pd.concat(
            [existing_metadata_from_table.set_index(metadata_name), grouped_new]
        ).sort_values(by=[metadata_name], ascending=True)

        existing_metadata_from_table["charge_id"] = _to_python_int_list_series(
            existing_metadata_from_table["charge_id"]
        )

        save_df_to_db(
            existing_metadata_from_table,
            metadata_name,
            if_exists="replace",
            ind_bool=True,
            dtype={"charge_id": ARRAY(INTEGER())},
        )

    if not grouped_existing.empty and not existing_metadata_from_table.empty:
        existing_metadata_from_table = merge_metadata(
            existing_metadata_from_table, grouped_existing, metadata_name
        )

        save_df_to_db(
            existing_metadata_from_table,
            metadata_name,
            if_exists="replace",
            dtype={"charge_id": ARRAY(INTEGER())},
        )

    if existing_metadata_from_table.empty:
        existing_metadata_from_table = grouped_new

        save_df_to_db(
            existing_metadata_from_table,
            metadata_name,
            if_exists="replace",
            ind_bool=True,
            dtype={"charge_id": ARRAY(INTEGER())},
        )
