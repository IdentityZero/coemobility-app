from unicodedata import category
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic

from configparser import ConfigParser
import settings
import utils

# Put all appearance related tools to the table
class CustomTableWidget(QtWidgets.QTableWidget):
    DEFAULT_FONT_FAMILY = "Arial"
    DEFAULT_HEADER_FONT_SIZE = 15

    def __init__(self, parent=None):
        super().__init__(parent)

        self.init_variables()
        self.setHeaderFont(self.DEFAULT_FONT_FAMILY, self.DEFAULT_HEADER_FONT_SIZE)
    
    def tableSetup(self,rowCount):
        self.rowCount = rowCount
        self.setRowCount(self.rowCount)
        
        # Image locations
        self.image_location = settings.MEDIA_FOLDER

    def init_variables(self):
        self.table_counter = 0

    def setTableHeaders(self,headers):
        """
        The function will accept a dictionary following this format:
            headers = { "Key1":{ "title": "Header Title1","column_position": 0,"column_width": 10},
            "Key2":{ "title": "Header Title2","column_position": 1,"column_width": 100},
            }
        """

        self.setColumnCount(len(headers))

        for key,value in headers.items():
            # Format
            # self.setHorizontalHeaderItem(column_position, QtWidgets.QTableWidgetItem(title))
            # self.setColumnWidth(column_position, width)

            # Preserved the key for future usage

            self.setHorizontalHeaderItem(value['column_position'], QtWidgets.QTableWidgetItem(value['title']))
            self.setColumnWidth(value['column_position'], value['column_width'])
    
    def setHeaderFont(self, font_family, font_size):
        font = QtGui.QFont(font_family, font_size)
        self.horizontalHeader().setFont(font)

    def setTableItem(self, items):
        """
        items will accept a list of dictionaries with the following format:
        items = {
        {"type": "text" ,"column_position": position1, "value": "String Value"},
        {"type": "counter" ,"column_position": position2, "value": IntegerValue},
        }

        The value of will be the following:
            "text" - String format
            "image" - 
            "counter" - Integer

        It is recommended to use column_position based on headers
            
        """
        for item in items:
            # print(item)
            if item['type'] == "counter":
                counter = QtWidgets.QTableWidgetItem()
                counter.setData(QtCore.Qt.EditRole, self.table_counter)
                self.setItem(self.rowCount-1, item['column_position'], counter)

            elif item['type'] == "image":
                image = utils.labelToPixMap(self.image_location,item['value'])
                self.setCellWidget(self.rowCount-1, item['column_position'], image)

            elif item['type'] == "text":
                text = QtWidgets.QTableWidgetItem(item['value'])
                text.setTextAlignment(QtCore.Qt.AlignCenter)
                self.setItem(self.rowCount-1, item['column_position'], text)

                
            else:
                self.setItem(self.rowCount-1, item['column_position'], QtWidgets.QTableWidgetItem("Bad Type"))
        
        self.sortTable()
        self.table_counter += 1
        
    def sortTable(self):
        self.sortItems(0, QtCore.Qt.DescendingOrder)

