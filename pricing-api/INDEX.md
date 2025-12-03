# 📚 Indeks dokumentacji - Pricing API

## 🚀 Start tutaj

### Nowy użytkownik?
1. **[QUICK_START.md](QUICK_START.md)** - zacznij tutaj! (5 minut)
2. **[README.md](README.md)** - pełna dokumentacja
3. **[EXAMPLES.md](EXAMPLES.md)** - przykłady użycia

### Developer?
1. **[DEPENDENCY_LIST.md](DEPENDENCY_LIST.md)** - wszystkie zależności
2. **[PODSUMOWANIE.md](PODSUMOWANIE.md)** - co zostało zrobione
3. **test_api.py** - uruchom testy

## 📄 Pliki dokumentacji

### 📖 [README.md](README.md)
**Główna dokumentacja**
- Instalacja krok po kroku
- Konfiguracja
- Szczegóły API
- Deployment
- Troubleshooting

**Czytaj gdy:**
- Chcesz poznać wszystkie funkcje
- Masz problem do rozwiązania
- Planujesz deployment

---

### ⚡ [QUICK_START.md](QUICK_START.md)
**Start w 5 minut**
- Minimalne kroki
- Szybkie uruchomienie
- Podstawowe testy

**Czytaj gdy:**
- Chcesz szybko przetestować API
- Nie masz czasu na długą dokumentację
- Potrzebujesz tylko podstaw

---

### 📋 [DEPENDENCY_LIST.md](DEPENDENCY_LIST.md)
**Lista wszystkich zależności**
- Pliki wymagane
- Struktura bazy danych
- Pliki mapowania
- Zależności Python
- Co kopiować z głównego projektu

**Czytaj gdy:**
- Przenosisz projekt do nowej lokalizacji
- Brakuje Ci jakichś plików
- Chcesz wiedzieć co jest potrzebne

---

### 💡 [EXAMPLES.md](EXAMPLES.md)
**Przykłady użycia**
- cURL
- Python (requests, asyncio, batch)
- JavaScript (fetch, axios)
- PHP
- PowerShell
- Excel/VBA
- Postman

**Czytaj gdy:**
- Chcesz zintegrować API z aplikacją
- Szukasz przykładów w swoim języku
- Potrzebujesz gotowego kodu

---

### 📊 [PODSUMOWANIE.md](PODSUMOWANIE.md)
**Co zostało zrobione**
- Lista plików
- Funkcjonalność
- Technologie
- Status testów
- Porównanie z główną aplikacją

**Czytaj gdy:**
- Chcesz wiedzieć co dokładnie zostało stworzone
- Potrzebujesz przeglądu projektu
- Piszesz raport/dokumentację

---

## 🔧 Pliki kodu

### `app.py`
Główna aplikacja Flask z endpointami:
- `/health` - health check
- `/api/pricing` - pobieranie cen

### `test_api.py`
Testy automatyczne:
- Health check
- Pricing endpoint
- Walidacja błędów
- Brakujące dane

### `test_example.py`
Przykłady testowania różnych tras

## ⚙️ Pliki konfiguracji

### `.env`
**NIE commituj tego pliku!**
Zawiera dane dostępowe do bazy danych:
- POSTGRES_HOST
- POSTGRES_PASSWORD
- itd.

### `.env.example`
Szablon dla `.env` (bez haseł)

### `requirements.txt`
Zależności Python (5 pakietów)

### `.gitignore`
Pliki ignorowane przez git

### `Procfile`
Dla deploymentu na Heroku

### `runtime.txt`
Wersja Python dla Heroku

## 📁 Folder `data/`

### `transeu_to_timocom_mapping.json`
Mapowanie region_id między giełdami:
```json
{
  "134": {
    "timocom_id": 89,
    "distance_km": 2.5
  }
}
```

### `postal_code_to_region_transeu.json`
Mapowanie kodów pocztowych na regiony:
```json
{
  "PL50": {
    "region_id": 134,
    "distance_km": 2.5
  }
}
```

## 🎯 Najczęstsze pytania

### Jak szybko przetestować API?
→ **[QUICK_START.md](QUICK_START.md)**

### Jak używać API w moim języku?
→ **[EXAMPLES.md](EXAMPLES.md)**

### Jakich plików potrzebuję?
→ **[DEPENDENCY_LIST.md](DEPENDENCY_LIST.md)**

### Jak zdeployować?
→ **[README.md](README.md)** - sekcja "Deployment"

### Co API zwraca?
→ **[README.md](README.md)** - sekcja "Response"

### Mam problem, co robić?
→ **[README.md](README.md)** - sekcja "Troubleshooting"

## 📈 Kolejność czytania

### Dla początkujących:
1. **INDEX.md** (ten plik) ← jesteś tutaj
2. **QUICK_START.md** ← zacznij tutaj
3. **README.md** ← potem to
4. **EXAMPLES.md** ← na końcu

### Dla zaawansowanych:
1. **PODSUMOWANIE.md** ← przegląd
2. **DEPENDENCY_LIST.md** ← techniczne
3. **app.py** ← kod źródłowy
4. **test_api.py** ← testy

### Dla deploymentu:
1. **README.md** - sekcja "Deployment"
2. **DEPENDENCY_LIST.md** - sekcja "Deployment do repo"
3. **Procfile** + **runtime.txt**

## 🎓 Terminologia

- **Kod pocztowy** - format: KOD_KRAJU + 2 cyfry (np. PL50, DE10)
- **Region ID** - ID regionu w bazie Trans.eu
- **TimoCom ID** - ID regionu w bazie TimoCom (mapowane)
- **Pricing** - ceny transportowe (EUR/km)
- **7d/30d/90d** - okresy czasu (dni wstecz)
- **avg** - średnia (average)
- **median** - mediana
- **trailer** - naczepa
- **lorry** - ciężarówka (Trans.eu)

## ✨ Quick Links

- **Uruchom API:** `python app.py`
- **Uruchom testy:** `python test_api.py`
- **Health check:** `curl http://localhost:5001/health`
- **Test zapytania:** `curl -X POST http://localhost:5001/api/pricing -H "Content-Type: application/json" -d '{"start_postal_code": "PL50", "end_postal_code": "DE10"}'`

## 📞 Support

W razie problemów:
1. Sprawdź **[README.md](README.md)** - sekcja "Troubleshooting"
2. Sprawdź **[DEPENDENCY_LIST.md](DEPENDENCY_LIST.md)**
3. Uruchom testy: `python test_api.py`
4. Skontaktuj się z zespołem deweloperskim

---

**Wersja:** 1.0.0  
**Data:** 3 grudnia 2025  
**Status:** ✅ Production Ready
