import pandas as pd
import sqlalchemy as sa

from config.settings import (
    BUCKET_NAME,
    POSTGRES_DB,
    POSTGRES_PASSWORD,
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_USER,
)
from clients.minio.minio_client import MinioClient

micl = MinioClient()

engine = sa.create_engine(
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)


def get_all_tables():
    """
    Get all user made tables from postgres

    Returns:
        Dataframe containing table_name column and all table names
    """
    sql_query = f"SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    try:
        return pd.read_sql(sql=sql_query, con=engine)
    except Exception as e:
        return pd.DataFrame()


def get_table(columns=None, table_name="vehicle", clause=""):
    """
    Get table information directly from postgres
    Returns:
        table dataframe
    """
    if columns is None:
        columns = "*"
    joined_columns = ",".join(columns)
    sql_query = f'SELECT {joined_columns} FROM {table_name} {clause}'
    try:
        return pd.read_sql(sql=sql_query, con=engine)
    except Exception as e:
        return pd.DataFrame()


def get_existing_metadata(table_name):
    """
    Get existing metadata from postgres
    Returns:
        list of existing IDs (vehicle, towers), and dataframe of the metadata table
    """
    sql_query = f"SELECT * FROM {table_name}"
    existing_ids = []
    existing_table = pd.DataFrame()

    try:
        existing_table = pd.read_sql(sql=sql_query, con=engine)
        existing_ids = existing_table[table_name].tolist()
        return existing_ids, existing_table
    except:
        return existing_ids, existing_table


def clean_db():
    """
    Clean up tables of duplicates
    Not cleaning up metadata tables because that has a different structure
    Metadata cleanup is handled in update_or_create_metadata
    """
    all_table_names = get_all_tables()["table_name"].to_list()
    if all_table_names:
        for table_name in all_table_names:
            if table_name in ["vehicle_states", "tower_states", "w4_calc"]:
                table_df = get_table(table_name=table_name)
                if table_df is None:
                    continue
                else:
                    table_df.drop_duplicates(inplace=True)
                    save_df_to_db(table_df, table_name=table_name,if_exists="replace")


def save_df_to_db(df, table_name, if_exists="append", ind_bool=False, dtype=None):
    """
    Save dataframe to postgres
    dtype must be specified if it uses a timestamp otherwise it will be saved as a string
    Returns:
        does not return
        saves a table in sql using engine as connection
    """
    if dtype is None:
        df.to_sql(table_name, engine, if_exists=if_exists, index=ind_bool)
    else:
        df.to_sql(table_name, engine, if_exists=if_exists, index=ind_bool, dtype=dtype)


def calculate_w4(asm_w4_df, asm_w6_df):
    """
    Function that calculates the WALLY 4 values for production and building consumption
    As instructed by ASM Terni
    Returns:
        does not return
        it saves a table in postgres called w4_calc
    """
    w4_calc = pd.DataFrame()
    # make sure the timestamp is in the correct date time format
    asm_w4_df["DateTime"] = pd.to_datetime(asm_w4_df["DateTime"])
    asm_w6_df["DateTime"] = pd.to_datetime(asm_w6_df["DateTime"])
    # set index to timestamp
    asm_w4_df.set_index("DateTime", inplace=True)
    asm_w6_df.set_index("DateTime", inplace=True)
    # resample every 5s, by default it gives the avg/mean back
    # ffill to fill NaNs with last valid input
    asm_w4_df = asm_w4_df.resample("5s").ffill()
    asm_w6_df = asm_w6_df.resample("5s").ffill()

    # the timestamp is cut into length of w6 in case w6 sensors
    # are cut off, which happens occasionally
    w4_calc["timestamp"] = asm_w4_df.index[:len(asm_w6_df)]
    w4_production = asm_w6_df["Value"]*(60 / 185)
    w4_production.fillna(0, inplace=True)
    w4_calc["w4_production"] = w4_production.values
    # element wise sum for building consumption calculation
    w4_building_consumption = [w4_value+w4_prod for w4_value, w4_prod in zip(asm_w4_df["Value"][:len(asm_w6_df)], w4_calc["w4_production"])]
    w4_calc["w4_building_consumption"] = w4_building_consumption
    save_df_to_db(
        w4_calc,
        "w4_calc",
        if_exists="replace",
    )


