"""
Przykład użycia API - test z różnymi trasami
"""
import requests
import json

API_URL = "http://localhost:5001"

# Lista tras do przetestowania
test_routes = [
    ("PL50", "DE10", "Wrocław -> Berlin"),
    ("PL00", "DE01", "Warszawa -> Berlin (region)"),
    ("PL52", "DE01", "Warszawa -> Hamburg"),
    ("PL02", "PL50", "Warszawa -> Wrocław"),
    ("DE10", "FR75", "Berlin -> Paryż"),
    ("PL80", "DE80", "Gdańsk -> Monachium"),
]

print("\n" + "="*80)
print("TESTOWANIE RÓŻNYCH TRAS")
print("="*80)

for start, end, description in test_routes:
    print(f"\n📍 {description}")
    print(f"   Trasa: {start} -> {end}")
    
    response = requests.post(
        f"{API_URL}/api/pricing",
        json={
            "start_postal_code": start,
            "end_postal_code": end
        }
    )
    
    if response.status_code == 200:
        data = response.json()['data']
        print(f"   ✅ Znaleziono dane!")
        print(f"   Region IDs: {data['start_region_id']} -> {data['end_region_id']}")
        
        # TimoCom
        if 'timocom' in data['pricing'] and '7d' in data['pricing']['timocom']:
            tc_7d = data['pricing']['timocom']['7d']
            avg = tc_7d['avg_price_per_km']
            print(f"   TimoCom 7d: trailer={avg.get('trailer')} EUR/km, oferty={tc_7d.get('total_offers')}")
        
        # Trans.eu
        if 'transeu' in data['pricing'] and '7d' in data['pricing']['transeu']:
            te_7d = data['pricing']['transeu']['7d']
            avg = te_7d['avg_price_per_km']
            print(f"   Trans.eu 7d: lorry={avg.get('lorry')} EUR/km")
    else:
        error = response.json()
        print(f"   ❌ Brak danych: {error.get('error')}")

print("\n" + "="*80)