class SettingsWidget(QtWidgets.QWidget):
    widget_closed = QtCore.pyqtSignal(str)

    def __init__(self,UI_FOLDER):
        super(SettingsWidget, self).__init__()

        self.init_UI(UI_FOLDER)
        self.setFixedSize(830, 700)
        self.init_actions()

        self.init_config()
        
        self.init_widgets()

    def init_UI(self,UI_FOLDER):
        uic.loadUi(f"{UI_FOLDER}/settings.ui", self)
        self.setWindowTitle("Settings")

    def init_config(self):
        self.config = ConfigParser()
        self.config.read(settings.CONFIG_FILE)

        self.TITLE = self.config["TITLE"]
        self.TABLE_HEADERS = self.config["TABLE_HEADERS"]
        self.TABLE_ITEM = self.config["TABLE_ITEM"]
    
    def init_widgets(self):
        self.init_appearance()
        self.init_files()
    
    def init_actions(self):
        self.appearanceSaveButton.clicked.connect(self.handleAppearanceSave)
        self.openFolder.clicked.connect(self.files_chooseMediaFolder)
        self.filesSaveButton.clicked.connect(self.handleFilesSave)
        self.logoutButton.clicked.connect(self.handleExit)
        self.logoutandSOButton.clicked.connect(lambda: self.handleExit(True))

    def files_chooseMediaFolder(self):
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(self,"Select Folder", str(settings.MEDIA_FOLDER))
        if folder_path:
            self.folderLocationLineEdit.setText(folder_path)

    def init_files(self):
        self.folderLocationLineEdit.setText(str(settings.MEDIA_FOLDER))

    def init_appearance(self):
        # Title
        config_title_font = QtGui.QFont(self.TITLE["FONT_FAMILY"])
        self.titleFontCB.setCurrentFont(config_title_font)
        self.titleFontSizeSB.setValue(int(self.TITLE["FONT_SIZE"]))

        # Tables
        config_header_font = QtGui.QFont(self.TABLE_HEADERS["FONT_FAMILY"])
        self.tableHeadersFontCB.setCurrentFont(config_header_font)
        self.tableHeadersFontSizeSB.setValue(int(self.TABLE_HEADERS["FONT_SIZE"]))

        config_table_item_font = QtGui.QFont(self.TABLE_ITEM["FONT_FAMILY"])
        self.tableItemFontCB.setCurrentFont(config_table_item_font)
        self.tableItemFontSizeSB.setValue(int(self.TABLE_ITEM["FONT_SIZE"]))


    # Closing event handlers
    def handleFilesSave(self):
        changed_folderLocationLineEdit = self.folderLocationLineEdit.text()

        settings_default = str(settings.DEFAULT_MEDIA_FOLDER).replace('\\','/')
        if changed_folderLocationLineEdit == settings_default:
            self.config["MEDIA_FOLDER"]["location"] = "DEFAULT"
            print("Default")
        else:
            self.config["MEDIA_FOLDER"]["location"] = changed_folderLocationLineEdit

        with open(settings.CONFIG_FILE, 'w') as configfile:
            self.config.write(configfile)
        
        self.close("Files")

    def handleAppearanceSave(self):
        changed_titleFontCB = self.titleFontCB.currentText()
        changed_titleFontSizeSB = self.titleFontSizeSB.value()
        self.config["TITLE"]["FONT_FAMILY"] = changed_titleFontCB
        self.config["TITLE"]["FONT_SIZE"] = str(changed_titleFontSizeSB)

        changed_tableHeadersFontCB = self.tableHeadersFontCB.currentText()
        changed_tableHeadersFontSizeSB = self.tableHeadersFontSizeSB.value()
        self.config["TABLE_HEADERS"]["FONT_FAMILY"] = changed_tableHeadersFontCB
        self.config["TABLE_HEADERS"]["FONT_SIZE"] = str(changed_tableHeadersFontSizeSB)

        changed_tableItemFontCB = self.tableItemFontCB.currentText()
        changed_tableItemFontSizeSB = self.tableItemFontSizeSB.value()
        self.config["TABLE_ITEM"]["FONT_FAMILY"] = changed_tableItemFontCB
        self.config["TABLE_ITEM"]["FONT_SIZE"] = str(changed_tableItemFontSizeSB)

        with open(settings.CONFIG_FILE, 'w') as configfile:
            self.config.write(configfile)
        
        self.close("Appearance")
    
    def handleExit(self, signout=False):
        if signout:
            utils.deleteToken()

        self.close("Exit")

    def close(self, page):
        self.widget_closed.emit(page)
        super().close()

