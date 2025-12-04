"""
Pricing API - SECURED VERSION
Wersja z zabezpieczeniami przed exploitami
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flasgger import Swagger
import os
from typing import Optional
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import json
from functools import wraps
import secrets
import re
import logging
import time

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Załaduj zmienne środowiskowe
load_dotenv()

app = Flask(__name__)

# STARTUP LOG - WERSJA Z OPTYMALIZACJĄ (1 zapytanie zamiast 6)
print("""
**********************************************
*                                            *
*   SECURED & OPTIMIZED PRICING API v2.0    *
*   - Single query optimization             *
*   - Connection pooling with validation    *
*   - Performance monitoring                *
*                                            *
**********************************************
""")

# Konfiguracja Swaggera
app.config['SWAGGER'] = {
    'title': 'Pricing API',
    'uiversion': 3,
    'description': 'API do wyceny tras transportowych na podstawie historycznych danych z giełd transportowych.',
    'termsOfService': '#',
    'contact': {
        'name': 'API Support',
        'url': '#',
        'email': 'support@example.com',
    },
    'license': {
        'name': 'MIT',
        'url': 'https://opensource.org/licenses/MIT',
    },
    'securityDefinitions': {
        'ApiKeyAuth': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-API-Key',
            'description': 'Klucz API do autoryzacji. Może być również przekazany jako `Authorization: Bearer <key>`.'
        }
    },
    'specs_route': '/apidocs/'
}
swagger = Swagger(app)

# CORS - tylko zaufane domeny (zmień w produkcji!)
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:5000').split(',')
CORS(app, resources={
    r"/api/*": {
        "origins": ALLOWED_ORIGINS,
        "methods": ["POST"],
        "allow_headers": ["Content-Type", "X-API-Key", "Authorization"]
    }
})

# Rate Limiting - ogranicz liczbę requestów
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per day", "20 per hour"],
    storage_uri="memory://",
    strategy="fixed-window"
)

# Konfiguracja
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_USER = os.getenv("POSTGRES_USER")
DB_NAME = os.getenv("POSTGRES_DB")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
API_KEY = os.getenv('API_KEY', '')
ENV = os.getenv('ENV', 'development')

# Connection Pool - zamiast tworzyć nowe połączenie za każdym razem
try:
    connection_pool = pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursor_factory=RealDictCursor,
        connect_timeout=10,
        options='-c statement_timeout=30000'  # 30 sekund timeout dla zapytań
    )
    logger.info("✅ Connection pool initialized")
except Exception as e:
    logger.error(f"❌ Failed to create connection pool: {e}")
    connection_pool = None

# Cache
_TRANSEU_TO_TIMOCOM_MAPPING = None
_POSTAL_CODE_MAPPING = None

# Regex dla walidacji kodu pocztowego (2 litery + 1-5 cyfr)
POSTAL_CODE_PATTERN = re.compile(r'^[A-Z]{2}\d{1,5}$')


@app.after_request
def add_security_headers(response):
    """Dodaje security headers do każdej odpowiedzi"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response


@app.before_request
def enforce_https():
    """Wymusza HTTPS w produkcji"""
    if ENV == 'production' and not request.is_secure:
        logger.warning(f"⚠️ HTTP request blocked from {request.remote_addr}")
        return jsonify({
            'success': False,
            'error': 'HTTPS required'
        }), 403


