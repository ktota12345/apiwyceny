# API Wyceny Tras - Dokumentacja

## Endpoint: `/api/route-pricing`

Backend API do pobierania średnich cen dla tras na podstawie kodów pocztowych i typu pojazdu.

### Metoda
`POST`

### URL
```
http://localhost:5000/api/route-pricing
```

### Request Headers
```
Content-Type: application/json
```

### Request Body (JSON)

```json
{
  "start_postal_code": "89",
  "end_postal_code": "50",
  "vehicle_type": "naczepa"
}
```

#### Parametry:
- **start_postal_code** (string, wymagane) - Kod pocztowy początku trasy
- **end_postal_code** (string, wymagane) - Kod pocztowy końca trasy
- **vehicle_type** (string, opcjonalne, domyślnie: "naczepa") - Typ pojazdu

#### Dostępne typy pojazdów:
- `naczepa` / `trailer` - Naczepa (TimoCom)
- `3.5t` / `3_5t` - Pojazd do 3.5t (TimoCom)
- `12t` - Pojazd do 12t (TimoCom)
- `lorry` - Ciężarówka (Trans.eu)
- `solo` - Solo (Trans.eu)
- `bus` - Bus (Trans.eu)
- `double_trailer` / `dbl_trailer` - Podwójna naczepa (Trans.eu)

### Response - Sukces (200)

```json
{
  "success": true,
  "data": {
    "start_postal_code": "89",
    "end_postal_code": "50",
    "vehicle_type": "naczepa",
    "distance_km": 955.63,
    "currency": "EUR",
    "unit": "EUR/km",
    "pricing": {
      "timocom": {
        "avg_7d": 1.0,
        "avg_30d": 1.04,
        "avg_90d": 1.07,
        "median_7d": 1.05,
        "median_30d": 1.05,
        "median_90d": 1.08,
        "offers_7d": 4012,
        "offers_30d": 24835,
        "offers_90d": 29253
      }
    },
    "route_info": {
      "lane_name": "NL89-CZ50",
      "origin": "NL89",
      "origin_country": "NL",
      "destination_country": "CZ",
      "historic_potential": "Historic"
    }
  }
}
```

#### Opis pól odpowiedzi:
- **pricing** - Dane cenowe dla wybranego typu pojazdu
  - **timocom** lub **transeu** - Źródło danych (zależy od typu pojazdu)
    - **avg_7d / avg_30d / avg_90d** - Średnia cena za km w okresie 7/30/90 dni
    - **median_7d / median_30d / median_90d** - Mediana ceny za km w okresie 7/30/90 dni
    - **offers_7d / offers_30d / offers_90d** - Liczba ofert w okresie 7/30/90 dni
- **distance_km** - Dystans trasy w kilometrach
- **route_info** - Dodatkowe informacje o trasie

### Response - Błędy

#### 400 - Brak wymaganych parametrów
```json
{
  "success": false,
  "error": "Brak kodów pocztowych (start_postal_code i end_postal_code wymagane)"
}
```

#### 400 - Nieznany typ pojazdu
```json
{
  "success": false,
  "error": "Nieznany typ pojazdu: xxx",
  "available_types": ["naczepa", "trailer", "3.5t", "3_5t", "12t", "lorry", "solo", "bus", "double_trailer", "dbl_trailer"]
}
```

#### 404 - Brak danych dla trasy
```json
{
  "success": false,
  "error": "Brak danych dla trasy 12345 -> 67890",
  "message": "Nie znaleziono trasy w bazie danych"
}
```

#### 500 - Błąd serwera
```json
{
  "success": false,
  "error": "Błąd serwera: [szczegóły błędu]"
}
```

## Przykłady użycia

### cURL
```bash
curl -X POST http://localhost:5000/api/route-pricing \
  -H "Content-Type: application/json" \
  -d '{
    "start_postal_code": "89",
    "end_postal_code": "50",
    "vehicle_type": "naczepa"
  }'
```

### Python (requests)
```python
import requests

url = "http://localhost:5000/api/route-pricing"
payload = {
    "start_postal_code": "89",
    "end_postal_code": "50",
    "vehicle_type": "naczepa"
}

response = requests.post(url, json=payload)
data = response.json()

if data['success']:
    pricing = data['data']['pricing']['timocom']
    print(f"Średnia cena (7 dni): {pricing['avg_7d']} EUR/km")
    print(f"Dystans: {data['data']['distance_km']} km")
else:
    print(f"Błąd: {data['error']}")
```

### JavaScript (fetch)
```javascript
fetch('http://localhost:5000/api/route-pricing', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    start_postal_code: '89',
    end_postal_code: '50',
    vehicle_type: 'naczepa'
  })
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    const pricing = data.data.pricing.timocom;
    console.log(`Średnia cena (7 dni): ${pricing.avg_7d} EUR/km`);
    console.log(`Dystans: ${data.data.distance_km} km`);
  } else {
    console.error(`Błąd: ${data.error}`);
  }
});
```

## Uruchomienie serwera

```bash
# Zainstaluj wymagane biblioteki
pip install -r requirements.txt

# Uruchom serwer Flask
python app.py
```

Serwer uruchomi się domyślnie na porcie 5000: `http://localhost:5000`

## Źródło danych

API korzysta z pliku CSV: `TRIVIUM_PRZETARG_2026_pelne_dane_AWS.csv`

Dane są ładowane do pamięci przy pierwszym żądaniu i cachowane dla lepszej wydajności.

## Uwagi

- Kody pocztowe są normalizowane (usuwane spacje i myślniki) przed wyszukiwaniem
- Nie wszystkie trasy mają dane dla wszystkich typów pojazdów
- Wartości `null` w odpowiedzi oznaczają brak danych dla danego okresu
- API zwraca dane tylko dla tras obecnych w pliku CSV