class CustomAddSubButton(QtWidgets.QPushButton):
    """
    CustomAddSubButton("add") or 
    CustomAddSubButton("sub")
    """
    def __init__(self, add_sub):
        super(CustomAddSubButton,self).__init__()
        self.DEFAULT_SIZE = 20 # 20px

        self.initIcon(add_sub)
        self.setMinimumSize(QtCore.QSize(self.DEFAULT_SIZE+10, self.DEFAULT_SIZE+10))
        self.setCustomStyleSheet()

        self.setCursor(QtCore.Qt.PointingHandCursor)

        self.setMouseTracking(True)
        
    def initIcon(self, add_sub):
        if add_sub == "add":
            icon = QtGui.QIcon(f"{settings.STATIC_FOLDER}/add button.png")
        else: 
            icon = QtGui.QIcon(f"{settings.STATIC_FOLDER}/subtract button.png")
        self.setIcon(icon)
        self.setDefaultIconSize()
    
    def setCustomStyleSheet(self):
        self.setStyleSheet("""
            QPushButton{
            background-color:rgba(230,223,223,1);
            border-radius:15px;}

            QPushButton:hover{
            background-color:#C9B6B6;
            }

            QPushButton:pressed{
            background-color:#A39595 ;
            } """)

    def increaseIconSize(self):
        self.setIconSize(QtCore.QSize(self.DEFAULT_SIZE+10, self.DEFAULT_SIZE+10))

    def setDefaultIconSize(self):
        self.setIconSize(QtCore.QSize(self.DEFAULT_SIZE, self.DEFAULT_SIZE))

    def enterEvent(self,event):
        self.increaseIconSize()
    
    def leaveEvent(self,event):
        self.setDefaultIconSize()

class ParkingCounterWidget(QtWidgets.QFrame):
    """
    when + is pressed, the value decreases
    This means that a vehicle came inside
    and vice versa
    """

    button_pressed = QtCore.pyqtSignal(list)

    def __init__(self, role,vehicle_category,parking_value):
        super(ParkingCounterWidget, self).__init__()

        # Create a layout for the frame
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.role = role
        self.vehicle_category = vehicle_category
        
        # Add widgets to the layout
        self.initWidgets(parking_value)
        self.initActions()
        
        # Set the layout for the frame
        self.setLayout(self.layout)
    
    def initWidgets(self,parking_value):
        # Add
        addButtonLayout = QtWidgets.QHBoxLayout()
        addButtonLayout.setContentsMargins(0,0,0,0)
        self.addButton = CustomAddSubButton("add")
        addButtonLayout.addWidget(self.addButton)

        # Label
        valueLayout = QtWidgets.QHBoxLayout()
        self.value = QtWidgets.QLabel(parking_value)
        self.styleLabel(self.value)
        valueLayout.addWidget(self.value)

        # Subtract
        subButtonLayout = QtWidgets.QHBoxLayout()
        subButtonLayout.setContentsMargins(0,0,0,0)
        self.subButton = CustomAddSubButton("sub")
        subButtonLayout.addWidget(self.subButton)

        # Adding the layouts
        self.layout.addLayout(addButtonLayout)
        self.layout.addLayout(valueLayout)
        self.layout.addLayout(subButtonLayout)

    def initActions(self):
        self.addButton.pressed.connect(lambda: self.setValue("add", buttonPressed=True))
        self.subButton.pressed.connect(lambda: self.setValue("sub", buttonPressed=True))

    def styleLabel(self, label):
        label.setAlignment(QtCore.Qt.AlignCenter)

        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(20)
        font.setWeight(QtGui.QFont.Bold)

        label.setFont(font)

    def setValue(self, action, buttonPressed=False):
        value = int(self.value.text())
        if action == "add":
            value -= 1
            if buttonPressed:
                self.button_pressed.emit([self.role, self.vehicle_category, "ADD"])
        elif action == "sub":
            value += 1
            if buttonPressed:
                self.button_pressed.emit([self.role, self.vehicle_category, "SUB"])
        
        self.value.setText(str(value))

