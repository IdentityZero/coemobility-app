from PyQt5.QtWidgets import QApplication
import sys


def main():
    # Internal Libraries
    from src.MainWindow import LoginWindow

    app = QApplication([sys.argv])
    main_window = LoginWindow()
    app.exec_()

    
if __name__ == "__main__":

    main()

