# Changelog - Pricing API

## [2.0.0] - 2024-12-04

### 🚀 Performance Improvements
- **Główna optymalizacja**: Zredukowano liczbę zapytań do bazy z 6 do 1
  - Przed: 3x TimoCom (7d, 30d, 90d) + 3x Trans.eu (7d, 30d, 90d)
  - Po: 1x TimoCom (30d) - jedyne dane faktycznie używane
  - **Przyspieszenie: ~6x**
- Dodano szczegółowe logowanie performance metrics:
  - Czas połączenia z bazą
  - Czas wykonania zapytań SQL
  - Czas obliczeń
  - Całkowity czas requestu

### 🔒 Security Enhancements
- Dodano weryfikację aktywności połączeń DB przed użyciem
- Implementacja auto-reconnect dla stale connections
- Dodano security headers:
  - X-Content-Type-Options: nosniff
  - X-Frame-Options: DENY
  - X-XSS-Protection: 1; mode=block
  - Strict-Transport-Security (HSTS)
- Connection pool z konfigurowalnymi timeoutami:
  - connect_timeout: 10s
  - statement_timeout: 30s

### 🐛 Bug Fixes
- Naprawiono problem z zamykającymi się połączeniami DB (`psycopg2.OperationalError`)
- Poprawiono obsługę długotrwałych zapytań SQL

### 📝 Existing Security Features (Confirmed)
- ✅ API Key authentication z timing-attack protection
- ✅ Rate limiting (100/day, 20/hour, 5/min per endpoint)
- ✅ Input validation (regex, length limits, sanitization)
- ✅ SQL injection protection (parametrized queries)
- ✅ CORS whitelist
- ✅ HTTPS enforcement w produkcji
- ✅ Comprehensive security logging

### 📊 Monitoring
- Dodano timestampy dla wszystkich operacji DB
- Logowanie czasów wykonania requestów
- Identyfikacja wąskich gardeł performance

---

## [1.0.0] - 2024-12-03

### Initial Release
- Basic route pricing endpoint
- TimoCom & Trans.eu data integration
- PostgreSQL database connection
- API key authentication
- Basic rate limiting
