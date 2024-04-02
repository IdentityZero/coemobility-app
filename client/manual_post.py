# import requests
# import asyncio
# import json
# from datetime import date, datetime
# from functools import partial


# async def post(url, data):
#     loop = asyncio.get_event_loop()

#     response = await loop.run_in_executor(None, partial(requests.post, url, data=data))

#     print(response.json())

# url = "http://localhost:8001/api/parking/manual/create/"

# post_data = {
#     "role": "Student",
#     "vehicle_category": "Motors",
#     "action": "exit",
#     "crossing_time" : str(datetime.now())
# }


# asyncio.run(post(url,post_data))


## Main template
# import requests
# import json
# from datetime import date, datetime
# time = datetime.now().timestamp()
# url = "http://localhost:8001/api/parking/manual/create/"

# post_data = {
#     "role": "Student",
#     "vehicle_category": "Motors",
#     "action": "entry",
#     "crossing_time" : str(datetime.now())
# }

# post_data_json = json.dumps(post_data)

# response = requests.post(url, json=post_data)
# time1 = datetime.now().timestamp()
# print(time1-time)

# print(response.json())


import requests
import json
from datetime import date, datetime
url = "http://localhost:8001/api/parking/manual/create/"

headers = {
    'Content-type':"application/json",
    'Connection':'keep-alive'
}

post_data = {
    "role": "Student",
    "vehicle_category": "Motors",
    "action": "entry",
    "crossing_time" : str(datetime.now())
}

# Create a Session object
session = requests.Session()

print("Session set")

# time = datetime.now().timestamp()
response1 = session.get(url, headers=headers, timeout=5)
# time1 = datetime.now().timestamp()
# print(time1-time)

# time = datetime.now().timestamp()
# response1 = session.post(url, json=post_data, headers=headers)
# time1 = datetime.now().timestamp()
# print(time1-time)

# time = datetime.now().timestamp()
# response1 = session.post(url, json=post_data, headers=headers)
# time1 = datetime.now().timestamp()
# print(time1-time)

# print(response1.json())
