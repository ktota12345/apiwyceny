# API Authorization - Pricing API

## 🔒 Autoryzacja API Key

API wymaga klucza API (API key) w każdym requeście do endpointu `/api/pricing`.

## Konfiguracja

### 1. Wygeneruj API Key

```bash
python generate_api_key.py
```

Lub użyj własnego klucza (min. 32 znaki, losowe).

### 2. Dodaj do .env

```bash
API_KEY=twoj-wygenerowany-api-key-tutaj
```

### 3. Restart API

```bash
python app.py
```

## Użycie

### Wymagane headery

**Opcja 1: X-API-Key**
```http
POST /api/pricing HTTP/1.1
X-API-Key: twoj-api-key
Content-Type: application/json
```

**Opcja 2: Authorization Bearer**
```http
POST /api/pricing HTTP/1.1
Authorization: Bearer twoj-api-key
Content-Type: application/json
```

## Przykłady

### cURL

```bash
curl -X POST http://localhost:5001/api/pricing \
  -H "X-API-Key: twoj-api-key" \
  -H "Content-Type: application/json" \
  -d '{"start_postal_code": "PL50", "end_postal_code": "DE10"}'
```

### Python (requests)

```python
import requests

headers = {
    'X-API-Key': 'twoj-api-key',
    'Content-Type': 'application/json'
}

response = requests.post(
    'http://localhost:5001/api/pricing',
    headers=headers,
    json={
        'start_postal_code': 'PL50',
        'end_postal_code': 'DE10'
    }
)
```

### JavaScript (fetch)

```javascript
const headers = {
  'X-API-Key': 'twoj-api-key',
  'Content-Type': 'application/json'
};

const response = await fetch('http://localhost:5001/api/pricing', {
  method: 'POST',
  headers: headers,
  body: JSON.stringify({
    start_postal_code: 'PL50',
    end_postal_code: 'DE10'
  })
});
```

### Axios

```javascript
const axios = require('axios');

const config = {
  headers: {
    'X-API-Key': 'twoj-api-key'
  }
};

const response = await axios.post(
  'http://localhost:5001/api/pricing',
  {
    start_postal_code: 'PL50',
    end_postal_code: 'DE10'
  },
  config
);
```

## Kody błędów

### 401 Unauthorized - Brak API key

```json
{
  "success": false,
  "error": "Brak API key",
  "message": "Wymagany header: X-API-Key lub Authorization: Bearer <key>"
}
```

**Rozwiązanie:** Dodaj header `X-API-Key` lub `Authorization: Bearer <key>`

### 403 Forbidden - Nieprawidłowy API key

```json
{
  "success": false,
  "error": "Nieprawidłowy API key"
}
```

**Rozwiązanie:** Sprawdź czy klucz w requeście zgadza się z `API_KEY` w `.env`

## Health Check

Endpoint `/health` **NIE wymaga** API key:

```bash
curl http://localhost:5001/health
```

## Bezpieczeństwo

### ✅ Dobre praktyki

1. **Nigdy nie commituj** `.env` z prawdziwym API key do repo
2. **Używaj HTTPS** w produkcji (nie HTTP)
3. **Rotuj klucze** regularnie (co 3-6 miesięcy)
4. **Oddzielne klucze** dla dev/staging/production
5. **Monitoruj** użycie API (logi requestów)

### ⚠️ Co zrobić gdy klucz wycieknie

1. Natychmiast wygeneruj nowy klucz:
   ```bash
   python generate_api_key.py
   ```

2. Zmień `API_KEY` w `.env`

3. Restart API:
   ```bash
   python app.py
   ```

4. Zaktualizuj klucze u wszystkich klientów

## Deployment

### Heroku

```bash
heroku config:set API_KEY=your-api-key
```

### Render

Dodaj w panelu Render:
- Key: `API_KEY`
- Value: `your-api-key`

### Docker

```bash
docker run -e API_KEY=your-api-key ...
```

## Rate Limiting (opcjonalnie)

Możesz dodać rate limiting używając `flask-limiter`:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per day", "10 per minute"]
)

@app.route('/api/pricing', methods=['POST'])
@require_api_key
@limiter.limit("5 per minute")
def get_pricing():
    ...
```

## FAQ

### Czy mogę mieć wiele kluczy API?

Obecnie API wspiera tylko jeden klucz. Możesz rozszerzyć kod żeby wspierać wiele kluczy:

```python
API_KEYS = os.getenv('API_KEYS', '').split(',')

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key not in API_KEYS:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function
```

### Jak sprawdzić czy API key działa?

```bash
# Test z poprawnym kluczem
curl -X POST http://localhost:5001/api/pricing \
  -H "X-API-Key: your-real-key" \
  -H "Content-Type: application/json" \
  -d '{"start_postal_code": "PL50", "end_postal_code": "DE10"}'

# Powinno zwrócić 200 OK

# Test z błędnym kluczem
curl -X POST http://localhost:5001/api/pricing \
  -H "X-API-Key: wrong-key" \
  -H "Content-Type: application/json" \
  -d '{"start_postal_code": "PL50", "end_postal_code": "DE10"}'

# Powinno zwrócić 403 Forbidden
```
