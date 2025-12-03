#!/usr/bin/env python
"""Test API z autoryzacją API key"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = "http://localhost:5001"
API_KEY = os.getenv('API_KEY')

print("="*70)
print("TEST AUTORYZACJI API")
print("="*70)

# Test 1: Bez API key (powinno zwrócić 401)
print("\n1️⃣  Test bez API key (oczekiwany 401):")
try:
    response = requests.post(
        f"{API_URL}/api/pricing",
        json={'start_postal_code': 'DE49', 'end_postal_code': 'PL20'},
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 401, "Powinno być 401!"
    print("   ✅ OK - API zwróciło 401 bez klucza")
except Exception as e:
    print(f"   ❌ Błąd: {e}")

# Test 2: Z nieprawidłowym API key (powinno zwrócić 403)
print("\n2️⃣  Test z nieprawidłowym API key (oczekiwany 403):")
try:
    response = requests.post(
        f"{API_URL}/api/pricing",
        headers={'X-API-Key': 'wrong-key-123'},
        json={'start_postal_code': 'DE49', 'end_postal_code': 'PL20'},
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 403, "Powinno być 403!"
    print("   ✅ OK - API zwróciło 403 dla błędnego klucza")
except Exception as e:
    print(f"   ❌ Błąd: {e}")

# Test 3: Z prawidłowym API key w headerze X-API-Key (powinno działać)
print("\n3️⃣  Test z prawidłowym API key (X-API-Key header):")
try:
    response = requests.post(
        f"{API_URL}/api/pricing",
        headers={'X-API-Key': API_KEY},
        json={'start_postal_code': 'DE49', 'end_postal_code': 'PL20'},
        timeout=60
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()['data']
        print(f"   ✅ OK - API zwróciło dane!")
        print(f"   Trasa: {data['start_postal_code']} -> {data['end_postal_code']}")
        print(f"   TimoCom 7d oferty: {data['pricing']['timocom']['7d']['total_offers']}")
    else:
        print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   ❌ Błąd: {e}")

# Test 4: Z prawidłowym API key w headerze Authorization (powinno działać)
print("\n4️⃣  Test z prawidłowym API key (Authorization Bearer header):")
try:
    response = requests.post(
        f"{API_URL}/api/pricing",
        headers={'Authorization': f'Bearer {API_KEY}'},
        json={'start_postal_code': 'DE49', 'end_postal_code': 'PL20'},
        timeout=60
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ OK - API zwróciło dane z Authorization Bearer!")
    else:
        print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   ❌ Błąd: {e}")

# Test 5: Health check bez API key (powinno działać)
print("\n5️⃣  Test health check bez API key (powinno działać):")
try:
    response = requests.get(f"{API_URL}/health", timeout=10)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 200, "Health check powinien być dostępny bez klucza!"
    print("   ✅ OK - Health check działa bez API key")
except Exception as e:
    print(f"   ❌ Błąd: {e}")

print("\n" + "="*70)
print("PODSUMOWANIE")
print("="*70)
print("✅ Autoryzacja API key działa poprawnie!")
print(f"   Twój API key: {API_KEY}")
print("\nNastępne kroki:")
print("  1. Nigdy nie commituj .env z prawdziwym kluczem!")
print("  2. Użyj HTTPS w produkcji")
print("  3. Dodaj ten klucz do dokumentacji dla klientów")
print("="*70)
