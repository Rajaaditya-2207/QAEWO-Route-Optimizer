"""
QAEWO Backend - Flask Application
Quantum Annealing + Whale Optimization for Route Optimization
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sys
import os
import traceback
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add quantum directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'quantum'))

app = Flask(__name__)
CORS(app)

# Configure Flask
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'backend': {
            'status': 'online',
            'message': 'Backend running successfully'
        },
        'frontend': {
            'status': 'deployed',
            'message': 'Frontend should be accessible at root URL'
        },
        'service': 'QAEWO - Quantum Annealing + Whale Optimization',
        'version': '2.0.0',
        'endpoints': {
            'health': '/api/health',
            'optimize': '/api/optimize-route'
        }
    })

@app.route('/api/optimize-route', methods=['POST'])
def optimize_route():
    """
    Route Optimization Endpoint
    Handles two scenarios:
    1. Start + Destination only (2 waypoints): Find alternative routes
    2. Start + Waypoints + Destination (3+): Optimize route through waypoints
    """
    try:
        data = request.get_json()
        waypoints = data.get('waypoints', [])
        
        if not waypoints or len(waypoints) < 2:
            return jsonify({
                'success': False,
                'error': 'At least 2 locations required (Start and Destination)'
            }), 400
        
        # Get API key from environment
        api_key = os.environ.get('ORS_API_KEY')
        
        num_waypoints = len(waypoints)
        start_point = waypoints[0]
        destination = waypoints[-1]
        intermediate_waypoints = waypoints[1:-1] if num_waypoints > 2 else []
        
        print(f"\n{'='*60}")
        print(f"Route Request:")
        print(f"  Start: {start_point.get('name')}")
        if intermediate_waypoints:
            print(f"  Waypoints: {[w.get('name') for w in intermediate_waypoints]}")
        print(f"  Destination: {destination.get('name')}")
        print(f"{'='*60}\n")
        
        # Try hybrid optimizer first (with real routing)
        if api_key:
            try:
                from hybrid_optimizer import HybridQuantumWhaleOptimizer
                from real_world_routing import RealWorldRouteOptimizer
                
                # Initialize route optimizer
                route_optimizer = RealWorldRouteOptimizer(api_key=api_key)
                
                # Scenario 1: Only Start and Destination (2 points) - Find alternative routes
                if num_waypoints == 2:
                    print(f"Finding alternative routes from {start_point.get('name')} to {destination.get('name')}...")
                    
                    # Use the HybridQuantumWhaleOptimizer which handles 2-waypoint alternatives
                    distance_matrix, route_details_matrix = route_optimizer.calculate_distance_matrix_real(waypoints)
                    
                    optimizer = HybridQuantumWhaleOptimizer(distance_matrix, waypoints, api_key=api_key)
                    optimizer.route_optimizer = route_optimizer
                    optimizer.route_details_matrix = route_details_matrix
                    optimizer.fixed_start = True  # Keep start fixed
                    optimizer.fixed_end = True    # Keep end fixed
                    
                    result = optimizer.optimize()
                
                # Scenario 2: Start + Waypoints + Destination (3+ points) - Optimize intermediate waypoints only
                else:
                    print(f"Optimizing route with {len(intermediate_waypoints)} intermediate waypoints...")
                    print(f"Start and destination are FIXED - only optimizing waypoint order")
                    
                    # Calculate distance matrix with real routing for all points
                    distance_matrix, route_details_matrix = route_optimizer.calculate_distance_matrix_real(waypoints)
                    
                    # Run hybrid optimization with fixed start and end
                    optimizer = HybridQuantumWhaleOptimizer(distance_matrix, waypoints, api_key=api_key)
                    optimizer.route_optimizer = route_optimizer
                    optimizer.route_details_matrix = route_details_matrix
                    optimizer.fixed_start = True  # Keep start (index 0) fixed
                    optimizer.fixed_end = True    # Keep destination (index n-1) fixed
                    
                    result = optimizer.optimize()
                
                # Enhance response with clear structure
                alt_routes = result.get('alternative_routes', [])
                print(f"\n=== SENDING TO FRONTEND ===")
                print(f"Alternative routes order: {[(r['name'], r['distance']) for r in alt_routes]}")
                print(f"===========================\n")
                
                # Use data from the best route (first in alternative_routes after sorting)
                best_route = alt_routes[0] if alt_routes else None
                
                # Get the optimized order - should always be [0, 1, 2, ...] for our use case
                # since we're keeping start and destination fixed
                optimized_order = best_route['path'] if best_route else result.get('optimized_order', result.get('best_path', []))
                
                # Ensure order is correct: start (0) should come first
                if optimized_order and optimized_order[0] != 0:
                    print(f"WARNING: Path starts with {optimized_order[0]}, correcting to start from 0")
                    # For 2-waypoint, should always be [0, 1]
                    if len(optimized_order) == 2:
                        optimized_order = [0, 1]
                
                print(f"Final optimized_order: {optimized_order}")
                print(f"Waypoint names in order: {[waypoints[i]['name'] for i in optimized_order]}")
                
                response_data = {
                    'optimized_order': optimized_order,
                    'total_distance': best_route['distance'] if best_route else result.get('total_distance', result.get('best_distance', 0)),
                    'total_duration': best_route['duration'] if best_route else result.get('total_duration', 0),
                    'route_geometry': best_route['geometry'] if best_route else result.get('route_geometry', []),
                    'segments': best_route['segments'] if best_route else result.get('segments', []),
                    'optimization_method': result.get('optimization_method', 'hybrid'),
                    'optimization_time': result.get('optimization_time', 0),
                    'quantum_iterations': result.get('quantum_iterations', 0),
                    'woa_iterations': result.get('woa_iterations', 0),
                    'alternative_routes': alt_routes,
                    'optimization_phases': result.get('optimization_phases', [])
                }
                
                return jsonify({
                    'success': True,
                    'data': response_data,
                    'mode': 'hybrid_quantum_whale_real_routing'
                })
                
            except requests.exceptions.HTTPError as e:
                # Handle specific API errors
                error_msg = str(e)
                if '2099' in error_msg or 'not found' in error_msg.lower():
                    return jsonify({
                        'success': False,
                        'error': 'Route not possible: Locations may not be connected by roads (e.g., across ocean). Please select locations on the same landmass.'
                    }), 400
                elif '2004' in error_msg:
                    return jsonify({
                        'success': False,
                        'error': 'Route is too long for alternative route calculation. System will retry with different strategy.'
                    }), 400
                else:
                    print(f"API Error: {e}")
                    print(traceback.format_exc())
                    return jsonify({
                        'success': False,
                        'error': f'Routing API error: {str(e)}'
                    }), 500
            except Exception as e:
                print(f"Hybrid optimizer error: {e}")
                print(traceback.format_exc())
                # Fall through to basic optimizer
        
        # Fallback to basic route optimizer (Haversine distances)
        try:
            from route_optimizer import HybridRouteOptimizer
            
            print(f"Using basic route optimizer with Quantum Annealing for {len(waypoints)} waypoints...")
            optimizer = HybridRouteOptimizer()
            result = optimizer.optimize(waypoints, use_quantum=True)
            
            # The basic optimizer returns best_route_index, not a full path
            # Create a simple ordered path based on nearest neighbor
            n = len(waypoints)
            if n == 2:
                # Simple 2-point route
                best_path = [0, 1]
            else:
                # Use nearest neighbor heuristic for path
                visited = [False] * n
                best_path = [0]  # Start at first waypoint
                visited[0] = True
                
                for _ in range(n - 1):
                    current = best_path[-1]
                    nearest_dist = float('inf')
                    nearest_idx = -1
                    
                    for j in range(n):
                        if not visited[j]:
                            dist = optimizer._haversine(waypoints[current], waypoints[j])
                            if dist < nearest_dist:
                                nearest_dist = dist
                                nearest_idx = j
                    
                    if nearest_idx != -1:
                        best_path.append(nearest_idx)
                        visited[nearest_idx] = True
            
            # Calculate total distance for the path
            total_dist = 0
            for i in range(len(best_path) - 1):
                total_dist += optimizer._haversine(waypoints[best_path[i]], waypoints[best_path[i + 1]])
            
            # Create segments
            segments = []
            for i in range(len(best_path) - 1):
                from_idx = best_path[i]
                to_idx = best_path[i + 1]
                dist = optimizer._haversine(waypoints[from_idx], waypoints[to_idx])
                segments.append({
                    'from': {
                        'index': from_idx,
                        'name': waypoints[from_idx].get('name', f'Point {from_idx + 1}'),
                        'coordinates': {'lat': waypoints[from_idx]['lat'], 'lng': waypoints[from_idx]['lng']}
                    },
                    'to': {
                        'index': to_idx,
                        'name': waypoints[to_idx].get('name', f'Point {to_idx + 1}'),
                        'coordinates': {'lat': waypoints[to_idx]['lat'], 'lng': waypoints[to_idx]['lng']}
                    },
                    'distance_km': float(dist),
                    'duration_minutes': float(dist / 40 * 60)  # 40 km/h average speed
                })
            
            # Create alternative routes from optimization phases
            alternative_routes = []
            for phase in result.get('optimization_phases', []):
                # For basic optimizer, create variations of the path
                alt_path = best_path.copy()
                if len(alt_path) > 2 and phase['name'] != 'Local Search':
                    # Create a different route variation
                    alt_path[1], alt_path[-1] = alt_path[-1], alt_path[1]  # Swap waypoints
                
                alt_dist = 0
                for i in range(len(alt_path) - 1):
                    alt_dist += optimizer._haversine(waypoints[alt_path[i]], waypoints[alt_path[i + 1]])
                
                alternative_routes.append({
                    'name': phase['name'],
                    'path': alt_path,
                    'distance': float(alt_dist),
                    'duration': float(alt_dist / 40 * 60),  # 40 km/h
                    'geometry': [[waypoints[i]['lat'], waypoints[i]['lng']] for i in alt_path]
                })
            
            # Add the final optimized route as the best
            alternative_routes.append({
                'name': 'Final Optimized Route',
                'path': best_path,
                'distance': float(total_dist),
                'duration': float(total_dist / 40 * 60),  # 40 km/h
                'geometry': [[waypoints[i]['lat'], waypoints[i]['lng']] for i in best_path]
            })
            
            # Format result to match expected structure
            formatted_result = {
                'optimized_order': best_path,
                'total_distance': float(total_dist),
                'total_duration': float(total_dist / 40 * 60),  # 40 km/h average speed
                'route_geometry': [[waypoints[i]['lat'], waypoints[i]['lng']] for i in best_path],
                'segments': segments,
                'optimization_method': 'quantum_annealing' if any('Quantum' in p['name'] for p in result.get('optimization_phases', [])) else 'hybrid',
                'optimization_time': 0.1,
                'quantum_iterations': len([p for p in result.get('optimization_phases', []) if 'Quantum' in p['name']]),
                'woa_iterations': len([p for p in result.get('optimization_phases', []) if 'Whale' in p['name']]),
                'alternative_routes': alternative_routes,
                'optimization_phases': result.get('optimization_phases', [])
            }
            
            return jsonify({
                'success': True,
                'data': formatted_result,
                'mode': 'basic_optimization'
            })
            
        except Exception as e:
            print(f"Basic optimizer error: {e}")
            print(traceback.format_exc())
            return jsonify({
                'success': False,
                'error': 'Optimization failed',
                'details': str(e)
            }), 500
            
    except Exception as e:
        print(f"Request error: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Invalid request',
            'details': str(e)
        }), 400

@app.route('/api/calculate-distance', methods=['POST'])
def calculate_distance():
    """
    Calculate distance between two points using real roads
    """
    try:
        data = request.get_json()
        point1 = data.get('point1')
        point2 = data.get('point2')
        
        if not point1 or not point2:
            return jsonify({
                'success': False,
                'error': 'Two points required'
            }), 400
        
        api_key = os.environ.get('ORS_API_KEY')
        
        if api_key:
            from real_world_routing import RealWorldRouteOptimizer
            route_optimizer = RealWorldRouteOptimizer(api_key=api_key)
            distance, route_info = route_optimizer.get_real_distance(point1, point2)
            
            return jsonify({
                'success': True,
                'distance_km': distance,
                'duration_minutes': route_info.get('duration', 0),
                'geometry': route_info.get('geometry', [])
            })
        else:
            # Fallback to Haversine
            from route_optimizer import HybridRouteOptimizer
            optimizer = HybridRouteOptimizer()
            distance = optimizer._haversine(point1, point2)
            
            return jsonify({
                'success': True,
                'distance_km': distance,
                'mode': 'haversine'
            })
            
    except Exception as e:
        print(f"Distance calculation error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"""
    ╔════════════════════════════════════════════════════════════╗
    ║  QAEWO Backend Server                                      ║
    ║  Quantum Annealing + Whale Optimization                    ║
    ║  Running on http://localhost:{port}                       ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
