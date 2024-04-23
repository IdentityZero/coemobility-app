# External Libraries
from configparser import ConfigParser
from datetime import datetime
import json
from queue import Queue
import requests
import time

import sys

from PyQt5 import uic
from PyQt5.QtCore import QResource
from PyQt5.QtGui import QFont, QMovie
from PyQt5.QtWidgets import QMainWindow, QApplication

import settings

# Internal Libraries
from parking import Entry, CoveredParking, coveredParkingNames, init_coveredParkingStatus, Parking, init_parking_status
from widgets import SettingsWidget, ParkingGridLayout
from utils import ImageManager, retrieveToken, storeToken,labelToPixMap,ImageManagerV2,timeit
from threads import WebSocketClientThread, CoveredParkingSSEThread,ManualParkingEntryThread, SetUpThread,RetrieveRfidEntriesThread

# for pyqt5 resource files
QResource.registerResource(f"{settings.STATIC_FOLDER}/static.rcc")

class LoginWindow(QMainWindow):
    def __init__(self, UI_FOLDER=None):
        super(LoginWindow,self).__init__()

        if UI_FOLDER is None:
            UI_FOLDER = settings.UI_FOLDER

        self.init_UI(UI_FOLDER)
        self.UI_FOLDER = UI_FOLDER
        self.login_url = settings.LOGIN_API

        self.password = ""
        self.init_actions()

        self.show()

        if retrieveToken() is not None:
            self.setUp()

    def init_UI(self,UI_FOLDER):
        uic.loadUi(f"{UI_FOLDER}/login 1.ui", self)
        self.setWindowTitle("Parking Operator Login")
    
    def resizeEvent(self, event):
        screen_width = self.width()

        titleFont = 9 + (screen_width-900)//200

        systemTitleFont = self.systemTitle.font()
        systemTitleFont.setPointSize(titleFont)
        self.systemTitle.setFont(systemTitleFont)

        loginTitleFont = self.loginTitle.font()
        loginTitleFont.setPointSize(titleFont+1)
        self.loginTitle.setFont(loginTitleFont)

        usernameTitle = self.usernameTitle.font()
        usernameTitle.setPointSize(titleFont+1)
        self.usernameTitle.setFont(usernameTitle)

        passwordTitle = self.passwordTitle.font()
        passwordTitle.setPointSize(titleFont+1)
        self.passwordTitle.setFont(passwordTitle)

        usernameLineEdit = self.usernameLineEdit.font()
        usernameLineEdit.setPointSize(titleFont+1)
        self.usernameLineEdit.setFont(usernameLineEdit)

        passwordLineEdit = self.passwordLineEdit.font()
        passwordLineEdit.setPointSize(titleFont+1)
        self.passwordLineEdit.setFont(usernameLineEdit)

        # Error message width
        self.loginError.setMaximumWidth(int(screen_width*7/18))

    def init_actions(self):
        self.loginButton.clicked.connect(self.login)
        # self.startButton.clicked.connect(self.openMainWindow)
    
    def login(self):
        self.loginButton.setEnabled(False)
        if not self.passwordLineEdit.text() or not self.usernameLineEdit.text():
            self.loginError.setText("Please fill in login fields")
            self.usernameLineEdit.setFocus()
            return
        
        username = self.usernameLineEdit.text()
        password = self.passwordLineEdit.text()
        
        try:
            auth_response = requests.post(self.login_url, json={"username": username, "password": password})
            if auth_response.status_code == 200:
                
                # !IMPORTANT - Change URL
                url = settings.PARKING_AUTH_API
                TOKEN = auth_response.json()['token']
                headers = {
                    "Authorization": f"Token {TOKEN}"
                }
            
                get_response = requests.get(url, headers=headers)
                isAuthorized = get_response.json()['Authorized']

                if not isAuthorized:
                    self.loginError.setText("You are not authorized to access this platform")
                    self.usernameLineEdit.setFocus()
                    self.loginButton.setEnabled(True)
                    return
                
            else:
                self.loginError.setText("Invalid Credentials")
                self.loginButton.setEnabled(True)
                return
            
        except requests.exceptions.RequestException:
            self.usernameLineEdit.setFocus()
            self.loginError.setText("No server connection\n.Check internet connection or contact admin")
            self.loginButton.setEnabled(True)
            return

        self.loginError.setText("")

        self.passwordLineEdit.setText("Successful")

        # check if user wants to keep signed in
        if self.rememberMeCheckBox.isChecked():
            storeToken(TOKEN)

        self.setUp()

    def setUp(self):
        # Move the GIF
        self.stackedWidget.setCurrentIndex(1)
        movie = QMovie(f"{settings.STATIC_FOLDER}/loading.gif")
        movie.setScaledSize(self.size())  # Set the movie size to match widget size
        movie.start()

        self.loadingGIF.setMovie(movie)
        QApplication.processEvents()

        # Images
        self.setupStatus.setText("Setting up the required files. Please wait a moment.")
        QApplication.processEvents()

        setUpOperations = [
            [(ImageManagerV2(category=settings.PROFILE_CATEGORYV2, media_folder=settings.MEDIA_FOLDER), 'start')],
            [(ImageManagerV2(category=settings.VEHICLE_CATEGORYV2, media_folder=settings.MEDIA_FOLDER), 'start')],
        ]

        self.setUpThread = SetUpThread(functions=setUpOperations)
        self.setUpThread.finished.connect(self.handle_setUpThreadFinished)
        self.setUpThread.start()

    def handle_setUpThreadFinished(self,msg):
        print(msg)
        self.setupStatus.setText("Set up finished. Starting application")
        QApplication.processEvents()

        self.setUpThread.wait()
        del self.setUpThread

        start = time.time()
        self.openMainWindow()
        end = time.time()
        print(f"Opening Main took {end - start:.6f} seconds to run.")

    def openMainWindow(self):

        self.main_window = MainWindow(self.UI_FOLDER)
        self.hide()

        self.main_window.showMaximized()

        # websocket
        self.main_window.websocket_worker = WebSocketClientThread(f"wss://{settings.DOMAIN_NAME_RAW}ws/parking_livec/")
        self.main_window.websocket_worker.data_received.connect(self.main_window.handle_web_socket_reply)
        self.main_window.websocket_worker.start()    

        #SSE

        self.main_window.loadApplication()

        self.main_window.sse_worker = CoveredParkingSSEThread()
        self.main_window.sse_worker.message.connect(self.main_window.handle_covered_parking_status)


