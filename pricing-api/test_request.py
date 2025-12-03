import requests
import json
import sys

url = "http://localhost:5001/api/pricing"
data = {
    "start_postal_code": "DE49",
    "end_postal_code": "PL20"
}

print(f"🚀 Wysyłanie requestu do {url}")
print(f"   Dane: {data}\n")

try:
    response = requests.post(url, json=data, timeout=10)
    
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}\n")
    
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if response.status_code == 200 and result.get('success'):
        print("\n✅ SUKCES - API zwróciło dane!")
        sys.exit(0)
    else:
        print(f"\n❌ BŁĄD - {result.get('error', 'Nieznany błąd')}")
        sys.exit(1)
        
except requests.exceptions.ConnectionError:
    print("❌ Nie można połączyć się z API")
    sys.exit(1)
except Exception as e:
    print(f"❌ Błąd: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
