import React, { useState, useEffect } from 'react';
import './App.css';
import MapView from './components/MapView';
import Dashboard from './components/Dashboard';
import WaypointManager from './components/WaypointManager';
import { optimizeRoute, checkBackendHealth } from './services/api';

function App() {
  const [waypoints, setWaypoints] = useState([]);
  const [optimizedRoute, setOptimizedRoute] = useState(null);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [backendStatus, setBackendStatus] = useState('checking');
  const [isDarkTheme, setIsDarkTheme] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    checkBackendHealth()
      .then(response => {
        setBackendStatus('connected');
        console.log('Backend connected:', response.data);
      })
      .catch(err => {
        setBackendStatus('disconnected');
        console.error('Backend not available:', err);
      });
  }, []);

  const handleAddWaypoint = (waypoint) => {
    setWaypoints([...waypoints, waypoint]);
    setError(null);
  };

  const handleRemoveWaypoint = (index) => {
    const newWaypoints = waypoints.filter((_, i) => i !== index);
    setWaypoints(newWaypoints);
    if (newWaypoints.length === 0) {
      setOptimizedRoute(null);
    }
  };

  const handleClearWaypoints = () => {
    setWaypoints([]);
    setOptimizedRoute(null);
    setError(null);
  };

  const handleOptimize = async () => {
    // Extract start, destination, and waypoints by type
    const start = waypoints.find(w => w.type === 'start');
    const destination = waypoints.find(w => w.type === 'destination');
    const intermediateWaypoints = waypoints.filter(w => w.type === 'waypoint');

    if (!start || !destination) {
      setError('Please add both start point and destination');
      return;
    }

    setIsOptimizing(true);
    setError(null);

    try {
      // Order waypoints: start, intermediate waypoints, destination
      // Backend will optimize the order of intermediate waypoints
      const orderedWaypoints = [start, ...intermediateWaypoints, destination].map(w => ({
        lat: w.lat,
        lng: w.lng,
        name: w.name,
        address: w.address
      }));

      console.log('Sending waypoints in order:', orderedWaypoints.map(w => w.name));

      const response = await optimizeRoute(orderedWaypoints);
      
      if (response.data.success) {
        setOptimizedRoute(response.data.data);
        console.log('Optimization result:', response.data.data);
      } else {
        setError(response.data.error || 'Optimization failed');
      }
    } catch (err) {
      console.error('Optimization error:', err);
      setError(err.response?.data?.error || 'Failed to connect to backend');
    } finally {
      setIsOptimizing(false);
    }
  };

  const handleMapClick = (lat, lng, name, address) => {
    handleAddWaypoint({ lat, lng, name, address, type: 'waypoint' });
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1 className="app-title">
            <span className="quantum-text">Q</span>AEWO
          </h1>
          <p className="app-subtitle">Quantum Annealing + Whale Optimization Route Optimizer</p>
        </div>
        <div className="header-controls">
          <button
            className="map-theme-toggle"
            onClick={() => setIsDarkTheme(!isDarkTheme)}
            title="Toggle map theme"
          >
            <span className="control-icon">{isDarkTheme ? '☀️' : '🌙'}</span>
            {isDarkTheme ? 'Light Map' : 'Dark Map'}
          </button>
          <div className={`backend-status ${backendStatus}`}>
            <span className="status-dot"></span>
            {backendStatus === 'connected' ? 'Backend Connected' : 
             backendStatus === 'disconnected' ? 'Backend Offline' : 'Checking...'}
          </div>
        </div>
      </header>

      <div className="app-container">
        <div className="left-panel">
          <WaypointManager
            waypoints={waypoints}
            onAddWaypoint={handleAddWaypoint}
            onRemoveWaypoint={handleRemoveWaypoint}
            onClearWaypoints={handleClearWaypoints}
            onOptimize={handleOptimize}
            isOptimizing={isOptimizing}
          />
          
          {error && (
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              {error}
            </div>
          )}

          <Dashboard 
            optimizedRoute={optimizedRoute}
            waypointCount={waypoints.length}
            waypoints={waypoints}
          />
        </div>

        <div className="right-panel">
          <MapView 
            waypoints={waypoints} 
            optimizedRoute={optimizedRoute} 
            onMapClick={handleMapClick}
            isDarkTheme={isDarkTheme}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
