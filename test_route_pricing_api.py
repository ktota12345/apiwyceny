"""
Skrypt testowy dla API wyceny tras
Testuje endpoint /api/route-pricing
"""

import requests
import json

# URL API (zmień na właściwy adres jeśli serwer działa na innym porcie)
BASE_URL = "http://localhost:5000"
ENDPOINT = "/api/route-pricing"

def test_api(start_postal, end_postal, vehicle_type="naczepa"):
    """
    Testuje API dla podanej trasy i typu pojazdu
    """
    url = f"{BASE_URL}{ENDPOINT}"
    
    payload = {
        "start_postal_code": start_postal,
        "end_postal_code": end_postal,
        "vehicle_type": vehicle_type
    }
    
    print(f"\n{'='*60}")
    print(f"TEST: {start_postal} -> {end_postal} ({vehicle_type})")
    print(f"{'='*60}")
    print(f"Request: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        print(f"\nStatus Code: {response.status_code}")
        
        data = response.json()
        print(f"\nResponse:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        if data.get('success'):
            # Wyświetl szczegóły
            route_data = data['data']
            print(f"\n✓ SUKCES!")
            print(f"  Dystans: {route_data.get('distance_km')} km")
            print(f"  Waluta: {route_data.get('currency')}")
            
            pricing = route_data.get('pricing', {})
            for source, metrics in pricing.items():
                print(f"\n  {source.upper()}:")
                if metrics.get('avg_7d'):
                    print(f"    Średnia 7d:  {metrics['avg_7d']} EUR/km")
                if metrics.get('avg_30d'):
                    print(f"    Średnia 30d: {metrics['avg_30d']} EUR/km")
                if metrics.get('avg_90d'):
                    print(f"    Średnia 90d: {metrics['avg_90d']} EUR/km")
                if metrics.get('offers_7d'):
                    print(f"    Oferty 7d:   {metrics['offers_7d']}")
        else:
            print(f"\n✗ BŁĄD: {data.get('error')}")
            
        return data
        
    except requests.exceptions.ConnectionError:
        print("\n❌ BŁĄD: Nie można połączyć się z serwerem!")
        print("   Upewnij się, że serwer Flask działa (python app.py)")
        return None
    except requests.exceptions.Timeout:
        print("\n❌ BŁĄD: Timeout - serwer nie odpowiada!")
        return None
    except Exception as e:
        print(f"\n❌ BŁĄD: {e}")
        return None

def main():
    """
    Uruchamia testy dla różnych tras i typów pojazdów
    """
    print("="*60)
    print("TEST API WYCENY TRAS")
    print("="*60)
    
    # Test 1: Podstawowa trasa - Naczepa
    test_api("89", "50", "naczepa")
    
    # Test 2: Ta sama trasa - Pojazd 3.5t
    test_api("89", "50", "3.5t")
    
    # Test 3: Ta sama trasa - Lorry (Trans.eu)
    test_api("89", "50", "lorry")
    
    # Test 4: Nieistniejąca trasa (powinien zwrócić 404)
    test_api("99999", "88888", "naczepa")
    
    # Test 5: Nieprawidłowy typ pojazdu (powinien zwrócić 400)
    test_api("89", "50", "nieznany_typ")
    
    # Test 6: Brak kodów pocztowych (powinien zwrócić 400)
    url = f"{BASE_URL}{ENDPOINT}"
    print(f"\n{'='*60}")
    print(f"TEST: Brak kodów pocztowych")
    print(f"{'='*60}")
    try:
        response = requests.post(url, json={}, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ BŁĄD: {e}")
    
    print("\n" + "="*60)
    print("TESTY ZAKOŃCZONE")
    print("="*60)

if __name__ == '__main__':
    main()
