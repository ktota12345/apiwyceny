"""
Route Pricing API
Backend API dla wyceny tras transportowych na podstawie kodów pocztowych
"""

from flask import Flask, jsonify, request
from functools import wraps
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Any, Optional

app = Flask(__name__)

# Konfiguracja bazy danych PostgreSQL
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_USER = os.getenv("POSTGRES_USER")
DB_NAME = os.getenv("POSTGRES_DB")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# Konfiguracja API Key
API_KEY = os.getenv("API_KEY")  # Wymagany API key dla dostępu
REQUIRE_API_KEY = os.getenv("REQUIRE_API_KEY", "true").lower() == "true"

# Cache dla mapowań kodów pocztowych
_POSTAL_MAPPING_TRANSEU = None
_POSTAL_MAPPING_TIMOCOM = None


def require_api_key(f):
    """Decorator sprawdzający API key w headerze X-API-Key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Jeśli nie wymaga API key, pomiń sprawdzanie
        if not REQUIRE_API_KEY:
            return f(*args, **kwargs)
        
        # Jeśli brak skonfigurowanego API key, ostrzeżenie
        if not API_KEY:
            print("⚠️ UWAGA: API_KEY nie jest skonfigurowany, ale REQUIRE_API_KEY=true!")
            return jsonify({
                'success': False,
                'error': 'API nie jest poprawnie skonfigurowane'
            }), 500
        
        # Sprawdź API key w headerze
        provided_key = request.headers.get('X-API-Key')
        
        if not provided_key:
            return jsonify({
                'success': False,
                'error': 'Brak API key. Wymagany header: X-API-Key'
            }), 401
        
        if provided_key != API_KEY:
            print(f"⚠️ Nieautoryzowana próba dostępu z IP: {request.remote_addr}")
            return jsonify({
                'success': False,
                'error': 'Nieprawidłowy API key'
            }), 403
        
        # API key prawidłowy, kontynuuj
        return f(*args, **kwargs)
    
    return decorated_function


@app.route('/')
def index():
    """Strona główna z informacją o API"""
    return jsonify({
        'service': 'Route Pricing API',
        'version': '1.0.0',
        'endpoints': {
            '/health': 'Health check',
            '/api/route-pricing': 'POST - Pobierz wycenę trasy'
        },
        'documentation': 'https://github.com/[your-repo]/route-pricing-api'
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'route-pricing-api'})


def _get_db_connection():
    """Nawiązuje połączenie z bazą danych PostgreSQL"""
    if not all([DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME]):
        print("⚠ Ostrzeżenie: Brak pełnej konfiguracji bazy danych")
        return None
    
    try:
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursor_factory=RealDictCursor,
        )
    except Exception as exc:
        print(f"❌ Błąd połączenia z bazą danych: {exc}")
        return None


def _load_postal_mappings():
    """Ładuje mapowania kodów pocztowych na region IDs"""
    global _POSTAL_MAPPING_TRANSEU, _POSTAL_MAPPING_TIMOCOM
    
    if _POSTAL_MAPPING_TRANSEU is None or _POSTAL_MAPPING_TIMOCOM is None:
        try:
            transeu_path = os.path.join(os.path.dirname(__file__), 'data', 'postal_code_to_region_transeu.json')
            timocom_path = os.path.join(os.path.dirname(__file__), 'data', 'postal_code_to_region_timocom.json')
            
            with open(transeu_path, 'r', encoding='utf-8') as f:
                _POSTAL_MAPPING_TRANSEU = json.load(f)
            
            with open(timocom_path, 'r', encoding='utf-8') as f:
                _POSTAL_MAPPING_TIMOCOM = json.load(f)
            
            print(f"✓ Załadowano mapowania: Trans.eu ({len(_POSTAL_MAPPING_TRANSEU)} kodów), TimoCom ({len(_POSTAL_MAPPING_TIMOCOM)} kodów)")
        except Exception as e:
            print(f"❌ Błąd ładowania mapowań: {e}")
            _POSTAL_MAPPING_TRANSEU = {}
            _POSTAL_MAPPING_TIMOCOM = {}
    
    return _POSTAL_MAPPING_TRANSEU, _POSTAL_MAPPING_TIMOCOM


def _normalize_postal_code(postal_code: str) -> str:
    """Normalizuje kod pocztowy do formatu [KRAJ][2_CYFRY]"""
    # Usuń spacje, myślniki i inne znaki
    clean = postal_code.upper().replace(' ', '').replace('-', '')
    
    # Jeśli kod zaczyna się od liter (kraj), weź 2 litery + 2 cyfry
    if len(clean) >= 4 and clean[:2].isalpha():
        return clean[:4]
    
    # Jeśli kod to tylko cyfry, spróbuj odgadnąć kraj (zakładamy PL)
    if clean.isdigit() and len(clean) >= 2:
        return f"PL{clean[:2]}"
    
    return clean


def _get_region_id(postal_code: str, source: str = 'transeu') -> Optional[int]:
    """Mapuje kod pocztowy na region ID"""
    transeu_map, timocom_map = _load_postal_mappings()
    
    normalized = _normalize_postal_code(postal_code)
    mapping = transeu_map if source == 'transeu' else timocom_map
    
    if normalized in mapping:
        return mapping[normalized].get('region_id')
    
    return None


def _get_pricing_from_db(start_region_id: int, end_region_id: int, vehicle_type: str, periods: list = [7, 30, 90]) -> Dict[str, Any]:
    """Pobiera dane cenowe z bazy PostgreSQL"""
    conn = _get_db_connection()
    
    if not conn:
        return {
            'success': False,
            'error': 'Brak połączenia z bazą danych'
        }
    
    try:
        # Określ źródło danych i kolumny na podstawie typu pojazdu
        vehicle_config = {
            'naczepa': {'source': 'timocom', 'table': 'public.offers', 'column': 'trailer_avg_price_per_km'},
            'trailer': {'source': 'timocom', 'table': 'public.offers', 'column': 'trailer_avg_price_per_km'},
            '3.5t': {'source': 'timocom', 'table': 'public.offers', 'column': 'vehicle_up_to_3_5_t_avg_price_per_km'},
            '3_5t': {'source': 'timocom', 'table': 'public.offers', 'column': 'vehicle_up_to_3_5_t_avg_price_per_km'},
            '12t': {'source': 'timocom', 'table': 'public.offers', 'column': 'vehicle_up_to_12_t_avg_price_per_km'},
            'lorry': {'source': 'transeu', 'table': 'public."OffersTransEU"', 'column': 'lorry_avg_price_per_km'},
        }
        
        config = vehicle_config.get(vehicle_type.lower())
        if not config:
            return {
                'success': False,
                'error': f'Nieznany typ pojazdu: {vehicle_type}',
                'available_types': list(vehicle_config.keys())
            }
        
        pricing_data = {}
        
        with conn.cursor() as cur:
            for period in periods:
                query = f"""
                    SELECT
                        ROUND(AVG({config['column']}), 4) AS avg_price,
                        ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {config['column']}), 4) AS median_price,
                        COUNT(*) AS offers_count
                    FROM {config['table']}
                    WHERE starting_id = %s
                      AND destination_id = %s
                      AND {config['column']} IS NOT NULL
                      AND enlistment_date >= CURRENT_DATE - CAST(%s AS INTEGER)
                """
                
                cur.execute(query, (start_region_id, end_region_id, period))
                result = cur.fetchone()
                
                if result and result['avg_price']:
                    pricing_data[f'avg_{period}d'] = float(result['avg_price'])
                    pricing_data[f'median_{period}d'] = float(result['median_price']) if result['median_price'] else None
                    pricing_data[f'offers_{period}d'] = int(result['offers_count'])
                else:
                    pricing_data[f'avg_{period}d'] = None
                    pricing_data[f'median_{period}d'] = None
                    pricing_data[f'offers_{period}d'] = 0
        
        return {
            'success': True,
            'source': config['source'],
            'pricing': pricing_data
        }
        
    except Exception as e:
        print(f"❌ Błąd zapytania do bazy: {e}")
        return {
            'success': False,
            'error': f'Błąd zapytania do bazy: {str(e)}'
        }
    finally:
        conn.close()


@app.route('/api/route-pricing', methods=['POST'])
@require_api_key
def get_route_pricing():
    """
    Endpoint do pobierania cen dla trasy na podstawie kodów pocztowych
    
    Request JSON:
    {
        "start_postal_code": "PL50",
        "end_postal_code": "DE10",
        "vehicle_type": "naczepa"
    }
    
    Response JSON:
    {
        "success": true,
        "data": {
            "start_postal_code": "PL50",
            "end_postal_code": "DE10",
            "vehicle_type": "naczepa",
            "pricing": {
                "timocom": {
                    "avg_7d": 1.0,
                    "avg_30d": 1.04,
                    "avg_90d": 1.07,
                    "median_7d": 1.05,
                    "offers_7d": 4012
                }
            }
        }
    }
    """
    try:
        data = request.json
        start_postal = data.get('start_postal_code', '').strip()
        end_postal = data.get('end_postal_code', '').strip()
        vehicle_type = data.get('vehicle_type', 'naczepa').lower()
        
        if not start_postal or not end_postal:
            return jsonify({
                'success': False,
                'error': 'Brak kodów pocztowych (start_postal_code i end_postal_code wymagane)'
            }), 400
        
        # Mapuj kody pocztowe na region IDs
        # Określ źródło na podstawie typu pojazdu
        source = 'timocom' if vehicle_type in ['naczepa', 'trailer', '3.5t', '3_5t', '12t'] else 'transeu'
        
        start_region_id = _get_region_id(start_postal, source)
        end_region_id = _get_region_id(end_postal, source)
        
        if start_region_id is None:
            return jsonify({
                'success': False,
                'error': f'Nie znaleziono regionu dla kodu pocztowego: {start_postal}',
                'hint': 'Użyj formatu: [KRAJ][2_CYFRY], np. PL50, DE10'
            }), 404
        
        if end_region_id is None:
            return jsonify({
                'success': False,
                'error': f'Nie znaleziono regionu dla kodu pocztowego: {end_postal}',
                'hint': 'Użyj formatu: [KRAJ][2_CYFRY], np. PL50, DE10'
            }), 404
        
        # Pobierz dane cenowe z bazy
        result = _get_pricing_from_db(start_region_id, end_region_id, vehicle_type)
        
        if not result['success']:
            return jsonify(result), 500
        
        # Sprawdź czy są jakiekolwiek dane
        has_data = any(result['pricing'].get(f'avg_{p}d') for p in [7, 30, 90])
        
        if not has_data:
            return jsonify({
                'success': False,
                'error': f'Brak danych dla trasy {start_postal} -> {end_postal} w bazie',
                'region_ids': {'start': start_region_id, 'end': end_region_id}
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'start_postal_code': start_postal,
                'end_postal_code': end_postal,
                'vehicle_type': vehicle_type,
                'region_ids': {
                    'start': start_region_id,
                    'end': end_region_id
                },
                'pricing': {
                    result['source']: result['pricing']
                },
                'currency': 'EUR',
                'unit': 'EUR/km',
                'data_source': 'postgresql'
            }
        })
        
    except Exception as e:
        print(f"❌ Błąd w /api/route-pricing: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Błąd serwera: {str(e)}'
        }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
