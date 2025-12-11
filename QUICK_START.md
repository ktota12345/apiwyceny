# 🚀 Quick Start Guide - API Wyceny Tras

## Minimalna Integracja w 5 Minut

### 1. Przygotuj Request

```javascript
POST /api/route-pricing

Headers:
  X-API-Key: twoj_klucz_api
  Content-Type: application/json

Body:
{
  "start_postal_code": "PL20",
  "end_postal_code": "DE49"
}
```

### 2. Odbierz Response

```javascript
{
  "success": true,
  "data": {
    "pricing": {
      "timocom": { "30d": {...} },      // Giełda TimoCom (30 dni)
      "transeu": { "30d": {...} },       // Giełda Trans.eu (30 dni)
      "historical": { "180d": {          // Twoje dane (180 dni)
        "FTL": {...},                    // Pełne ładunki
        "LTL": {...}                     // Ładunki częściowe
      }}
    },
    "currency": "EUR",
    "unit": "EUR/km"
  }
}
```

---

## 📊 Co Wyświetlić w GUI?

### Podstawowe Info:
- ✅ `start_postal_code` → `end_postal_code`
- ✅ `currency` (zawsze EUR)
- ✅ `unit` (zawsze EUR/km)

### Dane z Giełd (30 dni):

**TimoCom:**
```
pricing.timocom.30d.avg_price_per_km.trailer    // 0.85 EUR/km
pricing.timocom.30d.total_offers                 // 1245 ofert
```

**Trans.eu:**
```
pricing.transeu.30d.avg_price_per_km.lorry      // 0.87 EUR/km
pricing.transeu.30d.total_offers                 // 9240 ofert
```

### Dane Historyczne (180 dni):

**Match Info (dopasowanie trasy) 🆕:**
```
pricing.historical.180d.match_info.matched_start       // "PL20" (faktyczny kod)
pricing.historical.180d.match_info.matched_end         // "DE49" (faktyczny kod)
pricing.historical.180d.match_info.accuracy            // "exact" | "high" | "medium" | "low"
pricing.historical.180d.match_info.start_distance_km   // 0.0 (odległość od żądanego)
pricing.historical.180d.match_info.end_distance_km     // 0.0 (odległość od żądanego)
```

**FTL (Pełne ładunki):**
```
pricing.historical.180d.FTL.avg_price_per_km.client    // 0.95 EUR/km (sprzedaż)
pricing.historical.180d.FTL.avg_price_per_km.carrier   // 0.85 EUR/km (koszt)
pricing.historical.180d.FTL.total_orders               // 25 zleceń
pricing.historical.180d.FTL.top_carriers               // [4 przewoźników]
```

**LTL (Ładunki częściowe):**
```
pricing.historical.180d.LTL.avg_price_per_km.client    // 1.15 EUR/km
pricing.historical.180d.LTL.avg_price_per_km.carrier   // 1.05 EUR/km
pricing.historical.180d.LTL.total_orders               // 20 zleceń
pricing.historical.180d.LTL.top_carriers               // [4 przewoźników]
```

---

## 💡 Kluczowe Różnice

### Client vs Carrier (tylko w danych historycznych):
- **`client`** = Cena sprzedaży (ile dostajemy od klienta)
- **`carrier`** = Koszt realizacji (ile płacimy przewoźnikowi)
- **Marża** = client - carrier

### FTL vs LTL:
- **FTL** = Pełny ładunek → niższe stawki/km, wyższe kwoty
- **LTL** = Ładunek częściowy → wyższe stawki/km, niższe kwoty

### Okresy:
- **Giełdy** (TimoCom, Trans.eu) = ostatnie **30 dni**
- **Historia firmowa** (FTL/LTL) = ostatnie **180 dni** (6 miesięcy)

### Fuzzy Matching 🆕 (tylko dane historyczne):
API automatycznie znajduje najbliższą trasę gdy brak dokładnego dopasowania:
- **`exact`** = dokładne dopasowanie (< 1 km)
- **`high`** = bardzo podobna trasa (< 50 km)
- **`medium`** = podobna trasa (< 100 km)
- **`low`** = częściowe dopasowanie (start OK, end daleko)

**Rekomendacja UI:**
- `exact` → wyświetl normalnie
- `high`/`medium` → pokaż ikonę info ℹ️ z tooltipem
- `low` → pokaż ostrzeżenie ⚠️

---

## ⚡ Przykład Kodu

### JavaScript (fetch):

