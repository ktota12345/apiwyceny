# 🚛 Route Pricing API

Backend API dla wyceny tras transportowych na podstawie kodów pocztowych i danych z bazy PostgreSQL.

## 📋 Funkcjonalności

- **Wycena tras** - Pobieranie średnich cen dla tras na podstawie kodów pocztowych
- **Dane z PostgreSQL** - Aktualne średnie ceny z tabel TimoCom i Trans.eu
- **Mapowanie kodów** - Automatyczne mapowanie kodów pocztowych na regiony
- **Różne typy pojazdów** - Naczepa, 3.5t, 12t, lorry
- **Okresy czasowe** - Średnie dla 7, 30 i 90 dni

## 🚀 Szybki start

### Wymagania
- Python 3.11+
- PostgreSQL z tabelami: `public.offers` (TimoCom) i `public."OffersTransEU"` (Trans.eu)
- Pliki mapowania kodów pocztowych (w folderze `data/`)

### Instalacja lokalna

```bash
# Sklonuj repozytorium
git clone <your-repo-url>
cd route-pricing-api

# Zainstaluj zależności
pip install -r requirements.txt

# Skonfiguruj zmienne środowiskowe
cp .env.example .env
# Edytuj .env i dodaj dane do PostgreSQL

# Uruchom serwer
python app.py
```

Serwer uruchomi się na `http://localhost:5000`

## 🔐 Autentykacja

API wymaga **API Key** dla dostępu do chronionych endpointów.

**Header:**
```
X-API-Key: your-secret-api-key
```

Zobacz [SECURITY.md](SECURITY.md) dla szczegółów konfiguracji.

## 📡 Endpointy API

### GET `/` (publiczny)
Informacje o API

### GET `/health` (publiczny)
Health check

### POST `/api/route-pricing` 🔒
Pobierz wycenę trasy **(wymaga API key)**

**Headers:**
```
Content-Type: application/json
X-API-Key: your-secret-api-key
```

**Request:**
```json
{
  "start_postal_code": "PL50",
  "end_postal_code": "DE10",
  "vehicle_type": "naczepa"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "start_postal_code": "PL50",
    "end_postal_code": "DE10",
    "vehicle_type": "naczepa",
    "region_ids": {
      "start": 134,
      "end": 89
    },
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
    "currency": "EUR",
    "unit": "EUR/km",
    "data_source": "postgresql"
  }
}
```

## 🚢 Wdrożenie na Render

Zobacz [DEPLOY_RENDER.md](DEPLOY_RENDER.md) dla szczegółowej instrukcji.

## 🔧 Typy pojazdów

| Typ | Źródło | Opis |
|-----|--------|------|
| `naczepa` / `trailer` | TimoCom | Naczepa standardowa |
| `3.5t` / `3_5t` | TimoCom | Pojazd do 3.5 tony |
| `12t` | TimoCom | Pojazd do 12 ton |
| `lorry` | Trans.eu | Ciężarówka |

## 📝 Format kodów pocztowych

API akceptuje kody w formacie:
- **[KRAJ][2_CYFRY]** - np. `PL50`, `DE10`, `FR75`
- **[2_CYFRY]** - automatycznie dodaje `PL` - np. `50` → `PL50`

## 🗄️ Struktura bazy danych

### TimoCom - `public.offers`
- `starting_id` - ID regionu startowego
- `destination_id` - ID regionu docelowego
- `trailer_avg_price_per_km` - Średnia cena za km (naczepa)
- `vehicle_up_to_3_5_t_avg_price_per_km` - Średnia cena za km (3.5t)
- `vehicle_up_to_12_t_avg_price_per_km` - Średnia cena za km (12t)
- `enlistment_date` - Data oferty

### Trans.eu - `public."OffersTransEU"`
- `starting_id` - ID regionu startowego
- `destination_id` - ID regionu docelowego
- `lorry_avg_price_per_km` - Średnia cena za km (lorry)
- `enlistment_date` - Data oferty

## 📂 Struktura projektu

```
route-pricing-api/
├── app.py                      # Główna aplikacja Flask
├── requirements.txt            # Zależności Python
├── Procfile                    # Konfiguracja Render
├── runtime.txt                 # Wersja Python
├── render.yaml                 # Konfiguracja Render
├── .gitignore
├── .env.example
├── README.md
├── DEPLOY_RENDER.md           # Instrukcja wdrożenia
└── data/
    ├── postal_code_to_region_transeu.json
    └── postal_code_to_region_timocom.json
```

## 🔐 Zmienne środowiskowe

```bash
# Database
POSTGRES_HOST=your-database-host
POSTGRES_PORT=5432
POSTGRES_USER=your-username
POSTGRES_DB=your-database-name
POSTGRES_PASSWORD=your-password

# Security
API_KEY=your-secret-api-key-min-32-chars
REQUIRE_API_KEY=true
```

## 📊 Przykład użycia

### cURL
```bash
curl -X POST https://your-api.onrender.com/api/route-pricing \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "start_postal_code": "PL50",
    "end_postal_code": "DE10",
    "vehicle_type": "naczepa"
  }'
```

### Python
```python
import requests

url = "https://your-api.onrender.com/api/route-pricing"
headers = {
    "X-API-Key": "your-api-key-here"
}
data = {
    "start_postal_code": "PL50",
    "end_postal_code": "DE10",
    "vehicle_type": "naczepa"
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

### JavaScript
```javascript
fetch('https://your-api.onrender.com/api/route-pricing', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'your-api-key-here'
  },
  body: JSON.stringify({
    start_postal_code: 'PL50',
    end_postal_code: 'DE10',
    vehicle_type: 'naczepa'
  })
})
.then(r => r.json())
.then(data => console.log(data));
```

## 🛠️ Development

```bash
# Uruchom w trybie development
export FLASK_ENV=development
python app.py

# Testy (TODO)
pytest
```

## 📄 Licencja

MIT

## 👥 Autorzy

CargoScout Team
