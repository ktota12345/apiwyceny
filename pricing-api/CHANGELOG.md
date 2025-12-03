# Changelog - Pricing API

## [1.1.0] - 2025-12-03

### Added (Dodano)
- ✅ **Autoryzacja API Key** - endpoint `/api/pricing` wymaga teraz API key
- ✅ **Mediany cen** - dodano `median_price_per_km` dla TimoCom (trailer) i Trans.eu (lorry)
- ✅ **Liczby ofert** - dodano `total_offers` dla obu giełd
- ✅ **Rozbicie ofert po typach** - dodano `offers_by_vehicle_type` dla TimoCom (trailer, 3.5t, 12t)
- ✅ **Generator API key** - skrypt `generate_api_key.py` do generowania bezpiecznych kluczy
- ✅ **Dokumentacja autoryzacji** - plik `API_AUTHORIZATION.md` z instrukcjami
- ✅ **Testy autoryzacji** - `test_with_api_key.py` do testowania zabezpieczeń

### Changed (Zmieniono)
- 🔧 Usunięto logi debug (print statements) - nie wpływają już na performance
- 🔧 Skrócono docstringi dla lepszej czytelności
- 🔧 Uproszczono obsługę błędów (brak stack traces w produkcji)

### Security (Bezpieczeństwo)
- 🔒 Endpoint `/api/pricing` wymaga API key (401/403)
- 🔒 Health check `/health` nadal dostępny bez klucza
- 🔒 Wsparcie dla dwóch metod autoryzacji: `X-API-Key` i `Authorization: Bearer`

## [1.0.0] - 2025-12-03

### Initial Release

- ✅ Standalone REST API dla wyceny tras
- ✅ Endpoint `POST /api/pricing` z danymi dla TimoCom i Trans.eu
- ✅ Trzy okresy czasowe: 7d, 30d, 90d
- ✅ Mapowanie kodów pocztowych (format: PL50, DE10, etc.)
- ✅ Połączenie z PostgreSQL
- ✅ CORS enabled
- ✅ Health check endpoint
- ✅ Pełna dokumentacja (README.md)
