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
import math
from typing import Dict, Tuple, Optional, List
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'contractorDetails'))
from aws_distance_calculator import get_aws_route_distance

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Załaduj zmienne środowiskowe
load_dotenv()

app = Flask(__name__)

# STARTUP LOG - WERSJA Z OPTYMALIZACJĄ
print("""
**********************************************
*                                            *
*   SECURED & OPTIMIZED PRICING API v2.4    *
*   - Single query optimization             *
*   - Connection pooling with validation    *
*   - Performance monitoring                *
*   - Historical orders integration         *
*   - Fuzzy matching for routes (±100km)    *
*                                            *
**********************************************
""")

# Konfiguracja Swaggera
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,  # all in
            "model_filter": lambda tag: True,  # all in
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Pricing API",
        "description": "API do wyceny tras transportowych. Zwraca średnie stawki EUR/km z giełd transportowych (TimoCom i Trans.eu - ostatnie 30 dni) oraz z historycznych zleceń firmowych (ostatnie 6 miesięcy z top 4 przewoźnikami).",
        "contact": {
            "name": "API Support",
            "url": "#",
            "email": "support@example.com"
        },
        "termsOfService": "#",
        "version": "2.4.0",
        "license": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
    },
    "host": "localhost:5003",  # Zmień na właściwy host w produkcji
    "basePath": "/",
    "schemes": ["http", "https"],
    "securityDefinitions": {
        "ApiKeyAuth": {
            "type": "apiKey",
            "name": "X-API-Key",
            "in": "header",
            "description": "Klucz API do autoryzacji. Można również użyć headera Authorization: Bearer <key>"
        }
    }
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

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
DB_NAME_MAIN = os.getenv("POSTGRES_DB_MAIN")  # Baza ze zleceniami historycznymi
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
API_KEY = os.getenv('API_KEY', '')
ENV = os.getenv('ENV', 'development')

# Connection Pool - baza z danymi giełd (TimoCom, Trans.eu)
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
    logger.info("✅ Connection pool (exchanges) initialized")
except Exception as e:
    logger.error(f"❌ Failed to create connection pool (exchanges): {e}")
    connection_pool = None

# Connection Pool - baza ze zleceniami historycznymi
try:
    connection_pool_main = pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME_MAIN,
        cursor_factory=RealDictCursor,
        connect_timeout=10,
        options='-c statement_timeout=30000'
    )
    logger.info("✅ Connection pool (historical orders) initialized")
except Exception as e:
    logger.error(f"❌ Failed to create connection pool (historical orders): {e}")
    connection_pool_main = None

# Cache
_TRANSEU_TO_TIMOCOM_MAPPING = None
_POSTAL_CODE_MAPPING = None

# Regex dla walidacji kodu pocztowego (2 litery + 1-5 cyfr)
POSTAL_CODE_PATTERN = re.compile(r'^[A-Z]{2}\d{1,5}$')

