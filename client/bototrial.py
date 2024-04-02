import boto3
from pathlib import Path
import os
import time

from settings import BASE_DIR

AWS_ACCESS_KEY_ID = 'AKIAU6GD3HR22VGD2DMN'
AWS_SECRET_ACCESS_KEY = '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'
AWS_STORAGE_BUCKET_NAME_THUMBNAILS = 'coemobility-thumbnails'
AWS_S3_REGION_NAME = 'ap-southeast-1'

s3_client = boto3.client(
    's3',
    region_name = AWS_S3_REGION_NAME,
    aws_access_key_id = AWS_ACCESS_KEY_ID,
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY
)

BASE_DIR = Path(__file__).resolve().parent # BASE DIR when settings is called main

local_dir = BASE_DIR / "media"

# response = s3_client.list_objects_v2(Bucket=AWS_STORAGE_BUCKET_NAME_THUMBNAILS, Prefix='profile_pics/')
response = s3_client.list_objects_v2(Bucket=AWS_STORAGE_BUCKET_NAME_THUMBNAILS, Prefix='')


# # Print object names
if 'Contents' in response:
    for idx, obj in enumerate(response['Contents']):
        if obj['Size'] == 0:
            continue
        key = obj['Key']
        local_file_path = os.path.join(local_dir, key)
        # Download
        s3_client.download_file(AWS_STORAGE_BUCKET_NAME_THUMBNAILS, key, local_file_path)
        # a = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        break