```javascript
const response = await fetch('https://api.domain.com/api/route-pricing', {
  method: 'POST',
  headers: {
    'X-API-Key': 'your_api_key',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    start_postal_code: 'PL20',
    end_postal_code: 'DE49'
  })
});

const result = await response.json();

if (result.success) {
  // TimoCom
  const timocomPrice = result.data.pricing.timocom?.['30d']?.avg_price_per_km?.trailer;
  
  // Historical FTL
  const historical = result.data.pricing.historical?.['180d'];
  const ftlPrice = historical?.FTL?.avg_price_per_km?.client;
  const ftlCarriers = historical?.FTL?.top_carriers || [];
  
  // Match Info (fuzzy matching) 🆕
  const matchInfo = historical?.match_info;
  if (matchInfo?.accuracy !== 'exact') {
    console.log(`⚠️ Fuzzy match: ${matchInfo.matched_start} → ${matchInfo.matched_end}`);
    console.log(`Accuracy: ${matchInfo.accuracy}, Distance: ±${matchInfo.start_distance_km}km`);
  }
  
  console.log('TimoCom:', timocomPrice, 'EUR/km');
  console.log('Historical FTL:', ftlPrice, 'EUR/km');
  console.log('Top carriers:', ftlCarriers.length);
}
```

### Python:

```python
import requests

response = requests.post(
    'https://api.domain.com/api/route-pricing',
    headers={'X-API-Key': 'your_api_key'},
    json={
        'start_postal_code': 'PL20',
        'end_postal_code': 'DE49'
    }
)

data = response.json()

if data['success']:
    pricing = data['data']['pricing']
    
    # TimoCom
    timocom = pricing.get('timocom', {}).get('30d', {})
    print(f"TimoCom: {timocom.get('avg_price_per_km', {}).get('trailer')} EUR/km")
    
    # Historical
    historical = pricing.get('historical', {}).get('180d', {})
    
    # Match Info (fuzzy matching) 🆕
    match_info = historical.get('match_info', {})
    if match_info.get('accuracy') != 'exact':
        print(f"⚠️ Fuzzy match: {match_info.get('matched_start')} → {match_info.get('matched_end')}")
        print(f"Accuracy: {match_info.get('accuracy')}, Distance: ±{match_info.get('start_distance_km')}km")
    
    # FTL
    ftl = historical.get('FTL', {})
    print(f"FTL client: {ftl.get('avg_price_per_km', {}).get('client')} EUR/km")
    print(f"FTL carriers: {len(ftl.get('top_carriers', []))}")
```

---

## 🛡️ Obsługa Błędów

```javascript
if (!result.success) {
  switch (response.status) {
    case 400: // Złe dane
      console.error('Nieprawidłowy format danych');
      break;
    case 401: // Brak autentykacji
      console.error('Nieprawidłowy API Key');
      break;
    case 404: // Brak danych
      console.error('Brak danych dla tej trasy');
      break;
    case 429: // Rate limit
      console.error('Za dużo requestów - poczekaj');
      break;
    default:
      console.error('Błąd serwera');
  }
}
```

---

## ✅ Checklist GUI

- [ ] Wyświetl ceny z TimoCom (avg + median)
- [ ] Wyświetl ceny z Trans.eu (avg + median)
- [ ] Wyświetl ceny historyczne FTL (client + carrier)
- [ ] Wyświetl ceny historyczne LTL (client + carrier)
- [ ] Pokaż top przewoźników dla FTL (max 4)
- [ ] Pokaż top przewoźników dla LTL (max 4)
- [ ] 🆕 Sprawdź `match_info.accuracy` dla danych historycznych
- [ ] 🆕 Pokaż ikonę/ostrzeżenie dla fuzzy match (high/medium/low)
- [ ] 🆕 Wyświetl tooltip z dopasowanymi kodami (matched_start → matched_end)
- [ ] Obsłuż brak danych (`null` values)
- [ ] Obsłuż brak całego źródła (check `data_sources`)
- [ ] Pokaż liczbę ofert/zleceń
- [ ] Pokaż okres danych (30d vs 180d)
- [ ] Obsłuż błędy (401, 404, 429, 500)

---

## 📐 Przykładowy Layout GUI

```
┌─────────────────────────────────────────┐
│  Trasa: PL20 → DE49 (850 km)           │
├─────────────────────────────────────────┤
│  GIEŁDY (30 dni):                       │
│  • TimoCom trailer:    0.85 EUR/km     │
│  • Trans.eu lorry:     0.87 EUR/km     │
├─────────────────────────────────────────┤
│  DANE HISTORYCZNE (180 dni): ℹ️         │
│  Podobna trasa: PL22 → DE47 (+35km)    │
│                                          │
│  FTL (Pełne ładunki):                   │
│  • Cena sprzedaży:     0.95 EUR/km     │
│  • Koszt realizacji:   0.85 EUR/km     │
│  • Marża:              0.10 EUR/km     │
│  • Zleceń: 25                           │
│                                          │
│  Top przewoźnicy FTL:                   │
│  1. TRANS-POL (15 zleceń)              │
│  2. EURO-TRANS (8 zleceń)              │
│  ...                                    │
├─────────────────────────────────────────┤
│  LTL (Ładunki częściowe):               │
│  • Cena sprzedaży:     1.15 EUR/km     │
│  • Koszt realizacji:   1.05 EUR/km     │
│  • Marża:              0.10 EUR/km     │
│  • Zleceń: 20                           │
└─────────────────────────────────────────┘

Uwaga: ℹ️ lub ⚠️ pojawia się tylko gdy 
accuracy != 'exact'
```

---

Pełna dokumentacja → `API_DOCUMENTATION.md`
