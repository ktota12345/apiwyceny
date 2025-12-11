"""
AWS Location Service Distance Calculator for Trucks

Moduł do obliczania rzeczywistych dystansów drogowych dla ciężarówek 
wykorzystując AWS Location Service Routes API v2.

Wymagane zmienne środowiskowe:
- AWS_LOCATION_API_KEY: API key z AWS Location Service
- AWS_REGION: Region AWS (domyślnie 'eu-central-1')

Zależności:
- requests
- python-dotenv (opcjonalnie, do ładowania .env)
"""

import os
import requests
from typing import Optional, Dict


def get_aws_route_distance(
    start_lat: float, 
    start_lng: float, 
    end_lat: float, 
    end_lng: float, 
    return_geometry: bool = False,
    aws_api_key: Optional[str] = None,
    aws_region: Optional[str] = None
) -> Optional[Dict]:
    """
    Wywołuje AWS Location Service Routes API aby obliczyć rzeczywisty dystans drogowy dla ciężarówek.
    
    Args:
        start_lat (float): Szerokość geograficzna punktu startowego
        start_lng (float): Długość geograficzna punktu startowego
        end_lat (float): Szerokość geograficzna punktu końcowego
        end_lng (float): Długość geograficzna punktu końcowego
        return_geometry (bool): Czy zwrócić również geometrię trasy (dla mapy)
        aws_api_key (str, optional): AWS API Key. Jeśli None, pobiera z zmiennej środowiskowej AWS_LOCATION_API_KEY
        aws_region (str, optional): AWS Region. Jeśli None, pobiera z zmiennej środowiskowej AWS_REGION (domyślnie 'eu-central-1')
    
    Returns:
        Dict z kluczami:
            - 'distance' (float): Dystans w kilometrach (zaokrąglony do 2 miejsc po przecinku)
            - 'geometry' (List[List[float]]): Lista punktów trasy [[lng, lat], ...] (opcjonalnie)
            - 'duration' (int): Czas przejazdu w sekundach (opcjonalnie)
        
        None w przypadku błędu
    
    Example:
        >>> result = get_aws_route_distance(52.2297, 21.0122, 50.0647, 19.9450)
        >>> if result:
        ...     print(f"Dystans: {result['distance']} km")
        ... else:
        ...     print("Błąd obliczania dystansu")
        
        >>> # Z geometrią trasy
        >>> result = get_aws_route_distance(52.2297, 21.0122, 50.0647, 19.9450, return_geometry=True)
        >>> if result:
        ...     print(f"Punkty trasy: {len(result['geometry'])}")
    """
    # Pobierz konfigurację
    api_key = aws_api_key or os.getenv("AWS_LOCATION_API_KEY")
    region = aws_region or os.getenv("AWS_REGION", "eu-central-1")
    
    if not api_key:
        print("[AWS] ❌ BŁĄD: Brak API key (AWS_LOCATION_API_KEY)")
        return None
    
    try:
        # AWS Location Service Routes API v2 endpoint
        url = f"https://routes.geo.{region}.amazonaws.com/v2/routes?key={api_key}"
        
        print(f"[AWS] 🌐 URL: {url[:80]}...")
        print(f"[AWS] 📍 Origin: [{start_lng}, {start_lat}]")
        print(f"[AWS] 📍 Destination: [{end_lng}, {end_lat}]")
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # UWAGA: AWS wymaga kolejności [longitude, latitude]!
        payload = {
            "Origin": [start_lng, start_lat],
            "Destination": [end_lng, end_lat],
            "TravelMode": "Truck",              # Tryb dla ciężarówek
            "OptimizeRoutingFor": "FastestRoute",  # Najszybsza trasa
            "LegGeometryFormat": "Simple"       # Format geometrii trasy
        }
        
        print(f"[AWS] 📤 Wysyłam request do AWS...")
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        print(f"[AWS] 📥 Otrzymano odpowiedź: status={response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'Routes' in data and len(data['Routes']) > 0:
                route = data['Routes'][0]
                
                # Suma dystansów ze wszystkich legs i travel steps
                total_distance = 0
                for leg in route.get('Legs', []):
                    vehicle_details = leg.get('VehicleLegDetails', {})
                    travel_steps = vehicle_details.get('TravelSteps', [])
                    for step in travel_steps:
                        total_distance += step.get('Distance', 0)
                
                # Konwertuj metry na kilometry
                distance_km = total_distance / 1000.0
                result = {'distance': round(distance_km, 2)}
                
                # Dodaj geometrię jeśli żądana
                if return_geometry:
                    geometry_points = []
                    for leg in route.get('Legs', []):
                        leg_geometry = leg.get('Geometry', {})
                        if 'LineString' in leg_geometry:
                            # LineString to lista punktów [lng, lat]
                            geometry_points.extend(leg_geometry['LineString'])
                    
                    result['geometry'] = geometry_points
                    result['duration'] = route.get('Summary', {}).get('Duration', 0)  # Czas w sekundach
                    print(f"[AWS] ✓ Dystans: {distance_km:.2f} km, Punkty trasy: {len(geometry_points)}")
                else:
                    print(f"[AWS] ✓ Dystans AWS: {distance_km:.2f} km")
                
                return result
            else:
                print(f"[AWS] ❌ Brak tras w odpowiedzi")
                return None
        
        print(f"[AWS] ❌ Błąd API: status={response.status_code}")
        print(f"[AWS] Response body: {response.text[:500]}")
        return None
            
    except requests.exceptions.Timeout:
        print("[AWS] ❌ Timeout (15s) - brak odpowiedzi od AWS")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"[AWS] ❌ ConnectionError: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[AWS] ❌ RequestException: {e}")
        return None
    except Exception as e:
        print(f"[AWS] ❌ Nieoczekiwany błąd: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Oblicza dystans w linii prostej (great circle distance) między dwoma punktami.
    Używane jako fallback gdy AWS API jest niedostępny.
    
    Args:
        lat1, lon1: Współrzędne pierwszego punktu
        lat2, lon2: Współrzędne drugiego punktu
    
    Returns:
        float: Dystans w kilometrach
    """
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371  # Promień Ziemi w kilometrach
    
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    distance = R * c
    return round(distance, 2)


def get_route_distance_with_fallback(
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
    return_geometry: bool = False,
    road_factor: float = 1.3
) -> Dict:
    """
    Oblicza dystans z automatycznym fallback do Haversine w razie błędu AWS.
    
    Args:
        start_lat, start_lng: Współrzędne startu
        end_lat, end_lng: Współrzędne końca
        return_geometry: Czy zwrócić geometrię (tylko dla AWS)
        road_factor: Współczynnik drogi dla Haversine (domyślnie 1.3)
    
    Returns:
        Dict z kluczami:
            - 'distance' (float): Dystans w km
            - 'method' (str): 'aws' lub 'haversine_fallback'
            - 'geometry' (List, optional): Tylko dla AWS
            - 'duration' (int, optional): Tylko dla AWS
    """
    # Najpierw spróbuj AWS
    aws_result = get_aws_route_distance(
        start_lat, start_lng, end_lat, end_lng, return_geometry
    )
    
    if aws_result is not None:
        aws_result['method'] = 'aws'
        return aws_result
    
    # Fallback: Haversine
    print("[AWS] ⚠️  Używam fallback (Haversine)")
    haversine_dist = calculate_haversine_distance(start_lat, start_lng, end_lat, end_lng)
    road_distance = round(haversine_dist * road_factor, 2)
    
    return {
        'distance': road_distance,
        'method': 'haversine_fallback',
        'haversine_distance': haversine_dist,
        'road_factor': road_factor
    }


# Przykład użycia
if __name__ == "__main__":
    # Załaduj zmienne środowiskowe z .env (opcjonalnie)
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("python-dotenv nie jest zainstalowane - używam zmiennych systemowych")
    
    # Test 1: Warszawa -> Kraków
    print("\n" + "="*60)
    print("TEST 1: Warszawa -> Kraków")
    print("="*60)
    
    result = get_aws_route_distance(
        start_lat=52.2297,  # Warszawa
        start_lng=21.0122,
        end_lat=50.0647,    # Kraków
        end_lng=19.9450
    )
    
    if result:
        print(f"\n✅ Sukces! Dystans: {result['distance']} km")
    else:
        print("\n❌ Błąd obliczania dystansu")
    
    # Test 2: Z geometrią
    print("\n" + "="*60)
    print("TEST 2: Warszawa -> Kraków (z geometrią)")
    print("="*60)
    
    result = get_aws_route_distance(
        start_lat=52.2297,
        start_lng=21.0122,
        end_lat=50.0647,
        end_lng=19.9450,
        return_geometry=True
    )
    
    if result:
        print(f"\n✅ Dystans: {result['distance']} km")
        print(f"✅ Czas: {result.get('duration', 0)} sekund")
        print(f"✅ Punkty trasy: {len(result.get('geometry', []))}")
    
    # Test 3: Z fallback
    print("\n" + "="*60)
    print("TEST 3: Warszawa -> Kraków (z fallback)")
    print("="*60)
    
    result = get_route_distance_with_fallback(
        start_lat=52.2297,
        start_lng=21.0122,
        end_lat=50.0647,
        end_lng=19.9450
    )
    
    print(f"\n✅ Dystans: {result['distance']} km")
    print(f"✅ Metoda: {result['method']}")
