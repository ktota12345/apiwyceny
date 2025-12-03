"""
Test script dla Pricing API
Uruchom: python test_api.py
"""
import requests
import json

# URL API (zmień jeśli inny)
API_URL = "http://localhost:5001"

def test_health_check():
    """Test health check endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    
    response = requests.get(f"{API_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'
    print("✅ Health check passed!")


def test_pricing_api():
    """Test pricing endpoint z przykładową trasą"""
    print("\n" + "="*60)
    print("TEST 2: Pricing API - PL50 -> DE10")
    print("="*60)
    
    payload = {
        "start_postal_code": "PL50",
        "end_postal_code": "DE10"
    }
    
    print(f"Request: {json.dumps(payload, indent=2)}")
    
    response = requests.post(
        f"{API_URL}/api/pricing",
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200:
        data = response.json()
        assert data['success'] == True
        assert 'pricing' in data['data']
        print("\n✅ Pricing API test passed!")
        
        # Wyświetl podsumowanie
        if 'timocom' in data['data']['pricing']:
            print("\n📊 TimoCom:")
            for period, prices in data['data']['pricing']['timocom'].items():
                avg = prices.get('avg_price_per_km', {})
                print(f"  {period}: trailer={avg.get('trailer')} EUR/km, oferty={prices.get('total_offers', 0)}")
        
        if 'transeu' in data['data']['pricing']:
            print("\n📊 Trans.eu:")
            for period, prices in data['data']['pricing']['transeu'].items():
                avg = prices.get('avg_price_per_km', {})
                print(f"  {period}: lorry={avg.get('lorry')} EUR/km")
    else:
        print(f"\n⚠️ Test zwrócił status {response.status_code}")


def test_invalid_postal_code():
    """Test z nieprawidłowym kodem pocztowym"""
    print("\n" + "="*60)
    print("TEST 3: Invalid Postal Code")
    print("="*60)
    
    payload = {
        "start_postal_code": "INVALID",
        "end_postal_code": "DE10"
    }
    
    response = requests.post(
        f"{API_URL}/api/pricing",
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    assert response.status_code == 404
    assert response.json()['success'] == False
    print("✅ Invalid postal code test passed!")


def test_missing_data():
    """Test z trasą bez danych"""
    print("\n" + "="*60)
    print("TEST 4: Missing Data Route")
    print("="*60)
    
    payload = {
        "start_postal_code": "PL01",  # Prawdopodobnie brak danych
        "end_postal_code": "PL02"
    }
    
    response = requests.post(
        f"{API_URL}/api/pricing",
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 404:
        print("✅ Missing data test passed (brak danych - oczekiwane)!")
    elif response.status_code == 200:
        print("✅ Missing data test passed (znaleziono dane)!")


if __name__ == "__main__":
    try:
        print("\n🚀 Rozpoczynam testy Pricing API")
        print(f"API URL: {API_URL}")
        
        # Uruchom testy
        test_health_check()
        test_pricing_api()
        test_invalid_postal_code()
        test_missing_data()
        
        print("\n" + "="*60)
        print("✅ Wszystkie testy zakończone!")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ BŁĄD: Nie można połączyć się z API")
        print(f"Sprawdź czy serwer działa na {API_URL}")
        print("Uruchom: python app.py")
    except Exception as e:
        print(f"\n❌ BŁĄD: {e}")
        import traceback
        traceback.print_exc()
