import json
import requests

def sse_client():
    url = 'http://localhost:8000/api/sse/covered_parking_status/'

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                data = line.decode('utf-8')[2:-1]
                json_data = json.loads(data)
                print(json_data)  # Decode bytes to string
    except requests.exceptions.RequestException as e:
        print("Error:", e)

        

if __name__ == "__main__":
    sse_client()

