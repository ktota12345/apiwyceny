# 🚀 START HERE - Route Pricing API

## ✅ Co zostało przygotowane

Utworzono kompletne, osobne repozytorium API z pełną integracją PostgreSQL:

### Struktura projektu:
```
route-pricing-api/
├── app.py                                    # ✅ Główna aplikacja Flask + PostgreSQL
├── requirements.txt                          # ✅ Zależności (Flask, gunicorn, psycopg2)
├── Procfile                                  # ✅ Konfiguracja Render
├── runtime.txt                               # ✅ Python 3.11
├── render.yaml                               # ✅ Konfiguracja Render
├── .gitignore                                # ✅ Ignorowane pliki
├── .env.example                              # ✅ Przykład zmiennych środowiskowych
├── README.md                                 # ✅ Dokumentacja API
├── DEPLOY_RENDER.md                          # ✅ Instrukcja wdrożenia krok po kroku
├── test_api.py                               # ✅ Testy API
├── data/
│   ├── postal_code_to_region_transeu.json   # ✅ Mapowanie kodów Trans.eu
│   └── postal_code_to_region_timocom.json   # ✅ Mapowanie kodów TimoCom
└── .git/                                     # ✅ Git repository (1 commit)
```

### Funkcjonalności API:
- ✅ Endpoint `/api/route-pricing` - wycena tras
- ✅ Połączenie z PostgreSQL
- ✅ Mapowanie kodów pocztowych → region IDs
- ✅ Pobieranie danych z tabel `public.offers` i `public."OffersTransEU"`
- ✅ Obsługa 4 typów pojazdów (naczepa, 3.5t, 12t, lorry)
- ✅ Średnie i mediany dla okresów 7/30/90 dni
- ✅ Liczba ofert dla każdego okresu
- ✅ Health check endpoint
- ✅ Zwraca tylko JSON (bez HTML)

## 🎯 Następne kroki

### 1. Utwórz repozytorium GitHub

```bash
# Przejdź do katalogu
cd c:\Users\konra\Documents\route-pricing-api

# Utwórz nowe repo na GitHub (przez przeglądarkę):
# https://github.com/new
# Nazwa: route-pricing-api
# Opis: Backend API dla wyceny tras transportowych
# Public lub Private: Wybierz
# NIE inicjalizuj z README (już mamy pliki)

# Połącz lokalne repo z GitHub
git remote add origin https://github.com/[TWOJA-NAZWA]/route-pricing-api.git
git branch -M main
git push -u origin main
```

### 2. Wdróż na Render

Następuj instrukcji w **DEPLOY_RENDER.md** - wszystkie kroki krok po kroku!

**Szybka ścieżka:**
1. Idź na https://render.com i zaloguj się
2. **New +** → **PostgreSQL** (jeśli nie masz bazy)
3. **New +** → **Web Service**
4. Wybierz repo `route-pricing-api`
5. Dodaj zmienne środowiskowe (POSTGRES_*)
6. Deploy! 🚀

### 3. Testuj API

Po wdrożeniu:

```bash
# Health check (bez API key)
curl https://[twoja-nazwa].onrender.com/health

# Test wyceny (z API key!)
curl -X POST https://[twoja-nazwa].onrender.com/api/route-pricing \
  -H "Content-Type: application/json" \
  -H "X-API-Key: twoj-api-key" \
  -d '{
    "start_postal_code": "PL50",
    "end_postal_code": "DE10",
    "vehicle_type": "naczepa"
  }'
```

## 📋 Checklist wdrożenia

- [ ] Repozytorium GitHub utworzone
- [ ] Kod wypchnięty na GitHub
- [ ] Konto Render utworzone
- [ ] Baza PostgreSQL gotowa (z danymi)
- [ ] Web Service utworzony na Render
- [ ] Zmienne środowiskowe ustawione (POSTGRES_*)
- [ ] 🔐 API_KEY wygenerowany i dodany
- [ ] Deploy zakończony sukcesem
- [ ] Health check działa
- [ ] Test API działa (z API key)

