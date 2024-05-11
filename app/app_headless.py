import asyncio
import csv
import websockets
from datetime import datetime
import json
import time

def getFirstRow(csv_file_path):
    with open(csv_file_path, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            print("Sent first row")
            return row

def removeFirstRow(csv_file_path):
    with open(csv_file_path, 'r') as file:
        lines = file.readlines() # Read contents
        lines.pop(0) # Remove the first line

        with open(csv_file_path, 'w') as file:
            file.writelines(lines) # Rewrite

async def connect_to_websocket_server():
    uri = "wss://coemobility.com/ws/parking_livec/"
    csv_path = "rfid_entries.csv"
    async with websockets.connect(uri) as websocket:
        while True:
            # Get user input
            first_row = getFirstRow(csv_path)

            if first_row is None:
                continue

            rfid = first_row[0]
            t = first_row[1]
            
            full_msg = {"RFID": str(rfid), "Time": str(t)}
            json_msg = json.dumps(full_msg)


            # Send the message
            await websocket.send(json_msg)

            # Receive and print the response
            response = await websocket.recv()
            json_r = json.loads(response)
            if json_r:
                removeFirstRow(csv_path)


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(connect_to_websocket_server())

