"""
Prosty test API - sprawdza czy endpointy działają
Uwaga: Wymaga uruchomionego serwera i połączenia z bazą!
"""

import requests
import json
import os

BASE_URL = "http://localhost:5000"
API_KEY = os.getenv("API_KEY", "your-test-api-key")  # Pobierz z .env lub użyj testowego

def test_health():
    """Test health check"""
    print("\n" + "="*60)
    print("TEST: Health check")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Błąd: {e}")
        return False

def test_root():
    """Test root endpoint"""
    print("\n" + "="*60)
    print("TEST: Root endpoint")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Błąd: {e}")
        return False

def test_route_pricing(start="PL50", end="DE10", vehicle="naczepa"):
    """Test route pricing endpoint"""
    print("\n" + "="*60)
    print(f"TEST: Route pricing {start} -> {end} ({vehicle})")
    print("="*60)
    
    try:
        payload = {
            "start_postal_code": start,
            "end_postal_code": end,
            "vehicle_type": vehicle
        }
        
        headers = {
            "X-API-Key": API_KEY
        }
        
        response = requests.post(
            f"{BASE_URL}/api/route-pricing",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if data.get('success'):
            print("\n✓ Sukces!")
            pricing = data['data']['pricing']
            for source, metrics in pricing.items():
                print(f"\n{source.upper()}:")
                for key, value in metrics.items():
                    if value is not None:
                        print(f"  {key}: {value}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Błąd: {e}")
        return False

def test_unauthorized():
    """Test dostępu bez API key"""
    print("\n" + "="*60)
    print("TEST: Unauthorized access (bez API key)")
    print("="*60)
    
    try:
        payload = {
            "start_postal_code": "PL50",
            "end_postal_code": "DE10",
            "vehicle_type": "naczepa"
        }
        
        # Wywołanie BEZ headera X-API-Key
        response = requests.post(
            f"{BASE_URL}/api/route-pricing",
            json=payload,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        # Oczekujemy 401 Unauthorized
        if response.status_code == 401:
            print("\n✓ Zabezpieczenie działa! (401 Unauthorized)")
            return True
        else:
            print(f"\n⚠ Oczekiwano 401, otrzymano {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Błąd: {e}")
        return False

if __name__ == '__main__':
    print("="*60)
    print("ROUTE PRICING API - TESTY")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {API_KEY[:10]}..." if len(API_KEY) > 10 else "API Key: [BRAK]")
    print("Upewnij się, że serwer działa i masz połączenie z bazą!")
    
    results = []
    
    # Test 1: Health check
    results.append(("Health check", test_health()))
    
    # Test 2: Root endpoint
    results.append(("Root endpoint", test_root()))
    
    # Test 3: Unauthorized access
    results.append(("Unauthorized access", test_unauthorized()))
    
    # Test 4: Route pricing with API key
    results.append(("Route pricing (authorized)", test_route_pricing("PL50", "DE10", "naczepa")))
    
    # Podsumowanie
    print("\n" + "="*60)
    print("PODSUMOWANIE")
    print("="*60)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    print(f"\nWynik: {passed}/{total} testów zaliczonych")
