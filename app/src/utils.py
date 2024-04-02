from PyQt5 import QtCore, QtGui, QtWidgets

import boto3
from botocore.exceptions import EndpointConnectionError
import csv
from cryptography.fernet import Fernet
import keyring
import os
import pandas as pd
import requests
import time

import settings

def labelToPixMap(folder_location,file_name):
    image = QtWidgets.QLabel()
    image.setText("")
    image.setScaledContents(True)

    # insert file name to QPixMap
    full_path = os.path.join(folder_location, file_name)
    pixmap = QtGui.QPixmap(f'{folder_location}/{file_name}')
    image.setPixmap(pixmap)
    return image

class ImageManager:
    """
        # Flow
        # Get csv file //
        # Compare current and new, then get distinct //
        # overwrite new.csv with distinct data //
        # execute distinct stored in new.csv
    ONLY SUPPORTS DEL AND ADD
    """

    def __init__(self,
                category=None,
                download_path=None,
                csv_current_log_file=None,
                IMAGE_CSV_DOWNLOAD_ENDPOINT=settings.IMAGE_CSV_DOWNLOAD_ENDPOINT,
                MEDIA_DOWNLOAD_URL=settings.MEDIA_DOWNLOAD_URL):

        self.IMAGE_CSV_DOWNLOAD_ENDPOINT = IMAGE_CSV_DOWNLOAD_ENDPOINT
        self.MEDIA_DOWNLOAD_URL = MEDIA_DOWNLOAD_URL

        self.category = category
        self.download_path = download_path
        self.csv_current_log_file = download_path + csv_current_log_file
        self.csv_new_path = download_path + "new.csv"
        self.headers = ["ADD","DEL"]

        self.open_csv_current_log_file = open(self.csv_current_log_file, newline='', mode='a')
        self.csv_current_log_file_writer = csv.writer(self.open_csv_current_log_file)
    
    def run(self):
        self.download_csv()
        self.overwrite_new_to_distinct_csv_execute()
    
    def download_csv(self):
        try:
            response = requests.get(self.IMAGE_CSV_DOWNLOAD_ENDPOINT, json={"category": self.category})
            response.raise_for_status()

            with open(self.csv_new_path , 'wb') as csv_file:
                csv_file.write(response.content)

        except:
            # If no connection
            pass
    
    def overwrite_new_to_distinct_csv_execute(self):
        new = pd.read_csv(self.csv_new_path)
        current = pd.read_csv(self.csv_current_log_file)

        concat = pd.concat([new,current])
        
        distinct = concat.drop_duplicates(keep=False)

        distinct.to_csv(self.csv_new_path, index=False)
        distinct.apply(self.execute_csv, axis=1)

    def find_same_actions(self, actionname,actioncolumn, dataframe):
        same_actions = dataframe[dataframe[actioncolumn] == actionname]

        return same_actions

    def find_single_actions(self,column,dataframe):
        # Get unique file names
        duplicates = dataframe[column].duplicated(keep=False)

        single_actions = dataframe[~duplicates]

        return single_actions

    def execute_csv(self,dataframe):
        """
        ONLY SUPPORTS ADD AND DEL FUNCTIONS
        """

        # get csv to execute
        # data = pd.read_csv(self.csv_new_path)
        print("Executing")
        print(dataframe['file'])
        if dataframe['action'] == "ADD":
            self.add_image(dataframe)
        else:
            self.delete_image(dataframe)
        
    def execute_command_csv(self,df):
        if df['action'] == "ADD":
            print("Adding")
        else:
            print("Deleting")

    def delete_image(self, row):
        time = row['time']
        action = row['action']
        image_filepath = row['file']

        image_filename = image_filepath.split('/')[1]

        
        local_image_path = self.download_path+str(image_filename)
        if os.path.isfile(local_image_path):
            os.remove(local_image_path)

        self.csv_current_log_file_writer.writerow([time,action,image_filepath])
        self.open_csv_current_log_file.flush()

    def add_image(self, row):
        time = row['time']
        action = row['action']
        image_filepath = row['file']
        
        image_filename = image_filepath.split('/')[1]

        local_image_path = self.download_path+str(image_filename)
        
        try:
            url = self.MEDIA_DOWNLOAD_URL+image_filepath
            response = requests.get(url)
            if response.status_code == 200:
                save_path = local_image_path
                with open(save_path, 'wb') as f:
                    f.write(response.content)
        
            self.csv_current_log_file_writer.writerow([time,action,image_filepath])
            self.open_csv_current_log_file.flush()
        except:
            pass

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
                region_name = settings.AWS_S3_REGION_NAME,
                aws_access_key_id = settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
            )
        else:
            self.s3_client = boto3_client
    
        if Bucket is None:
            self.bucket = settings.AWS_STORAGE_BUCKET_NAME_THUMBNAILS
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

def storeToken(token):
    """
    Encrypt the token using the key from settings.TOKEN_ENCRYPTION_KEY
    Then, store it using keyring

    service name = "parking_system_token,
    username = "my_token"
    password = token

    """

    # Encryption Process
    key = settings.TOKEN_ENCRYPTION_KEY
    cipher = Fernet(key)

    encrypted_token =cipher.encrypt(token.encode()).decode()

    # Storing Process
    keyring.set_password("parking_system_token", "my_token", encrypted_token)

def retrieveToken():
    """
    Retrieve the encrypted token from keyring
    Decrypt the token using the key from settings.TOKEN_ENCRYPTION_KEY

    """
    key = settings.TOKEN_ENCRYPTION_KEY
    cipher = Fernet(key)

    encrypted_token = keyring.get_password("parking_system_token", "my_token")

    try:
        decrypted_token = cipher.decrypt(encrypted_token.encode()).decode()
    except AttributeError:
        return None

    return decrypted_token

def deleteToken():
    """
    Delete the access token
    """

    try:
        keyring.delete_password("parking_system_token", "my_token")
    except keyring.errors.PasswordDeleteError:
        pass

def timeit(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Method {func.__name__} took {end_time - start_time:.6f} seconds to run.")
        return result
    return wrapper

 
if __name__ == "__main__":

    pass



