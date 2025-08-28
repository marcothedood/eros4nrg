import io

from datetime import datetime
from minio import Minio
from config.settings import MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY


class MinioWrapper(object):
    """This object is used to establish a connection with Minio and make some basic operations"""

    def __init__(self):
        self.client = Minio(
            endpoint=MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False,
        )

    def put_file(self, bucket_name, file_name, file):
        """This function is used to upload files to S3 bucket
        Args:
        ---
            bucket_name (str): Provided bucket name
            file_name (str): Provided file name
            file: File to upload
        """
        self.client.fput_object(
            bucket_name=bucket_name, object_name=file_name, file_path=file
        )

    def put_stream(self, bucket_name, topic_name, msg):
        """This function is used to sink kafka stream data to Minio
        Args:
        ---
            bucket_name (str): Provided bucket name
            topic_name (str): Provide topic name
            msg (json): provided json data
        """
        value_as_stream = io.BytesIO(msg)
        string_now_format = datetime.utcnow().isoformat(
            sep="-", timespec="milliseconds"
        )
        object_name = "{}/{}".format(topic_name, string_now_format)
        self.client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=value_as_stream,
            length=len(msg),
        )
