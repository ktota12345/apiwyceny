# Changelog - Pricing API

## [2.2.0] - 2024-12-05

### 🔧 Critical Data Quality Fix
- **Zmiana ze średniej arytmetycznej na średnią ważoną**
  - Wcześniej: `AVG(cena_za_km)` - prosta średnia ze wszystkich rekordów
  - Teraz: `SUM(cena_za_km × liczba_ofert) / SUM(liczba_ofert)` - średnia ważona
  - **Powód:** Rekord z 10,000 ofert powinien mieć większy wpływ niż rekord z 10 ofertami
  - Dotyczy zarówno TimoCom jak i Trans.eu

### 🚨 Filtrowanie Outlierów
- **Dodano filtrowanie błędnych danych:** wartości > 5 EUR/km są automatycznie odrzucane
- **Przykład znalezionego błędu:** trailer: 7472 EUR/km (powinno być ~1.5 EUR/km)
- **Debug logging:** API loguje wszystkie odrzucone outliery z:
  - Datą rekordu
  - Wartościami dla każdego typu pojazdu
  - Liczbą ofert
- Filtrowanie działa dla wszystkich typów pojazdów:
  - TimoCom: trailer, 3.5t, 12t
  - Trans.eu: lorry

### 📊 Improved Data Accuracy
- Użycie CTE (Common Table Expressions) dla lepszej czytelności SQL
- NULLIF() zabezpiecza przed dzieleniem przez zero
- Filtrowane dane trafiają również do obliczania median

### 🐛 Bug Fixed
- Naprawiono zawyżone średnie spowodowane outlierami w bazie danych
- Średnie są teraz reprezentatywne dla rzeczywistego rynku transportowego

---

## [2.1.0] - 2024-12-04

### 🔄 API Response Structure Change
- **Przywrócono zwracanie średnich stawek EUR/km** zamiast obliczonych cen całkowitych
- API zwraca teraz dane z obu giełd (TimoCom i Trans.eu) dla ostatnich 30 dni
- Response zawiera:
  - Średnie stawki per km dla każdego typu pojazdu
  - Mediany cen
  - Liczbę ofert
  - Liczbę dni z danymi
- **Zachowano optymalizację**: nadal tylko 2 zapytania (TimoCom 30d + Trans.eu 30d) zamiast 6
- Zakomentowano kod obliczający cenę całkowitą (dystans × stawka) - gotowy do przywrócenia

### 📚 Documentation Updates
- Zaktualizowano Swagger z nową strukturą response
- Dodano dokumentację do test_client.py z przykładem response
- Zaktualizowano opis endpointa

### ⚡ Performance
- **Nadal 3x szybciej** niż w v1.0 (2 zapytania vs 6 zapytań)
- Zachowano connection pooling i monitoring

---

## [2.0.1] - 2024-12-04

### 📚 Documentation
- **Kompletna aktualizacja Swagger/OpenAPI dokumentacji**:
  - Dodano brakujące pole `dystans` jako required parameter
  - Zaktualizowano strukturę response z `calculated_prices` (cena_naczepa, cena_bus, cena_solo)
  - Dodano szczegółowe przykłady request/response
  - Dodano walidację pattern dla kodów pocztowych
  - Zaktualizowano opisy wszystkich kodów błędów (400, 401, 403, 404, 429, 500)
  - Dodano informacje o walutach i limitach rate limiting
- Zaktualizowano `/health` endpoint z wersją 2.0.0 i listą features

---

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
