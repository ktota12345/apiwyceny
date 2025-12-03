# HTTP Headers Guide - Pricing API

## 📤 Request Headers (Co musisz wysłać)

### Wymagane Headers

#### `Content-Type: application/json`
**WYMAGANE** dla wszystkich POST requestów

```bash
Content-Type: application/json
```

### Przykład pełnego requestu:

```http
POST /api/pricing HTTP/1.1
Host: localhost:5001
Content-Type: application/json
Content-Length: 65

{
  "start_postal_code": "PL50",
  "end_postal_code": "DE10"
}
```

## 📥 Response Headers (Co otrzymasz)

API automatycznie zwraca następujące headery:

### Standardowe Headers

```http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 1234
Date: Wed, 03 Dec 2025 10:23:23 GMT
Server: Werkzeug/3.0.3 Python/3.12.7
Connection: close
```

### CORS Headers

API ma włączone CORS dla wszystkich origin:

```http
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

To oznacza że możesz wywołać API z:
- ✅ Innej domeny (CORS)
- ✅ Przeglądarki (JavaScript)
- ✅ Aplikacji mobilnej
- ✅ Innego backendu

## 🔧 Przykłady dla różnych narzędzi

### cURL

```bash
curl -X POST http://localhost:5001/api/pricing \
  -H "Content-Type: application/json" \
  -d '{"start_postal_code": "PL50", "end_postal_code": "DE10"}'
```

### Python (requests)

```python
import requests

headers = {
    'Content-Type': 'application/json'
}

response = requests.post(
    'http://localhost:5001/api/pricing',
    json={  # json= automatycznie ustawia Content-Type
        'start_postal_code': 'PL50',
        'end_postal_code': 'DE10'
    }
)
```

**Uwaga:** `requests.post(..., json=data)` automatycznie dodaje `Content-Type: application/json`

### JavaScript (fetch)

```javascript
const headers = {
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

const response = await axios.post(
  'http://localhost:5001/api/pricing',
  {
    start_postal_code: 'PL50',
    end_postal_code: 'DE10'
  },
  {
    headers: {
      'Content-Type': 'application/json'
    }
  }
);
```

**Uwaga:** Axios automatycznie dodaje `Content-Type: application/json` dla obiektów

### PowerShell

```powershell
$headers = @{
    "Content-Type" = "application/json"
}

$body = @{
    start_postal_code = "PL50"
    end_postal_code = "DE10"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://localhost:5001/api/pricing" `
    -Method Post `
    -Headers $headers `
    -Body $body
```

### Postman

**Headers tab:**
```
Content-Type: application/json
```

**Body tab (raw, JSON):**
```json
{
  "start_postal_code": "PL50",
  "end_postal_code": "DE10"
}
```

## 🔒 Opcjonalne Headers (dla rozszerzeń)

### Autoryzacja (jeśli dodasz w przyszłości)

```http
Authorization: Bearer your-api-key-here
```

### Custom Headers (jeśli dodasz)

```http
X-API-Key: your-api-key
X-Request-ID: unique-request-id
X-Client-Version: 1.0.0
```

## ❌ Czego NIE potrzebujesz

### Nie musisz wysyłać:

- ❌ `Accept: application/json` - API zawsze zwraca JSON
- ❌ `Authorization` - API nie ma autoryzacji (na razie)
- ❌ `User-Agent` - opcjonalne
- ❌ `Accept-Encoding` - opcjonalne
- ❌ `Connection` - ustawiane automatycznie

## 📊 Response Status Codes

### Sukces
- `200 OK` - Znaleziono dane

### Błędy klienta
- `400 Bad Request` - Brak wymaganych pól
- `404 Not Found` - Brak danych dla trasy / nieprawidłowy kod pocztowy

### Błędy serwera
- `500 Internal Server Error` - Błąd serwera / bazy danych

## 🧪 Test Headers

### Sprawdź co API zwraca:

```bash
curl -v http://localhost:5001/health
```

Output:
```http
< HTTP/1.1 200 OK
< Server: Werkzeug/3.0.3 Python/3.12.7
< Date: Wed, 03 Dec 2025 10:23:23 GMT
< Content-Type: application/json
< Content-Length: 58
< Access-Control-Allow-Origin: *
< Connection: close
<
{"service":"Pricing API","status":"ok","version":"1.0.0"}
```

## 💡 Pro Tips

### 1. Python requests - najłatwiej
```python
import requests

# ✅ To wystarczy - Content-Type jest automatyczny
response = requests.post('http://localhost:5001/api/pricing', json=data)
```

### 2. Content-Length
Nie musisz ręcznie ustawiać - większość bibliotek robi to automatycznie

### 3. CORS w przeglądarce
API ma włączone CORS, więc możesz wywoływać z JavaScript bez problemów:

```javascript
// To działa nawet z innej domeny!
fetch('http://localhost:5001/api/pricing', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ start_postal_code: 'PL50', end_postal_code: 'DE10' })
})
```

## 🔍 Debug Headers

### Zobacz wszystkie headery w Python:

```python
import requests

response = requests.post(
    'http://localhost:5001/api/pricing',
    json={'start_postal_code': 'PL50', 'end_postal_code': 'DE10'}
)

print("Request Headers:")
print(response.request.headers)

print("\nResponse Headers:")
print(response.headers)
```

### W cURL:

```bash
# Pokaż tylko headery
curl -I http://localhost:5001/health

# Pokaż wszystko (verbose)
curl -v http://localhost:5001/health
```

## ⚠️ Częste błędy

### 1. Brak Content-Type
```bash
# ❌ Błąd - API nie zrozumie JSON
curl -X POST http://localhost:5001/api/pricing \
  -d '{"start_postal_code": "PL50"}'

# ✅ Poprawnie
curl -X POST http://localhost:5001/api/pricing \
  -H "Content-Type: application/json" \
  -d '{"start_postal_code": "PL50", "end_postal_code": "DE10"}'
```

### 2. Nieprawidłowy Content-Type
```python
# ❌ Błąd
headers = {'Content-Type': 'text/plain'}

# ✅ Poprawnie  
headers = {'Content-Type': 'application/json'}
```

### 3. Zapomniany JSON.stringify w JavaScript
```javascript
// ❌ Błąd
body: {start_postal_code: 'PL50'}

// ✅ Poprawnie
body: JSON.stringify({start_postal_code: 'PL50'})
```

## 📋 Checklist

Przed wysłaniem requestu sprawdź:

- [ ] Używasz metody **POST** (nie GET)
- [ ] Ustawiłeś header: `Content-Type: application/json`
- [ ] Body jest w formacie **JSON** (nie URL-encoded)
- [ ] Masz wymagane pola: `start_postal_code` i `end_postal_code`
- [ ] Kody pocztowe są w formacie: `KOD_KRAJU` + 2 cyfry (np. PL50)

## 🎓 Podsumowanie

### Minimalne wymagania:
```
POST /api/pricing HTTP/1.1
Content-Type: application/json

{"start_postal_code": "PL50", "end_postal_code": "DE10"}
```

### Co dostaniesz w odpowiedzi:
```
HTTP/1.1 200 OK
Content-Type: application/json
Access-Control-Allow-Origin: *

{"success": true, "data": {...}}
```

That's it! 🎉
