import requests
import json

"""
Test client dla API wyceny tras transportowych
Zwraca średnie stawki EUR/km z ostatnich 30 dni z giełd TimoCom i Trans.eu

Przykładowa struktura response:
{
  "success": true,
  "data": {
    "start_postal_code": "PL20",
    "end_postal_code": "DE49",
    "start_region_id": 135,
    "end_region_id": 98,
    "pricing": {
      "timocom": {
        "30d": {
          "avg_price_per_km": {
            "trailer": 1.50,    # Naczepa
            "3_5t": 1.00,       # Bus
            "12t": 1.20         # Solo
          },
          "median_price_per_km": {...},
          "total_offers": 24835,
          "days_with_data": 30
        }
      },
      "transeu": {
        "30d": {
          "avg_price_per_km": {
            "lorry": 0.87
          },
          "total_offers": 9240,
          "days_with_data": 28
        }
      }
    },
    "currency": "EUR",
    "unit": "EUR/km"
  }
}
"""

url = "http://127.0.0.1:5003/api/route-pricing"

payload = {
    "start_postal_code": "PL20",
    "end_postal_code": "DE49"
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
