# QAEWO - Quantum Route Optimizer

**Quantum Annealing + Whale Optimization Algorithm** for optimal route planning with real-world road routing.

## 🚀 Features

### Backend
- **Hybrid Quantum Optimization**: Quantum Annealing for exploration + WOA for exploitation
- **Real-World Routing**: Uses OpenRouteService API for actual road networks
- **Flask REST API**: Clean endpoints for route optimization and distance calculation

### Frontend
- **🗺️ Interactive Leaflet Map**: Light-themed map with real road route visualization
- **🔍 Smart City Search**: Comprehensive Indian cities database including Puducherry UT, Karaikal, and major cities
- **📍 Waypoint Management**: Easy start, end, and waypoint selection
- **📊 Real-time Dashboard**: Dark theme with purple glow borders showing distance, time, and optimization metrics
- **⚛️ Quantum Visualization**: See the optimization method and quality indicators
- **🎨 Modern UI**: Dark theme (#0f0f1e) with purple accents (#8b5cf6) and glow effects

## 📋 Prerequisites

- Python 3.8+
- Node.js 14+
- OpenRouteService API key (optional, free at https://openrouteservice.org)

## ⚙️ Installation

### Quick Setup (Windows)
```bash
# Run the automated setup
setup.bat
```

### Manual Setup

1. **Backend Setup**
```bash
cd backend
pip install -r requirements.txt
```

2. **Frontend Setup**
```bash
cd frontend
npm install
```

## 🎯 Running the Application

### 1. Start Backend (Flask)
```bash
cd backend
python app.py
```
Backend runs on `http://localhost:5000`

### 2. Start Frontend (React)
```bash
cd frontend
npm start
```
Frontend opens at `http://localhost:3000`

### 3. Configure API Key (Optional but Recommended)

For real-world routing with actual roads:
```bash
# Windows
set ORS_API_KEY=your_api_key_here

# Linux/Mac
export ORS_API_KEY=your_api_key_here
```

Get free API key at: https://openrouteservice.org/dev/#/signup

## 🗺️ Usage

1. **Search for Cities**: Use the search bar to find cities like Puducherry, Karaikal, Chennai, etc.
   - Includes comprehensive database of Indian cities
   - Special support for Puducherry UT regions (Puducherry, Karaikal, Yanam, Mahe)

2. **Add Waypoints**: 
   - Click on searched cities to add them as waypoints
   - Or enable "Click Mode" on the map to add custom points
   - First point is automatically marked as START (🟢)
   - Last point is marked as END (🔴)
   - Intermediate points are WAYPOINTS (🟣)

3. **Optimize Route**: Click the "⚛️ Optimize Route" button
   - Quantum + Whale optimization runs on backend
   - Shows real road routes on the map
   - Displays optimization quality and method used

4. **View Results**: 
   - Purple route line shows optimized path on map
   - Dashboard displays total distance (km) and time (minutes)
   - See optimization details: method, computation time, iterations
   - View optimized waypoint order

## 🧠 Algorithm

The application uses a hybrid approach:

1. **Quantum Annealing (Exploration)**: Uses Qiskit quantum circuits to explore solution space
2. **Whale Optimization (Exploitation)**: Nature-inspired algorithm refines the quantum solution
3. **Local Search**: 2-opt optimization for final refinement
4. **Real-World Routing**: Maps to actual road networks using OSRM/OpenRouteService

## 📁 Project Structure

```
QAEWO_WebApp/
├── backend/
│   ├── app.py                      # Flask server
│   ├── requirements.txt            # Python dependencies
│   └── quantum/
│       ├── hybrid_optimizer.py     # Main QA + WOA optimizer
│       ├── real_world_routing.py   # Road routing logic
│       └── route_optimizer.py      # Fallback optimizer
├── frontend/
│   ├── src/
│   │   ├── App.js                  # Main React component
│   │   ├── components/
│   │   │   └── Map.js              # Leaflet map component
│   │   └── data/
│   │       └── cities.js           # City database
│   └── package.json
└── README.md
```

## 🛠️ Technologies

**Backend:**
- Flask (Python web framework)
- Qiskit (Quantum computing)
- NumPy (Numerical computing)
- OpenRouteService (Real-world routing)

**Frontend:**
- React.js
- Leaflet (Interactive maps)
- TailwindCSS (Styling)
- Axios (API calls)

## 📝 API Endpoints

### `POST /api/optimize-route`
Optimize route with quantum + whale optimization

**Request:**
```json
{
  "waypoints": [
    {"lat": 13.0827, "lng": 80.2707, "name": "Chennai"},
    {"lat": 11.9317, "lng": 79.8076, "name": "Puducherry"}
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "best_path": [0, 1],
    "best_distance": 152.5,
    "route_details": {
      "total_distance_km": 152.5,
      "total_duration_minutes": 180,
      "segments": [...]
    },
    "route_geometry": [[lat, lng], ...]
  }
}
```

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

ISC License

## 🙏 Acknowledgments

- Qiskit for quantum computing framework
- OpenRouteService for routing APIs
- React and Leaflet communities

---

**Built with ⚛️ Quantum Computing and 🐋 Nature-Inspired Optimization**
