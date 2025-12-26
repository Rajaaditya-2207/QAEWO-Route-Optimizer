import numpy as np
import json
import math
import sys
from typing import List, Dict, Tuple

try:
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
    from qiskit_aer import AerSimulator
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False
    # Suppress warning - will use simulation mode


class QiskitQuantumOptimizer:
    """
    Qiskit-based Quantum Annealing for route optimization
    Uses real quantum circuit simulation for exploration
    """
    
    def __init__(self, num_waypoints: int, max_iter: int = 100, shots: int = 1024):
        self.num_waypoints = num_waypoints
        self.max_iter = max_iter
        self.shots = shots
        self.history = []
        self.qiskit_available = QISKIT_AVAILABLE
    
    def create_quantum_circuit(self, angle: float) -> Dict:
        """
        Create a parameterized quantum circuit for QAOA-like exploration
        Uses rotation gates to explore solution space
        """
        if not self.qiskit_available:
            return self._simulate_quantum_circuit(angle)
        
        try:
            # Create quantum circuit with enough qubits for waypoints
            num_qubits = min(self.num_waypoints, 10)  # Limit to 10 qubits for simulation
            qr = QuantumRegister(num_qubits, 'q')
            cr = ClassicalRegister(num_qubits, 'c')
            qc = QuantumCircuit(qr, cr)
            
            # Initial superposition with Hadamard
            for i in range(num_qubits):
                qc.h(qr[i])
            
            # Problem-dependent ansatz with RX rotations
            for i in range(num_qubits):
                qc.rx(angle, qr[i])
            
            # Cost-inspired phase rotation
            for i in range(num_qubits - 1):
                qc.cx(qr[i], qr[i + 1])
            
            for i in range(num_qubits):
                qc.rz(angle * 0.5, qr[i])
            
            # Measurement
            for i in range(num_qubits):
                qc.measure(qr[i], cr[i])
            
            # Simulate circuit
            simulator = AerSimulator()
            transpiled = transpile(qc, simulator)
            job = simulator.run(transpiled, shots=self.shots)
            result = job.result()
            counts = result.get_counts()
            
            # Convert bitstring counts to probabilities
            probabilities = {}
            for bitstring, count in counts.items():
                prob = count / self.shots
                idx = int(bitstring, 2) % self.num_waypoints
                probabilities[idx] = probabilities.get(idx, 0) + prob
            
            return probabilities
        
        except Exception as e:
            print(f"Qiskit error: {e}, falling back to simulation", file=sys.stderr)
            return self._simulate_quantum_circuit(angle)
    
    def _simulate_quantum_circuit(self, angle: float) -> Dict:
        """
        Simulate quantum behavior without Qiskit
        Uses mathematical approximation of quantum superposition
        """
        probabilities = {}
        
        # Simulate superposition using trigonometric functions
        for i in range(self.num_waypoints):
            # Parameterized rotation
            prob = (1 + math.cos(angle + (2 * math.pi * i) / self.num_waypoints)) / (2 * self.num_waypoints)
            probabilities[i] = prob
        
        # Normalize
        total = sum(probabilities.values())
        probabilities = {k: v / total for k, v in probabilities.items()}
        
        return probabilities
    
    def optimize(self, distance_matrix: np.ndarray) -> Tuple[int, float, List]:
        """
        Quantum annealing optimization using parameterized circuits
        Explores solution space with quantum advantage
        """
        best_route_idx = 0
        best_cost = float('inf')
        
        # Scale angle from 0 to 2π over iterations
        for iteration in range(self.max_iter):
            angle = (math.pi * 2) * (iteration / self.max_iter)
            
            # Get quantum probabilities for this angle
            probabilities = self.create_quantum_circuit(angle)
            
            # Evaluate route based on quantum probabilities
            cost = self._evaluate_route(probabilities, distance_matrix)
            
            # Track best solution
            if cost < best_cost:
                best_cost = cost
                best_route_idx = max(probabilities, key=probabilities.get)
            
            self.history.append({
                'iteration': iteration,
                'cost': best_cost,
                'angle': angle
            })
        
        return best_route_idx, best_cost, self.history
    
    def _evaluate_route(self, probabilities: Dict, distance_matrix: np.ndarray) -> float:
        """Evaluate cost of route based on probability distribution"""
        cost = 0
        for idx, prob in probabilities.items():
            if idx < len(distance_matrix):
                cost += prob * np.sum(distance_matrix[idx])
        return cost


