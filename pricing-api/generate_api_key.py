#!/usr/bin/env python
"""
Generator bezpiecznego API key
Uruchom: python generate_api_key.py
"""
import secrets
import string

def generate_api_key(length=48):
    """Generuje bezpieczny losowy API key"""
    alphabet = string.ascii_letters + string.digits
    api_key = ''.join(secrets.choice(alphabet) for _ in range(length))
    return api_key

if __name__ == '__main__':
    api_key = generate_api_key()
    print("\n" + "="*60)
    print("NOWY API KEY")
    print("="*60)
    print(f"\n{api_key}\n")
    print("Skopiuj ten klucz do pliku .env:")
    print(f"API_KEY={api_key}")
    print("\n" + "="*60)