class MainWindow(QMainWindow):
    def __init__(self, UI_FOLDER):

        super(MainWindow,self).__init__()
        
        self.setGeometry(0,0,1920,1080)
        self.setWindowTitle("Parking Management")

        self.UI_FOLDER = UI_FOLDER

        self.init_variables()
        self.get_config()
        self.init_UI(self.UI_FOLDER)
        self.init_tables()
        self.announcementLabel.hide()
        
        self.retrieveRFID = RetrieveRfidEntriesThread()
        self.retrieveRFID.rfid_data.connect(self.getRFID)
        

    def loadApplication(self):
        """
        This is where operations that take a lot of time to finish is executed
        """

        functions = [
            [coveredParkingNames],
            [init_coveredParkingStatus],
            [init_parking_status]
        ]

        self.loadApplicationThread = SetUpThread(functions=functions)
        self.loadApplicationThread.finished.connect(self.handle_loadApplication)
        self.loadApplicationThread.start()


    def handle_loadApplication(self,payload):
        if payload == "Finished":
            return
        
        payload = json.loads(payload)
        if payload['topic'] == "coveredParkingNames":
            self.coveredParkingDetails = json.loads(payload['data'])
        elif payload['topic'] == "init_coveredParkingStatus":
            self.init_status = json.loads(payload['data'])
        
        if ("coveredParkingDetails" in vars(self)) and ("init_status" in vars(self)) and (not self.hasInitializedCoveredParking):
            self.init_coveredParking()
            QApplication.processEvents()

        if payload['topic'] == "init_parking_status":
            # Final initialization
            self.init_parking(json.loads(payload['data']))
            QApplication.processEvents()
            self.init_appearance()
            QApplication.processEvents()
            self.init_actions()

            self.loadApplicationThread.wait()
            del self.loadApplicationThread
            # Start the SSE worker for automatic updating of the covered parkings
            self.sse_worker.start()
            self.retrieveRFID.start()


    def backgroundTask(self):
        # removal of entries
        timestamp = datetime.now().timestamp()
        self.entrance_entry.removeTimePeriodExpired(timestamp)

        # Parking Bay


    def init_variables(self):

        # Internal
        DEFAULT_COLUMN_WIDTH = 230
        DEFAULT_COLUMN_WIDTH_IMAGE = 80

        self.rowCount = 10

        self.DEFAULT_TABLE_HEADERS = {
            "Row Count":{ "title": "Row Count", "column_position": 0, "column_width": 0},
            "Car":{ "title": "Car", "column_position": 1, "column_width": DEFAULT_COLUMN_WIDTH_IMAGE},
            "Owner":{ "title": "Owner", "column_position": 2, "column_width": DEFAULT_COLUMN_WIDTH_IMAGE},
            "Role":{ "title": "Role", "column_position": 3, "column_width": DEFAULT_COLUMN_WIDTH},
            "Plate Number":{ "title": "Plate Number", "column_position": 4, "column_width": DEFAULT_COLUMN_WIDTH},
            "Name":{ "title": "Name", "column_position": 5, "column_width": DEFAULT_COLUMN_WIDTH+40},
            "Time":{ "title": "Time", "column_position": 6, "column_width": DEFAULT_COLUMN_WIDTH+20},
        }
        self.hasInitializedCoveredParking = False


    def init_UI(self,UI_FOLDER):
        uic.loadUi(f"{UI_FOLDER}/main.ui", self)


    def init_actions(self):
        self.rfid.returnPressed.connect(lambda: self.getRFID(int(self.rfid.text())))
        # self.rfid.returnPressed.connect(self.getRFID)
        self.settingsButton.clicked.connect(self.handleSettings)


    def init_tables(self):

        # Entrance table
        self.entrance_table.setTableHeaders(self.DEFAULT_TABLE_HEADERS)
        self.entrance_table.tableSetup(self.rowCount)

        self.exit_table.setTableHeaders(self.DEFAULT_TABLE_HEADERS)
        self.exit_table.tableSetup(self.rowCount)


    def init_appearance(self):
        TITLES_FONT = self.TITLE["FONT_FAMILY"] 
        TITLES_FONT_SIZE = int(self.TITLE["FONT_SIZE"]) 

        self.entrance_table.setHeaderFont(self.TABLE_HEADERS["FONT_FAMILY"], int(self.TABLE_HEADERS["FONT_SIZE"]))
        self.entrance_table.setFont(QFont(self.TABLE_ITEM["FONT_FAMILY"], int(self.TABLE_ITEM["FONT_SIZE"])))

        self.exit_table.setHeaderFont(self.TABLE_HEADERS["FONT_FAMILY"], int(self.TABLE_HEADERS["FONT_SIZE"]))
        self.exit_table.setFont(QFont(self.TABLE_ITEM["FONT_FAMILY"], int(self.TABLE_ITEM["FONT_SIZE"])))

        self.entrance_table_title.setFont(QFont(TITLES_FONT, TITLES_FONT_SIZE))
        self.exit_table_title.setFont(QFont(TITLES_FONT, TITLES_FONT_SIZE))

        self.covered_parking_title.setFont(QFont(TITLES_FONT, TITLES_FONT_SIZE))
        self.available_space_title.setFont(QFont(TITLES_FONT, TITLES_FONT_SIZE))


    def init_coveredParking(self):
        # Layout
        self.coveredParkings = {}

        for detail in self.coveredParkingDetails:
            self.coveredParkings[detail['area_name']] = CoveredParking(detail['area_name'], detail['max_parking'])
            self.coveredParkings[detail['area_name']].icon_hover.connect(self.handleCoveredParkingIconHover)
            self.coveredParkingMainVertical.addLayout(self.coveredParkings[detail['area_name']])
        
        for status in self.init_status:
            area = status["area"]
            id_area = status["id_area"]
            state = status["state"]
            time = status["time"]
            self.coveredParkings[area].setSpaceState(id_area,state)
        
        self.hasInitializedCoveredParking = True


    def init_parking(self, initial_parking_status):
        self.my_parking = Parking(initial_parking_status)
        status = self.my_parking.current_status
        keys = list(status.keys())
        roles = []
        categories = []

        for key in keys:
            key = key.split("_")
            role = key[0]
            category = key[1]

            if role not in roles:
                roles.append(role)
            
            if category not in categories:
                categories.append(key[1])
        
        self.my_parking_layout = ParkingGridLayout(roles,categories,status)
        self.my_parking_layout.button_pressed.connect(self.handleManualButtonPressed)
        
        self.manualParkingButtonPressedQueue = Queue()

        self.manualParkingEntryThread = ManualParkingEntryThread(self.manualParkingButtonPressedQueue)
        self.manualParkingEntryThread.start()
        self.manualParkingEntryThread.connection_status.connect(self.send_announcement)
        self.parkingLayoutFrame.setLayout(self.my_parking_layout)


    def get_config(self):
        config = ConfigParser()
        config.read(settings.CONFIG_FILE)

        # Text Related
        self.TITLE = config["TITLE"]
        self.TABLE_HEADERS = config["TABLE_HEADERS"]
        self.TABLE_ITEM = config["TABLE_ITEM"]


    # Event handlers
    def handleCoveredParkingIconHover(self,message):
        title, action = message

        if action.upper() == "HOVER":
            i = 1 # The image to appear is in the index 1 of the stacked widget
            self.availableParkingSpaceStackedWidget.setCurrentIndex(i)

            areaLocationImage = labelToPixMap(settings.STATIC_FOLDER,f"{title.upper()}.png")

            locationWidget = self.availableParkingSpaceStackedWidget.widget(i)
            locationWidget.layout().replaceWidget(self.locationImage, areaLocationImage)
            self.locationImage.deleteLater()
            self.locationImage = areaLocationImage

        else:
            self.availableParkingSpaceStackedWidget.setCurrentIndex(0)


    def handleManualButtonPressed(self,message):
        self.manualParkingButtonPressedQueue.put(message)


    def handleSettings(self):
        self.settings_window = SettingsWidget(self.UI_FOLDER)
        self.settings_window.widget_closed.connect(self.handle_settings_closed)
        self.settings_window.show()


    def handle_settings_closed(self, message):
        if message == "Appearance":
            self.get_config()
            self.init_appearance()
        elif message == "Exit":
            self.close()


    def handle_covered_parking_status(self, message):
        data = json.loads(message)
        area = data["area"]
        id_area = data["id_area"]
        state = data["state"]
        time = data["time"]
        self.coveredParkings[area].setSpaceState(id_area,state)


    def handle_web_socket_reply(self, message):
        self.retrieveRFID.start_read = True # To let sending of data to start again
        json_message = json.loads(message)
        exist = json_message['exist']
        time = json_message['time']
        status = json_message["status"]
        
        if exist:
            data = json_message['data']['vehicle_information']

            role = data["role"]
            category = data["category"]
            
            dict_data = [
                {"column_position": self.DEFAULT_TABLE_HEADERS["Row Count"]["column_position"], "type": "counter"},
                {"column_position": self.DEFAULT_TABLE_HEADERS["Car"]["column_position"], "type": "image", "value": data['vehicle_image']},
                {"column_position": self.DEFAULT_TABLE_HEADERS["Owner"]["column_position"], "type": "image", "value": data['owner_image']},
                {"column_position": self.DEFAULT_TABLE_HEADERS["Role"]["column_position"], "type": "text", "value": data['role']},
                {"column_position": self.DEFAULT_TABLE_HEADERS["Plate Number"]["column_position"], "type": "text", "value": data['vehicle_plate_number']},
                {"column_position": self.DEFAULT_TABLE_HEADERS["Time"]["column_position"], "type": "text", "value": time[:-4]},
                {"column_position": self.DEFAULT_TABLE_HEADERS["Name"]["column_position"], "type": "text", "value": data['name']},
            ]

            # self.entrance_table.setTableItem(dict_data)
            
        else:
            category = None
            dict_data = [
                {"column_position": self.DEFAULT_TABLE_HEADERS["Row Count"]["column_position"], "type": "counter"},
                {"column_position": self.DEFAULT_TABLE_HEADERS["Car"]["column_position"], "type": "image", "value": '/vehicle_pics/vehicle.png'},
                {"column_position": self.DEFAULT_TABLE_HEADERS["Owner"]["column_position"], "type": "image", "value": '/profile_pics/profile.png'},
                {"column_position": self.DEFAULT_TABLE_HEADERS["Role"]["column_position"], "type": "text", "value": "Unknown"},
                {"column_position": self.DEFAULT_TABLE_HEADERS["Plate Number"]["column_position"], "type": "text", "value": "Unknown"},
                {"column_position": self.DEFAULT_TABLE_HEADERS["Time"]["column_position"], "type": "text", "value": time[:-4]},
                {"column_position": self.DEFAULT_TABLE_HEADERS["Name"]["column_position"], "type": "text", "value": "Unknown"},
            ]
        
        if status == "ENTRANCE":
            self.entrance_table.setTableItem(dict_data)
            action = "add"
            
        else:
            self.exit_table.setTableItem(dict_data)
            action = "sub"

        if category is not None:
            set = f'{role}_{category}'
            self.my_parking_layout.setCounterValue(role,category,action)


    def send_announcement(self,message):
        self.announcementLabel.show()
        self.announcementLabel.setText(str(message))
        self.announcementLabel.update()


    # Entry point
    def getRFID(self, message):
        message = message.split(',')
        data = message[0]
        time = message[1].strip()
        print(data,time)

        if data == "":
            return
        
        # Dump to JSON
        message = {"RFID": str(data), "Time": str(time)}
        json_message = json.dumps(message)

        self.websocket_worker.send_message(json_message)

        self.rfid.clear()


if __name__ == "__main__":
    app = QApplication([sys.argv])
    main_window = MainWindow(UI_FOLDER=settings.UI_FOLDER)
    main_window.show()
    app.exec_()
