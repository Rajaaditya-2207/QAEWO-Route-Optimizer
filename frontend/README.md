# QAEWO Frontend

React-based frontend for the Quantum Annealing + Whale Optimization route optimizer.

## Features

- 🗺️ **Interactive Leaflet Map** with light theme
- 🔍 **City Search** with comprehensive Indian cities database (including Puducherry UT and Karaikal)
- 📍 **Waypoint Management** with start, end, and intermediate points
- ⚛️ **Quantum + WOA Optimization** visualization
- 📊 **Real-time Dashboard** with purple glow borders and dark theme
- 🛣️ **Real Road Routing** display with distance and time metrics

## Installation

1. Install dependencies:
```bash
npm install
```

2. Create `.env` file:
```bash
cp .env.example .env
```

3. Configure the backend API URL in `.env`:
```
REACT_APP_API_URL=http://localhost:5000
```

## Running the Application

Start the development server:
```bash
npm start
```

The application will open at `http://localhost:3000`

## Usage

1. **Search for Cities**: Use the search bar to find cities like Puducherry, Karaikal, Chennai, etc.
2. **Add Waypoints**: Click on searched cities or enable click mode to add points on the map
3. **Optimize Route**: Click "Optimize Route" button to run the quantum optimization
4. **View Results**: See the optimized route on the map and detailed metrics in the dashboard

## Components

- **App.js**: Main application container
- **MapView**: Leaflet map with route visualization
- **Dashboard**: Metrics and optimization results display
- **WaypointManager**: Waypoint list and management
- **SearchBar**: City search with autocomplete

## Theme

- **Dark Theme**: Main application with dark background (#0f0f1e)
- **Purple Glow**: Borders and accents with purple glow effects (#8b5cf6)
- **Light Map**: OpenStreetMap tiles with light theme for better visibility

## Build for Production

```bash
npm run build
```

The optimized production build will be in the `build/` directory.
