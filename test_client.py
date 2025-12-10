import requests
import json

"""
Test client dla API wyceny tras transportowych
Zwraca średnie stawki EUR/km:
- TimoCom i Trans.eu: ostatnie 30 dni
- Zlecenia historyczne: ostatnie 6 miesięcy (180 dni) z podziałem na FTL i LTL
  (każdy typ ładunku ma własne statystyki i top 4 przewoźników)

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
      },
      "historical": {
        "180d": {  # Ostatnie 6 miesięcy - podział na FTL i LTL
          "FTL": {  # Pełne ładunki (Full Truck Load)
            "avg_price_per_km": {
              "client": 0.95,     # Cena sprzedaży
              "carrier": 0.85     # Koszt realizacji
            },
            "median_price_per_km": {
              "client": 0.92,
              "carrier": 0.83
            },
            "avg_amounts": {
              "client": 850.50,
              "carrier": 750.00
            },
            "avg_distance": 900.5,
            "total_orders": 25,
            "days_with_data": 28,
            "top_carriers": [    # Top 4 przewoźników FTL
              {
                "carrier_id": 123,
                "carrier_name": "TRANS-POL SP. Z O.O.",
                "order_count": 15,
                "avg_client_price_per_km": 0.98,
                "avg_carrier_price_per_km": 0.88,
                "avg_client_amount": 880.00,
                "avg_carrier_amount": 790.00
              }
            ]
          },
          "LTL": {  # Ładunki częściowe (Less Than Truckload)
            "avg_price_per_km": {
              "client": 1.15,
              "carrier": 1.05
            },
            "median_price_per_km": {
              "client": 1.12,
              "carrier": 1.03
            },
            "avg_amounts": {
              "client": 450.00,
              "carrier": 380.00
            },
            "avg_distance": 400.0,
            "total_orders": 20,
            "days_with_data": 25,
            "top_carriers": [    # Top 4 przewoźników LTL
              {
                "carrier_id": 456,
                "carrier_name": "EXPRESS-TRANS",
                "order_count": 10,
                "avg_client_price_per_km": 1.18,
                "avg_carrier_price_per_km": 1.08,
                "avg_client_amount": 480.00,
                "avg_carrier_amount": 410.00
              }
            ]
          }
        }
      }
    },
    "currency": "EUR",
    "unit": "EUR/km",
    "data_sources": {
      "timocom": true,
      "transeu": true,
      "historical": true
    }
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
