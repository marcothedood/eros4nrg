import os

# MinIO Settings
MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT', 'eros-minio:9000')
MINIO_PORT = os.environ.get('MINIO_PORT', 9000)
MINIO_ACCESS_KEY = os.environ.get('MINIO_ROOT_USER', 'admin')
MINIO_SECRET_KEY = os.environ.get('MINIO_ROOT_PASSWORD', 'mylongpassword')
BUCKET_NAME = os.environ.get('MINIO_DEFAULT_BUCKETS', 'iotdata')

POSTGRES_USER = os.environ.get('POSTGRES_USER', 'admin')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'abc123')
POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'eros-postgres')
POSTGRES_PORT = os.environ.get('POSTGRES_PORT', 5432)
POSTGRES_DB = os.environ.get('POSTGRES_DB', 'data')