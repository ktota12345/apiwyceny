# Pricing API - API wyceny tras transportowych

Standalone REST API do pobierania historycznych cen transportowych z giełd TimoCom i Trans.eu.

## Funkcjonalność

API pobiera średnie i mediany cen transportowych dla zadanej trasy (kod pocztowy start → kod pocztowy koniec) z bazy danych PostgreSQL dla trzech przedziałów czasowych:
- **7 dni** - ostatni tydzień
- **30 dni** - ostatni miesiąc
- **90 dni** - ostatnie 3 miesiące

## Wymagania

- Python 3.8+
- PostgreSQL z danymi TimoCom i Trans.eu
- Pliki mapowania JSON (zawarte w folderze `data/`)

## Instalacja

### 1. Skopiuj repozytorium

```bash
git clone <your-repo>
cd pricing-api
```

### 2. Utwórz środowisko wirtualne

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# lub
venv\Scripts\activate  # Windows
```

### 3. Zainstaluj zależności

```bash
pip install -r requirements.txt
```

### 4. Konfiguracja

Skopiuj plik `.env.example` do `.env` i uzupełnij dane dostępowe do bazy:

```bash
cp .env.example .env
```

Edytuj `.env`:

```env
POSTGRES_HOST=twoj-host-bazy.com
POSTGRES_PORT=5432
POSTGRES_USER=twoj_user
POSTGRES_PASSWORD=twoje_haslo
POSTGRES_DB=nazwa_bazy
```

### 5. Uruchom API

**Developerski:**
```bash
python app.py
```

**Produkcyjny (z Gunicorn):**
```bash
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

API będzie dostępne pod adresem: `http://localhost:5001`

## 🔒 Autoryzacja API Key

API wymaga klucza autoryzacyjnego. Więcej informacji: **[API_AUTHORIZATION.md](API_AUTHORIZATION.md)**

### Szybki start:

1. Wygeneruj klucz:
   ```bash
   python generate_api_key.py
   ```

2. Dodaj do `.env`:
   ```
   API_KEY=twoj-wygenerowany-klucz
   ```

3. Użyj w requestach:
   ```bash
   curl -X POST http://localhost:5001/api/pricing \
     -H "X-API-Key: twoj-klucz" \
     -H "Content-Type: application/json" \
     -d '{"start_postal_code": "PL50", "end_postal_code": "DE10"}'
   ```

## Pola odpowiedzi

### TimoCom
- **`avg_price_per_km`** - średnie ceny EUR/km dla trailer, 3.5t, 12t
- **`median_price_per_km`** - mediany cen EUR/km (tylko trailer, reszta null)
- **`total_offers`** - całkowita liczba ofert w okresie
- **`offers_by_vehicle_type`** - rozbicie ofert po typach pojazdów
- **`days_with_data`** - liczba dni z danymi w okresie

### Trans.eu
- **`avg_price_per_km`** - średnia cena EUR/km dla lorry
- **`median_price_per_km`** - mediana ceny EUR/km dla lorry
- **`total_offers`** - całkowita liczba ofert w okresie
- **`days_with_data`** - liczba dni z danymi w okresie

## Użycie API

### Endpoint: `/api/pricing`

**Method:** `POST`

**Content-Type:** `application/json`

### Request

```json
{
  "start_postal_code": "PL50",
  "end_postal_code": "DE10"
}
```

**Format kodów pocztowych:**
- `KOD_KRAJU` (2 litery) + pierwsze 2 cyfry kodu pocztowego
- Przykłady: `PL50`, `DE10`, `FR75`, `ES28`, `IT20`

### Response (sukces)

```json
{
  "success": true,
  "data": {
    "start_postal_code": "PL50",
    "end_postal_code": "DE10",
    "start_region_id": 134,
    "end_region_id": 89,
    "pricing": {
      "timocom": {
        "7d": {
          "avg_price_per_km": {
            "trailer": 1.05,
            "3_5t": 0.85,
            "12t": 0.95
          },
          "median_price_per_km": {
            "trailer": 1.08,
            "3_5t": null,
            "12t": null
          },
          "total_offers": 4012,
          "offers_by_vehicle_type": {
            "trailer": 2340,
            "3_5t": 892,
            "12t": 780
          },
          "days_with_data": 7
        },
        "30d": {
          "avg_price_per_km": {
            "trailer": 1.04,
            "3_5t": 0.84,
            "12t": 0.94
          },
          "median_price_per_km": {
            "trailer": 1.05,
            "3_5t": null,
            "12t": null
          },
          "total_offers": 24835,
          "offers_by_vehicle_type": {
            "trailer": 14200,
            "3_5t": 5835,
            "12t": 4800
          },
          "days_with_data": 30
        },
        "90d": {
          "avg_price_per_km": {
            "trailer": 1.07,
            "3_5t": 0.86,
            "12t": 0.96
          },
          "median_price_per_km": {
            "trailer": 1.08,
            "3_5t": null,
            "12t": null
          },
          "total_offers": 29253,
          "offers_by_vehicle_type": {
            "trailer": 16500,
            "3_5t": 6753,
            "12t": 6000
          },
          "days_with_data": 85
        }
      },
      "transeu": {
        "7d": {
          "avg_price_per_km": {
            "lorry": 0.96
          },
          "median_price_per_km": {
            "lorry": 0.98
          },
          "total_offers": 1580,
          "days_with_data": 7
        },
        "30d": {
          "avg_price_per_km": {
            "lorry": 0.87
          },
          "median_price_per_km": {
            "lorry": 0.89
          },
          "total_offers": 9240,
          "days_with_data": 28
        },
        "90d": {
          "avg_price_per_km": {
            "lorry": 1.10
          },
          "median_price_per_km": {
            "lorry": 1.12
          },
          "total_offers": 28350,
          "days_with_data": 82
        }
      }
    },
    "currency": "EUR",
    "unit": "EUR/km",
    "data_sources": {
      "timocom": true,
      "transeu": true
    }
  }
}
```

