import requests
import json

response = requests.post(
    'http://localhost:5001/api/pricing',
    json={
        'start_postal_code': 'DE49',
        'end_postal_code': 'PL20'
    },
    timeout=60
)

print(f"Status: {response.status_code}\n")

result = response.json()

if result['success']:
    data = result['data']
    print(f"✅ SUKCES! API działa poprawnie!\n")
    print(f"Start: {data['start_postal_code']} (region {data['start_region_id']})")
    print(f"End: {data['end_postal_code']} (region {data['end_region_id']})")
    print()
    
    print("📊 TimoCom 7d:")
    tc7d = data['pricing']['timocom']['7d']
    print(f"   Trailer: {tc7d['avg_price_per_km']['trailer']} EUR/km")
    print(f"   3.5t: {tc7d['avg_price_per_km']['3_5t']} EUR/km")
    print(f"   12t: {tc7d['avg_price_per_km']['12t']} EUR/km")
    print(f"   Oferty: {tc7d['total_offers']}")
    print(f"   Dni z danymi: {tc7d['days_with_data']}")
    print()
    
    print("📊 Trans.eu 7d:")
    te7d = data['pricing']['transeu']['7d']
    print(f"   Lorry: {te7d['avg_price_per_km']['lorry']} EUR/km")
    print(f"   Dni z danymi: {te7d['days_with_data']}")
    print()
    
    print(f"Dostępne okresy TimoCom: {list(data['pricing']['timocom'].keys())}")
    print(f"Dostępne okresy Trans.eu: {list(data['pricing']['transeu'].keys())}")
else:
    print(f"❌ Błąd: {result['error']}")
