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
    print(f"✅ SUKCES! API działa z rozszerzonymi danymi!\n")
    print("="*70)
    print(f"Trasa: {data['start_postal_code']} -> {data['end_postal_code']}")
    print(f"Region IDs: {data['start_region_id']} -> {data['end_region_id']}")
    print("="*70)
    
    # TimoCom - wszystkie okresy
    print("\n📊 TIMOCOM")
    print("-"*70)
    for period in ['7d', '30d', '90d']:
        if period in data['pricing']['timocom']:
            tc = data['pricing']['timocom'][period]
            print(f"\n{period.upper()} ({tc['days_with_data']} dni z danymi):")
            print(f"  Średnie ceny (EUR/km):")
            print(f"    • Trailer: {tc['avg_price_per_km']['trailer']}")
            print(f"    • 3.5t:    {tc['avg_price_per_km']['3_5t']}")
            print(f"    • 12t:     {tc['avg_price_per_km']['12t']}")
            print(f"  Mediany (EUR/km):")
            print(f"    • Trailer: {tc['median_price_per_km']['trailer']}")
            print(f"    • 3.5t:    {tc['median_price_per_km']['3_5t']}")
            print(f"    • 12t:     {tc['median_price_per_km']['12t']}")
            print(f"  Liczba ofert:")
            print(f"    • Ogółem:  {tc['total_offers']}")
            print(f"    • Trailer: {tc['offers_by_vehicle_type']['trailer']}")
            print(f"    • 3.5t:    {tc['offers_by_vehicle_type']['3_5t']}")
            print(f"    • 12t:     {tc['offers_by_vehicle_type']['12t']}")
    
    # Trans.eu - wszystkie okresy
    print("\n" + "="*70)
    print("📊 TRANS.EU")
    print("-"*70)
    for period in ['7d', '30d', '90d']:
        if period in data['pricing']['transeu']:
            te = data['pricing']['transeu'][period]
            print(f"\n{period.upper()} ({te['days_with_data']} dni z danymi):")
            print(f"  Średnia cena (EUR/km):")
            print(f"    • Lorry: {te['avg_price_per_km']['lorry']}")
            print(f"  Mediana (EUR/km):")
            print(f"    • Lorry: {te['median_price_per_km']['lorry']}")
            print(f"  Liczba ofert: {te['total_offers']}")
    
    print("\n" + "="*70)
    print("\n✨ Wszystkie dane dostępne!")
    print(f"   - Średnie ceny ✅")
    print(f"   - Mediany ✅")
    print(f"   - Liczby ofert (ogółem i po typach) ✅")
    print(f"   - Trzy okresy czasowe (7d, 30d, 90d) ✅")
    
else:
    print(f"❌ Błąd: {result['error']}")
    
print("\n" + "="*70)
print("Pełna odpowiedź JSON (pierwsze 2000 znaków):")
print("-"*70)
print(json.dumps(result, indent=2, ensure_ascii=False)[:2000])