## 🔑 Zmienne środowiskowe (Render)

Dodaj w Render Dashboard → Your Service → Environment:

**Baza danych:**
```
POSTGRES_HOST=dpg-xxxxx.frankfurt-postgres.render.com
POSTGRES_PORT=5432
POSTGRES_USER=pricing_user
POSTGRES_DB=pricing_data
POSTGRES_PASSWORD=twoje_haslo
```

💡 **TIP:** Jeśli używasz bazy Render, kliknij "Add from Database" - szybsze!

**🔐 Zabezpieczenia (OBOWIĄZKOWE!):**

1. Wygeneruj API key (PowerShell):
```powershell
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
$apiKey = [Convert]::ToBase64String($bytes)
Write-Host "API_KEY=$apiKey"
```

2. Dodaj zmienne:
```
API_KEY=wygenerowany-klucz-tutaj
REQUIRE_API_KEY=true
```

⚠️ **WAŻNE:** Bez API_KEY Twoje API jest publiczne i niechronione!

## 📊 Format żądania API

```json
POST /api/route-pricing
Content-Type: application/json

{
  "start_postal_code": "PL50",    // Kod pocztowy start ([KRAJ][2_CYFRY])
  "end_postal_code": "DE10",      // Kod pocztowy koniec
  "vehicle_type": "naczepa"       // naczepa, 3.5t, 12t, lorry
}
```

## 📈 Format odpowiedzi API

```json
{
  "success": true,
  "data": {
    "start_postal_code": "PL50",
    "end_postal_code": "DE10",
    "vehicle_type": "naczepa",
    "region_ids": {
      "start": 134,
      "end": 89
    },
    "pricing": {
      "timocom": {
        "avg_7d": 1.0,
        "avg_30d": 1.04,
        "avg_90d": 1.07,
        "median_7d": 1.05,
        "median_30d": 1.05,
        "median_90d": 1.08,
        "offers_7d": 4012,
        "offers_30d": 24835,
        "offers_90d": 29253
      }
    },
    "currency": "EUR",
    "unit": "EUR/km",
    "data_source": "postgresql"
  }
}
```

## 🛠️ Test lokalny (opcjonalnie)

Jeśli chcesz przetestować lokalnie przed wdrożeniem:

```bash
# 1. Utwórz .env (skopiuj z .env.example)
cp .env.example .env

# 2. Edytuj .env i dodaj dane do bazy PostgreSQL
notepad .env

# 3. Zainstaluj zależności
pip install -r requirements.txt

# 4. Uruchom serwer
python app.py

# 5. W nowym terminalu - testy
python test_api.py
```

## 📚 Dokumentacja

- **README.md** - Pełna dokumentacja API
- **DEPLOY_RENDER.md** - Szczegółowa instrukcja wdrożenia
- **test_api.py** - Testy endpointów

## 🆘 Potrzebujesz pomocy?

### Problem z bazą danych?
- Sprawdź czy tabele istnieją: `public.offers` i `public."OffersTransEU"`
- Sprawdź czy dane są załadowane
- Sprawdź zmienne środowiskowe

### Problem z kodem pocztowym?
- Format: `[KRAJ][2_CYFRY]` np. `PL50`, `DE10`
- Sprawdź czy kod istnieje w plikach JSON w folderze `data/`

### Problem z Render?
- Zobacz logi: Dashboard → Your Service → Logs
- Sprawdź metryki: Dashboard → Your Service → Metrics
- Clear cache: Manual Deploy → "Clear build cache & deploy"

## ✨ Gotowe do startu!

Teraz masz:
- ✅ Kompletne API z PostgreSQL
- ✅ Pełną dokumentację
- ✅ Instrukcję wdrożenia krok po kroku
- ✅ Git repo gotowe do pusha

**Następny krok:** Utwórz repo na GitHub i wdróż na Render! 🚀

---

**Pytania?** Zobacz `DEPLOY_RENDER.md` dla szczegółów lub `README.md` dla dokumentacji API.
