import requests
url = "http://localhost:8001/api/covered_parking/"

post_data = {
    "area": "West",
    "id_area": 1,
    "state":0
}
response = requests.post(url, data=post_data)
# response = requests.get(url)

print(response.json())
# print(response)