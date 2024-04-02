import json
import requests

def main():
    url = 'http://localhost:8000/api/covered_parking_status/'

    response = requests.get(url)
    data = response.json()

    return data


if __name__ == "__main__":
    main()