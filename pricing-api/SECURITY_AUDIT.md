# 🔒 Audyt Bezpieczeństwa - Pricing API

**Data audytu:** 3 grudnia 2025  
**Wersja:** 1.1.0

## ✅ Zabezpieczenia obecne w kodzie

### 1. ✅ SQL Injection - ZABEZPIECZONE
**Status:** ✅ Bezpieczne

```python
# Parametryzowane zapytania SQL - zabezpiecza przed SQL injection
cur.execute(query, (timocom_start_id, timocom_end_id, days))
```

**Wniosek:** Używamy `psycopg2` z parametryzowanymi zapytaniami. SQL injection nie jest możliwy.

### 2. ✅ API Key Authorization - OK
**Status:** ✅ Zaimplementowane

```python
def require_api_key(f):
    api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
    if not api_key:
        return 401
    if api_key != API_KEY:
        return 403
```

**Wniosek:** Podstawowa autoryzacja działa, ale brak rate limiting.

### 3. ✅ Input Validation - Częściowe
**Status:** ⚠️ Do poprawy

```python
start_postal = data.get('start_postal_code', '').strip().upper()
end_postal = data.get('end_postal_code', '').strip().upper()
```

**Wniosek:** Podstawowa walidacja jest, ale brak:
- Sprawdzenia długości input
- Walidacji formatu (regex)
- Sanityzacji znaków specjalnych

---

## ⚠️ ZNALEZIONE PODATNOŚCI

### 1. ⚠️ BRAK RATE LIMITING (DoS Risk)
**Severity:** MEDIUM  
**CVSS Score:** 5.3

**Problem:**
```python
@app.route('/api/pricing', methods=['POST'])
@require_api_key
def get_pricing():
    # Brak ograniczeń liczby requestów
```

**Exploit:**
Atakujący z prawidłowym API key może wysłać tysiące requestów przeciążając:
- Bazę danych (wiele zapytań SQL)
- Serwer (CPU/Memory)

**Dowód koncepcji:**
```python
import requests
import concurrent.futures

def attack():
    for _ in range(10000):
        requests.post(url, headers={'X-API-Key': key}, json=data)

with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
    futures = [executor.submit(attack) for _ in range(10)]
```

**Naprawa:**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per day", "20 per hour"],
    storage_uri="memory://"
)

@app.route('/api/pricing', methods=['POST'])
@require_api_key
@limiter.limit("5 per minute")
def get_pricing():
    ...
```

**Instalacja:**
```bash
pip install Flask-Limiter
```

---

### 2. ⚠️ SŁABA WALIDACJA INPUTU (Input Validation Bypass)
**Severity:** LOW-MEDIUM  
**CVSS Score:** 4.3

**Problem:**
```python
# Brak walidacji długości i formatu
start_postal = data.get('start_postal_code', '').strip().upper()
```

**Exploit:**
```python
# Długi input może spowodować performance issue
payload = {
    'start_postal_code': 'A' * 1000000,  # 1MB danych
    'end_postal_code': 'B' * 1000000
}
```

**Naprawa:**
```python
import re

def validate_postal_code(postal_code: str) -> bool:
    """Waliduje format kodu pocztowego"""
    if not postal_code or len(postal_code) > 10:
        return False
    # Format: 2 litery + max 5 cyfr
    pattern = r'^[A-Z]{2}\d{1,5}$'
    return bool(re.match(pattern, postal_code))

# W endpoincie:
start_postal = data.get('start_postal_code', '').strip().upper()
if not validate_postal_code(start_postal):
    return jsonify({'error': 'Nieprawidłowy format kodu pocztowego'}), 400
```

---

### 3. ⚠️ TIMING ATTACK na API Key (API Key Enumeration)
**Severity:** LOW  
**CVSS Score:** 3.7

**Problem:**
```python
if api_key != API_KEY:  # Porównanie string - podatne na timing attack
    return 403
```

**Exploit:**
Atakujący może użyć timing attack do odkrycia API key znak po znaku:
```python
import time
import requests

def timing_attack(guess):
    start = time.perf_counter()
    requests.post(url, headers={'X-API-Key': guess})
    return time.perf_counter() - start

