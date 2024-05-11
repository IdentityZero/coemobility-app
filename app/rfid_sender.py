from datetime import datetime
import socket
import numpy as np

# TODO
# Error handling
# Check if coe registered

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
        entries_float = self.entries[1:, 1].astype(np.float64)

        filtered = self.entries[1:][(timestamp - entries_float) <= self.time_period]
        self.entries = np.concatenate((first_row, filtered), axis=0)

def rfidIsValid(data:str) -> bool:
    pass

def main(host:str, port:int, log_file_loc:str):

    REENTRY_TIME_THRESHOLD = 10
    ENTRIES = Entry(REENTRY_TIME_THRESHOLD)

    file = open(log_file_loc, mode='a')

    # Create a TCP socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("192.168.1.100",1000))
        # Connect to the remote host
        s.connect((host, port))
        counter = 0

        while True:

            data = s.recv(1024)[:-2] # remove /r/n

            if not data:
                continue

            data = data.decode()
            data = f"0000{data}"
            time = datetime.now()
            timestamp = time.timestamp()
            ENTRIES.removeTimePeriodExpired(timestamp)

            if not ENTRIES.insertEntries(data, timestamp):
                continue
            
            data_time = f"{data}, {time} \n"
            file.write(data_time)
            file.flush()

            counter += 1


if __name__ == "__main__":
    HOST_RFID_IP = '192.168.1.200'
    HOST_RFID_PORT = 2000

    ENTRY_LOG_FILE = "rfid_entries.csv"

    main(HOST_RFID_IP, HOST_RFID_PORT,ENTRY_LOG_FILE)

