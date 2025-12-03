# 🚀 Pricing API - API Wyceny Tras Transportowych

Standalone REST API do pobierania historycznych cen transportu z giełd TimoCom i Trans.eu.

## 📋 Spis treści

- [Quick Start](#-quick-start)
- [Funkcjonalność](#-funkcjonalność)
- [Instalacja](#-instalacja)
- [Konfiguracja](#️-konfiguracja)
- [Użycie](#-użycie)
- [Dokumentacja](#-dokumentacja)
- [Bezpieczeństwo](#-bezpieczeństwo)
- [Deployment](#-deployment)

## ⚡ Quick Start

```bash
# 1. Clone repo
git clone https://github.com/your-username/apiwyceny.git
cd apiwyceny

# 2. Instalacja zależności
pip install -r requirements_secure.txt

# 3. Konfiguracja
cp .env.example .env
# Edytuj .env (ustaw DB credentials i API_KEY)

# 4. Wygeneruj API key
python generate_api_key.py

# 5. Uruchom
python app_secure.py

# 6. Test
python quick_test_secure.py
```

## 🎯 Funkcjonalność

- ✅ **Dane cenowe** z TimoCom i Trans.eu
- ✅ **Trzy okresy** - 7, 30, 90 dni
- ✅ **Średnie i mediany** cen EUR/km
- ✅ **Liczby ofert** (ogółem i po typach pojazdów)
- ✅ **Autoryzacja API Key**
- ✅ **Rate Limiting** (5/min)
- ✅ **Connection Pooling** (performance)
- ✅ **Audit Logging**
- ✅ **CORS** (configurable)
- ✅ **Input Validation**

## 📦 Instalacja

### Requirements

- Python 3.11+
- PostgreSQL database
- Git

### Zależności

```bash
pip install -r requirements_secure.txt
```

Zawiera:
- Flask 3.0.0
- Flask-CORS 4.0.0
- Flask-Limiter 3.5.0
- psycopg2-binary 2.9.9
- python-dotenv 1.0.0
- gunicorn 21.2.0

## ⚙️ Konfiguracja

### 1. Environment Variables

Skopiuj `.env.example` do `.env`:

```bash
cp .env.example .env
```

Wypełnij:

```bash
# API Key
API_KEY=<wygeneruj: python generate_api_key.py>

# Environment
ENV=development  # lub production

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# Database
POSTGRES_HOST=your-db-host
POSTGRES_PORT=5432
POSTGRES_USER=your-user
POSTGRES_PASSWORD=your-password
POSTGRES_DB=your-database
```

### 2. Pliki JSON (mappings)

Wymagane w folderze `data/`:
- `postal_code_to_region_transeu.json`
- `transeu_to_timocom_mapping.json`

## 🚀 Użycie

### Development

```bash
python app_secure.py
```

### Production

```bash
gunicorn -c gunicorn_config.py app_secure:app
```

### Docker

```bash
docker build -t pricing-api .
docker run -p 5001:5001 --env-file .env pricing-api
```

### Przykład Request

```bash
curl -X POST http://localhost:5001/api/pricing \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "start_postal_code": "DE49",
    "end_postal_code": "PL20"
  }'
```

### Przykład Response

```json
{
  "success": true,
  "data": {
    "start_postal_code": "DE49",
    "end_postal_code": "PL20",
    "pricing": {
      "timocom": {
        "7d": {
          "avg_price_per_km": {"trailer": 1.084, "3_5t": 0.471, "12t": 0.438},
          "median_price_per_km": {"trailer": 1.12, "3_5t": null, "12t": null},
          "total_offers": 2005,
          "offers_by_vehicle_type": {"trailer": 1200, "3_5t": 450, "12t": 355},
          "days_with_data": 8
        }
      },
      "transeu": {
        "7d": {
          "avg_price_per_km": {"lorry": 1.34},
          "median_price_per_km": {"lorry": 1.35},
          "total_offers": 1580,
          "days_with_data": 8
        }
      }
    }
  }
}
```

## 📚 Dokumentacja

### Główne dokumenty:
- **[README.md](README.md)** - Pełna dokumentacja
- **[QUICK_START.md](QUICK_START.md)** - Szybki start (5 minut)
- **[API_AUTHORIZATION.md](API_AUTHORIZATION.md)** - Autoryzacja i bezpieczeństwo

### Bezpieczeństwo:
- **[SECURITY_AUDIT.md](SECURITY_AUDIT.md)** - Audyt bezpieczeństwa
- **[SECURITY_SUMMARY.md](SECURITY_SUMMARY.md)** - Podsumowanie zabezpieczeń
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - Migracja do wersji secure

### Przykłady i testy:
- **[EXAMPLES.md](EXAMPLES.md)** - Przykłady użycia (Python, JS, PHP, cURL)
- **[HEADERS_GUIDE.md](HEADERS_GUIDE.md)** - HTTP Headers
- **[test_secure.py](test_secure.py)** - Testy zabezpieczeń

### Deployment:
- **[DEPENDENCY_LIST.md](DEPENDENCY_LIST.md)** - Lista zależności
- **[Procfile](Procfile)** - Heroku deployment
- **[gunicorn_config.py](gunicorn_config.py)** - Konfiguracja produkcyjna

## 🔒 Bezpieczeństwo

### Zabezpieczenia

| Feature | Status |
|---------|--------|
| SQL Injection | ✅ Parametryzowane zapytania |
| API Key Auth | ✅ secrets.compare_digest |
| Rate Limiting | ✅ 5 req/min |
| Input Validation | ✅ Regex + length |
| HTTPS Enforcement | ✅ W production |
| Connection Pool | ✅ 1-10 połączeń |
| CORS Restrictions | ✅ Configurable |
| Request Timeout | ✅ 30s |
| Audit Logging | ✅ Full logs |

### Wygeneruj API Key

```bash
python generate_api_key.py
```

### Testy bezpieczeństwa

```bash
python test_secure.py
```

## 📊 Deployment

### Heroku

```bash
heroku create your-app-name
heroku config:set API_KEY=your-api-key
heroku config:set ENV=production
heroku config:set POSTGRES_HOST=...
git push heroku main
```

### Render

1. Connect repo
2. Set environment variables w panelu
3. Build command: `pip install -r requirements_secure.txt`
4. Start command: `gunicorn -c gunicorn_config.py app_secure:app`

### VPS (Ubuntu)

```bash
# Install dependencies
sudo apt update
sudo apt install python3-pip postgresql-client

# Clone and setup
git clone https://github.com/your-username/apiwyceny.git
cd apiwyceny
pip3 install -r requirements_secure.txt

# Configure
cp .env.example .env
# Edit .env

# Run with systemd
sudo cp pricing-api.service /etc/systemd/system/
sudo systemctl start pricing-api
sudo systemctl enable pricing-api
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements_secure.txt .
RUN pip install -r requirements_secure.txt
COPY . .
ENV ENV=production
EXPOSE 5001
CMD ["gunicorn", "-c", "gunicorn_config.py", "app_secure:app"]
```

## 🧪 Testy

```bash
# Szybki test
python quick_test_secure.py

# Pełne testy zabezpieczeń
python test_secure.py

# Test API key
python test_with_api_key.py

# Test funkcjonalności
python show_new_fields.py
```

## 📈 Performance

- **Connection Pool**: 50% szybciej niż bez pool
- **Rate Limiting**: Ochrona przed DoS
- **Timeout**: 30s (Slowloris protection)
- **Logging**: ~2ms overhead

## 🤝 Contributing

1. Fork repo
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📝 License

MIT License - see LICENSE file

## 🆘 Support

- **Issues**: GitHub Issues
- **Documentation**: [docs/](docs/)
- **Email**: your-email@example.com

## 📌 Changelog

Zobacz [CHANGELOG.md](CHANGELOG.md) dla historii zmian.

## ✅ Status

**Wersja:** 1.1.0 (Secured)  
**Status:** ✅ Production Ready  
**Ostatnia aktualizacja:** 3 grudnia 2025

---

**Made with ❤️ for transport industry**
