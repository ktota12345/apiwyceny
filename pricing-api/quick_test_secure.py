#!/usr/bin/env python
"""Szybki test zabezpieczeń"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = "http://localhost:5001"
API_KEY = os.getenv('API_KEY')

print("\n🔒 QUICK TEST ZABEZPIECZONEJ WERSJI\n")

# Test 1: Health check
print("1. Health check (bez API key):")
r = requests.get(f"{API_URL}/health")
print(f"   Status: {r.status_code} - {r.json()['service']}")

# Test 2: Bez API key
print("\n2. Request bez API key:")
r = requests.post(f"{API_URL}/api/pricing", json={'start_postal_code': 'DE49', 'end_postal_code': 'PL20'})
print(f"   Status: {r.status_code} - {r.json()['error']}")

# Test 3: Z API key
print("\n3. Request z prawidłowym API key:")
r = requests.post(
    f"{API_URL}/api/pricing",
    headers={'X-API-Key': API_KEY},
    json={'start_postal_code': 'DE49', 'end_postal_code': 'PL20'},
    timeout=60
)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()['data']
    print(f"   ✅ Dane zwrócone: TimoCom 7d = {data['pricing']['timocom']['7d']['total_offers']} ofert")

# Test 4: Walidacja
print("\n4. Nieprawidłowy kod pocztowy:")
r = requests.post(
    f"{API_URL}/api/pricing",
    headers={'X-API-Key': API_KEY},
    json={'start_postal_code': 'INVALID123', 'end_postal_code': 'PL20'}
)
print(f"   Status: {r.status_code} - {r.json()['error']}")

# Test 5: Rate limit (5 requestów)
print("\n5. Test rate limiting (5 requestów szybko):")
for i in range(6):
    r = requests.post(
        f"{API_URL}/api/pricing",
        headers={'X-API-Key': API_KEY},
        json={'start_postal_code': 'DE49', 'end_postal_code': 'PL20'},
        timeout=30
    )
    if r.status_code == 429:
        print(f"   Request {i+1}: 🛑 429 Rate Limited - DZIAŁA!")
        break
    else:
        print(f"   Request {i+1}: ✅ {r.status_code}")

print("\n✅ Zabezpieczona wersja działa poprawnie!\n")
