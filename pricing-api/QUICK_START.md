# Quick Start Guide - Pricing API

## 🚀 Start w 5 minut

### 1. Sprawdź czy masz wszystko
```bash
cd pricing-api
ls -la
```

Powinieneś zobaczyć:
- ✅ `app.py`
- ✅ `requirements.txt`
- ✅ `.env`
- ✅ `data/` (folder z plikami JSON)

### 2. Zainstaluj zależności
```bash
# Utwórz środowisko wirtualne (opcjonalnie)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Zainstaluj
pip install -r requirements.txt
```

### 3. Uruchom API
```bash
python app.py
```

Powinieneś zobaczyć:
```
 * Running on http://127.0.0.1:5001
```

### 4. Testuj!

**W nowym terminalu:**
```bash
# Health check
curl http://localhost:5001/health

# Test zapytania
curl -X POST http://localhost:5001/api/pricing \
  -H "Content-Type: application/json" \
  -d '{"start_postal_code": "PL50", "end_postal_code": "DE10"}'
```

**Lub uruchom testy:**
```bash
python test_api.py
```

## ✅ Gotowe!

API działa na `http://localhost:5001`

## 📖 Co dalej?

- **README.md** - pełna dokumentacja
- **EXAMPLES.md** - przykłady użycia w różnych językach
- **DEPENDENCY_LIST.md** - lista wszystkich zależności

## ❓ Problemy?

### API nie startuje
```bash
# Sprawdź czy port 5001 jest wolny
netstat -an | grep 5001  # Linux/Mac
netstat -an | findstr 5001  # Windows

# Zmień port
PORT=5002 python app.py
```

### Błąd połączenia z bazą
```bash
# Sprawdź plik .env
cat .env  # Linux/Mac
type .env # Windows

# Test połączenia
python -c "from app import _get_db_connection; conn = _get_db_connection(); print('✅ OK'); conn.close()"
```

### Brak danych dla trasy
To normalne - nie wszystkie trasy mają dane w bazie. Spróbuj innej trasy.

## 🌐 Deployment

### Heroku
```bash
git init
git add .
git commit -m "Initial commit"
heroku create your-app-name
heroku config:set POSTGRES_HOST=... POSTGRES_PORT=... POSTGRES_USER=... POSTGRES_PASSWORD=... POSTGRES_DB=...
git push heroku main
```

### Render
1. Push do GitHub
2. Połącz z Render.com
3. Dodaj zmienne środowiskowe w panelu
4. Deploy!

### Docker
```bash
docker build -t pricing-api .
docker run -p 5001:5001 --env-file .env pricing-api
```
