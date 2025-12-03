# Test finalny - Pricing API z rozszerzonymi danymi

## Co zostało dodane:

### ✅ TimoCom
1. **Mediany** - `median_price_per_km.trailer` (z kolumny `trailer_median_price_per_km`)
2. **Liczby ofert ogółem** - `total_offers` (suma `number_of_offers_total`)
3. **Liczby ofert po typach** - `offers_by_vehicle_type`:
   - `trailer` (suma `number_of_offers_trailer`)
   - `3_5t` (suma `number_of_offers_vehicle_up_to_3_5_t`)
   - `12t` (suma `number_of_offers_vehicle_up_to_12_t`)

### ✅ Trans.eu
1. **Mediany** - `median_price_per_km.lorry` (z kolumny `lorry_median_price_per_km`)
2. **Liczby ofert** - `total_offers` (suma `number_of_offers`)

## Uwagi:
- Mediany dla 3.5t i 12t w TimoCom są **null** - brak tych kolumn w bazie
- Wszystkie dane są agregowane za pomocą AVG() dla średnich i median, SUM() dla ofert

## Struktura odpowiedzi (przykład):

```json
{
  "success": true,
  "data": {
    "pricing": {
      "timocom": {
        "7d": {
          "avg_price_per_km": {
            "trailer": 1.084,
            "3_5t": 0.4707,
            "12t": 0.4375
          },
          "median_price_per_km": {
            "trailer": 1.12,  // ← NOWE
            "3_5t": null,      // ← Brak w bazie
            "12t": null        // ← Brak w bazie
          },
          "total_offers": 2005,  // ← NOWE
          "offers_by_vehicle_type": {  // ← NOWE
            "trailer": 1200,
            "3_5t": 450,
            "12t": 355
          },
          "days_with_data": 8
        }
      },
      "transeu": {
        "7d": {
          "avg_price_per_km": {
            "lorry": 1.34
          },
          "median_price_per_km": {  // ← NOWE
            "lorry": 1.35
          },
          "total_offers": 1580,  // ← NOWE
          "days_with_data": 8
        }
      }
    }
  }
}
```

## Test command:

```bash
python test_detailed_safe.py
```

lub

```python
import requests

response = requests.post(
    'http://localhost:5001/api/pricing',
    json={
        'start_postal_code': 'DE49',
        'end_postal_code': 'PL20'
    },
    timeout=60
)

data = response.json()['data']
tc7d = data['pricing']['timocom']['7d']

# Nowe pola dostępne:
print(f"Mediana trailer: {tc7d['median_price_per_km']['trailer']}")
print(f"Oferty ogółem: {tc7d['total_offers']}")
print(f"Oferty trailer: {tc7d['offers_by_vehicle_type']['trailer']}")
```

## Status: ✅ GOTOWE

API zostało rozszerzone o wszystkie dostępne dane z bazy:
- Średnie ✅
- Mediany ✅  
- Liczby ofert (ogółem i po typach) ✅
- Dokumentacja zaktualizowana ✅
