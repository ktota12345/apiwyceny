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

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Załaduj zmienne środowiskowe
load_dotenv()

app = Flask(__name__)

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
        cursor_factory=RealDictCursor
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
    """Pobiera połączenie z pool"""
    if connection_pool is None:
        raise Exception("Connection pool not initialized")
    
    try:
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
    timocom_start_id = map_transeu_to_timocom_id(start_region_id)
    timocom_end_id = map_transeu_to_timocom_id(end_region_id)
    
    conn = None
    try:
        conn = _get_db_connection()
        
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
            
            cur.execute(query, (timocom_start_id, timocom_end_id, days))
            result = cur.fetchone()
            
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
        'service': 'Pricing API (Secured)',
        'version': '1.1.0'
    })


@app.route('/api/pricing', methods=['POST'])
@require_api_key
@limiter.limit("5 per minute")  # Max 5 requestów na minutę
def get_pricing():
    """Pobierz dane cenowe dla trasy
    Endpoint do pobierania historycznych danych cenowych dla określonej trasy na podstawie kodów pocztowych.
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
        schema:
          id: PricingRequest
          type: object
          properties:
            start_postal_code:
              type: string
              description: Kod pocztowy miejsca początkowego (np. "DE49").
              example: "DE49"
            end_postal_code:
              type: string
              description: Kod pocztowy miejsca docelowego (np. "PL20").
              example: "PL20"
          required:
            - start_postal_code
            - end_postal_code
    responses:
      200:
        description: Sukces - dane cenowe zostały zwrócone.
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
                end_postal_code:
                  type: string
                pricing:
                  type: object
                  description: Obiekt zawierający dane cenowe z różnych źródeł i okresów.
      400:
        description: Błąd zapytania - brakujące lub nieprawidłowe dane wejściowe.
      401:
        description: Nieautoryzowany - brak klucza API.
      403:
        description: Zabroniony - nieprawidłowy klucz API lub wymagane HTTPS.
      404:
        description: Nie znaleziono - brak danych dla podanej trasy lub kodów pocztowych.
      429:
        description: Przekroczono limit zapytań.
      500:
        description: Wewnętrzny błąd serwera.
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
        
        if not start_postal or not end_postal:
            return jsonify({
                'success': False,
                'error': 'Brak kodów pocztowych (start_postal_code i end_postal_code wymagane)'
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
        
        # Pobierz ceny dla różnych okresów
        pricing_data = {
            'timocom': {},
            'transeu': {}
        }
        
        # TimoCom - 7, 30, 90 dni
        for days in [7, 30, 90]:
            timocom_data = get_timocom_pricing(start_region_id, end_region_id, days)
            if timocom_data:
                pricing_data['timocom'][f'{days}d'] = timocom_data
        
        # Trans.eu - 7, 30, 90 dni
        for days in [7, 30, 90]:
            transeu_data = get_transeu_pricing(start_region_id, end_region_id, days)
            if transeu_data:
                pricing_data['transeu'][f'{days}d'] = transeu_data
        
        # Sprawdź czy są jakiekolwiek dane
        has_timocom_data = len(pricing_data['timocom']) > 0
        has_transeu_data = len(pricing_data['transeu']) > 0
        
        if not has_timocom_data and not has_transeu_data:
            logger.info(f"ℹ️ No data found for route: {start_postal} -> {end_postal}")
            return jsonify({
                'success': False,
                'error': f'Brak danych dla trasy {start_postal} -> {end_postal}',
                'message': 'Nie znaleziono danych cenowych w bazie dla tej trasy'
            }), 404
        
        logger.info(f"✅ Successfully returned pricing data for {start_postal} -> {end_postal}")
        
        return jsonify({
            'success': True,
            'data': {
                'start_postal_code': start_postal,
                'end_postal_code': end_postal,
                'start_region_id': start_region_id,
                'end_region_id': end_region_id,
                'pricing': pricing_data,
                'currency': 'EUR',
                'unit': 'EUR/km',
                'data_sources': {
                    'timocom': has_timocom_data,
                    'transeu': has_transeu_data
                }
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
    port = int(os.environ.get('PORT', 5001))
    logger.info(f"🚀 Starting Pricing API (Secured) on port {port}")
    logger.info(f"🔒 Environment: {ENV}")
    logger.info(f"🌐 Allowed origins: {ALLOWED_ORIGINS}")
    app.run(debug=False, host='0.0.0.0', port=port)
