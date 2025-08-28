import os

# MinIO Settings
MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT', 'localhost:9000')
MINIO_PORT = os.environ.get('MINIO_PORT', 9000)
MINIO_ACCESS_KEY = os.environ.get('MINIO_ROOT_USER', 'admin')
MINIO_SECRET_KEY = os.environ.get('MINIO_ROOT_PASSWORD', 'eros4nrg')
BUCKET_NAME = os.environ.get('MINIO_DEFAULT_BUCKETS', 'iotdata')

POSTGRES_USER = os.environ.get('POSTGRES_USER', 'admin')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'eros4nrg')
POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.environ.get('POSTGRES_PORT', 5433)
POSTGRES_DB = os.environ.get('POSTGRES_DB', 'cleandata')

MSSQL_SERVER = os.environ.get('PYMSSQL_SERVER', '185.131.248.18')
MSSQL_DB = os.environ.get('PYMSSQL_SERVER', 'Runtime')
MSSQL_PORT = os.environ.get('PYMSSQL_SERVER', '1433')
MSSQL_USERNAME = os.environ.get('PYMSSQL_USERNAME', 'Read_Only_MARTEL_NEMO')
MSSQL_PASSWORD = os.environ.get('PYMSSQL_PASSWORD', 'NEMO2024')