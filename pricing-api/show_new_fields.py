#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Pokazuje nowe pola w API response"""

import requests
import json

print("="*70)
print("PRICING API - NOWE POLA W ODPOWIEDZI")
print("="*70)

try:
    response = requests.post(
        'http://localhost:5001/api/pricing',
        json={
            'start_postal_code': 'DE49',
            'end_postal_code': 'PL20'
        },
        timeout=60
    )
    
    if response.status_code == 200:
        data = response.json()['data']
        
        print("\n✅ SUKCES - Nowe dane dostępne!\n")
        
        # TimoCom 7d
        tc = data['pricing']['timocom']['7d']
        print("📊 TimoCom 7 dni:")
        print(f"   Średnia trailer:       {tc['avg_price_per_km']['trailer']} EUR/km")
        print(f"   ⭐ MEDIANA trailer:     {tc['median_price_per_km']['trailer']} EUR/km")
        print(f"   ⭐ Oferty OGÓŁEM:       {tc['total_offers']}")
        print(f"   ⭐ Oferty trailer:      {tc['offers_by_vehicle_type']['trailer']}")
        print(f"   ⭐ Oferty 3.5t:         {tc['offers_by_vehicle_type']['3_5t']}")
        print(f"   ⭐ Oferty 12t:          {tc['offers_by_vehicle_type']['12t']}")
        print(f"   Dni z danymi:          {tc['days_with_data']}")
        
        print()
        
        # Trans.eu 7d
        te = data['pricing']['transeu']['7d']
        print("📊 Trans.eu 7 dni:")
        print(f"   Średnia lorry:         {te['avg_price_per_km']['lorry']} EUR/km")
        print(f"   ⭐ MEDIANA lorry:       {te['median_price_per_km']['lorry']} EUR/km")
        print(f"   ⭐ Oferty OGÓŁEM:       {te['total_offers']}")
        print(f"   Dni z danymi:          {te['days_with_data']}")
        
        print("\n" + "="*70)
        print("LEGENDA: ⭐ = nowe pole")
        print("="*70)
        
        # Pokaż wszystkie dostępne okresy
        print("\n📅 Dostępne okresy:")
        for period in ['7d', '30d', '90d']:
            tc_offers = data['pricing']['timocom'][period]['total_offers']
            te_offers = data['pricing']['transeu'][period]['total_offers']
            print(f"   {period}: TimoCom {tc_offers} ofert, Trans.eu {te_offers} ofert")
        
    else:
        print(f"\n❌ Błąd {response.status_code}")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
except requests.exceptions.Timeout:
    print("\n⏱️ Timeout - zapytanie trwa zbyt długo")
    print("   Sprawdź czy w bazie są indeksy:")
    print("   CREATE INDEX idx_offers_route_date ON public.offers (starting_id, destination_id, enlistment_date DESC);")
except Exception as e:
    print(f"\n❌ Błąd: {e}")
    import traceback
    traceback.print_exc()
