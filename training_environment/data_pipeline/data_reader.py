import click
import pandas as pd
import time
import json
import os
from config.settings import BUCKET_NAME
from data_pipeline import utils as dp_utils
from clients.minio.minio_client import MinioClient
from threading import Thread

micl = MinioClient()

dp_utils.ensure_w4_schema()

def _normalize_emotion_df(df: pd.DataFrame, metadata_name: str) -> pd.DataFrame:
    """
    Normalizza i tipi per evitare che Pandas salvi TEXT.
    """
    df = df.copy()

    # timestamp
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # boolean
    if "in_charge" in df.columns:
        if df["in_charge"].dtype == object:
            df["in_charge"] = (
                df["in_charge"].astype(str).str.lower()
                .map({"true": True, "t": True, "1": True, "false": False, "f": False, "0": False})
            )

    for col in ["battery_percentage", "velocity", "km_tot", "kwh_charged"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["id", "charges_count", "vehicle", "tower"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    # tower: JSON
    if metadata_name == "tower" and "plugs_state" in df.columns:
        ps = df["plugs_state"]
        if ps.dtype == object:
            def _maybe_json(v):
                if isinstance(v, (dict, list)) or pd.isna(v):
                    return v
                if isinstance(v, str):
                    try:
                        return json.loads(v)
                    except Exception:
                        return v
                return v
            df["plugs_state"] = ps.apply(_maybe_json)

    return df

def process_emotion_data(emotion_files):
    for emotion_file in emotion_files:
        folder_name = "emotion"
        name = os.path.splitext(os.path.basename(emotion_file))[0]  # "vehicle_states_2025-..." -> "vehicle_states_2025-..."

        if name.startswith("vehicle_states"):
            table_name = "vehicle_states"; metadata_name = "vehicle"
        elif name.startswith("tower_states"):
            table_name = "tower_states";   metadata_name = "tower"
        else:
            continue

        emotion_df = dp_utils.get_df(folder_name=folder_name, drct_file=emotion_file)
        emotion_df = _normalize_emotion_df(emotion_df, metadata_name)

        print(f"[EMOTION] saving {len(emotion_df)} rows -> {table_name}")

        dp_utils.save_df_to_db(df=emotion_df, table_name=table_name)
        dp_utils.update_or_create_metadata(emotion_df, metadata_name)
        micl.delete_objects_in_dir(BUCKET_NAME, obj_name=emotion_file, folder_name=folder_name)


def process_emotion_parallel(drct_files):
    def base(f):
        return os.path.splitext(os.path.basename(f))[0]  # senza estensione

    tower_files   = [f for f in drct_files if base(f).startswith("tower_states")]
    vehicle_files = [f for f in drct_files if base(f).startswith("vehicle_states")]
    tower_thread = Thread(target=process_emotion_data, args=(tower_files,))
    vehicle_thread = Thread(target=process_emotion_data, args=(vehicle_files,))
    tower_thread.start(); vehicle_thread.start()
    tower_thread.join();  vehicle_thread.join()

def process_asm_data(drct_files):
    asm_w4_df = pd.DataFrame()
    asm_w6_df = pd.DataFrame()
    for asm_file in drct_files:
        folder_name = "asm"
        drct = asm_file.split(" ")[0].lower()
        tag_type = drct.split("_")[-1]

        asm_df = dp_utils.get_df(folder_name=folder_name, drct_file=asm_file)

        if tag_type == "w6":
            part = asm_df[["DateTime","Value"]]
            asm_w6_df = part if asm_w6_df.empty else pd.concat([asm_w6_df, part])
        elif tag_type == "w4":
            part = asm_df[["DateTime","Value"]]
            asm_w4_df = part if asm_w4_df.empty else pd.concat([asm_w4_df, part])

        # micl.delete_objects_in_dir(BUCKET_NAME, obj_name=asm_file, folder_name=folder_name)

    if not asm_w4_df.empty and not asm_w6_df.empty:
        dp_utils.calculate_w4(asm_w4_df, asm_w6_df)

@click.command()
def extract_and_transform_data():
    while True:
        drcts = [drct.replace("/", "") for drct in micl.list_directories(BUCKET_NAME)]
        emotion_files, asm_files = [], []

        for drct in drcts:
            drct_files = micl.list_directory_objects(BUCKET_NAME, directory=drct) or []
            if drct == "emotion":
                emotion_files = drct_files
            elif drct == "asm":
                asm_files = drct_files

        if not emotion_files and not asm_files:
            time.sleep(60)
            continue

        if asm_files:
            asm_thread = Thread(target=process_asm_data, args=(asm_files,))
            asm_thread.start(); asm_thread.join()

        if emotion_files:
            emotion_thread = Thread(target=process_emotion_parallel, args=(emotion_files,))
            emotion_thread.start(); emotion_thread.join()

        db_thread = Thread(target=dp_utils.clean_db)
        db_thread.start(); db_thread.join()

if __name__ == "__main__":
    extract_and_transform_data()
