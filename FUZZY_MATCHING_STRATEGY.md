# Strategia Fuzzy Matching dla Tras Historycznych

## 📋 Cel

Wyświetlanie danych historycznych nawet w sytuacji, gdy nie mamy 100% dopasowania podanych w żądaniu kodów pocztowych do tych w bazie danych.

## 🎯 Problem

Użytkownik może zapytać o trasę `PL30 -> DE60`, ale w bazie mamy tylko dane dla tras `PL32 -> DE58`. Bez fuzzy matching API zwróci brak danych historycznych, mimo że mamy podobne trasy.

## 💡 Rozwiązanie

### Algorytm Fuzzy Matching

1. **Geocodowanie kodów pocztowych**
   - Wykorzystanie tabeli `PostalCodeCoordinates` z pre-obliczonymi współrzędnymi
   - Format: `PL20` = country: `PL`, postal_code: `20`
   - Każdy unikalny kod z `ZleceniaSpeed` ma zapisane współrzędne geograficzne

2. **Hierarchiczne dopasowanie tras**
   
   **Krok 1:** Znajdź najbliższy punkt startowy
   - Oblicz odległość (Haversine) między żądanym punktem startowym a wszystkimi unikalnymi punktami startowymi w bazie
   - Filtruj tylko te < 100 km
   
   **Krok 2:** Dla najbliższego punktu startowego, znajdź najbliższy punkt końcowy
   - Oblicz odległość między żądanym punktem końcowym a punktami końcowymi dla wybranego punktu startowego
   - Wybierz trasę z najmniejszą sumą odległości (start + end)
   
   **Krok 3:** Oceń jakość dopasowania
   - `exact`: odległości < 1 km (praktycznie ten sam punkt)
   - `high`: odległości < 50 km (bardzo podobna trasa)
   - `medium`: odległości < 100 km (podobna trasa)
   - `low`: punkt startowy < 100 km, ale punkt końcowy > 100 km

3. **Zwracanie wyników z metadanymi**
   - Statystyki dla dopasowanej trasy
   - Informacje o dopasowaniu w `match_info`:
     - `matched_start`: faktyczny kod startowy
     - `matched_end`: faktyczny kod końcowy
     - `accuracy`: poziom dokładności
     - `start_distance_km`: odległość punktów startowych
     - `end_distance_km`: odległość punktów końcowych

## 📊 Przykład Odpowiedzi API

### Dokładne dopasowanie (exact)
```json
{
  "success": true,
  "data": {
    "pricing": {
      "historical": {
        "180d": {
          "match_info": {
            "matched_start": "PL20",
            "matched_end": "DE49",
            "accuracy": "exact",
            "start_distance_km": 0.0,
            "end_distance_km": 0.0
          },
          "FTL": { /* statystyki */ },
          "LTL": { /* statystyki */ }
        }
      }
    }
  }
}
```

### Fuzzy match z wysoką dokładnością
```json
{
  "success": true,
  "data": {
    "pricing": {
      "historical": {
        "180d": {
          "match_info": {
            "matched_start": "PL22",
            "matched_end": "DE47",
            "accuracy": "high",
            "start_distance_km": 35.2,
            "end_distance_km": 42.8
          },
          "FTL": { /* statystyki */ },
          "LTL": { /* statystyki */ }
        }
      }
    }
  }
}
```

### Fuzzy match z niską dokładnością
```json
{
  "success": true,
  "data": {
    "pricing": {
      "historical": {
        "180d": {
          "match_info": {
            "matched_start": "PL22",
            "matched_end": "DE10",
            "accuracy": "low",
            "start_distance_km": 45.5,
            "end_distance_km": 135.7
          },
          "FTL": { /* statystyki */ },
          "LTL": { /* statystyki */ }
        }
      }
    }
  }
}
```

## ⚙️ Implementacja

### Komponenty

1. **`haversine_distance()`**
   - Oblicza odległość między dwoma punktami geograficznymi w km
   - Wzór Haversine dla dokładnych obliczeń na sferze

2. **`get_postal_code_coordinates()`**
   - Pobiera współrzędne z tabeli `PostalCodeCoordinates`
   - Cache w pamięci dla wydajności

3. **`find_nearest_historical_route()`**
   - Główna logika fuzzy matching
   - Zwraca najbliższą trasę z metadanymi

4. **`get_historical_orders_pricing()` (zmodyfikowana)**
   - Najpierw próbuje exact match
   - Przy braku danych wywołuje fuzzy matching
   - Dodaje `match_info` do wyniku

