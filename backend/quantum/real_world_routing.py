import requests
import json
import math
import time
from typing import List, Dict, Tuple
import numpy as np
import openrouteservice
import os


class RealWorldRouteOptimizer:
    """
    Real-world routing using actual roads instead of straight-line distances.
    Uses OpenRouteService for routing.
    """
    
    def __init__(self, api_key: str, timeout: int = 30):
        """
        Initialize router
        Args:
            api_key: Your OpenRouteService API key.
            timeout: Request timeout in seconds.
        """
        if not api_key:
            raise ValueError("OpenRouteService API key is required.")
        
        self.api_key = api_key  # Store API key for REST calls
        self.client = openrouteservice.Client(key=api_key)
        self.timeout = timeout
        
        # Backup: Use Haversine if routing fails
        self.fallback_to_haversine = True
        
        # Cache for route calculations
        self.route_cache = {}
    
    def get_real_distance(self, point1: Dict, point2: Dict) -> Tuple[float, Dict]:
        """
        Get real distance between two points using actual roads
        Returns: (distance_in_km, route_data)
        """
        cache_key = f"{point1['lat']:.4f},{point1['lng']:.4f}_{point2['lat']:.4f},{point2['lng']:.4f}"
        
        if cache_key in self.route_cache:
            return self.route_cache[cache_key]
        
        try:
            distance, route_data = self._ors_distance(point1, point2)
            
            # Cache result
            self.route_cache[cache_key] = (distance, route_data)
            return distance, route_data
            
        except Exception as e:
            print(f"Routing error: {e}")
            # Fallback to Haversine
            if self.fallback_to_haversine:
                distance, route_data = self._haversine_distance(point1, point2)
                self.route_cache[cache_key] = (distance, route_data)
                return distance, route_data
            raise
    
    def get_alternative_routes(self, point1: Dict, point2: Dict, max_alternatives: int = 3) -> List[Tuple[float, Dict]]:
        """
        Get multiple alternative routes between two points (e.g., coastal vs inland)
        Returns: List of (distance_in_km, route_data) tuples
        """
        cache_key = f"{point1['lat']:.4f},{point1['lng']:.4f}_{point2['lat']:.4f},{point2['lng']:.4f}_alternatives"
        
        if cache_key in self.route_cache:
            return self.route_cache[cache_key]
        
        try:
            alternatives = self._ors_alternative_routes(point1, point2, max_alternatives)
            
            # Cache result
            self.route_cache[cache_key] = alternatives
            return alternatives
            
        except Exception as e:
            print(f"Alternative routing error: {e}")
            # Fallback to single route
            distance, route_data = self.get_real_distance(point1, point2)
            return [(distance, route_data)]
    
    def _ors_alternative_routes(self, point1: Dict, point2: Dict, max_alternatives: int = 3) -> List[Tuple[float, Dict]]:
        """
        Get multiple alternative routes using OpenRouteService REST API
        Returns different road options (e.g., coastal ECR vs inland NH)
        
        For routes >100km, ORS doesn't support alternative_routes, so we create
        alternative routes by forcing different paths via intermediate waypoints
        """
        alternatives = []
        
        # First try the standard alternative routes API
        try:
            # Use direct REST API call for alternative routes
            url = 'https://api.openrouteservice.org/v2/directions/driving-car'
            
            headers = {
                'Content-Type': 'application/json; charset=utf-8',
                'Accept': 'application/json, application/geo+json',
                'Authorization': self.api_key  # Use the stored API key
            }
            
            payload = {
                'coordinates': [
                    [point1['lng'], point1['lat']],
                    [point2['lng'], point2['lat']]
                ],
                'alternative_routes': {
                    'share_factor': 0.8,       # Routes differ by at least 80%
                    'target_count': max_alternatives,
                    'weight_factor': 2.0        # Allow routes up to 2x longer
                }
            }
            
            print(f"Attempting ORS alternative routes API...")
            
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            
            if response.status_code != 200:
                error_data = response.json()
                if 'error' in error_data and 'code' in error_data['error'] and error_data['error']['code'] == 2004:
                    # Route too long for alternative routes API (>100km)
                    print(f"Route exceeds 100km limit, generating alternatives via intermediate waypoints...")
                    return self._generate_alternatives_via_waypoints(point1, point2, max_alternatives)
                else:
                    print(f"ORS API Error Response: {response.text}")
            
            response.raise_for_status()
            
            data = response.json()
            
            if 'routes' in data:
                print(f"Got {len(data['routes'])} alternative routes from OpenRouteService")
                for i, route in enumerate(data['routes']):
                    summary = route['summary']
                    distance_km = summary['distance'] / 1000
                    
                    # Decode polyline geometry
                    geometry = route['geometry']
                    if isinstance(geometry, str):
                        decoded_geometry = openrouteservice.convert.decode_polyline(geometry)
                        coords = decoded_geometry['coordinates']
                    else:
                        # Already decoded coordinates
                        coords = geometry['coordinates'] if 'coordinates' in geometry else geometry
                    
                    alternatives.append((distance_km, {
                        'distance': distance_km,
                        'duration': summary['duration'] / 60,  # in minutes
                        'geometry': coords,
                        'legs': route.get('segments', []),
                        'provider': 'OpenRouteService',
                        'route_index': i
                    }))
            
            if not alternatives:
                raise Exception("No alternative routes found in response")
                
            return alternatives
        
        except requests.exceptions.RequestException as e:
            print(f"REST API request failed: {e}, falling back to single route")
            distance, route_data = self._ors_distance(point1, point2)
            return [(distance, route_data)]
        except Exception as e:
            print(f"Could not get alternative routes: {e}, falling back to single route")
            import traceback
            traceback.print_exc()
            distance, route_data = self._ors_distance(point1, point2)
            return [(distance, route_data)]
    
    def _generate_alternatives_via_waypoints(self, point1: Dict, point2: Dict, max_alternatives: int = 3) -> List[Tuple[float, Dict]]:
        """
        For long routes (>100km), generate alternatives using different routing strategies.
        Works globally for any land-based route.
        Uses route options, avoid_polygons, and preference parameters to find real alternatives.
        """
        alternatives = []
        url = 'https://api.openrouteservice.org/v2/directions/driving-car'
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json, application/geo+json',
            'Authorization': self.api_key
        }
        
        lat1, lng1 = point1['lat'], point1['lng']
        lat2, lng2 = point2['lat'], point2['lng']
        
        # Calculate straight-line distance as sanity check
        haversine_dist = self._haversine_distance_coords(lat1, lng1, lat2, lng2)
        print(f"Straight-line distance: {haversine_dist:.2f} km")
        
        # If straight-line distance is extremely large (>5000km), warn but try anyway
        if haversine_dist > 5000:
            print(f"⚠️  Warning: Very long route ({haversine_dist:.0f} km). Route may cross continents.")
        
        # Strategy 1: Get the direct/fastest route first
        try:
            payload = {
                'coordinates': [[lng1, lat1], [lng2, lat2]],
                'preference': 'fastest'
            }
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if 'routes' in data and len(data['routes']) > 0:
                route = data['routes'][0]
                summary = route['summary']
                distance_km = summary['distance'] / 1000
                geometry = route['geometry']
                
                if isinstance(geometry, str):
                    decoded_geometry = openrouteservice.convert.decode_polyline(geometry)
                    coords_list = decoded_geometry['coordinates']
                else:
                    coords_list = geometry['coordinates'] if 'coordinates' in geometry else geometry
                
                alternatives.append((distance_km, {
                    'distance': distance_km,
                    'duration': summary['duration'] / 60,
                    'geometry': coords_list,
                    'legs': route.get('segments', []),
                    'provider': 'OpenRouteService',
                    'route_type': 'fastest'
                }))
                print(f"Generated fastest route: {distance_km:.2f} km")
        except Exception as e:
            print(f"Could not generate fastest route: {e}")
        
        # Strategy 2: Try shortest distance route (different from fastest)
        if len(alternatives) < max_alternatives:
            try:
                payload = {
                    'coordinates': [[lng1, lat1], [lng2, lat2]],
                    'preference': 'shortest'
                }
                response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                
                if 'routes' in data and len(data['routes']) > 0:
                    route = data['routes'][0]
                    summary = route['summary']
                    distance_km = summary['distance'] / 1000
                    
                    # Only add if significantly different from fastest route
                    if not alternatives or abs(distance_km - alternatives[0][0]) > 5:
                        geometry = route['geometry']
                        if isinstance(geometry, str):
                            decoded_geometry = openrouteservice.convert.decode_polyline(geometry)
                            coords_list = decoded_geometry['coordinates']
                        else:
                            coords_list = geometry['coordinates'] if 'coordinates' in geometry else geometry
                        
                        alternatives.append((distance_km, {
                            'distance': distance_km,
                            'duration': summary['duration'] / 60,
                            'geometry': coords_list,
                            'legs': route.get('segments', []),
                            'provider': 'OpenRouteService',
                            'route_type': 'shortest'
                        }))
                        print(f"Generated shortest route: {distance_km:.2f} km")
            except Exception as e:
                print(f"Could not generate shortest route: {e}")
        
        # Strategy 3: Avoid highways to find local roads alternative
        if len(alternatives) < max_alternatives:
            try:
                payload = {
                    'coordinates': [[lng1, lat1], [lng2, lat2]],
                    'options': {
                        'avoid_features': ['highways']
                    }
                }
                response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                
                if 'routes' in data and len(data['routes']) > 0:
                    route = data['routes'][0]
                    summary = route['summary']
                    distance_km = summary['distance'] / 1000
                    
                    # Only add if significantly different
                    is_different = True
                    for alt_dist, _ in alternatives:
                        if abs(distance_km - alt_dist) < 5:
                            is_different = False
                            break
                    
                    if is_different:
                        geometry = route['geometry']
                        if isinstance(geometry, str):
                            decoded_geometry = openrouteservice.convert.decode_polyline(geometry)
                            coords_list = decoded_geometry['coordinates']
                        else:
                            coords_list = geometry['coordinates'] if 'coordinates' in geometry else geometry
                        
                        alternatives.append((distance_km, {
                            'distance': distance_km,
                            'duration': summary['duration'] / 60,
                            'geometry': coords_list,
                            'legs': route.get('segments', []),
                            'provider': 'OpenRouteService',
                            'route_type': 'no_highways'
                        }))
                        print(f"Generated no-highways route: {distance_km:.2f} km")
            except Exception as e:
                print(f"Could not generate no-highways route: {e}")
        
        if not alternatives:
            # Fallback to single best route
            print("No alternatives generated, using single route")
            distance, route_data = self._ors_distance(point1, point2)
            return [(distance, route_data)]
        
        return alternatives
    
    def _ors_distance(self, point1: Dict, point2: Dict) -> Tuple[float, Dict]:
        """
        Get distance using OpenRouteService.
        This uses actual road networks for accurate routing.
        """
        coords = ((point1['lng'], point1['lat']), (point2['lng'], point2['lat']))
        
        try:
            # Request directions
            routes = self.client.directions(
                coordinates=coords,
                profile='driving-car',
                format='json',
                radiuses=10000, # Increase radius for better matching
                geometry='true'
            )
            
            if routes and 'routes' in routes and len(routes['routes']) > 0:
                route = routes['routes'][0]
                summary = route['summary']
                distance_km = summary['distance'] / 1000
                
                # Decode polyline geometry
                decoded_geometry = openrouteservice.convert.decode_polyline(route['geometry'])
                
                return distance_km, {
                    'distance': distance_km,
                    'duration': summary['duration'] / 60,  # in minutes
                    'geometry': decoded_geometry['coordinates'], # Return decoded coordinates
                    'legs': route.get('segments', []),
                    'provider': 'OpenRouteService'
                }
            else:
                raise Exception("No route found by OpenRouteService")
        
        except openrouteservice.exceptions.ApiError as e:
            # API error - use fallback
            if self.fallback_to_haversine:
                return self._haversine_distance(point1, point2)
            raise
        except Exception as e:
            # Any error - use fallback
            if self.fallback_to_haversine:
                return self._haversine_distance(point1, point2)
            raise

    def _haversine_distance_coords(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Calculate straight-line distance between coordinates using Haversine formula
        Returns distance in kilometers
        """
        R = 6371  # Earth's radius in km
        lat1_rad, lon1_rad = math.radians(lat1), math.radians(lng1)
        lat2_rad, lon2_rad = math.radians(lat2), math.radians(lng2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        return R * c
    
    def _haversine_distance(self, point1: Dict, point2: Dict) -> Tuple[float, Dict]:
        """
        Fallback: Calculate straight-line distance using Haversine formula
        Note: This doesn't follow roads
        """
        distance_km = self._haversine_distance_coords(point1['lat'], point1['lng'], point2['lat'], point2['lng'])
        
        # Add road factor (actual roads are ~1.2-1.5x longer than straight line)
        road_factor = 1.3
        adjusted_distance = distance_km * road_factor
        
        return adjusted_distance, {
            'distance': adjusted_distance,
            'duration': (adjusted_distance / 60) * 60,  # Assume 60km/h average
            'geometry': [[point1['lng'], point1['lat']], [point2['lng'], point2['lat']]], # Simple line for fallback
            'provider': 'Haversine (Fallback)'
        }
    
    def calculate_distance_matrix_real(self, waypoints: List[Dict]) -> Tuple[np.ndarray, Dict]:
        """
        Calculate actual road distance matrix for all waypoint pairs
        Uses real routing data instead of straight-line distances
        """
        n = len(waypoints)
        matrix = np.zeros((n, n))
        route_data = {}
        
        print(f"Calculating real-world distance matrix for {n} waypoints using OpenRouteService...")
        
        # Calculate pairwise distances using directions API
        # Note: We use individual route calls instead of matrix endpoint
        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix[i][j] = 0
                else:
                    try:
                        distance, route_info = self.get_real_distance(waypoints[i], waypoints[j])
                        matrix[i][j] = distance
                    except Exception as e:
                        # Silently fallback to Haversine (API might be unavailable)
                        distance, _ = self._haversine_distance(waypoints[i], waypoints[j])
                        matrix[i][j] = distance
        
        return matrix, {}

        # Old matrix endpoint code (not available in free tier)
        try:
            if False:  # Disabled - matrix endpoint not available
                matrix_result = self.client.matrix(
                    locations=locations,
                    metrics=['distance', 'duration'],
                    profile='driving-car'
                )
                
                distances = np.array(matrix_result['distances']) / 1000 # Convert to km
                
                # Now, get the detailed route geometry for the final path later
                # This part will be handled after optimization
                
                # For now, we just return the distance matrix
                return distances, {'durations': matrix_result['durations']}

        except openrouteservice.exceptions.ApiError as e:
            print(f"ORS Matrix API error: {e}. Falling back to pairwise calculation.")
            # Fallback to pairwise if matrix fails
            for i in range(n):
                for j in range(i + 1, n):
                    if i != j:
                        try:
                            dist, _ = self.get_real_distance(waypoints[i], waypoints[j])
                            matrix[i][j] = dist
                            matrix[j][i] = dist
                        except Exception as e_pair:
                            print(f"Failed to get distance {i}->{j}: {e_pair}")
                            dist_fallback = self._haversine_simple(waypoints[i], waypoints[j]) * 1.3
                            matrix[i][j] = dist_fallback
                            matrix[j][i] = dist_fallback
            return matrix, {}
        except Exception as e:
            print(f"An unexpected error occurred with matrix calculation: {e}")
            # Fallback to pairwise if matrix fails
            for i in range(n):
                for j in range(i + 1, n):
                     if i != j:
                        try:
                            dist, _ = self.get_real_distance(waypoints[i], waypoints[j])
                            matrix[i][j] = dist
                            matrix[j][i] = dist
                        except Exception as e_pair:
                            print(f"Failed to get distance {i}->{j}: {e_pair}")
                            dist_fallback = self._haversine_simple(waypoints[i], waypoints[j]) * 1.3
                            matrix[i][j] = dist_fallback
                            matrix[j][i] = dist_fallback
            return matrix, {}

    @staticmethod
    def _haversine_simple(point1: Dict, point2: Dict) -> float:
        """Simple Haversine without exception handling"""
        R = 6371
        lat1, lon1 = math.radians(point1['lat']), math.radians(point1['lng'])
        lat2, lon2 = math.radians(point2['lat']), math.radians(point2['lng'])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        return R * c


class TSPSolver:
    """
    Traveling Salesman Problem solver using different algorithms
    """
    
    @staticmethod
    def nearest_neighbor(distance_matrix: np.ndarray, start_idx: int = 0) -> List[int]:
        """
        Nearest neighbor heuristic for TSP
        Good for quick approximations
        """
        n = len(distance_matrix)
        unvisited = set(range(n))
        current = start_idx
        path = [current]
        unvisited.remove(current)
        
        while unvisited:
            nearest = min(unvisited, key=lambda x: distance_matrix[current][x])
            path.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        
        return path
    
    @staticmethod
    def calculate_path_distance(path: List[int], distance_matrix: np.ndarray) -> float:
        """Calculate total distance for a given path"""
        total = 0
        for i in range(len(path) - 1):
            total += distance_matrix[path[i]][path[i + 1]]
        return total


if __name__ == "__main__":
    # Test the router
    # IMPORTANT: You need to set the ORS_API_KEY environment variable
    api_key = os.environ.get("ORS_API_KEY")
    
    if not api_key:
        print("Error: ORS_API_KEY environment variable not set.")
    else:
        test_points = [
            {'lat': 13.0827, 'lng': 80.2707},  # Chennai
            {'lat': 11.9317, 'lng': 79.8076},  # Puducherry (Corrected)
        ]
        
        router = RealWorldRouteOptimizer(api_key=api_key)
        
        # Test matrix calculation
        matrix, durations = router.calculate_distance_matrix_real(test_points)
        print("Distance Matrix (km):")
        print(matrix)
        
        # Test single route geometry
        dist, route_info = router.get_real_distance(test_points[0], test_points[1])
        print(f"\nDistance between Chennai and Puducherry: {dist:.2f} km")
        # print(f"Route info: {json.dumps(route_info, indent=2)}")
        print("Route geometry retrieved.")
