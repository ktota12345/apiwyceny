# 🚀 Wdrożenie Route Pricing API na Render

Szczegółowa instrukcja krok po kroku.

## Przygotowanie

### 1. Utwórz repozytorium GitHub

```bash
cd route-pricing-api

# Zainicjalizuj git
git init

# Dodaj wszystkie pliki
git add .

# Pierwszy commit
git commit -m "Initial commit: Route Pricing API"

# Połącz z GitHub (utwórz repo na GitHub najpierw)
git remote add origin https://github.com/[your-username]/route-pricing-api.git
git branch -M main
git push -u origin main
```

### 2. Przygotuj bazę danych PostgreSQL

Możesz użyć:
- **Render PostgreSQL** (darmowy plan)
- **Supabase** (darmowy)
- **ElephantSQL** (darmowy)
- Twoja istniejąca baza PostgreSQL

## Wdrożenie na Render

### Krok 1: Utwórz konto na Render

1. Idź na https://render.com
2. Zarejestruj się (możesz użyć GitHub)
3. Potwierdź email

### Krok 2: Dodaj bazę danych PostgreSQL (jeśli nie masz)

1. W Dashboard kliknij **"New +"** → **"PostgreSQL"**
2. Wypełnij:
   - **Name:** `route-pricing-db`
   - **Database:** `pricing_data`
   - **User:** (wygeneruje się automatycznie)
   - **Region:** Frankfurt (najbliżej Polski)
   - **Plan:** Free
3. Kliknij **"Create Database"**
4. Poczekaj ~2 minuty na inicjalizację
5. Zapisz **Connection String** (External Database URL):
   ```
   postgresql://user:password@host:port/database
   ```

### Krok 3: Załaduj dane do bazy (jeśli nowa baza)

Jeśli to nowa baza, musisz załadować tabele i dane:

```bash
# Połącz się z bazą
psql "postgresql://user:password@host:port/database"

# Lub użyj GUI: pgAdmin, DBeaver, etc.
```

**Struktura tabel:**

```sql
-- Tabela TimoCom
CREATE TABLE public.offers (
    id SERIAL PRIMARY KEY,
    starting_id INTEGER NOT NULL,
    destination_id INTEGER NOT NULL,
    trailer_avg_price_per_km DECIMAL(10, 4),
    vehicle_up_to_3_5_t_avg_price_per_km DECIMAL(10, 4),
    vehicle_up_to_12_t_avg_price_per_km DECIMAL(10, 4),
    number_of_offers_total INTEGER,
    enlistment_date DATE NOT NULL
);

CREATE INDEX idx_offers_route ON public.offers(starting_id, destination_id, enlistment_date);

-- Tabela Trans.eu
CREATE TABLE public."OffersTransEU" (
    id SERIAL PRIMARY KEY,
    starting_id INTEGER NOT NULL,
    destination_id INTEGER NOT NULL,
    lorry_avg_price_per_km DECIMAL(10, 4),
    enlistment_date DATE NOT NULL
);

CREATE INDEX idx_transeu_route ON public."OffersTransEU"(starting_id, destination_id, enlistment_date);
```

### Krok 4: Wdróż Web Service

1. W Dashboard Render kliknij **"New +"** → **"Web Service"**
2. Połącz z GitHub:
   - Kliknij **"Connect GitHub"**
   - Autoryzuj Render
   - Wybierz repozytorium `route-pricing-api`
3. Wypełnij ustawienia:

   **Podstawowe:**
   - **Name:** `route-pricing-api` (to będzie w URL)
   - **Region:** Frankfurt
   - **Branch:** `main`
   - **Root Directory:** (puste - root repo)
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Plan:** Free

4. **Environment Variables** - kliknij **"Add Environment Variable"** i dodaj:

   **Baza danych:**
   ```
   POSTGRES_HOST=dpg-xxxxx.frankfurt-postgres.render.com
   POSTGRES_PORT=5432
   POSTGRES_USER=your_username
   POSTGRES_DB=pricing_data
   POSTGRES_PASSWORD=your_password
   ```

   **Szybszy sposób (jeśli używasz Render PostgreSQL):**
   - Kliknij **"Add from Database"**
   - Wybierz swoją bazę `route-pricing-db`
   - Automatycznie doda wszystkie zmienne

   **🔐 Zabezpieczenia (WAŻNE!):**
   
   Wygeneruj silny API key:
   ```bash
   # PowerShell
   $bytes = New-Object byte[] 32
   [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
   $apiKey = [Convert]::ToBase64String($bytes)
   Write-Host "API_KEY=$apiKey"
   ```
   
   Lub użyj generatora online: https://randomkeygen.com/
   
   Dodaj zmienne zabezpieczeń:
   ```
   API_KEY=your-generated-secret-key-min-32-chars
   REQUIRE_API_KEY=true
   ```
   
   ⚠️ **UWAGA:** Bez API_KEY każdy będzie mógł korzystać z Twojego API!

