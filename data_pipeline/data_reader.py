import click
import pandas as pd
import sqlalchemy as sa
import time

from config.settings import BUCKET_NAME
from data_pipeline import utils as dp_utils
from clients.minio.minio_client import MinioClient
from threading import Thread

micl = MinioClient()


def process_emotion_data(emotion_files):
    for emotion_file in emotion_files:
        folder_name = "emotion"
        drct = emotion_file.split(" ")[0]
        metadata_name = drct.split("_")[0]
        dtype = {"timestamp": sa.types.TIMESTAMP}
        if metadata_name == "tower":
            dtype = {"plugs_state": sa.types.JSON, "timestamp": sa.types.TIMESTAMP}

        # save original states into postgres
        emotion_df = dp_utils.get_df(
            folder_name=folder_name, drct_file=emotion_file
        )
        dp_utils.save_df_to_db(df=emotion_df, table_name=drct, dtype=dtype)
        dp_utils.update_or_create_metadata(emotion_df, metadata_name)
        micl.delete_objects_in_dir(BUCKET_NAME, obj_name=emotion_file, folder_name=folder_name)


def process_emotion_parallel(drct_files):
    tower_files = [file for file in drct_files if file.startswith("tower_states")]
    vehicle_files = [file for file in drct_files if file.startswith("vehicle_states")]
    tower_thread = Thread(target=process_emotion_data, args=(tower_files,))
    vehicle_thread = Thread(target=process_emotion_data, args=(vehicle_files,))

    tower_thread.start()
    vehicle_thread.start()

    tower_thread.join()
    vehicle_thread.join()


def process_asm_data(drct_files):
    asm_w4_df = pd.DataFrame()
    asm_w6_df = pd.DataFrame()
    for asm_file in drct_files:
        folder_name = "asm"
        drct = asm_file.split(" ")[0].lower()
        tag_type = drct.split("_")[-1]

        asm_df = dp_utils.get_df(
            folder_name=folder_name, drct_file=asm_file
        )

        if tag_type == "w6":
            if asm_w6_df.empty:
                asm_w6_df = asm_df[["DateTime","Value"]]
            else:
                asm_w6_df = pd.concat([asm_w6_df, asm_df[["DateTime","Value"]]])

        if tag_type == "w4":
            if asm_w4_df.empty:
                asm_w4_df = asm_df[["DateTime","Value"]]
            else:
                asm_w4_df = pd.concat([asm_w4_df, asm_df[["DateTime","Value"]]])
        # micl.delete_objects_in_dir(BUCKET_NAME, obj_name=asm_file, folder_name=folder_name)
    dp_utils.calculate_w4(asm_w4_df, asm_w6_df)


@click.command()
def extract_and_transform_data():
    while True:
        drcts = [drct.replace("/", "") for drct in micl.list_directories(BUCKET_NAME)]
        emotion_files = []
        asm_files = []
        for drct in drcts:
            drct_files = micl.list_directory_objects(BUCKET_NAME, directory=drct)

            if not drct_files:
                time.sleep(60)
                continue

            if drct == "emotion":
                emotion_files = drct_files
            else:
                asm_files = drct_files

        if asm_files:
            asm_thread = Thread(target=process_asm_data, args=(asm_files,))
            asm_thread.start()
            asm_thread.join()

        if emotion_files:
            emotion_thread = Thread(target=process_emotion_parallel, args=(emotion_files,))
            emotion_thread.start()
            emotion_thread.join()

        db_thread = Thread(target=dp_utils.clean_db)
        db_thread.start()
        db_thread.join()


if __name__ == "__main__":
    extract_and_transform_data()
