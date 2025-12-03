"""
Pricing API - Standalone API dla wyceny tras transportowych
Endpoint: POST /api/pricing
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from decimal import Decimal
from typing import Any, Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import json

# Załaduj zmienne środowiskowe z pliku .env
load_dotenv()

app = Flask(__name__)
CORS(app)  # Włącz CORS dla wszystkich origin

# Konfiguracja połączenia z bazą danych
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_USER = os.getenv("POSTGRES_USER")
DB_NAME = os.getenv("POSTGRES_DB")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# Cache dla mapowania Trans.eu -> TimoCom
_TRANSEU_TO_TIMOCOM_MAPPING = None


def _get_db_connection():
    """Nawiązuje połączenie z bazą danych PostgreSQL"""
    if not all([DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME]):
        raise Exception("Brak pełnej konfiguracji bazy danych w pliku .env")
    
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
        raise Exception(f"Błąd połączenia z bazą danych: {exc}")


def _load_transeu_timocom_mapping():
    """Ładuje mapowanie Trans.eu -> TimoCom z pliku JSON"""
    global _TRANSEU_TO_TIMOCOM_MAPPING
    
    if _TRANSEU_TO_TIMOCOM_MAPPING is not None:
        return _TRANSEU_TO_TIMOCOM_MAPPING
    
    try:
        mapping_path = os.path.join(os.path.dirname(__file__), 'data', 'transeu_to_timocom_mapping.json')
        with open(mapping_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Konwertuj klucze ze string na int
            _TRANSEU_TO_TIMOCOM_MAPPING = {int(k): v['timocom_id'] for k, v in data.items()}
    except Exception as e:
        _TRANSEU_TO_TIMOCOM_MAPPING = {}
    
    return _TRANSEU_TO_TIMOCOM_MAPPING


def map_transeu_to_timocom_id(transeu_id: int) -> int:
    """Konwertuje Trans.eu region ID na TimoCom region ID"""
    mapping = _load_transeu_timocom_mapping()
    return mapping.get(transeu_id, transeu_id)


def get_timocom_pricing(start_region_id: int, end_region_id: int, days: int = 7):
    """
    Pobiera dane cenowe TimoCom z bazy danych PostgreSQL
    
    Args:
        start_region_id: Trans.eu region ID (będzie skonwertowane na TimoCom ID)
        end_region_id: Trans.eu region ID (będzie skonwertowane na TimoCom ID)
        days: liczba dni wstecz
    
    Returns:
        Dict z cenami lub None jeśli brak danych
    """
    # Konwertuj Trans.eu ID na TimoCom ID
    timocom_start_id = map_transeu_to_timocom_id(start_region_id)
    timocom_end_id = map_transeu_to_timocom_id(end_region_id)
    
    print(f"🔄 Mapowanie TimoCom: Trans.eu [{start_region_id} -> {end_region_id}] → TimoCom [{timocom_start_id} -> {timocom_end_id}]")
    
    conn = _get_db_connection()
    
    try:
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
                    '3_5t': None,  # Brak kolumny median dla 3.5t w bazie
                    '12t': None   # Brak kolumny median dla 12t w bazie
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
        return None
    finally:
        conn.close()


def get_transeu_pricing(start_region_id: int, end_region_id: int, days: int = 7):
    """
    Pobiera dane cenowe Trans.eu z bazy danych PostgreSQL
    
    Args:
        start_region_id: Trans.eu region ID
        end_region_id: Trans.eu region ID
        days: liczba dni wstecz
    
    Returns:
        Dict z cenami lub None jeśli brak danych
    """
    print(f"🔄 Trans.eu: Zapytanie dla regionów {start_region_id} -> {end_region_id}")
    
    conn = _get_db_connection()
    
    try:
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
        return None
    finally:
        conn.close()


# Cache dla mapowania kodów pocztowych
_POSTAL_CODE_MAPPING = None

def _load_postal_code_mapping():
    """Ładuje mapowanie kodów pocztowych na regiony"""
    global _POSTAL_CODE_MAPPING
    
    if _POSTAL_CODE_MAPPING is not None:
        return _POSTAL_CODE_MAPPING
    
    try:
        mapping_path = os.path.join(os.path.dirname(__file__), 'data', 'postal_code_to_region_transeu.json')
        with open(mapping_path, 'r', encoding='utf-8') as f:
            _POSTAL_CODE_MAPPING = json.load(f)
        print(f"✓ Załadowano mapowanie kodów pocztowych ({len(_POSTAL_CODE_MAPPING)} kodów)")
    except Exception as e:
        print(f"⚠ Nie udało się załadować mapowania kodów pocztowych: {e}")
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
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'Pricing API',
        'version': '1.0.0'
    })


@app.route('/api/pricing', methods=['POST'])
@require_api_key
def get_pricing():
    """
    Endpoint do pobierania cen dla trasy
    
    Request JSON:
    {
        "start_postal_code": "PL50",
        "end_postal_code": "DE10"
    }
    
    Response JSON:
    {
        "success": true,
        "data": {
            "start_postal_code": "PL50",
            "end_postal_code": "DE10",
            "start_region_id": 134,
            "end_region_id": 89,
            "pricing": {
                "timocom": {
                    "7d": { "avg": {...}, "median": {...}, "offers": 4012, "days": 7 },
                    "30d": {...},
                    "90d": {...}
                },
                "transeu": {
                    "7d": { "avg": {...}, "median": {...}, "days": 7 },
                    "30d": {...},
                    "90d": {...}
                }
            },
            "currency": "EUR",
            "unit": "EUR/km"
        }
    }
    """
    try:
        data = request.json
        
        if not data:
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
        
        # Konwertuj kody pocztowe na region IDs
        start_region_id = postal_code_to_region_id(start_postal)
        end_region_id = postal_code_to_region_id(end_postal)
        
        if not start_region_id or not end_region_id:
            return jsonify({
                'success': False,
                'error': f'Nie znaleziono regionu dla kodów: {start_postal if not start_region_id else ""} {end_postal if not end_region_id else ""}',
                'message': 'Użyj formatu: KOD_KRAJU + 2 cyfry (np. PL50, DE10, FR75)'
            }), 404
        
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
            return jsonify({
                'success': False,
                'error': f'Brak danych dla trasy {start_postal} -> {end_postal}',
                'message': 'Nie znaleziono danych cenowych w bazie dla tej trasy'
            }), 404
        
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
        return jsonify({
            'success': False,
            'error': 'Błąd serwera'
        }), 500


if __name__ == '__main__':
    # Pobierz port z zmiennej środowiskowej lub użyj 5001 lokalnie
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