5. Kliknij **"Create Web Service"**

### Krok 5: Poczekaj na deploy

1. Render zacznie budować aplikację (~3-5 minut)
2. Możesz obserwować logi w czasie rzeczywistym
3. Gdy zobaczysz: `==> Build successful 🎉` - gotowe!
4. Twoje API będzie dostępne pod: `https://route-pricing-api.onrender.com`

## Testowanie

### Test 1: Health check

```bash
curl https://route-pricing-api.onrender.com/health
```

Powinno zwrócić:
```json
{
  "status": "healthy",
  "service": "route-pricing-api"
}
```

### Test 2: Wycena trasy

```bash
curl -X POST https://route-pricing-api.onrender.com/api/route-pricing \
  -H "Content-Type: application/json" \
  -d '{
    "start_postal_code": "PL50",
    "end_postal_code": "DE10",
    "vehicle_type": "naczepa"
  }'
```

## Troubleshooting

### Problem: "Application failed to respond"

**Rozwiązanie:**
1. Sprawdź logi w Render Dashboard → "Logs"
2. Sprawdź czy zmienne środowiskowe są ustawione
3. Sprawdź czy baza danych jest dostępna

### Problem: "Module 'psycopg2' not found"

**Rozwiązanie:**
- Upewnij się że `requirements.txt` zawiera `psycopg2-binary`
- Trigger manual deploy: Dashboard → "Manual Deploy" → "Clear build cache & deploy"

### Problem: "Connection to database failed"

**Rozwiązanie:**
1. Sprawdź zmienne środowiskowe (POSTGRES_*)
2. Sprawdź czy baza danych jest aktywna (Render Dashboard → Databases)
3. Sprawdź czy External URL jest poprawny

### Problem: "Brak danych dla trasy"

**Rozwiązanie:**
1. Sprawdź czy tabele zawierają dane dla tych region_ids
2. Sprawdź format kodu pocztowego (PL50, DE10)
3. Sprawdź logi API: `print` statements będą widoczne w Logs

## Monitoring

### Logi
Dashboard → Your Service → "Logs" - logi w czasie rzeczywistym

### Metryki
Dashboard → Your Service → "Metrics" - CPU, pamięć, requesty

### Alerty
Dashboard → Your Service → "Alerts" - powiadomienia email

## Aktualizacja

### Automatyczna (Git push)

```bash
# Wprowadź zmiany w kodzie
git add .
git commit -m "Update: ..."
git push

# Render automatycznie wykryje zmiany i wdroży nową wersję
```

### Ręczna

Dashboard → Your Service → "Manual Deploy" → "Deploy latest commit"

## Konfiguracja domeny własnej (opcjonalnie)

1. Dashboard → Your Service → "Settings"
2. Kliknij "Add Custom Domain"
3. Wprowadź domenę: `api.yourdomain.com`
4. Dodaj CNAME record u swojego providera DNS:
   ```
   CNAME api route-pricing-api.onrender.com
   ```
5. Poczekaj na SSL (automatyczny Let's Encrypt)

## Skalowanie

### Free Plan
- ✅ 512 MB RAM
- ✅ 0.1 CPU
- ✅ Automatyczne sleep po 15 min bezczynności
- ✅ SSL/HTTPS
- ❌ Brak sleep - wymaga płatnego planu

### Paid Plans ($7/miesiąc+)
- 🚀 Więcej RAM/CPU
- 🚀 Brak auto-sleep
- 🚀 Więcej równoczesnych requestów
- 🚀 Auto-scaling

## Backup bazy danych

### Ręczny backup

```bash
# Pobierz dump
pg_dump "postgresql://user:password@host:port/database" > backup.sql

# Przywróć z backupu
psql "postgresql://user:password@host:port/database" < backup.sql
```

### Automatyczny backup (Render Paid)

Dashboard → Your Database → "Settings" → "Backups"

## Bezpieczeństwo

### ✅ Render zapewnia:
- HTTPS/SSL automatyczny
- Izolacja środowisk
- Firewall
- DDoS protection

### 🔐 Zalecenia:
- Nie commituj `.env` do git (jest w `.gitignore`)
- Używaj mocnych haseł do bazy
- Rotuj credentials regularnie
- Monitoruj logi pod kątem anomalii

## Koszty

### Free Plan:
- Web Service: **$0** (750 godzin/miesiąc)
- PostgreSQL: **$0** (1 GB storage, wygasa po 90 dni)
- Bandwidth: **100 GB/miesiąc**

### Paid Plan:
- Web Service: **$7-$85/miesiąc** (zależnie od zasobów)
- PostgreSQL: **$7-$120/miesiąc** (zależnie od storage)

## Support

- **Render Docs:** https://render.com/docs
- **Community Forum:** https://community.render.com
- **Status:** https://status.render.com

## Gotowe! 🎉

Twoje API jest teraz live na:
```
https://route-pricing-api.onrender.com
```

Test:
```bash
curl https://route-pricing-api.onrender.com/health
```
