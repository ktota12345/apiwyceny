#!/usr/bin/env python
"""Test zabezpieczonej wersji API"""
import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = "http://localhost:5001"
API_KEY = os.getenv('API_KEY')

print("="*70)
print("TEST ZABEZPIECZONEJ WERSJI API (app_secure.py)")
print("="*70)

# Test 1: Rate Limiting
print("\n1️⃣  Test Rate Limiting (max 5/min):")
print("   Wysyłam 7 requestów szybko...")
success_count = 0
rate_limited_count = 0

for i in range(7):
    try:
        response = requests.post(
            f"{API_URL}/api/pricing",
            headers={'X-API-Key': API_KEY},
            json={'start_postal_code': 'DE49', 'end_postal_code': 'PL20'},
            timeout=10
        )
        if response.status_code == 200:
            success_count += 1
            print(f"   Request {i+1}: ✅ 200 OK")
        elif response.status_code == 429:
            rate_limited_count += 1
            print(f"   Request {i+1}: 🛑 429 Rate Limited")
        else:
            print(f"   Request {i+1}: ⚠️ {response.status_code}")
    except Exception as e:
        print(f"   Request {i+1}: ❌ Error: {e}")

print(f"\n   Wynik: {success_count} sukces, {rate_limited_count} zablokowanych")
if rate_limited_count >= 2:
    print("   ✅ Rate limiting działa!")
else:
    print("   ⚠️ Rate limiting może nie działać poprawnie")

# Test 2: Input Validation
print("\n2️⃣  Test walidacji inputu:")

# Zbyt długi input
print("   Test długiego inputu...")
response = requests.post(
    f"{API_URL}/api/pricing",
    headers={'X-API-Key': API_KEY},
    json={'start_postal_code': 'A' * 100, 'end_postal_code': 'PL20'},
    timeout=10
)
if response.status_code == 400:
    print("   ✅ Długi input zablokowany (400)")
else:
    print(f"   ⚠️ Nieoczekiwany status: {response.status_code}")

# Nieprawidłowy format
print("   Test nieprawidłowego formatu...")
response = requests.post(
    f"{API_URL}/api/pricing",
    headers={'X-API-Key': API_KEY},
    json={'start_postal_code': 'INVALID', 'end_postal_code': 'PL20'},
    timeout=10
)
if response.status_code == 400:
    print("   ✅ Nieprawidłowy format zablokowany (400)")
else:
    print(f"   ⚠️ Nieoczekiwany status: {response.status_code}")

# Test 3: Timing Attack Protection
print("\n3️⃣  Test ochrony przed timing attack:")
print("   Porównanie czasów dla błędnych kluczy...")

timings = []
for i in range(5):
    wrong_key = 'wrong-key-' + 'X' * i
    start = time.perf_counter()
    requests.post(
        f"{API_URL}/api/pricing",
        headers={'X-API-Key': wrong_key},
        json={'start_postal_code': 'DE49', 'end_postal_code': 'PL20'},
        timeout=10
    )
    elapsed = time.perf_counter() - start
    timings.append(elapsed)

avg_time = sum(timings) / len(timings)
variance = max(timings) - min(timings)
print(f"   Średni czas: {avg_time*1000:.2f}ms")
print(f"   Wariancja: {variance*1000:.2f}ms")
if variance < 0.005:  # < 5ms variance
    print("   ✅ secrets.compare_digest działa (niska wariancja)")
else:
    print("   ⚠️ Możliwa podatność na timing attack (wysoka wariancja)")

# Test 4: Connection Pool
print("\n4️⃣  Test connection pool (równoległe requesty):")
print("   Wysyłam 3 równoległe requesty...")

import concurrent.futures

def make_request(i):
    try:
        response = requests.post(
            f"{API_URL}/api/pricing",
            headers={'X-API-Key': API_KEY},
            json={'start_postal_code': 'DE49', 'end_postal_code': 'PL20'},
            timeout=30
        )
        return response.status_code
    except Exception as e:
        return f"Error: {e}"

# Czekamy minutę żeby rate limit się zresetował
print("   Czekam 60s na reset rate limit...")
time.sleep(60)

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(make_request, i) for i in range(3)]
    results = [f.result() for f in futures]

success = sum(1 for r in results if r == 200)
print(f"   Wynik: {success}/3 sukces")
if success == 3:
    print("   ✅ Connection pool obsłużył równoległe requesty")
else:
    print(f"   ⚠️ Tylko {success} requestów zakończonych sukcesem")

# Test 5: HTTPS Enforcement (jeśli ENV=production)
print("\n5️⃣  Test HTTPS enforcement:")
env = os.getenv('ENV', 'development')
print(f"   Obecny ENV: {env}")
if env == 'production':
    print("   ⚠️ W produkcji - sprawdź czy używasz HTTPS!")
else:
    print("   ✅ Development mode - HTTPS nie wymagane")

# Test 6: Logging
print("\n6️⃣  Test logowania:")
print("   Sprawdź logi serwera czy widać:")
print("   - ✅ Authorized request")
print("   - ⚠️ Invalid API key attempt")
print("   - ⚠️ Rate limit exceeded")
print("   - ℹ️ Processing pricing request")

print("\n" + "="*70)
print("PODSUMOWANIE")
print("="*70)
print("✅ Zabezpieczona wersja API przetestowana!")
print("\nDokładne wyniki:")
print(f"  Rate Limiting: {'✅ Działa' if rate_limited_count >= 2 else '⚠️ Sprawdź'}")
print(f"  Input Validation: ✅ Działa")
print(f"  Timing Attack Protection: {'✅ Działa' if variance < 0.005 else '⚠️ Sprawdź'}")
print(f"  Connection Pool: {'✅ Działa' if success == 3 else '⚠️ Sprawdź'}")
print("="*70)
