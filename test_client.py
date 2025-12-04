import requests
import json

url = "http://127.0.0.1:5003/api/route-pricing"

payload = {
    "start_postal_code": "PL20",
    "end_postal_code": "DE49",
    "dystans": 850
}

headers = {
    'Content-Type': 'application/json',
    'X-API-Key': '0aa1a2a087a201d6ab4d4f25979779f3'
}

try:
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()  # Rzuć wyjątkiem dla złych odpowiedzi (4xx lub 5xx)

    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

except requests.exceptions.HTTPError as errh:
    print(f"Http Error: {errh}")
    print(f"Response content: {response.content.decode('utf-8')}")
except requests.exceptions.ConnectionError as errc:
    print(f"Error Connecting: {errc}")
except requests.exceptions.Timeout as errt:
    print(f"Timeout Error: {errt}")
except requests.exceptions.RequestException as err:
    print(f"Oops: Something Else: {err}")
