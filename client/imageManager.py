import boto3
from botocore.exceptions import EndpointConnectionError
import csv
import os
import pandas as pd
from pathlib import Path
import time

MEDIA_FOLDER = Path(__file__).resolve().parent / 'media'

AWS_ACCESS_KEY_ID = 'AKIAU6GD3HR22VGD2DMN'
AWS_SECRET_ACCESS_KEY = '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'
AWS_STORAGE_BUCKET_NAME_THUMBNAILS = 'coemobility-thumbnails'
AWS_S3_REGION_NAME = 'ap-southeast-1'

class ImageManagerV2:
    """
    This class needs a boto3 client
    Made for AWS only to get resources from s3.
    If none is given, the default was created by the team.
    Which may or may not exist anymore.

    A category is needed to differentiate resources
    The category will be a folder that exists both in the local file path and S3 bucket
    Category should be of the same name.
    Add Prefix for the s3 client if needed

    To test if the right credentials are placed.
    Using the listAllResourcesInS3Bucket method.
    """
    def __init__(self, category, media_folder, boto3_client=None, Bucket=None, Prefix=None):
        self.category = category
        self.media_folder = media_folder
        self.category_folder = str(media_folder) + '/' +category

        if boto3_client is None:
            self.s3_client = boto3.client(
                's3',
                region_name = AWS_S3_REGION_NAME,
                aws_access_key_id = AWS_ACCESS_KEY_ID,
                aws_secret_access_key = AWS_SECRET_ACCESS_KEY
            )
        else:
            self.s3_client = boto3_client
    
        if Bucket is None:
            self.bucket = AWS_STORAGE_BUCKET_NAME_THUMBNAILS
        else:
            self.bucket = Bucket

        if Prefix is None:
            self.prefix = ''
        else:
            self.prefix = Prefix

    def start(self):
        listS3BucketStatus = self.listAllResourcesInS3Bucket()
        if listS3BucketStatus != 0:
            return 2

        previousList = self.retrievePreviousResourcesList()

        downloadResourcesStatus = self.downloadNewResources(previousList)
        if downloadResourcesStatus != 0:
            return 3
        
        return 0

    def listAllResourcesInS3Bucket(self):
        """
        This will create a csv file inside the download path called <category>_current_list.csv
        """
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket, Prefix=self.prefix)
                    
            with open(str(self.category_folder) +f'/{self.category}_current_list.csv', mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['filename', 'date'])
            
                if 'Contents' in response:
                    for idx, obj in enumerate(response['Contents']):
                        if obj['Size'] == 0:
                            continue
                        writer.writerow([obj['Key'], obj['LastModified']])
            
            file.close()

            return 0

        except EndpointConnectionError:
            return 1

    def retrievePreviousResourcesList(self):
        """
        Look for the previous records
        Create one if none
        """
        previous_path = f"{self.category_folder}/{self.category}_previous_list.csv"
        if not os.path.exists(previous_path):
            with open(previous_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['filename', 'date'])
            file.close()

        previous = pd.read_csv(f"{self.category_folder}/{self.category}_previous_list.csv")

        return previous

    def downloadNewResources(self, previousResourcesList):
        newList = pd.read_csv(f"{self.category_folder}/{self.category}_current_list.csv")
        all = pd.concat([newList,previousResourcesList])
        distinct = all.drop_duplicates(keep=False)

        # differentiate if its new or its gone

        # if distinct is not in new, its gone then DELETE
        concat_distinct_new = pd.concat([distinct, newList, newList])
        toDelete = concat_distinct_new.drop_duplicates(keep=False)
        self.deleteResourceSequence(toDelete)

        # if distinct is not in previous, its new then DOWNLOAD
        concat_distinct_prev = pd.concat([distinct, previousResourcesList,previousResourcesList])
        toDownload = concat_distinct_prev.drop_duplicates(keep=False)
        return self.downloadResourceSequence(toDownload)

    def downloadResourceSequence(self, todownload_df):
        retry_download = 0
        file = open(f"{self.category_folder}/{self.category}_previous_list.csv", mode='a', newline='')
        writer = csv.writer(file)

        for row in todownload_df.itertuples():
            try:
                local_file_path = os.path.join(self.media_folder, row.filename)
                self.s3_client.download_file(self.bucket, row.filename, local_file_path)
                writer.writerow([row.filename, row.date])
            except EndpointConnectionError:
                retry_download += 1
                if retry_download == 3:
                    file.close()
                    return 1
                continue
        
        file.close()
        return 0

    def deleteResourceSequence(self,toDelete_df):
        rows_to_delete = []
        previous_list_csv = f"{self.category_folder}/{self.category}_previous_list.csv"
        for index, row in toDelete_df.iterrows():
            filename = str(self.category_folder) + "/"+ row.filename

            rows_to_delete.append(index + 1) # +1 for the headers
            if os.path.exists(filename):
                os.remove()
        
        # Delete remove log file of deleted images
        with open(previous_list_csv, mode='r') as file:
            csv_reader = csv.reader(file)
            rows = list(csv_reader)

        rows = [row for index, row in enumerate(rows) if index not in rows_to_delete]

        with open(previous_list_csv, mode='w', newline='') as file:
            csv_writer = csv.writer(file)
            csv_writer.writerows(rows)
        
        file.close()

    def imageManagerV2ExceptionsMap(self):
        """
        return key - Problem
        0 - Success
        1 - EndpointConnectionError
        2 - Getting bucket list error
        3 - Downloading resources error
        """
        pass
     

if __name__ == "__main__":
    category = 'profile_pics'

    download_path = MEDIA_FOLDER
    obj = ImageManagerV2(category, download_path, Prefix=category)
    obj.start()


