import numpy as np
import json
import math
import sys
import os
import time
from typing import List, Dict, Tuple
from real_world_routing import RealWorldRouteOptimizer, TSPSolver

try:
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
    from qiskit_aer import AerSimulator
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False


class HybridQuantumWhaleOptimizer:
    """
    Advanced hybrid optimizer combining:
    1. Quantum Annealing (Exploration) - using Qiskit
    2. Whale Optimization Algorithm (Exploitation) - nature-inspired
    3. Real-world routing (using OSRM for actual roads)
    
    This creates a powerful hybrid approach for TSP with real-world constraints
    """
    
    def __init__(self, distance_matrix: np.ndarray, waypoints: List[Dict], api_key: str = None):
        self.distance_matrix = distance_matrix
        self.waypoints = waypoints
        self.n = len(waypoints)
        self.best_path = None
        self.best_distance = float('inf')
        self.optimization_history = []
        self.fixed_start = False  # If True, keep first waypoint fixed
        self.fixed_end = False    # If True, keep last waypoint fixed
        
        # Initialize route optimizer with API key if provided
        self.route_optimizer = None
        self.api_key = api_key
        if api_key:
            try:
                self.route_optimizer = RealWorldRouteOptimizer(api_key=api_key)
            except Exception as e:
                print(f"Failed to initialize route optimizer: {e}")
                self.route_optimizer = None
        self.route_data = {}
    
    def optimize(self) -> Dict:
        """
        Main optimization function using hybrid approach
        """
        start_time = time.time()
        
        result = {
            'waypoints': self.waypoints,
            'optimization_phases': [],
            'best_path': None,
            'best_distance': None,
            'route_details': None,
            'algorithm_summary': 'Quantum Annealing (Exploration) + Whale Optimization (Exploitation)'
        }
        
        # Phase 1: Quantum Annealing for Exploration
        print("Phase 1: Quantum Annealing (Exploration)...")
        qa_path, qa_distance = self._quantum_annealing_phase()
        
        result['optimization_phases'].append({
            'name': 'Quantum Annealing',
            'algorithm': 'Parameterized Quantum Circuits with QAOA-like structure',
            'best_path': qa_path,
            'best_distance': float(qa_distance),
            'description': 'Explores solution space using quantum superposition and entanglement'
        })
        
        # Phase 2: Whale Optimization for Exploitation
        print("Phase 2: Whale Optimization (Exploitation)...")
        woa_path, woa_distance = self._whale_optimization_phase(initial_path=qa_path)
        
        result['optimization_phases'].append({
            'name': 'Whale Optimization',
            'algorithm': 'WOA with bubble-net hunting strategy',
            'best_path': woa_path,
            'best_distance': float(woa_distance),
            'description': 'Exploits best solutions found by QA for fine-tuning'
        })
        
        # Phase 3: Local Search Optimization
        print("Phase 3: Local Search Optimization...")
        final_path, final_distance = self._local_search_phase(woa_path)
        
        result['optimization_phases'].append({
            'name': 'Local Search',
            'algorithm': '2-opt improvement',
            'best_path': final_path,
            'best_distance': float(final_distance),
            'description': 'Applies 2-opt swaps for final refinement'
        })
        
        # Select overall best
        all_results = [
            (qa_path, qa_distance),
            (woa_path, woa_distance),
            (final_path, final_distance)
        ]
        self.best_path, self.best_distance = min(all_results, key=lambda x: x[1])
        
        # Get route details with real distances and geometry
        self.route_data = self._get_route_details(self.best_path)
        
        result['best_path'] = self.best_path
        result['best_distance'] = float(self.best_distance)
        result['route_details'] = self.route_data
        
        # Add final route geometry for drawing on map
        result['route_geometry'] = self._get_final_route_geometry(self.best_path)
        
        # Add comprehensive data for frontend
        result['optimized_order'] = self.best_path
        result['total_distance'] = float(self.route_data['total_distance_km'])
        result['total_duration'] = float(self.route_data['total_duration_minutes'])
        result['segments'] = self.route_data['segments']
        result['optimization_method'] = 'hybrid'
        result['optimization_time'] = time.time() - start_time
        result['quantum_iterations'] = len([h for h in self.optimization_history if h['phase'] == 'QA'])
        result['woa_iterations'] = len([h for h in self.optimization_history if h['phase'] == 'WOA'])
        
        # Generate truly diverse alternative routes using different strategies
        result['alternative_routes'] = []
        
        # Collect all unique routes found during optimization
        unique_routes = {}
        
        # Add QA route
        qa_key = tuple(qa_path)
        if qa_key not in unique_routes:
            qa_route_details = self._get_route_details(qa_path)
            unique_routes[qa_key] = {
                'name': 'Quantum Annealing Route',
                'path': qa_path,
                'distance': float(qa_distance),
                'duration': float(qa_route_details['total_duration_minutes']),
                'geometry': self._get_final_route_geometry(qa_path),
                'segments': qa_route_details['segments'],
                'color': '#f59e0b'  # Orange
            }
        
        # Add WOA route
        woa_key = tuple(woa_path)
        if woa_key not in unique_routes:
            woa_route_details = self._get_route_details(woa_path)
            unique_routes[woa_key] = {
                'name': 'Whale Optimization Route',
                'path': woa_path,
                'distance': float(woa_distance),
                'duration': float(woa_route_details['total_duration_minutes']),
                'geometry': self._get_final_route_geometry(woa_path),
                'segments': woa_route_details['segments'],
                'color': '#10b981'  # Green
            }
        
        # Add Final optimized route
        final_key = tuple(final_path)
        if final_key not in unique_routes:
            final_route_details = self._get_route_details(final_path)
            unique_routes[final_key] = {
                'name': 'Final Optimized Route',
                'path': final_path,
                'distance': float(final_distance),
                'duration': float(final_route_details['total_duration_minutes']),
                'geometry': self._get_final_route_geometry(final_path),
                'segments': final_route_details['segments'],
                'color': '#8b5cf6'  # Purple
            }
        
        # For small problems, use exhaustive search to get ALL routes
        if self.n <= 5:
            print(f"Using exhaustive search for small problem ({self.n} waypoints)...")
            try:
                all_routes = self._generate_alternative_routes()
                print(f"Exhaustive search found {len(all_routes)} routes")
                
                # Keep routes as list to preserve distance-sorted order
                # Deduplicate by creating a dictionary then converting back to sorted list
                if self.n == 2:
                    # For 2-waypoint: different routes can have same path, dedupe by rounded distance
                    seen_distances = set()
                    unique_routes_list = []
                    for route in all_routes:
                        rounded_dist = round(route['distance'], 1)
                        if rounded_dist not in seen_distances:
                            seen_distances.add(rounded_dist)
                            unique_routes_list.append(route)
                    all_routes = unique_routes_list
                else:
                    # For 3+ waypoints: dedupe by path
                    unique_routes_dict = {}
                    for route in all_routes:
                        path_key = tuple(route['path'])
                        if path_key not in unique_routes_dict:
                            unique_routes_dict[path_key] = route
                    all_routes = list(unique_routes_dict.values())
                    # Re-sort after deduplication
                    all_routes.sort(key=lambda x: x['distance'])
                
                # Update the best path from exhaustive search
                if all_routes:
                    best_route = all_routes[0]  # First route is shortest
                    self.best_path = best_route['path']
                    self.best_distance = best_route['distance']
                    result['best_path'] = self.best_path
                    result['best_distance'] = float(self.best_distance)
                    result['route_details'] = {'segments': best_route['segments'], 'total_distance_km': best_route['distance'], 'total_duration_minutes': best_route['duration']}
                    result['route_geometry'] = best_route['geometry']
                    result['total_distance'] = best_route['distance']
                    result['total_duration'] = best_route['duration']
                    result['alternative_routes'] = all_routes  # Store as sorted list
                    print(f"Best route from exhaustive search: {self.best_path} with distance {self.best_distance:.2f} km")
                    print(f"Stored {len(all_routes)} routes in distance order")
                    return result
            except Exception as e:
                print(f"Error in exhaustive search: {e}")
                import traceback
                traceback.print_exc()
        else:
            # Generate additional alternative routes if we have less than 3 unique routes
            if len(unique_routes) < 3:
                print(f"Generating additional alternative routes... (currently have {len(unique_routes)})")
                try:
                    alternative_strategies = self._generate_alternative_routes()
                    print(f"Generated {len(alternative_strategies)} additional strategies")
                    
                    for i, alt_route in enumerate(alternative_strategies):
                        alt_key = tuple(alt_route['path'])
                        if alt_key not in unique_routes and len(unique_routes) < 7:
                            unique_routes[alt_key] = alt_route
                            print(f"Added {alt_route['name']} to alternatives")
                        else:
                            print(f"Skipped {alt_route['name']} (duplicate path or limit reached)")
                except Exception as e:
                    print(f"Error generating alternative routes: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Sort routes by distance and add to result
        sorted_routes = sorted(unique_routes.values(), key=lambda x: x['distance'])
        result['alternative_routes'] = sorted_routes
        print(f"Returning {len(sorted_routes)} alternative routes to frontend")
        
        return result
    
    def _quantum_annealing_phase(self) -> Tuple[List[int], float]:
        """
        Phase 1: Quantum Annealing for exploration
        Uses parameterized quantum circuits to explore solution space
        """
        best_path = list(range(self.n))
        best_distance = self._calculate_path_distance(best_path)
        
        if not QISKIT_AVAILABLE:
            # Fallback: Use nearest neighbor
            best_path = TSPSolver.nearest_neighbor(self.distance_matrix)
            best_distance = self._calculate_path_distance(best_path)
            return best_path, best_distance
        
        try:
            for iteration in range(20):  # Reduced iterations for speed
                # Create parameterized circuit
                angle = (2 * math.pi) * (iteration / 20)
                
                # Simulate quantum circuit
                qr = QuantumRegister(min(self.n, 8), 'q')
                cr = ClassicalRegister(min(self.n, 8), 'c')
                qc = QuantumCircuit(qr, cr)
                
                # Hadamard superposition
                for i in range(min(self.n, 8)):
                    qc.h(qr[i])
                
                # Problem-dependent ansatz
                for i in range(min(self.n, 8)):
                    qc.rx(angle, qr[i])
                
                # Entanglement
                for i in range(min(self.n - 1, 7)):
                    qc.cx(qr[i], qr[i + 1])
                
                # Phase rotation
                for i in range(min(self.n, 8)):
                    qc.rz(angle * 0.5, qr[i])
                
                # Measurement
                for i in range(min(self.n, 8)):
                    qc.measure(qr[i], cr[i])
                
                # Execute
                simulator = AerSimulator()
                transpiled = transpile(qc, simulator)
                job = simulator.run(transpiled, shots=512)
                result = job.result()
                counts = result.get_counts()
                
                # Convert measurement to path
                if counts:
                    best_bitstring = max(counts, key=counts.get)
                    path = self._bitstring_to_path(best_bitstring)
                    distance = self._calculate_path_distance(path)
                    
                    if distance < best_distance:
                        best_distance = distance
                        best_path = path
                
                self.optimization_history.append({
                    'phase': 'QA',
                    'iteration': iteration,
                    'best_distance': best_distance
                })
        
        except Exception as e:
            print(f"Quantum error: {e}, using nearest neighbor fallback")
            best_path = TSPSolver.nearest_neighbor(self.distance_matrix)
            best_distance = self._calculate_path_distance(best_path)
        
        return best_path, best_distance
    
    def _whale_optimization_phase(self, initial_path: List[int]) -> Tuple[List[int], float]:
        """
        Phase 2: Whale Optimization Algorithm
        Exploits the quantum solution using nature-inspired algorithm
        """
        best_path = initial_path.copy()
        best_distance = self._calculate_path_distance(best_path)
        
        # Initialize agents (whale positions)
        num_agents = max(5, min(self.n, 10))
        agents = [best_path.copy() for _ in range(num_agents)]
        
        a_max = 2
        l_min = -1
        l_max = 1
        
        for iteration in range(30):  # WOA iterations
            a = a_max - iteration * (a_max / 30)
            
            for i in range(num_agents):
                r = np.random.random()
                A = 2 * a * r - a
                C = 2 * r
                l = np.random.uniform(l_min, l_max)
                p = np.random.random()
                
                if p < 0.5:
                    if abs(A) < 1:
                        # Update towards best
                        agents[i] = self._update_path(agents[i], best_path, A, C)
                    else:
                        # Update towards random agent
                        rand_idx = np.random.randint(0, num_agents)
                        agents[i] = self._update_path(agents[i], agents[rand_idx], A, C)
                else:
                    # Spiral update
                    agents[i] = self._spiral_update_path(agents[i], best_path, l)
                
                # Evaluate
                distance = self._calculate_path_distance(agents[i])
                
                if distance < best_distance:
                    best_distance = distance
                    best_path = agents[i].copy()
            
            self.optimization_history.append({
                'phase': 'WOA',
                'iteration': iteration,
                'best_distance': best_distance
            })
        
        return best_path, best_distance
    
    def _local_search_phase(self, initial_path: List[int]) -> Tuple[List[int], float]:
        """
        Phase 3: 2-opt local search for final refinement
        """
        path = initial_path.copy()
        best_distance = self._calculate_path_distance(path)
        improved = True
        iteration = 0
        
        while improved and iteration < 50:
            improved = False
            iteration += 1
            
            for i in range(1, self.n - 1):
                for j in range(i + 1, self.n):
                    # 2-opt swap
                    new_path = path[:i] + path[i:j][::-1] + path[j:]
                    new_distance = self._calculate_path_distance(new_path)
                    
                    if new_distance < best_distance:
                        path = new_path
                        best_distance = new_distance
                        improved = True
                        break
                
                if improved:
                    break
            
            self.optimization_history.append({
                'phase': 'LocalSearch',
                'iteration': iteration,
                'best_distance': best_distance
            })
        
        return path, best_distance
    
    def _update_path(self, current: List[int], target: List[int], A: float, C: float) -> List[int]:
        """Update path position in whale optimization"""
        new_path = current.copy()
        
        # Perform some swaps based on parameters
        num_swaps = max(1, int(abs(A) * self.n))
        for _ in range(num_swaps):
            i, j = np.random.choice(self.n, 2, replace=False)
            new_path[i], new_path[j] = new_path[j], new_path[i]
        
        return new_path
    
    def _spiral_update_path(self, current: List[int], best: List[int], l: float) -> List[int]:
        """Spiral movement in whale optimization"""
        new_path = current.copy()
        
        # Perform spiral-like moves (more swaps)
        num_swaps = max(2, int(abs(l) * self.n))
        for _ in range(num_swaps):
            i, j = np.random.choice(self.n, 2, replace=False)
            new_path[i], new_path[j] = new_path[j], new_path[i]
        
        return new_path
    
    def _bitstring_to_path(self, bitstring: str) -> List[int]:
        """Convert quantum bitstring to valid path"""
        # Use bitstring as seed for path generation
        seed = int(bitstring, 2) if bitstring else 0
        np.random.seed(seed % (2**31))
        path = list(range(self.n))
        np.random.shuffle(path)
        return path
    
    def _calculate_path_distance(self, path: List[int]) -> float:
        """Calculate total distance for a path"""
        if len(path) != self.n:
            return float('inf')
        
        total = 0
        for i in range(self.n - 1):
            total += self.distance_matrix[path[i]][path[i + 1]]
        # No return to origin for this model
        # total += self.distance_matrix[path[self.n - 1]][path[0]] 
        return total
    
    def _get_route_details(self, path: List[int]) -> Dict:
        """Get detailed route information with real routing data"""
        details = {
            'path': path,
            'waypoints_in_order': [self.waypoints[i] for i in path],
            'segments': [],
            'total_distance_km': 0,
            'total_duration_minutes': 0
        }
        
        for i in range(len(path) - 1):
            from_idx = path[i]
            to_idx = path[i + 1]
            
            from_waypoint = self.waypoints[from_idx]
            to_waypoint = self.waypoints[to_idx]
            
            # Get real route info if available
            try:
                distance, route_info = self.route_optimizer.get_real_distance(from_waypoint, to_waypoint)
                duration = route_info.get('duration', distance / 60 * 60)
                geometry = route_info.get('geometry', [])
            except:
                distance = self.distance_matrix[from_idx][to_idx]
                duration = distance / 60 * 60  # Assume 60 km/h
                geometry = []
            
            segment = {
                'from': {
                    'index': from_idx,
                    'name': from_waypoint.get('name', f"Point {from_idx}"),
                    'coordinates': {'lat': from_waypoint['lat'], 'lng': from_waypoint['lng']}
                },
                'to': {
                    'index': to_idx,
                    'name': to_waypoint.get('name', f"Point {to_idx}"),
                    'coordinates': {'lat': to_waypoint['lat'], 'lng': to_waypoint['lng']}
                },
                'distance_km': float(distance),
                'duration_minutes': float(distance / 40 * 60),  # 40 km/h average speed
                'geometry': geometry
            }
            
            details['segments'].append(segment)
            details['total_distance_km'] += segment['distance_km']
            details['total_duration_minutes'] += segment['duration_minutes']
        
        return details

    def _get_final_route_geometry(self, path: List[int]) -> List[List[float]]:
        """
        Get the final, combined route geometry for the best path.
        Returns coordinates in [lat, lng] format for Leaflet
        """
        full_geometry = []
        for i in range(len(path) - 1):
            from_waypoint = self.waypoints[path[i]]
            to_waypoint = self.waypoints[path[i+1]]
            
            # Get the geometry for this specific leg
            try:
                _, route_info = self.route_optimizer.get_real_distance(from_waypoint, to_waypoint)
                if route_info and route_info.get('geometry'):
                    # The geometry is a list of [lon, lat] points from ORS
                    # We need to swap them to [lat, lon] for Leaflet
                    for point in route_info['geometry']:
                        full_geometry.append([point[1], point[0]])  # Swap lon,lat to lat,lng
            except Exception as e:
                print(f"Could not retrieve geometry for segment {path[i]}->{path[i+1]}: {e}", file=sys.stderr)
                # Fallback to a straight line between the points
                full_geometry.append([from_waypoint['lat'], from_waypoint['lng']])
                full_geometry.append([to_waypoint['lat'], to_waypoint['lng']])

        return full_geometry

    def _generate_alternative_routes(self) -> List[Dict]:
        """
        Generate additional alternative routes using different strategies
        to ensure we always have multiple options to show
        
        For 2-waypoint problems: Get alternative road routes from OpenRouteService
        For 3-5 waypoint problems: Check all permutations
        """
        alternatives = []
        colors = ['#3b82f6', '#ef4444', '#f97316', '#14b8a6', '#a855f7', '#ec4899', '#f59e0b']  # Blue, Red, Orange, Teal, Purple, Pink, Amber
        
        # Special case: 2 waypoints - get alternative routes from API (coastal vs inland, etc.)
        if self.n == 2 and self.route_optimizer:
            print(f"2-waypoint problem: requesting alternative routes from OpenRouteService (coastal/inland/etc)...")
            try:
                point1 = self.waypoints[0]
                point2 = self.waypoints[1]
                
                # Get up to 3 alternative routes from ORS
                alt_routes = self.route_optimizer.get_alternative_routes(point1, point2, max_alternatives=3)
                
                for i, (distance, route_info) in enumerate(alt_routes):
                    # Build route details
                    geometry = [[coord[1], coord[0]] for coord in route_info['geometry']]  # Swap to lat,lng
                    
                    alternatives.append({
                        'name': f'Route Option {i+1}' if i > 0 else 'Fastest Route',
                        'path': [0, 1],  # Always 0->1 for 2 waypoints
                        'distance': float(distance),
                        'duration': float(route_info['duration']),
                        'geometry': geometry,
                        'segments': [{
                            'from': {'name': point1.get('name', 'Start'), 'coordinates': {'lat': point1['lat'], 'lng': point1['lng']}},
                            'to': {'name': point2.get('name', 'End'), 'coordinates': {'lat': point2['lat'], 'lng': point2['lng']}},
                            'distance_km': float(distance),
                            'duration_minutes': float(route_info['duration']),
                            'geometry': geometry
                        }],
                        'color': colors[i % len(colors)]
                    })
                
                # Sort by distance (shortest first)
                print(f"Before sorting: {[(r['name'], r['distance']) for r in alternatives]}")
                alternatives.sort(key=lambda x: x['distance'])
                print(f"After sorting: {[(r['distance'], r['name']) for r in alternatives]}")
                
                # Reassign names after sorting
                for i, route in enumerate(alternatives):
                    old_name = route['name']
                    route['name'] = f'Route Option {i+1}' if i > 0 else 'Fastest Route'
                    print(f"Route {i}: {route['distance']:.2f} km - renamed from '{old_name}' to '{route['name']}'")
                
                print(f"Got {len(alternatives)} alternative routes from OpenRouteService (sorted by distance)")
                print(f"Final route order: {[(r['name'], r['distance']) for r in alternatives]}")
                return alternatives
                
            except Exception as e:
                print(f"Could not get alternative routes from ORS: {e}")
                import traceback
                traceback.print_exc()
        
        # For small problems (3-5 cities), generate all permutations
        if self.n >= 3 and self.n <= 5:
            import itertools
            
            # If start and end are fixed, only permute intermediate waypoints
            if self.fixed_start and self.fixed_end and self.n > 2:
                intermediate_indices = list(range(1, self.n - 1))
                num_perms = math.factorial(len(intermediate_indices)) if intermediate_indices else 1
                print(f"Fixed start/end: checking {num_perms} permutations of {len(intermediate_indices)} intermediate waypoints...")
                
                if intermediate_indices:
                    intermediate_perms = list(itertools.permutations(intermediate_indices))
                    all_perms = [[0] + list(perm) + [self.n - 1] for perm in intermediate_perms]
                else:
                    all_perms = [[0, self.n - 1]]
            else:
                print(f"Small problem detected ({self.n} waypoints), checking all {math.factorial(self.n)} permutations...")
                all_perms = [list(perm) for perm in itertools.permutations(range(self.n))]
            
            # Calculate real distance for each permutation
            perm_results = []
            for path in all_perms:
                # Get actual route details (with real routing)
                try:
                    route_details = self._get_route_details(path)
                    distance = route_details['total_distance_km']
                    perm_results.append((path, distance, route_details))
                except Exception as e:
                    print(f"Error calculating route for {path}: {e}")
                    continue
            
            # Sort by distance
            perm_results.sort(key=lambda x: x[1])
            
            # Take top 5 unique routes
            added_count = 0
            for i, (path, distance, route_details) in enumerate(perm_results):
                if added_count >= 5:
                    break
                    
                alternatives.append({
                    'name': f'Route Option {i+1}' if i > 0 else 'Optimal Route',
                    'path': path,
                    'distance': float(distance),
                    'duration': float(route_details['total_duration_minutes']),
                    'geometry': self._get_final_route_geometry(path),
                    'segments': route_details['segments'],
                    'color': colors[i % len(colors)]
                })
                added_count += 1
            
            return alternatives
        
        # For larger problems, use heuristics
        # Strategy 1: Nearest Neighbor (greedy approach)
        try:
            nn_path = TSPSolver.nearest_neighbor(self.distance_matrix)
            nn_route_details = self._get_route_details(nn_path)
            alternatives.append({
                'name': 'Nearest Neighbor Route',
                'path': nn_path,
                'distance': float(nn_route_details['total_distance_km']),
                'duration': float(nn_route_details['total_duration_minutes']),
                'geometry': self._get_final_route_geometry(nn_path),
                'segments': nn_route_details['segments'],
                'color': colors[0]
            })
        except Exception as e:
            print(f"Could not generate nearest neighbor route: {e}")
        
        # Strategy 2: Farthest Insertion (different construction heuristic)
        try:
            fi_path = self._farthest_insertion()
            fi_route_details = self._get_route_details(fi_path)
            alternatives.append({
                'name': 'Farthest Insertion Route',
                'path': fi_path,
                'distance': float(fi_route_details['total_distance_km']),
                'duration': float(fi_route_details['total_duration_minutes']),
                'geometry': self._get_final_route_geometry(fi_path),
                'segments': fi_route_details['segments'],
                'color': colors[1]
            })
        except Exception as e:
            print(f"Could not generate farthest insertion route: {e}")
        
        # Strategy 3: Random restart with 2-opt (different local optimum)
        try:
            for i in range(2):  # Generate 2 different random routes
                random_path = list(range(self.n))
                np.random.seed(42 + i)  # Different seed for each
                np.random.shuffle(random_path)
                random_path, _ = self._local_search_phase(random_path)
                random_route_details = self._get_route_details(random_path)
                alternatives.append({
                    'name': f'Random Restart Route {i+1}',
                    'path': random_path,
                    'distance': float(random_route_details['total_distance_km']),
                    'duration': float(random_route_details['total_duration_minutes']),
                    'geometry': self._get_final_route_geometry(random_path),
                    'segments': random_route_details['segments'],
                    'color': colors[3 + i]
                })
        except Exception as e:
            print(f"Could not generate random restart route: {e}")
            import traceback
            traceback.print_exc()
        
        return alternatives
    
    def _farthest_insertion(self) -> List[int]:
        """
        Farthest Insertion heuristic for TSP
        Builds tour by always inserting the farthest unvisited city
        """
        n = self.n
        if n <= 2:
            return list(range(n))
        
        # Start with two farthest cities
        max_dist = 0
        start_i, start_j = 0, 1
        for i in range(n):
            for j in range(i + 1, n):
                if self.distance_matrix[i][j] > max_dist:
                    max_dist = self.distance_matrix[i][j]
                    start_i, start_j = i, j
        
        tour = [start_i, start_j]
        unvisited = set(range(n)) - {start_i, start_j}
        
        while unvisited:
            # Find farthest city from tour
            farthest_city = None
            max_min_dist = -1
            
            for city in unvisited:
                min_dist = min(self.distance_matrix[city][tour_city] for tour_city in tour)
                if min_dist > max_min_dist:
                    max_min_dist = min_dist
                    farthest_city = city
            
            # Find best insertion position
            best_pos = 0
            best_cost = float('inf')
            
            for pos in range(len(tour)):
                next_pos = (pos + 1) % len(tour)
                cost = (self.distance_matrix[tour[pos]][farthest_city] + 
                       self.distance_matrix[farthest_city][tour[next_pos]] -
                       self.distance_matrix[tour[pos]][tour[next_pos]])
                
                if cost < best_cost:
                    best_cost = cost
                    best_pos = next_pos
            
            tour.insert(best_pos, farthest_city)
            unvisited.remove(farthest_city)
        
        return tour


# Main execution
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No waypoints provided"}))
        sys.exit(1)

    waypoints = json.loads(sys.argv[1])
    
    # Get API key from environment variable
    # IMPORTANT: You need to set the ORS_API_KEY environment variable
    api_key = os.environ.get("ORS_API_KEY")
    if not api_key:
        print(json.dumps({"error": "OpenRouteService API key not found. Please set the ORS_API_KEY environment variable."}))
        sys.exit(1)

    if waypoints and len(waypoints) > 1:
        # Get real-world distance matrix
        route_optimizer = RealWorldRouteOptimizer(api_key=api_key)
        distance_matrix, _ = route_optimizer.calculate_distance_matrix_real(waypoints)
        
        # Run hybrid optimization
        optimizer = HybridQuantumWhaleOptimizer(distance_matrix, waypoints)
        # Pass the route_optimizer instance to the hybrid optimizer
        optimizer.route_optimizer = route_optimizer 
        result = optimizer.optimize()
        
        print(json.dumps(result))
    else:
        print(json.dumps({"error": "Insufficient waypoints provided. Need at least 2."}))