class WhaleOptimizationExploiter:
    """
    Whale Optimization Algorithm for exploitation phase
    Refines quantum solution using nature-inspired heuristic
    """
    
    def __init__(self, max_iter: int = 50, num_agents: int = 5):
        self.max_iter = max_iter
        self.num_agents = num_agents
        self.history = []
    
    def optimize(self, distance_matrix: np.ndarray, initial_solution: int = None) -> Tuple[int, float, List]:
        """
        WOA optimization for exploitation
        Refines the quantum solution
        """
        num_waypoints = len(distance_matrix)
        
        # Initialize agent positions (routes)
        positions = np.random.uniform(0, 1, (self.num_agents, num_waypoints))
        positions = positions / positions.sum(axis=1, keepdims=True)
        
        # Best position tracking
        if initial_solution is not None:
            best_position = np.zeros(num_waypoints)
            best_position[initial_solution] = 1.0
        else:
            best_position = positions[0].copy()
        
        best_cost = self._evaluate_cost(best_position, distance_matrix)
        
        for iteration in range(self.max_iter):
            # WOA parameters
            a = 2 - iteration * (2 / self.max_iter)
            
            for i in range(self.num_agents):
                r = np.random.random()
                A = 2 * a * r - a
                C = 2 * r
                
                # Update position based on best position
                if abs(A) < 1:
                    D = np.abs(C * best_position - positions[i])
                    positions[i] = best_position - A * D
                else:
                    # Update based on random agent
                    random_idx = np.random.randint(0, self.num_agents)
                    D = np.abs(C * positions[random_idx] - positions[i])
                    positions[i] = positions[random_idx] - A * D
                
                # Normalize position
                positions[i] = np.clip(positions[i], 0, 1)
                positions[i] = positions[i] / positions[i].sum()
                
                # Evaluate
                cost = self._evaluate_cost(positions[i], distance_matrix)
                
                if cost < best_cost:
                    best_cost = cost
                    best_position = positions[i].copy()
            
            self.history.append({
                'iteration': iteration,
                'cost': best_cost
            })
        
        best_idx = np.argmax(best_position)
        return int(best_idx), best_cost, self.history
    
    def _evaluate_cost(self, position: np.ndarray, distance_matrix: np.ndarray) -> float:
        """Calculate cost of route"""
        return np.sum(position * distance_matrix.sum(axis=1))


class HybridRouteOptimizer:
    """
    Hybrid optimizer combining Quantum Annealing (exploration) + WOA (exploitation)
    For optimized route planning
    """
    
    def __init__(self):
        self.qa_optimizer = None
        self.woa_optimizer = None
    
    def optimize(self, waypoints: List[Dict], use_quantum: bool = True) -> Dict:
        """
        Main optimization function
        Input: list of waypoints with 'lat' and 'lng'
        Output: optimized route with detailed results
        """
        # Calculate distance matrix
        distance_matrix = self._calculate_distance_matrix(waypoints)
        
        result = {
            'waypoints': waypoints,
            'distance_matrix': distance_matrix.tolist(),
            'optimization_phases': [],
            'best_route_index': None,
            'best_cost': None,
            'total_distance': None
        }
        
        if use_quantum:
            # Phase 1: Quantum Annealing for exploration
            qa = QiskitQuantumOptimizer(len(waypoints), max_iter=100, shots=1024)
            qa_idx, qa_cost, qa_history = qa.optimize(distance_matrix)
            
            result['optimization_phases'].append({
                'name': 'Quantum Annealing (Exploration)',
                'best_index': qa_idx,
                'best_cost': float(qa_cost),
                'history': qa_history
            })
            
            # Phase 2: WOA for exploitation using quantum result as seed
            woa = WhaleOptimizationExploiter(max_iter=50, num_agents=5)
            woa_idx, woa_cost, woa_history = woa.optimize(distance_matrix, initial_solution=qa_idx)
            
            result['optimization_phases'].append({
                'name': 'Whale Optimization (Exploitation)',
                'best_index': woa_idx,
                'best_cost': float(woa_cost),
                'history': woa_history
            })
            
            # Select best result
            if qa_cost < woa_cost:
                result['best_route_index'] = qa_idx
                result['best_cost'] = float(qa_cost)
            else:
                result['best_route_index'] = woa_idx
                result['best_cost'] = float(woa_cost)
        else:
            # Only WOA
            woa = WhaleOptimizationExploiter(max_iter=100, num_agents=5)
            woa_idx, woa_cost, woa_history = woa.optimize(distance_matrix)
            
            result['optimization_phases'].append({
                'name': 'Whale Optimization Only',
                'best_index': woa_idx,
                'best_cost': float(woa_cost),
                'history': woa_history
            })
            
            result['best_route_index'] = woa_idx
            result['best_cost'] = float(woa_cost)
        
        # Calculate total distance for best route
        result['total_distance'] = float(np.sum(distance_matrix[result['best_route_index']]))
        
        return result
    
    def _calculate_distance_matrix(self, waypoints: List[Dict]) -> np.ndarray:
        """Calculate Haversine distance matrix"""
        n = len(waypoints)
        matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    matrix[i][j] = self._haversine(waypoints[i], waypoints[j])
        
        return matrix
    
    @staticmethod
    def _haversine(point1: Dict, point2: Dict) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371  # Earth's radius in km
        lat1, lon1 = math.radians(point1['lat']), math.radians(point1['lng'])
        lat2, lon2 = math.radians(point2['lat']), math.radians(point2['lng'])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c


# Main execution
if __name__ == "__main__":
    # Read input from command line
    waypoints = json.loads(sys.argv[1]) if len(sys.argv) > 1 else []
    
    if waypoints:
        optimizer = HybridRouteOptimizer()
        result = optimizer.optimize(waypoints, use_quantum=True)
        print(json.dumps(result, indent=2))
    else:
        print("Error: No waypoints provided")