# Odkryj każdy znak mierząc czas odpowiedzi
```

**Naprawa:**
```python
import secrets

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not api_key:
            return jsonify({'success': False, 'error': 'Brak API key'}), 401
        
        # Używamy secrets.compare_digest - odporny na timing attacks
        if not secrets.compare_digest(api_key, API_KEY):
            return jsonify({'success': False, 'error': 'Nieprawidłowy API key'}), 403
        
        return f(*args, **kwargs)
    return decorated_function
```

---

### 4. ⚠️ INFORMATION DISCLOSURE (Error Messages)
**Severity:** LOW  
**CVSS Score:** 3.1

**Problem:**
```python
except Exception as e:
    return jsonify({'success': False, 'error': 'Błąd serwera'}), 500
```

**Dobra praktyka:** ✅ Nie pokazujemy szczegółów błędów

Ale w logach może być:
```python
except Exception as exc:
    return None  # Nie logujemy błędu!
```

**Naprawa:**
```python
import logging

logger = logging.getLogger(__name__)

try:
    # ...
except Exception as exc:
    logger.error(f"Database error: {exc}", exc_info=True)
    return None
```

---

### 5. ⚠️ BRAK HTTPS ENFORCEMENT
**Severity:** HIGH (w produkcji)  
**CVSS Score:** 7.4

**Problem:**
API akceptuje HTTP - API key przesyłany plain text!

**Exploit:**
Man-in-the-middle może przechwycić API key:
```
HTTP Request:
POST /api/pricing
X-API-Key: dxWr5OjMTEb9pkf3SVWZdkLbJzyRwI0KVuVstHBPnKFJRFvv  ← PLAIN TEXT!
```

**Naprawa:**
```python
@app.before_request
def enforce_https():
    """Wymusza HTTPS w produkcji"""
    if not request.is_secure and os.getenv('ENV') == 'production':
        return jsonify({'error': 'HTTPS required'}), 403
```

---

### 6. ⚠️ DATABASE CONNECTION POOLING (Resource Exhaustion)
**Severity:** MEDIUM  
**CVSS Score:** 5.3

**Problem:**
```python
def get_timocom_pricing(...):
    conn = _get_db_connection()  # Nowe połączenie za każdym razem!
    # ...
    conn.close()
```

**Exploit:**
Wiele równoczesnych requestów wyczerpie pool połączeń do bazy.

**Naprawa:**
```python
from psycopg2 import pool

connection_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)

def _get_db_connection():
    return connection_pool.getconn()

def _return_db_connection(conn):
    connection_pool.putconn(conn)
```

---

### 7. ⚠️ CORS - WILDCARD (*) (XSS Risk)
**Severity:** MEDIUM  
**CVSS Score:** 5.4

**Problem:**
```python
CORS(app)  # Domyślnie: Access-Control-Allow-Origin: *
```

**Exploit:**
Każda strona może wywołać API i wykraść dane:
```javascript
// Evil website
fetch('http://your-api.com/api/pricing', {
  headers: {'X-API-Key': stolen_key}
}).then(r => r.json()).then(steal_data)
```

**Naprawa:**
```python
from flask_cors import CORS

# Tylko zaufane domeny
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://yourdomain.com",
            "https://app.yourdomain.com"
        ],
        "methods": ["POST"],
        "allow_headers": ["Content-Type", "X-API-Key", "Authorization"]
    }
})
```

---

### 8. ⚠️ NO REQUEST TIMEOUT (Slowloris Attack)
**Severity:** MEDIUM  
**CVSS Score:** 5.3

**Problem:**
Brak timeoutu dla requestów - atakujący może trzymać połączenia otwarte.

**Exploit:**
```python
# Slow POST attack
import socket
s = socket.socket()
s.connect(('localhost', 5001))
s.send(b'POST /api/pricing HTTP/1.1\r\n')
s.send(b'X-API-Key: key\r\n')
# Nie wysyłamy końca - trzymamy połączenie
time.sleep(1000)
```

**Naprawa:**
```python
# W Gunicorn config
timeout = 30
graceful_timeout = 30
```

```bash
gunicorn --timeout 30 --graceful-timeout 30 -w 4 app:app
```

---

### 9. ✅ ENVIRONMENT VARIABLES - OK ale...
**Severity:** INFO  
**CVSS Score:** N/A

**Obecny stan:** ✅ `.env` w `.gitignore`

**Ale:**
```bash
# .env zawiera REALNY API key!
API_KEY=dxWr5OjMTEb9pkf3SVWZdkLbJzyRwI0KVuVstHBPnKFJRFvv
```

**Rekomendacja:**
- Rotuj klucz przed deploymentem
- Użyj secrets managera (AWS Secrets Manager, HashiCorp Vault)
- Nigdy nie loguj API_KEY

---

### 10. ⚠️ NO AUDIT LOGGING (Brak śladów)
**Severity:** LOW  
**CVSS Score:** 2.1

**Problem:**
Brak logowania:
- Kto używa API
- Kiedy i jakie zapytania
- Nieudane próby autoryzacji

**Naprawa:**
```python
import logging

