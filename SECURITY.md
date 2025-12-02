# 🔐 Zabezpieczenia API

## Mechanizm autentykacji: API Key

Route Pricing API używa prostego i skutecznego mechanizmu API Key do autoryzacji żądań.

## Jak to działa

Każde żądanie do chronionego endpointu musi zawierać header:
```
X-API-Key: your-secret-api-key
```

### Chronione endpointy:
- ✅ `/api/route-pricing` - **Wymaga API key**

### Publiczne endpointy:
- ✅ `/` - Informacje o API (bez autentykacji)
- ✅ `/health` - Health check (bez autentykacji)

## Konfiguracja

### 1. Wygeneruj silny API key

**Opcja A: Użyj generatora online**
- https://randomkeygen.com/ - CodeIgniter Encryption Keys (512-bit)
- https://api-key-generator.com/

**Opcja B: Wygeneruj w Pythonie**
```python
import secrets
api_key = secrets.token_urlsafe(32)
print(f"API_KEY={api_key}")
```

**Opcja C: Wygeneruj w PowerShell**
```powershell
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
$apiKey = [Convert]::ToBase64String($bytes)
Write-Host "API_KEY=$apiKey"
```

**Przykład silnego klucza:**
```
API_KEY=rp_live_8f4e2d9a1b6c3f7e2d9a1b6c3f7e2d9a1b6c3f7e2d9a
```

### 2. Dodaj do zmiennych środowiskowych

**Lokalnie (.env):**
```bash
API_KEY=your-generated-api-key-here
REQUIRE_API_KEY=true
```

**Na Render:**
1. Dashboard → Your Service → Environment
2. Add Environment Variable
3. **Key:** `API_KEY`
4. **Value:** `your-generated-api-key-here`
5. **Key:** `REQUIRE_API_KEY`
6. **Value:** `true`
7. Save Changes
8. Redeploy

### 3. Wyłączenie autentykacji (NIE ZALECANE w produkcji!)

Jeśli z jakiegoś powodu chcesz wyłączyć autentykację:

```bash
REQUIRE_API_KEY=false
```

⚠️ **UWAGA:** To usuwa całą ochronę API! Używaj tylko w środowisku deweloperskim.

## Użycie API z autentykacją

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

### Python (requests)
```python
import requests

url = "https://your-api.onrender.com/api/route-pricing"
headers = {
    "Content-Type": "application/json",
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

### JavaScript (fetch)
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

### Postman
1. Utwórz nowe żądanie POST
2. URL: `https://your-api.onrender.com/api/route-pricing`
3. Headers tab:
   - Key: `Content-Type`, Value: `application/json`
   - Key: `X-API-Key`, Value: `your-api-key-here`
4. Body tab → raw → JSON:
   ```json
   {
     "start_postal_code": "PL50",
     "end_postal_code": "DE10",
     "vehicle_type": "naczepa"
   }
   ```
5. Send

## Kody błędów

### 401 Unauthorized
```json
{
  "success": false,
  "error": "Brak API key. Wymagany header: X-API-Key"
}
```
**Przyczyna:** Brak headera `X-API-Key` w żądaniu

**Rozwiązanie:** Dodaj header z API key

### 403 Forbidden
```json
{
  "success": false,
  "error": "Nieprawidłowy API key"
}
```
**Przyczyna:** Podany API key jest nieprawidłowy

**Rozwiązanie:** Sprawdź czy używasz poprawnego API key

### 500 Internal Server Error
```json
{
  "success": false,
  "error": "API nie jest poprawnie skonfigurowane"
}
```
**Przyczyna:** Serwer wymaga API key, ale nie jest on skonfigurowany

**Rozwiązanie:** Dodaj zmienną środowiskową `API_KEY` na serwerze

## Bezpieczeństwo

### ✅ Dobre praktyki

1. **Przechowuj bezpiecznie:**
   - ❌ Nie commituj API key do repozytorium
   - ❌ Nie udostępniaj API key publicznie
   - ✅ Używaj zmiennych środowiskowych
   - ✅ Dodaj `.env` do `.gitignore`

2. **Rotuj regularnie:**
   - Zmieniaj API key co 3-6 miesięcy
   - Zmień natychmiast jeśli podejrzewasz kompromitację

3. **Monitoruj użycie:**
   - Sprawdzaj logi pod kątem nieautoryzowanych prób dostępu
   - Render Dashboard → Logs → szukaj "Nieautoryzowana próba"

4. **Różne klucze dla różnych środowisk:**
   - Development: `API_KEY_DEV=...`
   - Production: `API_KEY_PROD=...`

5. **Używaj HTTPS:**
   - Render automatycznie zapewnia SSL/TLS
   - Nigdy nie wysyłaj API key przez HTTP (niezaszyfrowane)

### ⚠️ Czego unikać

- ❌ Hardcodowanie API key w kodzie
- ❌ Udostępnianie tego samego klucza wielu użytkownikom
- ❌ Używanie słabych kluczy (np. "123456", "apikey", "secret")
- ❌ Logowanie API key w plaintext
- ❌ Wysyłanie API key w URL (query params)

## Rate Limiting (opcjonalnie - TODO)

W przyszłości można dodać:
- Limit żądań per API key (np. 1000/dzień)
- Limit żądań per IP
- Mechanizm throttling

## Zaawansowane (opcjonalnie - TODO)

Możliwe rozszerzenia:
- Multiple API keys (różni użytkownicy)
- API key expiration (wygasanie kluczy)
- Scoped permissions (różne uprawnienia per key)
- JWT tokens zamiast API keys
- OAuth 2.0

## Support

Jeśli masz problemy z autentykacją:
1. Sprawdź czy API key jest poprawnie ustawiony (logi serwera)
2. Sprawdź czy header `X-API-Key` jest wysyłany
3. Sprawdź czy wartość API key się zgadza
4. Sprawdź logi Render: Dashboard → Logs

## Testowanie zabezpieczeń

Uruchom testy:
```bash
python test_api.py
```

Test sprawdzi:
- ✅ Czy endpoint bez API key zwraca 401
- ✅ Czy endpoint z prawidłowym API key zwraca 200
- ✅ Czy endpoint z nieprawidłowym API key zwraca 403

## Podsumowanie

- 🔑 Każde żądanie wymaga headera `X-API-Key`
- 🔒 Chroniony endpoint: `/api/route-pricing`
- 🌐 Publiczne endpointy: `/` i `/health`
- ⚙️ Konfiguracja: zmienna środowiskowa `API_KEY`
- 🔧 Włącz/wyłącz: `REQUIRE_API_KEY=true/false`
- 🛡️ Render automatycznie zapewnia HTTPS
