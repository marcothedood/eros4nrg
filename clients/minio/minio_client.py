import io
import pandas as pd

from io import BytesIO
from minio import Minio
from config.settings import MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY


class MinioClient(object):
    """This Python object performs basic ops in MinIO storage"""

    def __init__(self):
        self.client = Minio(
            endpoint=MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False,
        )

    def list_directories(self, bucket_name):
        objects = self.client.list_objects(
            bucket_name=bucket_name,
        )
        return [obj.object_name for obj in objects]

    def list_directory_objects(self, bucket_name, directory, with_prefix=False):
        """This function is used to list directory objects
        Args:
        ----
            bucket_name (str): provided bucket name
            directory (str): provided directory name
        """
        objects = self.client.list_objects(
            bucket_name=bucket_name, prefix=directory, recursive=True
        )
        if with_prefix:
            dir_files = [obj.object_name for obj in objects]
        else:
            dir_files = [
                obj.object_name.replace("{}/".format(directory), "") for obj in objects
            ]
        return dir_files

    def delete_objects_in_dir(self, bucket_name, obj_name, folder_name):
        if obj_name:
            errors = self.client.remove_object(
                bucket_name, folder_name + "/" + obj_name
            )
            if errors:
                for error in errors:
                    print(error)

    def read_csv(
        self,
        bucket_name,
        directory,
        file_name,
    ):
        """This function is used to read a csv file from MinIO as pd.DataFrame"""
        file_object = self.client.get_object(
            bucket_name=bucket_name, object_name="{}/{}".format(directory, file_name)
        )
        file_df = pd.read_csv(io.BytesIO(file_object.read()))
        return file_df

    def read_excel_(
        self,
        bucket_name,
        directory,
        file_name,
        use_cols_=None,
        sheet_name_=0,
        parse_dates_=False,
    ):
        """This function is used to read an excel file from MinIO as pd.DataFrame"""
        file_object = self.client.get_object(
            bucket_name=bucket_name, object_name="{}/{}".format(directory, file_name)
        )
        file_df = pd.read_excel(
            io.BytesIO(file_object.read()),
            usecols=use_cols_,
            parse_dates=parse_dates_,
            sheet_name=sheet_name_,
        )
        return file_df

    def file_to_df(
        self, bucket_name, directory, file_name, delimiter_=None, parse_dates_=False
    ):
        """This function is used to transform an object stored to pandas DataFrame
        Args:
        ----
            bucket_name (str): provided bucket name
            directory (str): provided directory name
            file_name (str): provided file name
        """
        file_object = self.client.get_object(
            bucket_name=bucket_name,
            object_name="{}/{}".format(directory, file_name),
        )
        file_df = pd.read_csv(
            file_object, delimiter=delimiter_, parse_dates=parse_dates_
        )
        return file_df

    def put_df_(self, bucket_name, directory, file_name, df):
        """This function is used to upload a pandas dataframe on MinIO
        Args:
        ----
            bucket_name (str): provided bucket name
            directory (str): provided directory name
            file_name (str): provided file name
            df (pd.DataFrame): provided pandas DataFrame
        """
        csv_data = df.to_csv(index=False).encode("utf-8")
        self.client.put_object(
            bucket_name=bucket_name,
            object_name="{}/{}".format(directory, file_name),
            data=BytesIO(csv_data),
            length=len(csv_data),
            content_type="application/csv",
        )

    def put_json_(self, bucket_name, directory, file_name, df):
        """This function is used to upload a pandas dataframe on MinIO
        Args:
        ----
            bucket_name (str): provided bucket name
            directory (str): provided directory name
            file_name (str): provided file name
            df (pd.DataFrame): provided pandas DataFrame
        """

        dict_data = df.to_json(orient="records").encode("utf-8")
        self.client.put_object(
            bucket_name=bucket_name,
            object_name="{}/{}".format(directory, file_name),
            data=BytesIO(dict_data),
            length=len(dict_data),
            content_type="application/json",
        )