### Tabela PostalCodeCoordinates

```sql
CREATE TABLE "PostalCodeCoordinates" (
    id SERIAL PRIMARY KEY,
    country VARCHAR(2) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lng DOUBLE PRECISION NOT NULL,
    label VARCHAR(500),
    geocoded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(country, postal_code)
);

CREATE INDEX idx_postal_code_country 
ON "PostalCodeCoordinates" (country, postal_code);
```

## 🔍 Kryteria Jakości

### Dlaczego 100 km?

- **Transport międzynarodowy**: trasy 500+ km
- **Margines błędu**: 100 km to ~10-20% typowej trasy
- **Wartość biznesowa**: dane z podobnej trasy są lepsze niż brak danych
- **Cena za km**: nie zmienia się drastycznie w promieniu 100 km dla tego samego regionu

### Poziomy Dokładności

| Accuracy | Start Distance | End Distance | Zastosowanie |
|----------|----------------|--------------|--------------|
| `exact` | < 1 km | < 1 km | Ten sam kod pocztowy lub bardzo bliski |
| `high` | < 50 km | < 50 km | Bardzo podobna trasa, wysokie zaufanie |
| `medium` | < 100 km | < 100 km | Podobna trasa, umiarkowane zaufanie |
| `low` | < 100 km | > 100 km | Tylko start jest podobny, niskie zaufanie |

## 🎨 Rekomendacje UI/UX

### Wyświetlanie w GUI

1. **Exact match**: Wyświetl normalnie bez dodatkowych oznaczeń

2. **High/Medium accuracy**: 
   - Pokaż ikonę ostrzeżenia ⚠️
   - Tooltip: "Dane z podobnej trasy: PL22 → DE47 (odległość: 35km, 43km)"

3. **Low accuracy**:
   - Pokaż ikonę ⚠️ z żółtym tłem
   - Wyraźna informacja: "Uwaga: Dane z trasy o podobnym punkcie startowym, ale innym końcowym"
   - Tooltip z dokładnymi odległościami

### Przykład kodu (JavaScript)

```javascript
const matchInfo = response.data.pricing.historical['180d'].match_info;

if (matchInfo.accuracy === 'exact') {
  // Wyświetl normalnie
  showHistoricalData(data);
} else if (matchInfo.accuracy === 'high' || matchInfo.accuracy === 'medium') {
  // Pokaż z ostrzeżeniem
  showHistoricalDataWithWarning(
    data,
    `Dane z podobnej trasy: ${matchInfo.matched_start} → ${matchInfo.matched_end} 
     (odległość: ${matchInfo.start_distance_km}km, ${matchInfo.end_distance_km}km)`
  );
} else if (matchInfo.accuracy === 'low') {
  // Pokaż z wyraźnym ostrzeżeniem
  showHistoricalDataWithStrongWarning(
    data,
    `⚠️ Niska dokładność: Trasa ${matchInfo.matched_start} → ${matchInfo.matched_end} 
     ma podobny punkt startowy (+${matchInfo.start_distance_km}km), 
     ale inny końcowy (+${matchInfo.end_distance_km}km)`
  );
}
```

## 🚀 Korzyści

1. **Lepsza użyteczność**: Dane historyczne dostępne dla większej liczby zapytań
2. **Transparentność**: Użytkownik wie, skąd pochodzą dane
3. **Elastyczność**: System dostosowuje się do dostępnych danych
4. **Wartość biznesowa**: Wykorzystanie istniejących danych do generowania insights

## ⚡ Optymalizacja

### Aktualna implementacja
- Współrzędne pobierane z tabeli `PostalCodeCoordinates`
- Zapytanie SQL pobiera wszystkie unikalne trasy z ostatnich 180 dni
- Obliczenia odległości w Pythonie (Haversine)

### Możliwe przyszłe usprawnienia
1. **Cache tras**: Cachowanie unikalnych tras w Redis
2. **PostGIS**: Użycie `ST_Distance` dla obliczeń w bazie
3. **Spatial Index**: Indeksy geograficzne dla szybszego wyszukiwania
4. **Pre-aggregacja**: Tabela z pre-obliczonymi dystansami między popularnymi punktami

## 📝 Historia zmian

- **v2.4.0** (2024-12-11): Dodanie fuzzy matching dla tras historycznych
  - Implementacja algorytmu Haversine
  - Integracja z `PostalCodeCoordinates`
  - Dodanie `match_info` do odpowiedzi API
  - Dokumentacja Swagger zaktualizowana
