from configparser import ConfigParser
import numpy as np
import requests

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QGridLayout, QLabel, QVBoxLayout

from utils import labelToPixMap, timeit
from widgets import CoveredParkingTitle
import settings

class Entry:
    # Data means RFID Code
    def __init__(self,time_period=3):
        self.entries = np.array([[0,0]])
        self.time_period = time_period
    
    def insertEntries(self, data, datetime_timestamp):
        # Check if it exists already
        if self.entryExist(data):
            return False

        toStack = [data, datetime_timestamp]
        self.entries = np.vstack([self.entries, toStack])
        return True
    
    def entryExist(self, data):
        first_column = self.entries[:, 0]

        return np.any(first_column == data)

    def getIndex(self, data):
        first_column = self.entries[:, 0]
        indices = np.where(first_column == data)[0]

        return indices

    def removeTimePeriodExpired(self, timestamp):
        # to preserve 0,0
        if len(self.entries) == 1:
            return

        first_row = self.entries[:1]

        filtered = self.entries[1:][(timestamp - self.entries[1:, 1]) <= self.time_period]
        self.entries = np.concatenate((first_row, filtered), axis=0)

class Parking:
    def __init__(self, parking_status):
        self.my_parking = {}
        self.init_my_parking(parking_status)
        self.current_status = parking_status
    
    # def init_parking_status(self):
        # url = settings.PARKING_STATUS_ENDPOINT

        # response = requests.get(url)
        # data = response.json()
        # self.current_status = data

        # return data

    def init_my_parking(self,status):
        # Change

        for key, value in status.items():
            self.my_parking[key] = {
                'current': value['current'],
                'max': 100,
            }
            
    def refreshDisplay(self, set,label=None):
        available = self.my_parking[set]['max'] -self.my_parking[set]['current']
        if label is not None:
            label.setText(str(available))
            return
        
        return
        
    def insertParking(self, role,vehicle, action,label=None):
        set = f'{role}_{vehicle}'

        if action == "ENTRANCE":
            self.my_parking[set]['current'] +=1
        else: 
            self.my_parking[set]['current'] -=1

        available = self.my_parking[set]['max'] -self.my_parking[set]['current']
        if label is not None:
            label.setText(str(available))
            return
        
        return available

def init_parking_status():
    url = settings.PARKING_STATUS_ENDPOINT

    response = requests.get(url)
    data = response.json()

    return data

def coveredParkingNames():
    response = requests.get(settings.COVERED_PARKING_NAMES_ENDPOINT)

    if response.status_code == 200:
        details = response.json()

        # Download the images
        # Should separate this function but nvm for now

        # for detail in details:
        #     url = detail['area_image']
        #     fileExtension = url.split(".")[1]

        #     area_name = detail['area_name']
        #     save_path = f"{settings.STATIC_FOLDER}\{area_name.upper()}.{fileExtension}"
        #     # TODO

        #     response = requests.get(url)
        #     if response.status_code == 200:
        #         with open(save_path, 'wb') as f:
        #             f.write(response.content)

        return details['results']
    
    return []

def init_coveredParkingStatus():
    url = settings.COVERED_PARKING_STATUS

    response = requests.get(url)
    data = response.json()

    return data

class CoveredParking(QGridLayout):
    icon_hover = pyqtSignal(list)
    def __init__(self, title, size, limit_per_row=5):
        super(CoveredParking, self).__init__()

        self.STATIC_FOLDER = settings.STATIC_FOLDER

        self.titleName = title
        self.title = CoveredParkingTitle(title)
        self.title.icon_hover.connect(self.handle_icon_hover)
        self.innerLayout = QGridLayout()
        self.park_space = []

        self.addWidget(self.title,0,0,1,5)

        self.setRows(size, limit_per_row)
        self.setRowStretch(1,2)
    
    def setRows(self, size, limit_per_row):

        for i in range(size):
            row = (i // limit_per_row) + 1 # Row 0 is for the title
            column = i % limit_per_row

            image = CoveredParkingSpace(i+1, True)
            self.park_space.append(image)

            self.addLayout(image, row,column)
        
    def setSpaceState(self, id, state):
        space = self.park_space[id-1]
        space.setIcon(not state) # Fix this later, not because True means its occupied so we should inverse 

    def handle_icon_hover(self,message):
        payload = [self.titleName, message]
        self.icon_hover.emit(payload)
    
class CoveredParkingSpace(QVBoxLayout):
    def __init__(self, id, availability_state = False):
        super(CoveredParkingSpace, self).__init__()

        self.STATIC_FOLDER = settings.STATIC_FOLDER
        self.get_config()
        self.setTitle(id)
        self.addWidget(self.title, alignment=Qt.AlignHCenter)

        self.icon = ""

        self.setIcon(availability_state)
    
    def get_config(self):
        config = ConfigParser()
        config.read(settings.CONFIG_FILE)

        self.TABLE_ITEM = config["TABLE_ITEM"]

    def setTitle(self, id):
        self.title = QLabel(str(id))
        self.title.setStyleSheet("background:None;")
        self.setTitleFont()
    
    def setTitleFont(self):
        self.title.setFont(QFont(self.TABLE_ITEM["FONT_FAMILY"], int(self.TABLE_ITEM["FONT_SIZE"])))
    
    def setIcon(self, availability_state):

        if not self.icon == "":
            self.removeWidget(self.icon)

        if availability_state:
            self.icon = labelToPixMap(self.STATIC_FOLDER, "available_sign.png")
        else:
            self.icon = labelToPixMap(self.STATIC_FOLDER, "unavailable_sign.png")
        
        self.addWidget(self.icon)

if __name__ == "__main__":
    val = coveredParkingNames()
    print(val)