def require_api_key(f):
    """Dekorator sprawdzający API key - odporny na timing attacks"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not api_key:
            logger.warning(f"⚠️ Missing API key from {request.remote_addr}")
            return jsonify({
                'success': False,
                'error': 'Brak API key',
                'message': 'Wymagany header: X-API-Key lub Authorization: Bearer <key>'
            }), 401
        
        # secrets.compare_digest - zabezpiecza przed timing attacks
        if not secrets.compare_digest(api_key, API_KEY):
            logger.warning(f"⚠️ Invalid API key attempt from {request.remote_addr}: {api_key[:10]}...")
            return jsonify({
                'success': False,
                'error': 'Nieprawidłowy API key'
            }), 403
        
        logger.info(f"✅ Authorized request from {request.remote_addr}")
        return f(*args, **kwargs)
    return decorated_function


def validate_postal_code(postal_code: str) -> bool:
    """
    Waliduje format kodu pocztowego
    
    Args:
        postal_code: Kod pocztowy do walidacji
    
    Returns:
        True jeśli poprawny format, False w przeciwnym razie
    """
    if not postal_code:
        return False
    
    # Limit długości - ochrona przed DoS
    if len(postal_code) > 10:
        logger.warning(f"⚠️ Postal code too long: {len(postal_code)} chars")
        return False
    
    # Walidacja formatu regex
    return bool(POSTAL_CODE_PATTERN.match(postal_code))


def _get_db_connection():
    """Pobiera połączenie z pool i weryfikuje, czy jest aktywne"""
    if connection_pool is None:
        raise Exception("Connection pool not initialized")
    
    try:
        conn = connection_pool.getconn()
        
        # Sprawdź czy połączenie jest aktywne
        try:
            with conn.cursor() as test_cursor:
                test_cursor.execute('SELECT 1')
        except Exception as e:
            logger.warning(f"⚠️ Stale connection detected, reconnecting: {e}")
            # Jeśli połączenie martwe, zamknij i pobierz nowe
            try:
                conn.close()
            except:
                pass
            connection_pool.putconn(conn, close=True)
            conn = connection_pool.getconn()
        
        return conn
    except Exception as e:
        logger.error(f"❌ Failed to get connection from pool: {e}")
        raise


def _return_db_connection(conn):
    """Zwraca połączenie do pool"""
    if connection_pool and conn:
        connection_pool.putconn(conn)


def _load_transeu_timocom_mapping():
    """Ładuje mapowanie Trans.eu -> TimoCom z pliku JSON"""
    global _TRANSEU_TO_TIMOCOM_MAPPING
    
    if _TRANSEU_TO_TIMOCOM_MAPPING is not None:
        return _TRANSEU_TO_TIMOCOM_MAPPING
    
    try:
        mapping_path = os.path.join(os.path.dirname(__file__), 'data', 'transeu_to_timocom_mapping.json')
        with open(mapping_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _TRANSEU_TO_TIMOCOM_MAPPING = {int(k): v['timocom_id'] for k, v in data.items()}
        logger.info(f"✅ Loaded Trans.eu->TimoCom mapping ({len(_TRANSEU_TO_TIMOCOM_MAPPING)} regions)")
    except Exception as e:
        logger.error(f"❌ Failed to load mapping: {e}")
        _TRANSEU_TO_TIMOCOM_MAPPING = {}
    
    return _TRANSEU_TO_TIMOCOM_MAPPING


def map_transeu_to_timocom_id(transeu_id: int) -> int:
    """Konwertuje Trans.eu region ID na TimoCom region ID"""
    mapping = _load_transeu_timocom_mapping()
    return mapping.get(transeu_id, transeu_id)


def get_timocom_pricing(start_region_id: int, end_region_id: int, days: int = 7):
    """Pobiera dane cenowe TimoCom z bazy danych PostgreSQL"""
    start_time = time.time()
    
    timocom_start_id = map_transeu_to_timocom_id(start_region_id)
    timocom_end_id = map_transeu_to_timocom_id(end_region_id)
    
    conn = None
    try:
        conn_start = time.time()
        conn = _get_db_connection()
        logger.info(f"⏱️ Połączenie z bazą: {(time.time() - conn_start)*1000:.0f}ms")
        
        with conn.cursor() as cur:
            query = """
                SELECT
                    ROUND(AVG(o.trailer_avg_price_per_km), 4) AS avg_trailer_price,
                    ROUND(AVG(o.vehicle_up_to_3_5_t_avg_price_per_km), 4) AS avg_3_5t_price,
                    ROUND(AVG(o.vehicle_up_to_12_t_avg_price_per_km), 4) AS avg_12t_price,
                    ROUND(AVG(o.trailer_median_price_per_km), 4) AS median_trailer_price,
                    SUM(o.number_of_offers_total) AS total_offers,
                    SUM(o.number_of_offers_trailer) AS total_offers_trailer,
                    SUM(o.number_of_offers_vehicle_up_to_3_5_t) AS total_offers_3_5t,
                    SUM(o.number_of_offers_vehicle_up_to_12_t) AS total_offers_12t,
                    COUNT(DISTINCT o.enlistment_date) AS days_count
                FROM public.offers AS o
                WHERE o.starting_id = %s
                  AND o.destination_id = %s
                  AND o.enlistment_date >= CURRENT_DATE - CAST(%s AS INTEGER);
            """
            
            query_start = time.time()
            cur.execute(query, (timocom_start_id, timocom_end_id, days))
            result = cur.fetchone()
            logger.info(f"⏱️ Zapytanie SQL ({days}d): {(time.time() - query_start)*1000:.0f}ms")
            
            if not result or (not result['avg_trailer_price'] and not result['avg_3_5t_price'] and not result['avg_12t_price']):
                return None
            
            return {
                'avg_price_per_km': {
                    'trailer': float(result['avg_trailer_price']) if result['avg_trailer_price'] else None,
                    '3_5t': float(result['avg_3_5t_price']) if result['avg_3_5t_price'] else None,
                    '12t': float(result['avg_12t_price']) if result['avg_12t_price'] else None
                },
                'median_price_per_km': {
                    'trailer': float(result['median_trailer_price']) if result['median_trailer_price'] else None,
                    '3_5t': None,
                    '12t': None
                },
                'total_offers': int(result['total_offers']) if result['total_offers'] else 0,
                'offers_by_vehicle_type': {
                    'trailer': int(result['total_offers_trailer']) if result['total_offers_trailer'] else 0,
                    '3_5t': int(result['total_offers_3_5t']) if result['total_offers_3_5t'] else 0,
                    '12t': int(result['total_offers_12t']) if result['total_offers_12t'] else 0
                },
                'days_with_data': int(result['days_count']) if result['days_count'] else 0
            }
            
    except Exception as exc:
        logger.error(f"❌ TimoCom query error: {exc}", exc_info=True)
        return None
    finally:
        if conn:
            _return_db_connection(conn)
        logger.info(f"⏱️ CAŁKOWITY CZAS get_timocom_pricing ({days}d): {(time.time() - start_time)*1000:.0f}ms")


def get_transeu_pricing(start_region_id: int, end_region_id: int, days: int = 7):
    """Pobiera dane cenowe Trans.eu z bazy danych PostgreSQL"""
    conn = None
    try:
        conn = _get_db_connection()
        
        with conn.cursor() as cur:
            query = """
                SELECT
                    ROUND(AVG(o.lorry_avg_price_per_km), 4) AS avg_lorry_price,
                    ROUND(AVG(o.lorry_median_price_per_km), 4) AS median_lorry_price,
                    SUM(o.number_of_offers) AS total_offers,
                    COUNT(DISTINCT o.enlistment_date) AS days_count
                FROM public."OffersTransEU" AS o
                WHERE o.starting_id = %s
                  AND o.destination_id = %s
                  AND o.enlistment_date >= CURRENT_DATE - CAST(%s AS INTEGER);
            """
            
            cur.execute(query, (start_region_id, end_region_id, days))
            result = cur.fetchone()
            
            if not result or not result['avg_lorry_price']:
                return None
            
            return {
                'avg_price_per_km': {
                    'lorry': float(result['avg_lorry_price']) if result['avg_lorry_price'] else None
                },
                'median_price_per_km': {
                    'lorry': float(result['median_lorry_price']) if result['median_lorry_price'] else None
                },
                'total_offers': int(result['total_offers']) if result['total_offers'] else 0,
                'days_with_data': int(result['days_count']) if result['days_count'] else 0
            }
            
    except Exception as exc:
        logger.error(f"❌ Trans.eu query error: {exc}", exc_info=True)
        return None
    finally:
        if conn:
            _return_db_connection(conn)




def _load_postal_code_mapping():
    """Ładuje mapowanie kodów pocztowych na regiony"""
    global _POSTAL_CODE_MAPPING
    
    if _POSTAL_CODE_MAPPING is not None:
        return _POSTAL_CODE_MAPPING
    
    try:
        mapping_path = os.path.join(os.path.dirname(__file__), 'data', 'postal_code_to_region_transeu.json')
        with open(mapping_path, 'r', encoding='utf-8') as f:
            _POSTAL_CODE_MAPPING = json.load(f)
        logger.info(f"✅ Loaded postal code mapping ({len(_POSTAL_CODE_MAPPING)} codes)")
    except Exception as e:
        logger.error(f"❌ Failed to load postal code mapping: {e}")
        _POSTAL_CODE_MAPPING = {}
    
    return _POSTAL_CODE_MAPPING

def postal_code_to_region_id(postal_code: str) -> Optional[int]:
    """Konwertuje kod pocztowy (np. PL50) na region ID"""
    mapping = _load_postal_code_mapping()
    normalized = postal_code.upper().replace(' ', '').replace('-', '')
    
    if normalized in mapping:
        return mapping[normalized]['region_id']
    
    return None


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint - dostępny bez API key"""
    return jsonify({
        'status': 'ok',
        'service': 'Pricing API (Secured & Optimized)',
        'version': '2.0.0',
        'features': {
            'security': 'API Key + Rate Limiting + HTTPS',
            'optimization': 'Single query (6x faster)',
            'monitoring': 'Performance metrics enabled'
        }
    })


