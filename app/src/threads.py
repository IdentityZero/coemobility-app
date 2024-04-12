import asyncio
from datetime import datetime
import json
from numpy import isin
from operator import call
import requests
from queue import Queue
import websockets
import time

from PyQt5.QtCore import QThread, pyqtSignal

import settings

class SetUpThread(QThread):
    """
    AS OF NOW only accepts classes and a method name. The methods are not accepting arguments
    UPDATE:
        Accepts function without arguments
    """
    finished = pyqtSignal(str)

    def __init__(self, functions):
        super().__init__()
        self.functions = functions

    def run(self):
        for function_set in self.functions:
            function = function_set[0]

            if isinstance(function, tuple):
                obj, method_name = function
                method = getattr(obj, method_name)
                method()
            elif callable(function):
                result = function()
                function_name = function.__name__
                if not isinstance(result,str):
                    result = json.dumps(result)
                
                payload = {
                    "topic": function_name,
                    "data": result
                }

                payload = json.dumps(payload)
                self.finished.emit(payload)

        self.finished.emit("Finished")


class WebSocketClientThread(QThread):
    data_received = pyqtSignal(str)

    def __init__(self, uri):
        super().__init__()
        self.uri = uri
        self.websocket = None  # Store the websocket object
    
    async def connect_to_websocket(self):
        self.websocket = await websockets.connect(self.uri)

        while True:
            message = await self.websocket.recv()
            self.data_received.emit(message)
    
    def send_message(self, message):
        if self.websocket:
            asyncio.run_coroutine_threadsafe(self.websocket.send(message), self.websocket.loop)
    
    def run(self):
        print("Web socket Thread running")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.connect_to_websocket())


class CoveredParkingSSEThread(QThread):
    message = pyqtSignal(str)

    def __init__(self):
        super(CoveredParkingSSEThread, self).__init__()
        self.sse_url = settings.COVERED_PARKING_SSE_ENDPOINT

    def run(self):
        headers = {'Cache-Control': 'no-cache', 'Connection': 'keep-alive'}
        with requests.get(self.sse_url, headers=headers, stream=True) as response:
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        data = line.decode('utf-8')[2:-1]
                    self.message.emit(data)
            else:
                print("Failed to connect to SSE endpoint")


class ManualParkingEntryThread(QThread):
    connection_status = pyqtSignal(str)

    def __init__(self,queue):
        super(ManualParkingEntryThread, self).__init__()
        self.queue = queue
        self.post_endpoint = settings.CREATE_MANUAL_PARKING_ENDPOINT

        self.connectToEndpoint(self.post_endpoint)

    def connectToEndpoint(self,endpoint):
        # Create a Session object
        self.session = requests.Session()
        # Keep connection alive for faster posting
        self.headers = {
            'Content-type':"application/json",
            'Connection':'keep-alive'
        }

        # Start initial connection for the connection
        init_con = self.session.get(self.post_endpoint, headers=self.headers)

    def run(self):
        print("ManualParkingEntryThread Run")
        while True:
            if not self.queue.empty():
                message = self.queue.get()

                entry = 1

                while entry != 0:
                    # if successful post entry returns 0
                    entry = self.post_entry(message,self.post_endpoint, self.headers)
                    if entry == 1:
                        print("Emitting")
                        self.connection_status.emit("No internet connection!")
                    time.sleep(3)
                
            time.sleep(1)
    
    def post_entry(self,message_list,endpoint, headers):
        """
        message_list must contain [role, vehicle_category, action]
        action must only be "ADD" or "SUB"
        Add means entrance
        Sub means exit
        """

        current_time = str(datetime.now())

        # unpack message list payload
        role = message_list[0]
        vehicle_category = message_list[1]
        action = message_list[2]

        if action == "ADD":
            action_motion = "entry"
        else:
            action_motion = "exit"

        post_data = {
            "role": role,
            "vehicle_category": vehicle_category,
            "action": action_motion,
            "crossing_time" : current_time
        }

        try:
            response = self.session.post(endpoint, json=post_data, headers=headers)
            if response.status_code != 201:
                return 1
            return 0 
        except:
            print("Connection timeout")
            return 1