logger = logging.getLogger(__name__)

@app.route('/api/pricing', methods=['POST'])
@require_api_key
def get_pricing():
    # Log każdego requesta
    logger.info(f"API request from {request.remote_addr}")
    # ...
    
# W require_api_key:
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            logger.warning(f"Missing API key from {request.remote_addr}")
            return 401
            
        if not secrets.compare_digest(api_key, API_KEY):
            logger.warning(f"Invalid API key attempt from {request.remote_addr}: {api_key[:10]}...")
            return 403
```

---

## 📊 Podsumowanie podatności

| # | Podatność | Severity | CVSS | Status |
|---|-----------|----------|------|--------|
| 1 | Brak Rate Limiting | MEDIUM | 5.3 | ⚠️ Do naprawy |
| 2 | Słaba walidacja inputu | LOW-MEDIUM | 4.3 | ⚠️ Do poprawy |
| 3 | Timing attack na API key | LOW | 3.7 | ⚠️ Do naprawy |
| 4 | Information disclosure | LOW | 3.1 | ✅ OK (partial) |
| 5 | Brak HTTPS enforcement | HIGH | 7.4 | ⚠️ KRYTYCZNE (prod) |
| 6 | Brak connection pooling | MEDIUM | 5.3 | ⚠️ Do poprawy |
| 7 | CORS wildcard | MEDIUM | 5.4 | ⚠️ Do zmiany |
| 8 | Brak request timeout | MEDIUM | 5.3 | ⚠️ Do ustawienia |
| 9 | Secrets management | INFO | N/A | ℹ️ Rekomendacja |
| 10 | Brak audit logging | LOW | 2.1 | ⚠️ Do dodania |

## 🎯 Priorytet napraw

### 🔴 KRYTYCZNE (natychmiast):
1. ✅ **SQL Injection** - już zabezpieczone
2. ⚠️ **HTTPS w produkcji** - enforce przed deploymentem

### 🟡 WYSOKIE (przed production):
3. ⚠️ **Rate Limiting** - dodaj flask-limiter
4. ⚠️ **CORS restrictions** - ogranicz do zaufanych domen
5. ⚠️ **Connection pooling** - optymalizacja

### 🟢 ŚREDNIE (wkrótce):
6. ⚠️ **Input validation** - dodaj regex + length checks
7. ⚠️ **Timing attack fix** - użyj secrets.compare_digest
8. ⚠️ **Request timeout** - ustaw w gunicorn
9. ⚠️ **Audit logging** - dodaj logging

### ℹ️ NISKIE (opcjonalne):
10. ℹ️ **Secrets manager** - dla enterprise

## ✅ Zalecenia końcowe

1. **Dla developmentu (localhost):**
   - Obecny kod jest OK
   - Dodaj rate limiting (5/min)

2. **Dla production:**
   - ✅ HTTPS REQUIRED
   - ✅ Rate limiting REQUIRED  
   - ✅ CORS restrictions REQUIRED
   - ✅ Connection pooling RECOMMENDED
   - ✅ Audit logging RECOMMENDED

3. **Monitoring:**
   - Loguj failed auth attempts
   - Monitor rate limits
   - Alert na suspicious activity

## 📝 Next Steps

Czy chcesz żebym zaimplementował te poprawki?
Mogę stworzyć wersję `app_secure.py` z wszystkimi zabezpieczeniami.