@app.route('/api/route-pricing', methods=['POST'])
@require_api_key
@limiter.limit("5 per minute")  # Max 5 requestów na minutę
def get_route_pricing():
    """Pobierz wycenę trasy transportowej
    Endpoint do obliczania ceny transportu na podstawie kodów pocztowych i dystansu.
    Używa danych historycznych z TimoCom (średnia z 30 dni) dla trzech typów pojazdów.
    ---
    tags:
      - Pricing
    consumes:
      - application/json
    produces:
      - application/json
    security:
      - ApiKeyAuth: []
    parameters:
      - in: body
        name: body
        required: true
        description: Dane zapytania o wycenę trasy
        schema:
          id: PricingRequest
          type: object
          required:
            - start_postal_code
            - end_postal_code
            - dystans
          properties:
            start_postal_code:
              type: string
              description: Kod pocztowy miejsca początkowego (format ISO 2-literowy kod kraju + cyfry, np. "PL20", "DE49")
              example: "PL20"
              pattern: "^[A-Z]{2}\\d{1,5}$"
            end_postal_code:
              type: string
              description: Kod pocztowy miejsca docelowego (format ISO 2-literowy kod kraju + cyfry, np. "DE49", "FR75")
              example: "DE49"
              pattern: "^[A-Z]{2}\\d{1,5}$"
            dystans:
              type: number
              description: Dystans trasy w kilometrach
              example: 850
              minimum: 1
    responses:
      200:
        description: Sukces - obliczone ceny dla wszystkich typów pojazdów
        schema:
          id: PricingResponse
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                start_postal_code:
                  type: string
                  description: Kod pocztowy startu
                  example: "PL20"
                end_postal_code:
                  type: string
                  description: Kod pocztowy celu
                  example: "DE49"
                distance_km:
                  type: number
                  description: Dystans w kilometrach
                  example: 850
                calculated_prices:
                  type: object
                  description: Obliczone ceny dla każdego typu pojazdu (średnia z 30 dni TimoCom * dystans)
                  properties:
                    cena_naczepa:
                      type: number
                      description: Cena dla naczepy (trailer)
                      example: 1275.50
                      nullable: true
                    cena_bus:
                      type: number
                      description: Cena dla busa (do 3.5t)
                      example: 850.75
                      nullable: true
                    cena_solo:
                      type: number
                      description: Cena dla solo (do 12t)
                      example: 1020.25
                      nullable: true
                currency:
                  type: string
                  description: Waluta cen
                  example: "EUR"
        examples:
          application/json:
            success: true
            data:
              start_postal_code: "PL20"
              end_postal_code: "DE49"
              distance_km: 850
              calculated_prices:
                cena_naczepa: 1275.50
                cena_bus: 850.75
                cena_solo: 1020.25
              currency: "EUR"
      400:
        description: Błąd zapytania - brakujące lub nieprawidłowe dane wejściowe
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Brak wszystkich wymaganych pól: start_postal_code, end_postal_code, dystans"
      401:
        description: Nieautoryzowany - brak klucza API
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Brak API key"
            message:
              type: string
              example: "Wymagany header: X-API-Key lub Authorization: Bearer <key>"
      403:
        description: Zabroniony - nieprawidłowy klucz API lub wymagane HTTPS
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Nieprawidłowy API key"
      404:
        description: Nie znaleziono - brak danych dla podanej trasy lub kodów pocztowych
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Brak danych dla trasy PL20 -> DE49"
            message:
              type: string
              example: "Nie znaleziono danych cenowych w bazie dla tej trasy"
      429:
        description: Przekroczono limit zapytań (5 per minute, 20 per hour, 100 per day)
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Rate limit exceeded"
      500:
        description: Wewnętrzny błąd serwera
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Wewnętrzny błąd serwera"
    """
    try:
        data = request.json
        
        if not data:
            logger.warning(f"⚠️ Empty JSON from {request.remote_addr}")
            return jsonify({
                'success': False,
                'error': 'Brak danych JSON w request'
            }), 400
        
        start_postal = data.get('start_postal_code', '').strip().upper()
        end_postal = data.get('end_postal_code', '').strip().upper()
        distance = data.get('dystans')
        
        if not all([start_postal, end_postal, distance]):
            return jsonify({
                'success': False,
                'error': 'Brak wszystkich wymaganych pól: start_postal_code, end_postal_code, dystans'
            }), 400
        
        # Walidacja formatów kodów pocztowych
        if not validate_postal_code(start_postal):
            logger.warning(f"⚠️ Invalid start postal code: {start_postal}")
            return jsonify({
                'success': False,
                'error': f'Nieprawidłowy format kodu pocztowego: {start_postal}',
                'message': 'Użyj formatu: KOD_KRAJU (2 litery) + cyfry (np. PL50, DE10)'
            }), 400
        
        if not validate_postal_code(end_postal):
            logger.warning(f"⚠️ Invalid end postal code: {end_postal}")
            return jsonify({
                'success': False,
                'error': f'Nieprawidłowy format kodu pocztowego: {end_postal}',
                'message': 'Użyj formatu: KOD_KRAJU (2 litery) + cyfry (np. PL50, DE10)'
            }), 400
        
        # Konwertuj kody pocztowe na region IDs
        start_region_id = postal_code_to_region_id(start_postal)
        end_region_id = postal_code_to_region_id(end_postal)
        
        if not start_region_id or not end_region_id:
            missing = []
            if not start_region_id:
                missing.append(start_postal)
            if not end_region_id:
                missing.append(end_postal)
            
            logger.info(f"ℹ️ Region not found for: {', '.join(missing)}")
            return jsonify({
                'success': False,
                'error': f'Nie znaleziono regionu dla kodów: {", ".join(missing)}',
                'message': 'Użyj formatu: KOD_KRAJU + 2 cyfry (np. PL50, DE10, FR75)'
            }), 404
        
        logger.info(f"📊 Processing pricing request: {start_postal}({start_region_id}) -> {end_postal}({end_region_id})")
        
        request_start = time.time()
        
        # OPTYMALIZACJA: Pobierz tylko dane z 30 dni TimoCom (to jedyne, które używamy)
        timocom_start = time.time()
        timocom_30d = get_timocom_pricing(start_region_id, end_region_id, days=30)
        logger.info(f"⏱️ Zapytanie TimoCom 30d: {(time.time() - timocom_start)*1000:.0f}ms")
        
        # Sprawdź czy są dane
        if not timocom_30d:
            logger.info(f"ℹ️ No data found for route: {start_postal} -> {end_postal}")
            return jsonify({
                'success': False,
                'error': f'Brak danych dla trasy {start_postal} -> {end_postal}',
                'message': 'Nie znaleziono danych cenowych w bazie dla tej trasy'
            }), 404

        # Sprawdź czy mamy kompletne dane
        if 'avg_price_per_km' not in timocom_30d:
            return jsonify({
                'success': False,
                'error': 'Brak wystarczających danych z 30 dni do obliczenia ceny'
            }), 404

        calc_start = time.time()
        avg_rates = timocom_30d['avg_price_per_km']
        calculated_prices = {}
        for vehicle, rate in avg_rates.items():
            # Zmieniamy klucze, aby pasowały do oczekiwań (bus, solo, naczepa)
            vehicle_key = vehicle
            if vehicle == 'trailer':
                vehicle_key = 'naczepa'
            elif vehicle == '3_5t':
                vehicle_key = 'bus'
            elif vehicle == '12t':
                vehicle_key = 'solo'

            if rate is not None:
                calculated_prices[f'cena_{vehicle_key}'] = round(rate * float(distance), 2)
            else:
                calculated_prices[f'cena_{vehicle_key}'] = None
        logger.info(f"⏱️ Obliczenia cen: {(time.time() - calc_start)*1000:.0f}ms")
        logger.info(f"⏱️ ⭐ CAŁKOWITY CZAS REQUESTU: {(time.time() - request_start)*1000:.0f}ms")
        logger.info(f"✅ Successfully returned calculated prices for {start_postal} -> {end_postal}")

        return jsonify({
            'success': True,
            'data': {
                'start_postal_code': start_postal,
                'end_postal_code': end_postal,
                'distance_km': distance,
                'calculated_prices': calculated_prices,
                'currency': 'EUR'
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Server error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Błąd serwera'
        }), 500


@app.errorhandler(429)
def ratelimit_handler(e):
    """Handler dla rate limit errors"""
    logger.warning(f"⚠️ Rate limit exceeded from {request.remote_addr}")
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded',
        'message': 'Przekroczono limit requestów. Spróbuj ponownie później.'
    }), 429


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5003))
    logger.info(f"🚀 Starting Pricing API (Secured) on port {port}")
    logger.info(f"🔒 Environment: {ENV}")
    logger.info(f"🌐 Allowed origins: {ALLOWED_ORIGINS}")
    app.run(debug=False, host='0.0.0.0', port=port)
