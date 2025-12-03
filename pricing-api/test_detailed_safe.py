import requests
import json

try:
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
    
    if result.get('success'):
        data = result['data']
        print(f"✅ API działa z rozszerzonymi danymi!\n")
        
        # TimoCom 7d przykład
        if '7d' in data['pricing'].get('timocom', {}):
            tc7d = data['pricing']['timocom']['7d']
            print("📊 TimoCom 7d:")
            print(f"   Średnia trailer: {tc7d['avg_price_per_km']['trailer']} EUR/km")
            print(f"   Mediana trailer: {tc7d['median_price_per_km']['trailer']} EUR/km")
            print(f"   Oferty ogółem: {tc7d['total_offers']}")
            print(f"   Oferty trailer: {tc7d['offers_by_vehicle_type']['trailer']}")
            print(f"   Oferty 3.5t: {tc7d['offers_by_vehicle_type']['3_5t']}")
            print(f"   Oferty 12t: {tc7d['offers_by_vehicle_type']['12t']}")
            print(f"   Dni z danymi: {tc7d['days_with_data']}\n")
        
        # Trans.eu 7d przykład
        if '7d' in data['pricing'].get('transeu', {}):
            te7d = data['pricing']['transeu']['7d']
            print("📊 Trans.eu 7d:")
            print(f"   Średnia lorry: {te7d['avg_price_per_km']['lorry']} EUR/km")
            print(f"   Mediana lorry: {te7d['median_price_per_km']['lorry']} EUR/km")
            print(f"   Oferty: {te7d['total_offers']}")
            print(f"   Dni z danymi: {te7d['days_with_data']}\n")
        
        print("✨ Nowe pola w odpowiedzi:")
        print("   ✅ median_price_per_km (mediany)")
        print("   ✅ total_offers (liczba ofert)")
        print("   ✅ offers_by_vehicle_type (rozbicie po typach - tylko TimoCom)")
        
    else:
        print(f"❌ Błąd: {result.get('error', 'Nieznany błąd')}")
        
except Exception as e:
    print(f"❌ Wyjątek: {e}")
    import traceback
    traceback.print_exc()