class ParkingGridLayout(QtWidgets.QGridLayout):
    button_pressed = QtCore.pyqtSignal(list)

    def __init__(self, role_list,category_list, gridDetail_dict=None):
        super(ParkingGridLayout, self).__init__()
        self.role_list = role_list
        self.category_list = category_list

        self.init_grid(role_list,category_list)

        if gridDetail_dict is not None:
            self.counters = {}
            self.init_gridDetails(gridDetail_dict)
    
    def init_grid(self,role_list, category_list):
        # Leave 0,0 empty
        # +1 to all iterators to leave 0 empty
        for i,role in enumerate(role_list):
            label = QtWidgets.QLabel(role)
            self.styleLabel(label)
            self.addWidget(label, 0, i+1)

        for i,category in enumerate(category_list):
            label = QtWidgets.QLabel(category)
            self.styleLabel(label)
            self.addWidget(label, i+1,0)

    def init_gridDetails(self, gridDetail_dict):
        for key, value in gridDetail_dict.items():
            # Separate keys
            keys = key.split("_")

            role = keys[0]
            category = keys[1]

            # +1 to all indexes
            role_i = self.role_list.index(role) + 1
            category_i = self.category_list.index(category) + 1

            try:
                value = value['available']
            except KeyError:
                value = 100
            
            counter = ParkingCounterWidget(role,category,str(value))
            counter.button_pressed.connect(self.handleButtonPressed)
            self.addWidget(counter,category_i,role_i,)

            # Add to list of counters
            keyword = f"{role}_{category}"
            self.counters[keyword] = counter
    
    def setCounterValue(self, role,vehicle_category,action):
        keyword = f"{role}_{vehicle_category}"
        counter = self.counters[keyword]

        counter.setValue(action)

    def styleLabel(self, label):
        label.setAlignment(QtCore.Qt.AlignCenter)

        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(14)
        font.setWeight(QtGui.QFont.Bold)

        label.setFont(font)

    def handleButtonPressed(self, message):
        self.button_pressed.emit(message)

class CoveredParkingTitle(QtWidgets.QFrame):
    icon_hover = QtCore.pyqtSignal(str)
    def __init__(self,title):
        super(CoveredParkingTitle, self).__init__()
        self.setMaximumHeight(70)

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.init_widgets(title)
        self.setCustomStylesheet()

        self.shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QtGui.QColor(0, 0, 0, 150))
        self.shadow.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow)
        
        self.setLayout(self.layout)

    def init_widgets(self, title):
        
        # For title
        label = QtWidgets.QLabel(str(title))
        label.setAlignment(QtCore.Qt.AlignRight  | QtCore.Qt.AlignVCenter)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        font.setWeight(QtGui.QFont.Bold)
        label.setFont(font)
        label.setStyleSheet("background:none;")
        
        # For magnifying icon
        # Frame
        buttonFrame = QtWidgets.QFrame()
        buttonFrame.setStyleSheet("background:none;")
        buttonFrameLayout = QtWidgets.QHBoxLayout()
        buttonFrameLayout.setContentsMargins(0,0,0,0)
        buttonFrameLayout.setAlignment(QtCore.Qt.AlignLeft)
        buttonFrame.setLayout(buttonFrameLayout)

        # Button
        button = QtWidgets.QPushButton()
        button.setMaximumSize(30, 30)
        icon = QtGui.QIcon(f"{settings.STATIC_FOLDER}/magnifiying glass.png")
        button.setCursor(QtCore.Qt.PointingHandCursor)
        button.setIcon(icon)
        button.setStyleSheet("background-color: rgba(171,164,155,0.8); border:None;")

        button.setMouseTracking(True)
        button.enterEvent = lambda event: self.on_hover("Hover")
        button.leaveEvent  = lambda event: self.on_hover("Leave")

        buttonFrameLayout.addWidget(button)

        self.layout.addWidget(label, stretch=1)
        self.layout.addWidget(buttonFrame, stretch=1)

    def setCustomStylesheet(self):
        self.setStyleSheet("""
            QFrame{
                background-color: rgba(171,164,155,0.8);
                }
        """)
    
    def on_hover(self, event):
        self.icon_hover.emit(event)

class TrialFrame(QtWidgets.QFrame):
    def __init__(self):
        super(TrialFrame,self).__init__()
        
        layout = QtWidgets.QVBoxLayout()
        label = CoveredParkingTitle("West")

        layout.addWidget(label)

        self.setLayout(layout)

        

if __name__ == '__main__':
    # For testing widgets
    import sys
    app = QtWidgets.QApplication(sys.argv)
    widget = TrialFrame()
    widget.show()
    sys.exit(app.exec_())