def get_df(folder_name, drct_file):
    """
    Get dataframe back from csv file in MinIO bucket
    Returns:
        dataframe of the file
    """
    return micl.file_to_df(
        bucket_name=BUCKET_NAME, file_name=drct_file, directory=folder_name
    )


def get_new_and_existing_dfs(df, existing_ids, metadata_name):
    """
    Check metadata based on existing ids list
    Returns:
        dataframe with new metadata
        dataframe with metadata already in metadata table
    """
    new_dfs = df.loc[~df[metadata_name].isin(existing_ids)]
    existing_dfs = df.loc[df[metadata_name].isin(existing_ids)]
    return new_dfs, existing_dfs


def merge_metadata(existing_metadata, grouped_df, metadata_name):
    """
    Merge metadata from new dataframe into existing dataframe
    Concat alone doesn't work because the list of charge_ids are stored as a list
    Thus this custom function is created
    """
    if metadata_name not in existing_metadata.keys():
        existing_metadata = existing_metadata.reset_index()

    for metadata_id in existing_metadata[metadata_name]:
        relevant_list = existing_metadata.loc[
            existing_metadata[metadata_name] == metadata_id
        ]["charge_id"].values[0]
        if metadata_id in grouped_df["charge_id"].keys():
            # delete duplicate by converting it to set
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
    return existing_metadata


def update_or_create_metadata(transformed_df, metadata_name):
    """
    Update or create metadata from dataframe
    Concat alone doesn't work because the list of charge_ids are stored as a list
    Thus this custom function is created
    """
    existing_ids, existing_metadata_from_table = get_existing_metadata(metadata_name)
    new_dfs_from_source, existing_dfs_from_source = get_new_and_existing_dfs(
        transformed_df, existing_ids, metadata_name
    )
    grouped_new_dfs_from_source = (
        new_dfs_from_source.rename(columns={"id": "charge_id"})
        .groupby(metadata_name)["charge_id"]
        .apply(list)
        .to_frame()
    )
    grouped_existing_dfs_from_source = (
        existing_dfs_from_source.rename(columns={"id": "charge_id"})
        .groupby(metadata_name)["charge_id"]
        .apply(list)
        .to_frame()
    )
    if not grouped_new_dfs_from_source.empty and not existing_metadata_from_table.empty:
        existing_metadata_from_table = pd.concat(
            [
                existing_metadata_from_table.set_index(metadata_name),
                grouped_new_dfs_from_source,
            ]
        ).sort_values(by=[metadata_name], ascending=True)
        save_df_to_db(
            existing_metadata_from_table,
            metadata_name,
            if_exists="replace",
            ind_bool=True,
            dtype={"charge_id": sa.types.ARRAY(sa.Integer)},
        )

    if (
        not grouped_existing_dfs_from_source.empty
        and not existing_metadata_from_table.empty
    ):
        existing_metadata_from_table = merge_metadata(
            existing_metadata_from_table,
            grouped_existing_dfs_from_source,
            metadata_name,
        )
        save_df_to_db(
            existing_metadata_from_table,
            metadata_name,
            if_exists="replace",
            dtype={"charge_id": sa.types.ARRAY(sa.Integer)},
        )

    if existing_metadata_from_table.empty:
        existing_metadata_from_table = grouped_new_dfs_from_source
        save_df_to_db(
            existing_metadata_from_table,
            metadata_name,
            if_exists="replace",
            ind_bool=True,
            dtype={"charge_id": sa.types.ARRAY(sa.Integer)},
        )