# Stałe dla fuzzy matching
DISTANCE_THRESHOLD_KM = 100  # próg odległości w km dla dopasowania


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Oblicza odległość w kilometrach między dwoma punktami geograficznymi
    używając wzoru Haversine.
    
    Args:
        lat1, lon1: Współrzędne punktu 1 (szerokość, długość geograficzna)
        lat2, lon2: Współrzędne punktu 2 (szerokość, długość geograficzna)
    
    Returns:
        Odległość w kilometrach
    """
    # Promień Ziemi w kilometrach
    R = 6371.0
    
    # Konwersja stopni na radiany
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Różnice
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Wzór Haversine
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance


def get_postal_code_coordinates(postal_code: str, conn) -> Optional[Tuple[float, float]]:
    """
    Pobiera współrzędne geograficzne dla danego kodu pocztowego z tabeli PostalCodeCoordinates.
    
    Args:
        postal_code: Kod pocztowy (np. "PL20", "DE49")
        conn: Połączenie z bazą danych
    
    Returns:
        Tuple (lat, lng) lub None jeśli nie znaleziono
    """
    try:
        # Rozdziel kod na country i postal_code (np. "PL20" -> "PL", "20")
        country = postal_code[:2].upper()
        code = postal_code[2:]
        
        with conn.cursor() as cur:
            # Najpierw spróbuj dokładnego dopasowania
            cur.execute("""
                SELECT lat, lng 
                FROM "PostalCodeCoordinates"
                WHERE country = %s AND postal_code = %s
                LIMIT 1;
            """, (country, code))
            
            result = cur.fetchone()
            if result:
                return (result['lat'], result['lng'])
            
            # Jeśli nie znaleziono, spróbuj z LIKE (kod może mieć myślnik)
            cur.execute("""
                SELECT lat, lng 
                FROM "PostalCodeCoordinates"
                WHERE country = %s AND postal_code LIKE %s
                LIMIT 1;
            """, (country, f"{code}%"))
            
            result = cur.fetchone()
            if result:
                return (result['lat'], result['lng'])
            
            return None
            
    except Exception as e:
        logger.error(f"❌ Error getting coordinates for {postal_code}: {e}")
        return None


def find_nearest_historical_route(
    start_postal: str, 
    end_postal: str, 
    conn,
    distance_threshold: float = DISTANCE_THRESHOLD_KM
) -> Optional[Dict]:
    """
    Znajduje najbliższą trasę historyczną używając fuzzy matching.
    
    Algorytm:
    1. Pobiera współrzędne dla podanych kodów pocztowych
    2. Znajduje najbliższy kod startowy z historii (< distance_threshold km)
    3. Dla tego kodu startowego, znajduje najbliższy kod końcowy (< distance_threshold km)
    4. Zwraca informacje o dopasowanej trasie wraz z flagą dokładności
    
    Args:
        start_postal: Kod pocztowy startu z requestu
        end_postal: Kod pocztowy końca z requestu
        conn: Połączenie z bazą danych
        distance_threshold: Maksymalna odległość w km dla dopasowania (domyślnie 100km)
    
    Returns:
        Dict z informacjami o dopasowanej trasie lub None
        {
            'matched_start': str,  # Dopasowany kod startowy
            'matched_end': str,    # Dopasowany kod końcowy
            'start_distance': float,  # Odległość od punktu startowego w km
            'end_distance': float,    # Odległość od punktu końcowego w km
            'accuracy': str  # 'exact', 'high', 'low'
        }
    """
    try:
        # 1. Pobierz współrzędne dla podanych kodów
        start_coords = get_postal_code_coordinates(start_postal, conn)
        end_coords = get_postal_code_coordinates(end_postal, conn)
        
        if not start_coords:
            logger.warning(f"⚠️ Brak współrzędnych dla kodu startowego: {start_postal}")
            return None
        
        if not end_coords:
            logger.warning(f"⚠️ Brak współrzędnych dla kodu końcowego: {end_postal}")
            return None
        
        logger.info(f"📍 Request coords: Start {start_postal} {start_coords}, End {end_postal} {end_coords}")
        
        # 2. Znajdź wszystkie unikalne trasy historyczne z ich współrzędnymi
        with conn.cursor() as cur:
            query = """
                WITH unique_routes AS (
                    SELECT DISTINCT
                        "loadingRegionCode" AS start_code,
                        "unloadingRegionCode" AS end_code
                    FROM "ZleceniaSpeed"
                    WHERE 
                        "status" = 'Z'
                        AND "clientId" != 1
                        AND "routeDistance" > 499
                        AND "orderDate" >= CURRENT_DATE - INTERVAL '180 days'
                        AND "cargoType" IN ('FTL', 'LTL')
                        AND "clientPricePerKm" IS NOT NULL
                        AND "clientPricePerKm" > 0
                )
                SELECT 
                    ur.start_code,
                    ur.end_code,
                    pcc_start.lat AS start_lat,
                    pcc_start.lng AS start_lng,
                    pcc_end.lat AS end_lat,
                    pcc_end.lng AS end_lng
                FROM unique_routes ur
                LEFT JOIN "PostalCodeCoordinates" pcc_start 
                    ON SUBSTRING(ur.start_code FROM 1 FOR 2) = pcc_start.country 
                    AND pcc_start.postal_code LIKE SUBSTRING(ur.start_code FROM 3) || '%'
                LEFT JOIN "PostalCodeCoordinates" pcc_end
                    ON SUBSTRING(ur.end_code FROM 1 FOR 2) = pcc_end.country 
                    AND pcc_end.postal_code LIKE SUBSTRING(ur.end_code FROM 3) || '%'
                WHERE 
                    pcc_start.lat IS NOT NULL 
                    AND pcc_end.lat IS NOT NULL;
            """
            
            cur.execute(query)
            historical_routes = cur.fetchall()
            
            if not historical_routes:
                logger.info("ℹ️ Brak tras historycznych z współrzędnymi")
                return None
            
            logger.info(f"🔍 Znaleziono {len(historical_routes)} unikalnych tras historycznych")
        
        # 3. Znajdź najbliższy punkt startowy
        best_match = None
        min_start_distance = float('inf')
        
        for route in historical_routes:
            # Oblicz odległość punktu startowego
            start_distance = haversine_distance(
                start_coords[0], start_coords[1],
                route['start_lat'], route['start_lng']
            )
            
            # Jeśli punkt startowy jest za daleko, pomiń tę trasę
            if start_distance > distance_threshold:
                continue
            
            # Oblicz odległość punktu końcowego
            end_distance = haversine_distance(
                end_coords[0], end_coords[1],
                route['end_lat'], route['end_lng']
            )
            
            # Jeśli punkt końcowy jest za daleko, sprawdź czy jest to najlepsze dopasowanie startu
            # (może być użyte z flagą low_accuracy)
            if end_distance > distance_threshold:
                # Zapisz tylko jeśli to najlepsze dopasowanie startu (do późniejszego użycia)
                if start_distance < min_start_distance:
                    min_start_distance = start_distance
                    if not best_match or best_match.get('end_distance', float('inf')) > distance_threshold:
                        best_match = {
                            'matched_start': route['start_code'],
                            'matched_end': route['end_code'],
                            'start_distance': start_distance,
                            'end_distance': end_distance,
                            'accuracy': 'low'
                        }
                continue
            
            # Oba punkty są w zasięgu - wybierz najlepsze dopasowanie
            # Priorytet: najmniejsza suma odległości
            total_distance = start_distance + end_distance
            current_best_total = float('inf')
            
            if best_match and best_match['accuracy'] != 'low':
                current_best_total = best_match['start_distance'] + best_match['end_distance']
            
            if total_distance < current_best_total or (best_match and best_match['accuracy'] == 'low'):
                # Określ poziom dokładności
                if start_distance < 1 and end_distance < 1:
                    accuracy = 'exact'
                elif start_distance < 50 and end_distance < 50:
                    accuracy = 'high'
                else:
                    accuracy = 'medium'
                
                best_match = {
                    'matched_start': route['start_code'],
                    'matched_end': route['end_code'],
                    'start_distance': start_distance,
                    'end_distance': end_distance,
                    'accuracy': accuracy
                }
        
        if best_match:
            logger.info(f"✅ Znaleziono dopasowanie: {best_match['matched_start']}->{best_match['matched_end']} "
                       f"(start: {best_match['start_distance']:.1f}km, end: {best_match['end_distance']:.1f}km, "
                       f"accuracy: {best_match['accuracy']})")
        else:
            logger.info("ℹ️ Nie znaleziono dopasowania w promieniu 100km")
        
        return best_match
        
    except Exception as e:
        logger.error(f"❌ Error in find_nearest_historical_route: {e}", exc_info=True)
        return None


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


def _get_db_connection_main():
    """Pobiera połączenie z pool_main (baza ze zleceniami historycznymi) i weryfikuje, czy jest aktywne"""
    if connection_pool_main is None:
        raise Exception("Connection pool (main) not initialized")
    
    try:
        conn = connection_pool_main.getconn()
        
        # Sprawdź czy połączenie jest aktywne
        try:
            with conn.cursor() as test_cursor:
                test_cursor.execute('SELECT 1')
        except Exception as e:
            logger.warning(f"⚠️ Stale connection (main) detected, reconnecting: {e}")
            # Jeśli połączenie martwe, zamknij i pobierz nowe
            try:
                conn.close()
            except:
                pass
            connection_pool_main.putconn(conn, close=True)
            conn = connection_pool_main.getconn()
        
        return conn
    except Exception as e:
        logger.error(f"❌ Failed to get connection from pool (main): {e}")
        raise


def _return_db_connection_main(conn):
    """Zwraca połączenie do pool_main"""
    if connection_pool_main and conn:
        connection_pool_main.putconn(conn)


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
            # Próg dla outlierów - wartości powyżej 5 EUR/km są podejrzane
            OUTLIER_THRESHOLD = 5.0

            # Zoptymalizowane zapytanie - 1 zamiast 2
            query = """
                WITH all_offers AS (
                    SELECT
                        *,
                        (trailer_avg_price_per_km > %(threshold)s OR
                         vehicle_up_to_3_5_t_avg_price_per_km > %(threshold)s OR
                         vehicle_up_to_12_t_avg_price_per_km > %(threshold)s) AS is_outlier
                    FROM public.offers
                    WHERE
                        starting_id = %(start_id)s
                        AND destination_id = %(end_id)s
                        AND enlistment_date >= CURRENT_DATE - CAST(%(days)s AS INTEGER)
                ),
                outliers AS (
                    SELECT
                        enlistment_date,
                        trailer_avg_price_per_km,
                        vehicle_up_to_3_5_t_avg_price_per_km,
                        vehicle_up_to_12_t_avg_price_per_km
                    FROM all_offers
                    WHERE is_outlier = TRUE
                    ORDER BY
                        GREATEST(
                            COALESCE(trailer_avg_price_per_km, 0),
                            COALESCE(vehicle_up_to_3_5_t_avg_price_per_km, 0),
                            COALESCE(vehicle_up_to_12_t_avg_price_per_km, 0)
                        ) DESC
                    LIMIT 5
                ),
                clean_offers AS (
                    SELECT * FROM all_offers WHERE is_outlier = FALSE
                ),
                aggregated_data AS (
                    SELECT
                        -- Średnie ważone
                        SUM(trailer_avg_price_per_km * number_of_offers_trailer) / NULLIF(SUM(number_of_offers_trailer), 0) AS avg_trailer_price,
                        SUM(vehicle_up_to_3_5_t_avg_price_per_km * number_of_offers_vehicle_up_to_3_5_t) / NULLIF(SUM(number_of_offers_vehicle_up_to_3_5_t), 0) AS avg_3_5t_price,
                        SUM(vehicle_up_to_12_t_avg_price_per_km * number_of_offers_vehicle_up_to_12_t) / NULLIF(SUM(number_of_offers_vehicle_up_to_12_t), 0) AS avg_12t_price,
                        
                        -- Mediany i sumy
                        AVG(trailer_median_price_per_km) AS median_trailer_price,
                        SUM(number_of_offers_total) AS total_offers,
                        SUM(number_of_offers_trailer) AS total_offers_trailer,
                        SUM(number_of_offers_vehicle_up_to_3_5_t) AS total_offers_3_5t,
                        SUM(number_of_offers_vehicle_up_to_12_t) AS total_offers_12t,
                        COUNT(DISTINCT enlistment_date) AS days_count
                    FROM clean_offers
                )
                SELECT
                    (SELECT json_agg(t) FROM aggregated_data t) AS aggregated,
                    (SELECT json_agg(o) FROM outliers o) AS outliers;
            """
            
            query_start = time.time()
            cur.execute(query, {
                'start_id': timocom_start_id,
                'end_id': timocom_end_id,
                'days': days,
                'threshold': OUTLIER_THRESHOLD
            })
            result = cur.fetchone()
            logger.info(f"⏱️ Zapytanie SQL ({days}d): {(time.time() - query_start)*1000:.0f}ms")

            # Logowanie outlierów
            if result and result['outliers']:
                outliers = result['outliers']
                logger.warning(f"🚨 TimoCom: Znaleziono {len(outliers)} outlierów (>{OUTLIER_THRESHOLD} EUR/km) dla trasy {timocom_start_id}->{timocom_end_id}:")
                for idx, outlier in enumerate(outliers, 1):
                    logger.warning(f"   #{idx} Data: {outlier['enlistment_date']}, "
                                 f"Trailer: {outlier['trailer_avg_price_per_km']}, "
                                 f"3.5t: {outlier['vehicle_up_to_3_5_t_avg_price_per_km']}, "
                                 f"12t: {outlier['vehicle_up_to_12_t_avg_price_per_km']}")

            # Przetwarzanie zagregowanych danych
            if not result or not result['aggregated']:
                return None

            agg_data = result['aggregated'][0]
            if not agg_data or (not agg_data.get('avg_trailer_price') and not agg_data.get('avg_3_5t_price') and not agg_data.get('avg_12t_price')):
                return None

            return {
                'avg_price_per_km': {
                    'trailer': float(agg_data['avg_trailer_price']) if agg_data.get('avg_trailer_price') else None,
                    '3_5t': float(agg_data['avg_3_5t_price']) if agg_data.get('avg_3_5t_price') else None,
                    '12t': float(agg_data['avg_12t_price']) if agg_data.get('avg_12t_price') else None
                },
                'median_price_per_km': {
                    'trailer': float(agg_data['median_trailer_price']) if agg_data.get('median_trailer_price') else None,
                    '3_5t': None,
                    '12t': None
                },
                'total_offers': int(agg_data['total_offers']) if agg_data.get('total_offers') else 0,
                'offers_by_vehicle_type': {
                    'trailer': int(agg_data['total_offers_trailer']) if agg_data.get('total_offers_trailer') else 0,
                    '3_5t': int(agg_data['total_offers_3_5t']) if agg_data.get('total_offers_3_5t') else 0,
                    '12t': int(agg_data['total_offers_12t']) if agg_data.get('total_offers_12t') else 0
                },
                'days_with_data': int(agg_data['days_count']) if agg_data.get('days_count') else 0
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
            OUTLIER_THRESHOLD = 5.0

            query = '''
                WITH all_offers AS (
                    SELECT
                        *,
                        (lorry_avg_price_per_km > %(threshold)s) AS is_outlier
                    FROM public."OffersTransEU"
                    WHERE
                        starting_id = %(start_id)s
                        AND destination_id = %(end_id)s
                        AND enlistment_date >= CURRENT_DATE - CAST(%(days)s AS INTEGER)
                ),
                outliers AS (
                    SELECT
                        enlistment_date,
                        lorry_avg_price_per_km,
                        number_of_offers
                    FROM all_offers
                    WHERE is_outlier = TRUE
                    ORDER BY lorry_avg_price_per_km DESC
                    LIMIT 5
                ),
                clean_offers AS (
                    SELECT * FROM all_offers WHERE is_outlier = FALSE
                ),
                aggregated_data AS (
                    SELECT
                        SUM(lorry_avg_price_per_km * number_of_offers) / NULLIF(SUM(number_of_offers), 0) AS avg_lorry_price,
                        AVG(lorry_median_price_per_km) AS median_lorry_price,
                        SUM(number_of_offers) AS total_offers,
                        COUNT(DISTINCT enlistment_date) AS days_count
                    FROM clean_offers
                )
                SELECT
                    (SELECT json_agg(t) FROM aggregated_data t) AS aggregated,
                    (SELECT json_agg(o) FROM outliers o) AS outliers;
            '''

            cur.execute(query, {
                'start_id': start_region_id,
                'end_id': end_region_id,
                'days': days,
                'threshold': OUTLIER_THRESHOLD
            })
            result = cur.fetchone()

            if result and result['outliers']:
                outliers = result['outliers']
                logger.warning(f"🚨 Trans.eu: Znaleziono {len(outliers)} outlierów (>{OUTLIER_THRESHOLD} EUR/km) dla trasy {start_region_id}->{end_region_id}:")
                for idx, outlier in enumerate(outliers, 1):
                    logger.warning(f"   #{idx} Data: {outlier['enlistment_date']}, "
                                 f"Lorry: {outlier['lorry_avg_price_per_km']}, "
                                 f"Oferty: {outlier['number_of_offers']}")

            if not result or not result['aggregated']:
                return None

            agg_data = result['aggregated'][0]
            if not agg_data or not agg_data.get('avg_lorry_price'):
                return None

            return {
                'avg_price_per_km': {
                    'lorry': float(agg_data['avg_lorry_price']) if agg_data.get('avg_lorry_price') else None
                },
                'median_price_per_km': {
                    'lorry': float(agg_data['median_lorry_price']) if agg_data.get('median_lorry_price') else None
                },
                'total_offers': int(agg_data['total_offers']) if agg_data.get('total_offers') else 0,
                'days_with_data': int(agg_data['days_count']) if agg_data.get('days_count') else 0
            }
            
    except Exception as exc:
        logger.error(f"❌ Trans.eu query error: {exc}", exc_info=True)
        return None
    finally:
        if conn:
            _return_db_connection(conn)


def get_historical_orders_pricing(start_region_code: str, end_region_code: str, days: int = 180):
    """
    Pobiera statystyki z tabeli zleceń historycznych (ZleceniaSpeed) z fuzzy matching.
    
    Algorytm:
    1. Najpierw próbuje dokładnego dopasowania kodów pocztowych
    2. Jeśli nie znajdzie, używa fuzzy matching (najbliższe punkty w promieniu 100km)
    3. Zwraca dane ze wskaźnikiem dokładności dopasowania
    
    Args:
        start_region_code: Kod regionu startu (np. "PL20")
        end_region_code: Kod regionu celu (np. "DE49")
        days: Liczba dni wstecz (domyślnie 180 - ostatnie pół roku)
    
    Returns:
        Słownik ze statystykami (w tym top 4 przewoźników) oraz metadata o dopasowaniu
        lub None jeśli brak danych
    """
    logger.info(f"🔍 get_historical_orders_pricing called: {start_region_code} → {end_region_code}")
    start_time = time.time()
    conn = None
    try:
        conn_start = time.time()
        conn = _get_db_connection_main()
        logger.info(f"⏱️ Połączenie z bazą (historical): {(time.time() - conn_start)*1000:.0f}ms")
        
        # Metadata o dopasowaniu (domyślnie exact match)
        match_metadata = {
            'matched_start': start_region_code,
            'matched_end': end_region_code,
            'accuracy': 'exact',
            'start_distance_km': 0.0,
            'end_distance_km': 0.0
        }
        
        with conn.cursor() as cur:
            # Próg dla outlierów - analogiczny do giełd
            OUTLIER_THRESHOLD = 5.0
            
            # Zoptymalizowane zapytanie z podziałem na FTL i LTL oraz top 4 przewoźnikami
            query = """
                WITH all_orders AS (
                    SELECT
                        "orderDate",
                        "carrierId",
                        "carrierName",
                        "cargoType",
                        "clientPricePerKm",
                        "carrierPricePerKm",
                        "clientAmount",
                        "carrierAmount",
                        "routeDistance",
                        "clientCurrency",
                        "carrierCurrency",
                        "status",
                        -- Outlier: cena za km > 5 EUR
                        ("clientPricePerKm" > %(threshold)s OR "carrierPricePerKm" > %(threshold)s) AS is_outlier
                    FROM "ZleceniaSpeed"
                    WHERE
                        "loadingRegionCode" = %(start_code)s
                        AND "unloadingRegionCode" = %(end_code)s
                        AND "orderDate" >= CURRENT_DATE - CAST(%(days)s AS INTEGER)
                        AND "status" = 'Z'  -- Tylko zlecenia zakończone
                        AND "clientPricePerKm" IS NOT NULL
                        AND "clientPricePerKm" > 0
                        AND "cargoType" IN ('FTL', 'LTL')  -- Tylko FTL i LTL
                        AND "clientId" != 1  -- Pomijamy klienta Motiva (id = 1)
                        AND "routeDistance" > 499  -- Tylko trasy powyżej 499 km
                ),
                outliers AS (
                    SELECT
                        "orderDate",
                        "cargoType",
                        "clientPricePerKm",
                        "carrierPricePerKm",
                        "clientAmount",
                        "carrierAmount"
                    FROM all_orders
                    WHERE is_outlier = TRUE
                    ORDER BY "clientPricePerKm" DESC
                    LIMIT 5
                ),
                clean_orders AS (
                    SELECT * FROM all_orders WHERE is_outlier = FALSE
                ),
                aggregated_data AS (
                    SELECT
                        "cargoType",
                        -- Średnie ceny za km
                        AVG("clientPricePerKm") AS avg_client_price_per_km,
                        AVG("carrierPricePerKm") AS avg_carrier_price_per_km,
                        
                        -- Mediany
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY "clientPricePerKm") AS median_client_price_per_km,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY "carrierPricePerKm") AS median_carrier_price_per_km,
                        
                        -- Średnie kwoty całkowite
                        AVG("clientAmount") AS avg_client_amount,
                        AVG("carrierAmount") AS avg_carrier_amount,
                        
                        -- Średni dystans
                        AVG("routeDistance") AS avg_distance,
                        
                        -- Liczba zleceń
                        COUNT(*) AS total_orders,
                        COUNT(DISTINCT DATE("orderDate")) AS days_count
                    FROM clean_orders
                    GROUP BY "cargoType"
                ),
                top_carriers AS (
                    SELECT
                        "cargoType",
                        "carrierId",
                        "carrierName",
                        COUNT(*) AS order_count,
                        AVG("clientPricePerKm") AS avg_client_price_per_km,
                        AVG("carrierPricePerKm") AS avg_carrier_price_per_km,
                        AVG("clientAmount") AS avg_client_amount,
                        AVG("carrierAmount") AS avg_carrier_amount,
                        ROW_NUMBER() OVER (PARTITION BY "cargoType" ORDER BY COUNT(*) DESC) AS rn
                    FROM clean_orders
                    WHERE "carrierId" IS NOT NULL 
                        AND "carrierName" IS NOT NULL
                    GROUP BY "cargoType", "carrierId", "carrierName"
                )
                SELECT
                    (SELECT json_agg(t) FROM aggregated_data t) AS aggregated,
                    (SELECT json_agg(o) FROM outliers o) AS outliers,
                    (SELECT json_agg(c) FROM top_carriers c WHERE c.rn <= 4) AS top_carriers;
            """
            
            query_start = time.time()
            cur.execute(query, {
                'start_code': start_region_code,
                'end_code': end_region_code,
                'days': days,
                'threshold': OUTLIER_THRESHOLD
            })
            result = cur.fetchone()
            logger.info(f"⏱️ Zapytanie SQL (historical {days}d): {(time.time() - query_start)*1000:.0f}ms")
            
            # Logowanie outlierów
            if result and result['outliers']:
                outliers = result['outliers']
                logger.warning(f"🚨 Historical: Znaleziono {len(outliers)} outlierów (>{OUTLIER_THRESHOLD} EUR/km) dla trasy {start_region_code}->{end_region_code}:")
                for idx, outlier in enumerate(outliers, 1):
                    logger.warning(f"   #{idx} Data: {outlier['orderDate']}, "
                                 f"Client: {outlier['clientPricePerKm']} EUR/km, "
                                 f"Carrier: {outlier['carrierPricePerKm']} EUR/km")
            
            # Przetwarzanie zagregowanych danych
            if not result or not result['aggregated']:
                # BRAK DOKŁADNEGO DOPASOWANIA - spróbuj fuzzy matching
                logger.info(f"ℹ️ Brak dokładnego dopasowania dla {start_region_code}->{end_region_code}, próbuję fuzzy matching...")
                
                fuzzy_match = find_nearest_historical_route(start_region_code, end_region_code, conn)
                
                if not fuzzy_match:
                    logger.info("ℹ️ Fuzzy matching nie znalazł dopasowania")
                    return None
                
                # Znaleziono fuzzy match - pobierz dane dla dopasowanej trasy
                logger.info(f"🎯 Używam fuzzy match: {fuzzy_match['matched_start']}->{fuzzy_match['matched_end']}")
                
                # Aktualizuj metadata
                match_metadata = {
                    'matched_start': fuzzy_match['matched_start'],
                    'matched_end': fuzzy_match['matched_end'],
                    'accuracy': fuzzy_match['accuracy'],
                    'start_distance_km': round(fuzzy_match['start_distance'], 2),
                    'end_distance_km': round(fuzzy_match['end_distance'], 2)
                }
                
                # Wykonaj zapytanie ponownie z dopasowanymi kodami
                query_start = time.time()
                cur.execute(query, {
                    'start_code': fuzzy_match['matched_start'],
                    'end_code': fuzzy_match['matched_end'],
                    'days': days,
                    'threshold': OUTLIER_THRESHOLD
                })
                result = cur.fetchone()
                logger.info(f"⏱️ Zapytanie SQL fuzzy match (historical {days}d): {(time.time() - query_start)*1000:.0f}ms")
                
                # Sprawdź czy są dane dla dopasowanej trasy
                if not result or not result['aggregated']:
                    logger.warning("⚠️ Brak danych nawet dla dopasowanej trasy")
                    return None
            
            # Sprawdź czy są jakiekolwiek dane
            if not result['aggregated'] or len(result['aggregated']) == 0:
                return None
            
            # Inicjalizacja struktur dla FTL i LTL
            ftl_data = None
            ltl_data = None
            
            # Przetwarzanie danych zagregowanych według cargoType
            for agg_data in result['aggregated']:
                cargo_type = agg_data.get('cargoType')
                
                stats = {
                    'avg_price_per_km': {
                        'client': float(agg_data['avg_client_price_per_km']) if agg_data.get('avg_client_price_per_km') else None,
                        'carrier': float(agg_data['avg_carrier_price_per_km']) if agg_data.get('avg_carrier_price_per_km') else None
                    },
                    'median_price_per_km': {
                        'client': float(agg_data['median_client_price_per_km']) if agg_data.get('median_client_price_per_km') else None,
                        'carrier': float(agg_data['median_carrier_price_per_km']) if agg_data.get('median_carrier_price_per_km') else None
                    },
                    'avg_amounts': {
                        'client': float(agg_data['avg_client_amount']) if agg_data.get('avg_client_amount') else None,
                        'carrier': float(agg_data['avg_carrier_amount']) if agg_data.get('avg_carrier_amount') else None
                    },
                    'avg_distance': float(agg_data['avg_distance']) if agg_data.get('avg_distance') else None,
                    'total_orders': int(agg_data['total_orders']) if agg_data.get('total_orders') else 0,
                    'days_with_data': int(agg_data['days_count']) if agg_data.get('days_count') else 0,
                    'top_carriers': []
                }
                
                if cargo_type == 'FTL':
                    ftl_data = stats
                elif cargo_type == 'LTL':
                    ltl_data = stats
            
            # Przetwarzanie top przewoźników według cargoType
            if result.get('top_carriers'):
                for carrier in result['top_carriers']:
                    cargo_type = carrier.get('cargoType')
                    carrier_info = {
                        'carrier_id': int(carrier['carrierId']) if carrier.get('carrierId') else None,
                        'carrier_name': carrier.get('carrierName'),
                        'order_count': int(carrier['order_count']) if carrier.get('order_count') else 0,
                        'avg_client_price_per_km': float(carrier['avg_client_price_per_km']) if carrier.get('avg_client_price_per_km') else None,
                        'avg_carrier_price_per_km': float(carrier['avg_carrier_price_per_km']) if carrier.get('avg_carrier_price_per_km') else None,
                        'avg_client_amount': float(carrier['avg_client_amount']) if carrier.get('avg_client_amount') else None,
                        'avg_carrier_amount': float(carrier['avg_carrier_amount']) if carrier.get('avg_carrier_amount') else None
                    }
                    
                    if cargo_type == 'FTL' and ftl_data:
                        ftl_data['top_carriers'].append(carrier_info)
                    elif cargo_type == 'LTL' and ltl_data:
                        ltl_data['top_carriers'].append(carrier_info)
            
            # Zwróć dane tylko jeśli jest FTL lub LTL
            if not ftl_data and not ltl_data:
                return None
            
            result_data = {
                'match_info': match_metadata  # Informacja o dopasowaniu
            }
            
            if ftl_data:
                result_data['FTL'] = ftl_data
            if ltl_data:
                result_data['LTL'] = ltl_data
            
            return result_data
            
    except Exception as exc:
        logger.error(f"❌ Historical orders query error: {exc}", exc_info=True)
        return None
    finally:
        if conn:
            _return_db_connection_main(conn)
        logger.info(f"⏱️ CAŁKOWITY CZAS get_historical_orders_pricing ({days}d): {(time.time() - start_time)*1000:.0f}ms")


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
        'version': '2.4.0',
        'features': {
            'security': 'API Key + Rate Limiting + HTTPS',
            'optimization': 'Single optimized query per data source',
            'monitoring': 'Performance metrics enabled',
            'data_sources': 'TimoCom + Trans.eu exchanges + Historical orders',
            'data': 'Weighted avg rates EUR/km from exchanges and real orders',
            'data_quality': 'Outlier filtering (>5 EUR/km removed)',
            'fuzzy_matching': 'Intelligent route matching (±100km threshold) with accuracy levels'
        }
    })


@app.route('/api/route-pricing', methods=['POST'])
@require_api_key
@limiter.limit("5 per minute")  # Max 5 requestów na minutę
def get_route_pricing():
    """Pobierz dane cenowe dla trasy transportowej
    Endpoint zwraca średnie stawki transportowe EUR/km z trzech źródeł:
    - TimoCom: ostatnie 30 dni (różne typy pojazdów)
    - Trans.eu: ostatnie 30 dni
    - Zlecenia historyczne firmowe: ostatnie 6 miesięcy (180 dni) z top 4 przewoźnikami
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
    responses:
      200:
        description: Sukces - średnie stawki z giełd (30 dni) i zleceń historycznych (180 dni z top przewoźnikami)
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
                start_region_id:
                  type: integer
                  description: ID regionu Trans.eu dla startu
                  example: 135
                end_region_id:
                  type: integer
                  description: ID regionu Trans.eu dla celu
                  example: 98
                pricing:
                  type: object
                  description: Dane cenowe z giełd (30 dni) i zleceń historycznych firmowych (180 dni)
                  properties:
                    timocom:
                      type: object
                      properties:
                        30d:
                          type: object
                          properties:
                            avg_price_per_km:
                              type: object
                              description: Średnie stawki EUR/km dla różnych typów pojazdów
                              properties:
                                trailer:
                                  type: number
                                  description: Naczepa
                                  example: 1.50
                                  nullable: true
                                3_5t:
                                  type: number
                                  description: Bus (do 3.5t)
                                  example: 1.00
                                  nullable: true
                                12t:
                                  type: number
                                  description: Solo (do 12t)
                                  example: 1.20
                                  nullable: true
                            median_price_per_km:
                              type: object
                              description: Mediany cen EUR/km
                              properties:
                                trailer:
                                  type: number
                                  example: 1.55
                                  nullable: true
                            total_offers:
                              type: integer
                              description: Całkowita liczba ofert
                              example: 24835
                            offers_by_vehicle_type:
                              type: object
                              description: Liczba ofert według typu pojazdu
                            days_with_data:
                              type: integer
                              description: Liczba dni z danymi
                              example: 30
                    transeu:
                      type: object
                      properties:
                        30d:
                          type: object
                          properties:
                            avg_price_per_km:
                              type: object
                              properties:
                                lorry:
                                  type: number
                                  example: 0.87
                                  nullable: true
                            median_price_per_km:
                              type: object
                              properties:
                                lorry:
                                  type: number
                                  example: 0.89
                                  nullable: true
                            total_offers:
                              type: integer
                              example: 9240
                            days_with_data:
                              type: integer
                              example: 28
                    historical:
                      type: object
                      description: Statystyki z rzeczywistych zleceń historycznych (ostatnie 6 miesięcy) z podziałem na FTL i LTL
                      properties:
                        180d:
                          type: object
                          description: Dane podzielone według typu ładunku
                          properties:
                            FTL:
                              type: object
                              description: Pełne ładunki (Full Truck Load)
                              properties:
                                avg_price_per_km:
                                  type: object
                                  description: Średnie ceny za km
                                  properties:
                                    client:
                                      type: number
                                      description: Cena sprzedaży
                                      example: 0.95
                                      nullable: true
                                    carrier:
                                      type: number
                                      description: Koszt realizacji
                                      example: 0.85
                                      nullable: true
                                median_price_per_km:
                                  type: object
                                  properties:
                                    client:
                                      type: number
                                      example: 0.92
                                      nullable: true
                                    carrier:
                                      type: number
                                      example: 0.83
                                      nullable: true
                                avg_amounts:
                                  type: object
                                  properties:
                                    client:
                                      type: number
                                      example: 850.50
                                      nullable: true
                                    carrier:
                                      type: number
                                      example: 750.00
                                      nullable: true
                                avg_distance:
                                  type: number
                                  example: 900.5
                                  nullable: true
                                total_orders:
                                  type: integer
                                  example: 25
                                days_with_data:
                                  type: integer
                                  example: 28
                                top_carriers:
                                  type: array
                                  description: Top 4 przewoźników FTL
                                  items:
                                    type: object
                                    properties:
                                      carrier_id:
                                        type: integer
                                        example: 123
                                      carrier_name:
                                        type: string
                                        example: "TRANS-POL SP. Z O.O."
                                      order_count:
                                        type: integer
                                        example: 15
                                      avg_client_price_per_km:
                                        type: number
                                        example: 0.98
                                        nullable: true
                                      avg_carrier_price_per_km:
                                        type: number
                                        example: 0.88
                                        nullable: true
                                      avg_client_amount:
                                        type: number
                                        example: 880.00
                                        nullable: true
                                      avg_carrier_amount:
                                        type: number
                                        example: 790.00
                                        nullable: true
                            LTL:
                              type: object
                              description: Ładunki częściowe (Less Than Truckload)
                              properties:
                                avg_price_per_km:
                                  type: object
                                  properties:
                                    client:
                                      type: number
                                      example: 1.15
                                      nullable: true
                                    carrier:
                                      type: number
                                      example: 1.05
                                      nullable: true
                                median_price_per_km:
                                  type: object
                                  properties:
                                    client:
                                      type: number
                                      example: 1.12
                                      nullable: true
                                    carrier:
                                      type: number
                                      example: 1.03
                                      nullable: true
                                avg_amounts:
                                  type: object
                                  properties:
                                    client:
                                      type: number
                                      example: 450.00
                                      nullable: true
                                    carrier:
                                      type: number
                                      example: 380.00
                                      nullable: true
                                avg_distance:
                                  type: number
                                  example: 400.0
                                  nullable: true
                                total_orders:
                                  type: integer
                                  example: 20
                                days_with_data:
                                  type: integer
                                  example: 25
                                top_carriers:
                                  type: array
                                  description: Top 4 przewoźników LTL
                                  items:
                                    type: object
                                    properties:
                                      carrier_id:
                                        type: integer
                                        example: 456
                                      carrier_name:
                                        type: string
                                        example: "EXPRESS-TRANS"
                                      order_count:
                                        type: integer
                                        example: 10
                                      avg_client_price_per_km:
                                        type: number
                                        example: 1.18
                                        nullable: true
                                      avg_carrier_price_per_km:
                                        type: number
                                        example: 1.08
                                        nullable: true
                                      avg_client_amount:
                                        type: number
                                        example: 480.00
                                        nullable: true
                                      avg_carrier_amount:
                                        type: number
                                        example: 410.00
                                        nullable: true
                            match_info:
                              type: object
                              description: Informacje o dopasowaniu tras (fuzzy matching)
                              properties:
                                matched_start:
                                  type: string
                                  description: Faktyczny kod startowy użyty do statystyk
                                  example: "PL20"
                                matched_end:
                                  type: string
                                  description: Faktyczny kod końcowy użyty do statystyk
                                  example: "DE49"
                                accuracy:
                                  type: string
                                  description: Poziom dokładności dopasowania
                                  enum: ["exact", "high", "medium", "low"]
                                  example: "exact"
                                start_distance_km:
                                  type: number
                                  description: Odległość między żądanym a dopasowanym punktem startowym (km)
                                  example: 0.0
                                end_distance_km:
                                  type: number
                                  description: Odległość między żądanym a dopasowanym punktem końcowym (km)
                                  example: 0.0
                currency:
                  type: string
                  description: Waluta
                  example: "EUR"
                unit:
                  type: string
                  description: Jednostka
                  example: "EUR/km"
                route_distance:
                  type: object
                  description: Rzeczywisty dystans drogowy dla ciężarówek (obliczony przez AWS Location Service)
                  properties:
                    distance_km:
                      type: number
                      description: Dystans w kilometrach
                      example: 587.45
                    method:
                      type: string
                      description: Metoda obliczania dystansu
                      enum: ["aws_truck_route", "haversine_fallback"]
                      example: "aws_truck_route"
                data_sources:
                  type: object
                  description: Dostępność danych ze źródeł
                  properties:
                    timocom:
                      type: boolean
                      example: true
                    transeu:
                      type: boolean
                      example: true
                    historical:
                      type: boolean
                      example: true
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
              example: "Brak wszystkich wymaganych pól: start_postal_code, end_postal_code"
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
        if not all([start_postal, end_postal]):
            return jsonify({
                'success': False,
                'error': 'Brak wszystkich wymaganych pól: start_postal_code, end_postal_code'
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
        
        # NOWE: Oblicz rzeczywisty dystans drogowy dla ciężarówek używając AWS Location Service
        route_distance_km = None
        distance_method = None
        
        # Pobierz współrzędne dla kodów pocztowych
        conn_main = _get_db_connection_main()
        try:
            start_coords = get_postal_code_coordinates(start_postal, conn_main)
            end_coords = get_postal_code_coordinates(end_postal, conn_main)
            
            if start_coords and end_coords:
                logger.info(f"📍 Coordinates: Start {start_postal} ({start_coords[0]:.5f}, {start_coords[1]:.5f}), End {end_postal} ({end_coords[0]:.5f}, {end_coords[1]:.5f})")
                
                # Wywołaj AWS API
                aws_start = time.time()
                aws_result = get_aws_route_distance(
                    start_lat=start_coords[0],
                    start_lng=start_coords[1],
                    end_lat=end_coords[0],
                    end_lng=end_coords[1],
                    return_geometry=False
                )
                
                if aws_result:
                    route_distance_km = aws_result['distance']
                    distance_method = 'aws_truck_route'
                    logger.info(f"⏱️ AWS Route Distance: {route_distance_km} km ({(time.time() - aws_start)*1000:.0f}ms)")
                else:
                    # Fallback do Haversine
                    haversine_dist = haversine_distance(start_coords[0], start_coords[1], end_coords[0], end_coords[1])
                    route_distance_km = round(haversine_dist * 1.3, 2)  # Współczynnik drogi 1.3
                    distance_method = 'haversine_fallback'
                    logger.info(f"⚠️ AWS failed, using Haversine fallback: {route_distance_km} km")
            else:
                logger.warning(f"⚠️ Could not get coordinates for distance calculation")
        finally:
            _return_db_connection_main(conn_main)
        
        # OPTYMALIZACJA: Pobierz tylko dane z 30 dni z obu giełd
        timocom_start = time.time()
        timocom_30d = get_timocom_pricing(start_region_id, end_region_id, days=30)
        logger.info(f"⏱️ Zapytanie TimoCom 30d: {(time.time() - timocom_start)*1000:.0f}ms")
        
        transeu_start = time.time()
        transeu_30d = get_transeu_pricing(start_region_id, end_region_id, days=30)
        logger.info(f"⏱️ Zapytanie Trans.eu 30d: {(time.time() - transeu_start)*1000:.0f}ms")
        
        # NOWE: Pobierz statystyki z zleceń historycznych (ostatnie 6 miesięcy)
        logger.info(f"📊 Calling get_historical_orders_pricing({start_postal}, {end_postal})")
        historical_start = time.time()
        historical_180d = get_historical_orders_pricing(start_postal, end_postal)  # domyślnie 180 dni
        logger.info(f"⏱️ Zapytanie Historical Orders 180d: {(time.time() - historical_start)*1000:.0f}ms")
        
        # Sprawdź czy są jakiekolwiek dane
        if not timocom_30d and not transeu_30d and not historical_180d:
            logger.info(f"ℹ️ No data found for route: {start_postal} -> {end_postal}")
            return jsonify({
                'success': False,
                'error': f'Brak danych dla trasy {start_postal} -> {end_postal}',
                'message': 'Nie znaleziono danych cenowych w bazie dla tej trasy'
            }), 404

        # ZAKOMENTOWANE: Obliczanie ceny całkowitej (dystans x stawka)
        # calc_start = time.time()
        # avg_rates = timocom_30d['avg_price_per_km']
        # calculated_prices = {}
        # for vehicle, rate in avg_rates.items():
        #     # Zmieniamy klucze, aby pasowały do oczekiwań (bus, solo, naczepa)
        #     vehicle_key = vehicle
        #     if vehicle == 'trailer':
        #         vehicle_key = 'naczepa'
        #     elif vehicle == '3_5t':
        #         vehicle_key = 'bus'
        #     elif vehicle == '12t':
        #         vehicle_key = 'solo'
        #
        #     if rate is not None:
        #         calculated_prices[f'cena_{vehicle_key}'] = round(rate * float(distance), 2)
        #     else:
        #         calculated_prices[f'cena_{vehicle_key}'] = None
        # logger.info(f"⏱️ Obliczenia cen: {(time.time() - calc_start)*1000:.0f}ms")
        
        logger.info(f"⏱️ ⭐ CAŁKOWITY CZAS REQUESTU: {(time.time() - request_start)*1000:.0f}ms")
        logger.info(f"✅ Successfully returned pricing data for {start_postal} -> {end_postal}")

        # Przygotuj response ze stawkami średnimi z 30 dni
        response_data = {
            'start_postal_code': start_postal,
            'end_postal_code': end_postal,
            'start_region_id': start_region_id,
            'end_region_id': end_region_id,
            'pricing': {
                'timocom': {
                    '30d': timocom_30d
                } if timocom_30d else {},
                'transeu': {
                    '30d': transeu_30d
                } if transeu_30d else {},
                'historical': {
                    '180d': historical_180d
                } if historical_180d else {}
            },
            'currency': 'EUR',
            'unit': 'EUR/km',
            'data_sources': {
                'timocom': bool(timocom_30d),
                'transeu': bool(transeu_30d),
                'historical': bool(historical_180d)
            }
        }
        
        # Dodaj dystans drogowy jeśli został obliczony
        if route_distance_km is not None:
            response_data['route_distance'] = {
                'distance_km': route_distance_km,
                'method': distance_method
            }

        return jsonify({
            'success': True,
            'data': response_data
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
