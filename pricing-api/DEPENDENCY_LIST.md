# Lista zależności i plików - Pricing API

## Pliki wymagane do działania

### 1. Główne pliki aplikacji
```
pricing-api/
├── app.py                          # Główna aplikacja Flask z API
├── requirements.txt                # Zależności Python
├── .env                           # Konfiguracja (kopia z głównego projektu)
└── .gitignore                     # Ignorowane pliki
```

### 2. Pliki mapowania (data/)
```
data/
├── transeu_to_timocom_mapping.json    # Mapowanie Trans.eu ID -> TimoCom ID
└── postal_code_to_region_transeu.json # Mapowanie kodów pocztowych -> Region ID
```

### 3. Pliki dokumentacji
```
├── README.md                      # Pełna dokumentacja API
├── DEPENDENCY_LIST.md            # Ten plik - lista zależności
├── test_api.py                   # Testy automatyczne
└── test_example.py               # Przykłady użycia
```

## Zależności Python (requirements.txt)

```
Flask==3.0.0                # Framework web
flask-cors==4.0.0           # CORS dla API
psycopg2-binary==2.9.9      # Sterownik PostgreSQL
python-dotenv==1.0.0        # Ładowanie zmiennych .env
gunicorn==21.2.0            # WSGI server produkcyjny
```

## Zależności zewnętrzne

### Baza danych PostgreSQL
- **Wymagane:** PostgreSQL 12+
- **Tabele:**
  - `public.offers` (TimoCom)
  - `public."OffersTransEU"` (Trans.eu)

### Struktura tabeli `public.offers` (TimoCom)
```sql
Kolumny:
- starting_id (INTEGER)
- destination_id (INTEGER)
- enlistment_date (DATE)
- trailer_avg_price_per_km (DECIMAL)
- vehicle_up_to_3_5_t_avg_price_per_km (DECIMAL)
- vehicle_up_to_12_t_avg_price_per_km (DECIMAL)
- number_of_offers_total (INTEGER)

Indeks (zalecany):
CREATE INDEX idx_offers_route_date 
ON public.offers (starting_id, destination_id, enlistment_date DESC);
```

### Struktura tabeli `public."OffersTransEU"`
```sql
Kolumny:
- starting_id (INTEGER)
- destination_id (INTEGER)
- enlistment_date (DATE)
- lorry_avg_price_per_km (DECIMAL)

Indeks (zalecany):
CREATE INDEX idx_offerstranseu_route_date 
ON public."OffersTransEU" (starting_id, destination_id, enlistment_date DESC);
```

## Zmienne środowiskowe (.env)

```env
POSTGRES_HOST=          # Host bazy danych
POSTGRES_PORT=5432      # Port PostgreSQL
POSTGRES_USER=          # Użytkownik bazy
POSTGRES_PASSWORD=      # Hasło
POSTGRES_DB=            # Nazwa bazy danych
```

## Pliki kopiowane z głównego projektu

### Z folderu `static/data/`
1. **transeu_to_timocom_mapping.json** (31.6 KB)
   - Mapowanie region_id między giełdami
   - Format: `{"134": {"timocom_id": 89, "distance_km": 2.5}, ...}`
   - Źródło: `wyceniarka/static/data/transeu_to_timocom_mapping.json`

2. **postal_code_to_region_transeu.json** (152.7 KB)
   - Mapowanie kody pocztowe -> Trans.eu region ID
   - Format: `{"PL50": {"region_id": 134, "distance_km": 2.5}, ...}`
   - Źródło: `wyceniarka/static/data/postal_code_to_region_transeu.json`

### Z głównego folderu
3. **.env** (9.0 KB)
   - Dane dostępowe do bazy PostgreSQL
   - Źródło: `wyceniarka/.env`
   - **UWAGA:** Ten plik NIE powinien być commitowany do repo!

## Uruchomienie - krok po kroku

### 1. Skopiuj folder
```bash
# Cały folder pricing-api zawiera wszystko co potrzebne
cp -r pricing-api /twoja/nowa/lokalizacja/
cd /twoja/nowa/lokalizacja/pricing-api
```

### 2. Utwórz środowisko wirtualne
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# lub
venv\Scripts\activate     # Windows
```

### 3. Zainstaluj zależności
```bash
pip install -r requirements.txt
```

### 4. Sprawdź konfigurację
```bash
# Upewnij się że plik .env istnieje i ma poprawne dane
cat .env  # Linux/Mac
type .env # Windows
```

### 5. Uruchom API
```bash
# Developerski
python app.py

# Produkcyjny
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

### 6. Testuj
```bash
# W nowym terminalu
python test_api.py
```

## Deployment do repo

### Co commitować:
✅ `app.py`
✅ `requirements.txt`
✅ `.gitignore`
✅ `.env.example`
✅ `README.md`
✅ `DEPENDENCY_LIST.md`
✅ `test_api.py`
✅ `test_example.py`
✅ `data/transeu_to_timocom_mapping.json`
✅ `data/postal_code_to_region_transeu.json`

### Czego NIE commitować:
❌ `.env` (zawiera hasła!)
❌ `__pycache__/`
❌ `venv/`
❌ `*.pyc`

### Kroki deployment:
```bash
cd pricing-api
git init
git add .
git commit -m "Initial commit - Pricing API"
git remote add origin <your-repo-url>
git push -u origin main
```

### Po sklonowaniu repo przez inną osobę:
```bash
git clone <your-repo-url>
cd pricing-api
cp .env.example .env
# Edytuj .env i uzupełnij dane bazy
pip install -r requirements.txt
python app.py
```

## Troubleshooting

### Brakujące pliki mapowania
```bash
# Sprawdź czy pliki są w folderze data/
ls -la data/

# Jeśli brakują, skopiuj z głównego projektu:
cp ../static/data/transeu_to_timocom_mapping.json data/
cp ../static/data/postal_code_to_region_transeu.json data/
```

### Problemy z połączeniem do bazy
```bash
# Sprawdź czy .env istnieje
ls -la .env

# Sprawdź zawartość (bez pokazywania hasła)
grep POSTGRES_HOST .env
grep POSTGRES_DB .env

# Test połączenia z bazą
python -c "from app import _get_db_connection; conn = _get_db_connection(); print('✅ Połączenie OK'); conn.close()"
```

### Port zajęty
```bash
# Zmień port w app.py (linia ostatnia):
# app.run(debug=False, host='0.0.0.0', port=5002)  # zmienione z 5001 na 5002

# Lub użyj zmiennej środowiskowej:
PORT=5002 python app.py
```

## Struktura importów w app.py

```python
from flask import Flask, jsonify, request  # Framework
from flask_cors import CORS                # CORS
import psycopg2                           # PostgreSQL
from psycopg2.extras import RealDictCursor # Słownikowe wyniki
from dotenv import load_dotenv            # Zmienne .env
import json                               # JSON
import os                                 # Ścieżki plików
from decimal import Decimal               # Konwersje
from typing import Any, Dict, Optional    # Type hints
```

## Minimalna wersja Python

**Python 3.8+** (ze względu na type hints i nowsze features Flask)

Sprawdź wersję:
```bash
python --version
```

## Rozmiar projektu

```
Całkowity rozmiar: ~200 KB
├── Kod Python (app.py + testy): ~20 KB
├── Pliki mapowania JSON: ~180 KB
└── Dokumentacja: ~15 KB
```

## Kontakt

W razie problemów z zależnościami lub brakami plików, skontaktuj się z zespołem deweloperskim.
