"""
Klient API do pobierania wycen tras
Prosty wrapper dla endpoint /api/route-pricing
"""

import requests
from typing import Optional, Dict, Any


class RoutePricingClient:
    """
    Klient do komunikacji z API wyceny tras
    """
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        Inicjalizuje klienta
        
        Args:
            base_url: URL serwera API (domyślnie: http://localhost:5000)
        """
        self.base_url = base_url.rstrip('/')
        self.endpoint = f"{self.base_url}/api/route-pricing"
    
    def get_route_pricing(
        self,
        start_postal_code: str,
        end_postal_code: str,
        vehicle_type: str = "naczepa",
        timeout: int = 10
    ) -> Dict[str, Any]:
        """
        Pobiera wycenę dla trasy
        
        Args:
            start_postal_code: Kod pocztowy początku trasy
            end_postal_code: Kod pocztowy końca trasy
            vehicle_type: Typ pojazdu (domyślnie: naczepa)
            timeout: Timeout żądania w sekundach
            
        Returns:
            Słownik z danymi odpowiedzi API
            
        Raises:
            requests.exceptions.RequestException: W przypadku błędu komunikacji
        """
        payload = {
            "start_postal_code": start_postal_code,
            "end_postal_code": end_postal_code,
            "vehicle_type": vehicle_type
        }
        
        response = requests.post(self.endpoint, json=payload, timeout=timeout)
        return response.json()
    
    def get_average_price(
        self,
        start_postal_code: str,
        end_postal_code: str,
        vehicle_type: str = "naczepa",
        period: str = "7d"
    ) -> Optional[float]:
        """
        Pobiera średnią cenę dla trasy w wybranym okresie
        
        Args:
            start_postal_code: Kod pocztowy początku trasy
            end_postal_code: Kod pocztowy końca trasy
            vehicle_type: Typ pojazdu
            period: Okres (7d, 30d, 90d)
            
        Returns:
            Średnia cena w EUR/km lub None jeśli brak danych
        """
        try:
            result = self.get_route_pricing(start_postal_code, end_postal_code, vehicle_type)
            
            if not result.get('success'):
                return None
            
            pricing = result['data']['pricing']
            
            # Znajdź źródło danych (timocom lub transeu)
            source = list(pricing.keys())[0] if pricing else None
            
            if not source:
                return None
            
            return pricing[source].get(f'avg_{period}')
            
        except Exception as e:
            print(f"Błąd: {e}")
            return None
    
    def get_total_cost(
        self,
        start_postal_code: str,
        end_postal_code: str,
        vehicle_type: str = "naczepa",
        period: str = "7d"
    ) -> Optional[float]:
        """
        Oblicza całkowity koszt trasy
        
        Args:
            start_postal_code: Kod pocztowy początku trasy
            end_postal_code: Kod pocztowy końca trasy
            vehicle_type: Typ pojazdu
            period: Okres (7d, 30d, 90d)
            
        Returns:
            Całkowity koszt w EUR lub None jeśli brak danych
        """
        try:
            result = self.get_route_pricing(start_postal_code, end_postal_code, vehicle_type)
            
            if not result.get('success'):
                return None
            
            data = result['data']
            distance = data.get('distance_km')
            pricing = data['pricing']
            
            if not distance:
                return None
            
            # Znajdź źródło danych (timocom lub transeu)
            source = list(pricing.keys())[0] if pricing else None
            
            if not source:
                return None
            
            avg_price_per_km = pricing[source].get(f'avg_{period}')
            
            if avg_price_per_km is None:
                return None
            
            return distance * avg_price_per_km
            
        except Exception as e:
            print(f"Błąd: {e}")
            return None
    
    def compare_vehicle_types(
        self,
        start_postal_code: str,
        end_postal_code: str,
        vehicle_types: list = None,
        period: str = "7d"
    ) -> Dict[str, Optional[float]]:
        """
        Porównuje ceny dla różnych typów pojazdów
        
        Args:
            start_postal_code: Kod pocztowy początku trasy
            end_postal_code: Kod pocztowy końca trasy
            vehicle_types: Lista typów pojazdów do porównania
            period: Okres (7d, 30d, 90d)
            
        Returns:
            Słownik {typ_pojazdu: średnia_cena}
        """
        if vehicle_types is None:
            vehicle_types = ["naczepa", "3.5t", "12t", "lorry"]
        
        results = {}
        
        for vehicle_type in vehicle_types:
            avg_price = self.get_average_price(
                start_postal_code,
                end_postal_code,
                vehicle_type,
                period
            )
            results[vehicle_type] = avg_price
        
        return results


# Przykłady użycia
if __name__ == '__main__':
    # Utwórz klienta
    client = RoutePricingClient()
    
    print("="*60)
    print("PRZYKŁADY UŻYCIA CLIENT API")
    print("="*60)
    
    # Przykład 1: Pobierz pełne dane
    print("\n1. Pobieranie pełnych danych:")
    result = client.get_route_pricing("89", "50", "naczepa")
    if result.get('success'):
        print(f"   ✓ Trasa: {result['data']['start_postal_code']} -> {result['data']['end_postal_code']}")
        print(f"   ✓ Dystans: {result['data']['distance_km']} km")
        pricing = result['data']['pricing']['timocom']
        print(f"   ✓ Średnia 7d: {pricing['avg_7d']} EUR/km")
    else:
        print(f"   ✗ Błąd: {result.get('error')}")
    
    # Przykład 2: Pobierz tylko średnią cenę
    print("\n2. Pobieranie średniej ceny:")
    avg_price = client.get_average_price("89", "50", "naczepa", "30d")
    if avg_price:
        print(f"   ✓ Średnia cena (30d): {avg_price} EUR/km")
    else:
        print("   ✗ Brak danych")
    
    # Przykład 3: Oblicz całkowity koszt
    print("\n3. Obliczanie całkowitego kosztu:")
    total_cost = client.get_total_cost("89", "50", "naczepa", "7d")
    if total_cost:
        print(f"   ✓ Całkowity koszt: {total_cost:.2f} EUR")
    else:
        print("   ✗ Brak danych")
    
    # Przykład 4: Porównaj różne typy pojazdów
    print("\n4. Porównanie typów pojazdów:")
    comparison = client.compare_vehicle_types("89", "50", period="7d")
    for vehicle_type, price in comparison.items():
        if price:
            print(f"   ✓ {vehicle_type:15s}: {price:.2f} EUR/km")
        else:
            print(f"   - {vehicle_type:15s}: Brak danych")
    
    print("\n" + "="*60)
