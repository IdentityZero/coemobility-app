from configparser import ConfigParser
from pathlib import Path
import os

config = ConfigParser()

BASE_DIR = Path(__file__).resolve().parent.parent # BASE DIR when settings is called main

# FOLDER LOCATIONS
UI_FOLDER = BASE_DIR / "ui" 
STATIC_FOLDER = BASE_DIR / "static"
MEDIA_FOLDER = BASE_DIR / "media"
DEFAULT_MEDIA_FOLDER = BASE_DIR / "media"

# Config Location
CONFIG_FILE = BASE_DIR / "settings.ini"
config.read(str(CONFIG_FILE))

media = config["MEDIA_FOLDER"]

if not media["location"] == "DEFAULT":
    MEDIA_FOLDER = media["location"]

# Image locations
VEHICLE_IMAGE_PATH = f"{MEDIA_FOLDER}/vehicle_pics/"
VEHICLE_CATEGORY = "vehicles"
VEHICLE_CSV = "vehicle_pics.csv"
VEHICLE_CATEGORYV2 = "vehicle_pics"

PROFILE_IMAGE_PATH = f"{MEDIA_FOLDER}/profile_pics/"
PROFILE_CATEGORY = "profiles"
PROFILE_CSV = "profile_pics.csv"

PROFILE_CATEGORYV2 = "profile_pics"

# API ENDPOINTS
# DOMAIN NAME INTO 1 VARIABLE ONLY
# DOMAIN_NAME_RAW = "192.168.55.105:8000/"
DOMAIN_NAME_RAW = "coemobility.com/"
DOMAIN_NAME = "https://" + DOMAIN_NAME_RAW
DOMAIN_NAME_ASGI = "https://" + DOMAIN_NAME_RAW 

IMAGE_CSV_DOWNLOAD_ENDPOINT = DOMAIN_NAME + "api/download-csv/"
MEDIA_DOWNLOAD_URL = DOMAIN_NAME + "media/"
LOGIN_API = DOMAIN_NAME + "api/auth/"
PARKING_AUTH_API = DOMAIN_NAME + "api/auth/parking/"

COVERED_PARKING_NAMES_ENDPOINT = DOMAIN_NAME + "api/covered_parking/areas/"
COVERED_PARKING_STATUS = DOMAIN_NAME + "api/covered_parking/"
COVERED_PARKING_SSE_ENDPOINT = DOMAIN_NAME_ASGI + "api/sse/covered_parking_status/"

PARKING_STATUS_ENDPOINT = DOMAIN_NAME + "api/parking/status/"
CREATE_MANUAL_PARKING_ENDPOINT = DOMAIN_NAME + "api/parking/manual/create/"


# SENSITIVE
# THINK OF ANOTHER WAY OF STORING THIS
# USE TO ENCRYPT TOKEN IN OS ENVIRONMENT VARIABLES
TOKEN_ENCRYPTION_KEY = b"5yJy-elXSwZRcgBL1XwjM0K9OxmCIw7kT6i8ULZ8HUM="
AWS_ACCESS_KEY_ID = 'AKIAU6GD3HR22VGD2DMN'
AWS_SECRET_ACCESS_KEY = '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'
AWS_STORAGE_BUCKET_NAME_THUMBNAILS = 'coemobility-thumbnails'
AWS_S3_REGION_NAME = 'ap-southeast-1'