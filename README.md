# 🚚 Pricing API v2.0 - API wyceny tras transportowych

[![Version](https://img.shields.io/badge/version-2.0.1-blue.svg)](CHANGELOG.md)
[![Security](https://img.shields.io/badge/security-enhanced-green.svg)](#security)
[![Performance](https://img.shields.io/badge/performance-optimized-brightgreen.svg)](#performance)

Standalone REST API do kalkulacji cen transportowych na podstawie historycznych danych z giełdy TimoCom.

## ✨ Funkcjonalność

API oblicza cenę transportu dla zadanej trasy (kod pocztowy start → kod pocztowy koniec) poprzez:
1. Mapowanie kodów pocztowych na regiony Trans.eu
2. Konwersję regionów Trans.eu na regiony TimoCom
3. Pobranie średnich cen z ostatnich **30 dni** z TimoCom
4. Obliczenie końcowej ceny: `stawka_za_km * dystans` dla każdego typu pojazdu

**Typy pojazdów:**
- 🚐 **Bus** (do 3.5t)
- 🚛 **Solo** (do 12t)
- 🚚 **Naczepa** (trailer)

## 🚀 Co nowego w v2.0?

- ⚡ **6x szybsze** - zredukowano zapytania do bazy z 6 do 1
- 🔒 **Enhanced security** - dodano security headers (XSS, HSTS, clickjacking protection)
- 📊 **Performance monitoring** - szczegółowe logi czasów wykonania
- 🔄 **Connection resilience** - auto-reconnect dla stale DB connections
- 📚 **Complete Swagger docs** - pełna dokumentacja OpenAPI

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

# Security
API_KEY=wygenerowany-klucz-api
REQUIRE_API_KEY=true
ENV=development

# CORS (oddzielone przecinkami)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5000
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

API będzie dostępne pod adresem: `http://localhost:5003`

### 6. Swagger Documentation

Po uruchomieniu API, dokumentacja Swagger dostępna jest pod:

```
http://localhost:5003/apidocs/
```

## 🔒 Security & Authentication

### API Key Authentication

Każde żądanie do `/api/route-pricing` wymaga klucza API.

**Sposoby przekazania klucza:**

1. Header `X-API-Key`:
   ```bash
   X-API-Key: twoj-klucz-api
   ```

2. Header `Authorization` (Bearer token):
   ```bash
   Authorization: Bearer twoj-klucz-api
   ```

### Konfiguracja API Key

1. Wygeneruj klucz (lub użyj istniejącego):
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. Dodaj do `.env`:
   ```env
   API_KEY=twoj-wygenerowany-klucz
   REQUIRE_API_KEY=true
   ```

### Rate Limiting

- **Global:** 100 requestów/dzień, 20 requestów/godzinę
- **Endpoint `/api/route-pricing`:** 5 requestów/minutę

### Security Features

- ✅ Timing-attack resistant authentication (`secrets.compare_digest`)
- ✅ HTTPS enforcement w produkcji
- ✅ CORS whitelist
- ✅ Security headers (XSS, clickjacking, HSTS)
- ✅ Input validation & sanitization
- ✅ SQL injection protection
- ✅ DoS protection (rate limiting, input length limits)

## ⚡ Performance

### Optymalizacje v2.0

- **Single query:** Zredukowano zapytania do bazy z 6 do 1 (~6x szybciej)
- **Connection pooling:** Min 1, max 10 połączeń z auto-reconnect
- **Statement timeout:** 30 sekund dla długich zapytań
- **Connection validation:** Automatyczna weryfikacja połączeń przed użyciem

### Performance Monitoring

W logach aplikacji zobaczysz szczegółowe metryki:

```
⏱️ Połączenie z bazą: 15ms
⏱️ Zapytanie SQL (30d): 234ms
⏱️ CAŁKOWITY CZAS get_timocom_pricing (30d): 250ms
⏱️ Zapytanie TimoCom 30d: 251ms
⏱️ Obliczenia cen: 1ms
⏱️ ⭐ CAŁKOWITY CZAS REQUESTU: 252ms
```

## 📖 Użycie API

### Endpoint: `/api/route-pricing`

**Method:** `POST`  
**Content-Type:** `application/json`  
**Authentication:** API Key (required)

### Request

```json
{
  "start_postal_code": "PL20",
  "end_postal_code": "DE49"
}
```

**Pola:**
- `start_postal_code` (string, required) - Kod pocztowy startu
- `end_postal_code` (string, required) - Kod pocztowy celu

**Format kodów pocztowych:**
- `KOD_KRAJU` (2 litery ISO) + cyfry (1-5 cyfr)
- Przykłady: `PL20`, `DE49`, `FR75`, `ES28`, `IT20`
- Pattern regex: `^[A-Z]{2}\d{1,5}$`

### Response (sukces - 200 OK)

```json
{
  "success": true,
  "data": {
    "start_postal_code": "PL20",
    "end_postal_code": "DE49",
    "distance_km": 850,
    "calculated_prices": {
      "cena_naczepa": 1275.50,
      "cena_bus": 850.75,
      "cena_solo": 1020.25
    },
    "currency": "EUR"
  }
}
```

**Pola odpowiedzi:**
- `success` (boolean) - Status powodzenia
- `data.start_postal_code` (string) - Kod pocztowy startu
- `data.end_postal_code` (string) - Kod pocztowy celu
- `data.distance_km` (number) - Dystans w km
- `data.calculated_prices` (object) - Obliczone ceny:
  - `cena_naczepa` (number|null) - Cena dla naczepy w EUR
  - `cena_bus` (number|null) - Cena dla busa w EUR
  - `cena_solo` (number|null) - Cena dla solo w EUR
- `data.currency` (string) - Waluta ("EUR")

### Response (błąd - 400 Bad Request)

```json
{
  "success": false,
  "error": "Brak wszystkich wymaganych pól: start_postal_code, end_postal_code"
}
```

### Response (błąd - 401 Unauthorized)

```json
{
  "success": false,
  "error": "Brak API key",
  "message": "Wymagany header: X-API-Key lub Authorization: Bearer <key>"
}
```

### Response (błąd - 404 Not Found)

```json
{
  "success": false,
  "error": "Brak danych dla trasy PL20 -> DE49",
  "message": "Nie znaleziono danych cenowych w bazie dla tej trasy"
}
```

### Response (błąd - 429 Too Many Requests)

```json
{
  "error": "Rate limit exceeded"
}
```

## 🏥 Health Check

### Endpoint: `/health`

**Method:** `GET`  
**Authentication:** None (public endpoint)

**Response:**

```json
{
  "status": "ok",
  "service": "Pricing API (Secured & Optimized)",
  "version": "2.0.0",
  "features": {
    "security": "API Key + Rate Limiting + HTTPS",
    "optimization": "Single query (6x faster)",
    "monitoring": "Performance metrics enabled"
  }
}
```

## 📝 Przykłady użycia

### cURL

```bash
curl -X POST http://localhost:5003/api/route-pricing \
  -H "Content-Type: application/json" \
  -H "X-API-Key: twoj-klucz-api" \
  -d '{"start_postal_code": "PL20", "end_postal_code": "DE49", "dystans": 850}'
```

### Python (requests)

```python
import requests

url = "http://localhost:5003/api/route-pricing"

payload = {
    "start_postal_code": "PL20",
    "end_postal_code": "DE49",
    "dystans": 850
}

headers = {
    'Content-Type': 'application/json',
    'X-API-Key': 'twoj-klucz-api'
}

response = requests.post(url, json=payload, headers=headers)
data = response.json()

if data['success']:
    prices = data['data']['calculated_prices']
    print(f"Cena naczepa: {prices['cena_naczepa']} EUR")
    print(f"Cena bus: {prices['cena_bus']} EUR")
    print(f"Cena solo: {prices['cena_solo']} EUR")
```

### JavaScript (fetch)

```javascript
fetch('http://localhost:5003/api/route-pricing', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'twoj-klucz-api'
  },
  body: JSON.stringify({
    start_postal_code: 'PL20',
    end_postal_code: 'DE49',
    dystans: 850
  })
})
.then(res => res.json())
.then(data => {
  if (data.success) {
    console.log('Calculated prices:', data.data.calculated_prices);
    console.log(`Naczepa: ${data.data.calculated_prices.cena_naczepa} EUR`);
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