### Response (błąd - brak danych)

```json
{
  "success": false,
  "error": "Brak danych dla trasy PL50 -> DE10",
  "message": "Nie znaleziono danych cenowych w bazie dla tej trasy"
}
```

### Response (błąd - nieprawidłowy kod)

```json
{
  "success": false,
  "error": "Nie znaleziono regionu dla kodów: PL99",
  "message": "Użyj formatu: KOD_KRAJU + 2 cyfry (np. PL50, DE10, FR75)"
}
```

## Health Check

### Endpoint: `/health`

**Method:** `GET`

**Response:**

```json
{
  "status": "ok",
  "service": "Pricing API",
  "version": "1.0.0"
}
```

## Przykłady użycia

### cURL

```bash
curl -X POST http://localhost:5001/api/pricing \
  -H "Content-Type: application/json" \
  -d '{"start_postal_code": "PL50", "end_postal_code": "DE10"}'
```

### Python (requests)

```python
import requests

response = requests.post(
    'http://localhost:5001/api/pricing',
    json={
        'start_postal_code': 'PL50',
        'end_postal_code': 'DE10'
    }
)

data = response.json()
if data['success']:
    timocom_7d = data['data']['pricing']['timocom']['7d']
    print(f"TimoCom 7d średnia (trailer): {timocom_7d['avg_price_per_km']['trailer']} EUR/km")
    print(f"Oferty: {timocom_7d['total_offers']}")
```

### JavaScript (fetch)

```javascript
fetch('http://localhost:5001/api/pricing', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    start_postal_code: 'PL50',
    end_postal_code: 'DE10'
  })
})
.then(res => res.json())
.then(data => {
  if (data.success) {
    console.log('TimoCom 7d:', data.data.pricing.timocom['7d']);
  }
});
```

## Struktura plików

```
pricing-api/
├── app.py                          # Główna aplikacja Flask
├── requirements.txt                # Zależności Python
├── .env                           # Konfiguracja (NIE commituj!)
├── .env.example                   # Szablon konfiguracji
├── .gitignore                     # Pliki ignorowane przez git
├── README.md                      # Ta dokumentacja
└── data/                          # Pliki mapowania
    ├── transeu_to_timocom_mapping.json
    └── postal_code_to_region_transeu.json
```

## Struktura bazy danych

### Tabela: `public.offers` (TimoCom)

```sql
CREATE TABLE public.offers (
    starting_id INTEGER,
    destination_id INTEGER,
    enlistment_date DATE,
    trailer_avg_price_per_km DECIMAL,
    vehicle_up_to_3_5_t_avg_price_per_km DECIMAL,
    vehicle_up_to_12_t_avg_price_per_km DECIMAL,
    number_of_offers_total INTEGER
);

-- Indeks dla wydajności
CREATE INDEX idx_offers_route_date 
ON public.offers (starting_id, destination_id, enlistment_date DESC);
```

### Tabela: `public."OffersTransEU"` (Trans.eu)

```sql
CREATE TABLE public."OffersTransEU" (
    starting_id INTEGER,
    destination_id INTEGER,
    enlistment_date DATE,
    lorry_avg_price_per_km DECIMAL
);

-- Indeks dla wydajności
CREATE INDEX idx_offerstranseu_route_date 
ON public."OffersTransEU" (starting_id, destination_id, enlistment_date DESC);
```

## Deployment

### Docker (opcjonalnie)

Utwórz `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5001

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "app:app"]
```

Build i uruchom:

```bash
docker build -t pricing-api .
docker run -p 5001:5001 --env-file .env pricing-api
```

### Heroku

```bash
echo "web: gunicorn app:app" > Procfile
git add .
git commit -m "Initial commit"
heroku create your-app-name
heroku config:set POSTGRES_HOST=... POSTGRES_PORT=... POSTGRES_USER=... POSTGRES_PASSWORD=... POSTGRES_DB=...
git push heroku main
```

### Render.com

1. Połącz z repozytorium GitHub
2. Wybierz "Web Service"
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`
5. Dodaj zmienne środowiskowe w panelu Render

## Troubleshooting

### Problem: "Błąd połączenia z bazą danych"

**Rozwiązanie:**
- Sprawdź czy plik `.env` istnieje i ma poprawne dane
- Sprawdź połączenie sieciowe z bazą danych
- Sprawdź firewall i security groups

### Problem: "Nie znaleziono regionu dla kodów"

**Rozwiązanie:**
- Sprawdź format kodu pocztowego (musi być: 2 litery + 2 cyfry, np. PL50)
- Sprawdź czy pliki mapowania w folderze `data/` są poprawne
- Sprawdź czy kod znajduje się w pliku `postal_code_to_region_transeu.json`

### Problem: "Brak danych dla trasy"

**Rozwiązanie:**
- Ta trasa może nie mieć danych w bazie
- Sprawdź czy w bazie są dane dla tych regionów
- Sprawdź zakres dat w tabeli (czy są dane z ostatnich 90 dni)

## Licencja

Proprietary - Użytek wewnętrzny

## Kontakt

W razie pytań skontaktuj się z zespołem deweloperskim.
