import React, { useState } from 'react';
import SearchBar from './SearchBar';
import './WaypointManager.css';

function WaypointManager({ 
  waypoints, 
  onAddWaypoint, 
  onRemoveWaypoint, 
  onClearWaypoints,
  onOptimize,
  isOptimizing 
}) {
  const [showStartSearch, setShowStartSearch] = useState(false);
  const [showDestSearch, setShowDestSearch] = useState(false);
  const [showWaypointSearch, setShowWaypointSearch] = useState(false);

  // Parse waypoints structure: {start, destination, waypoints[]}
  const startPoint = waypoints.find(w => w.type === 'start');
  const destination = waypoints.find(w => w.type === 'destination');
  const intermediateWaypoints = waypoints.filter(w => w.type === 'waypoint');

  const handleStartSelect = (location) => {
    // Remove existing start if any
    onAddWaypoint({...location, type: 'start'});
    setShowStartSearch(false);
  };

  const handleDestSelect = (location) => {
    // Remove existing destination if any
    onAddWaypoint({...location, type: 'destination'});
    setShowDestSearch(false);
  };

  const handleWaypointSelect = (location) => {
    onAddWaypoint({...location, type: 'waypoint'});
    setShowWaypointSearch(false);
  };

  const removeByType = (type, index = null) => {
    if (type === 'waypoint' && index !== null) {
      // Find the actual index of this waypoint in the full array
      const waypointItems = waypoints.filter(w => w.type === 'waypoint');
      const targetWaypoint = waypointItems[index];
      const actualIndex = waypoints.findIndex(w => w === targetWaypoint);
      if (actualIndex !== -1) onRemoveWaypoint(actualIndex);
    } else {
      const actualIndex = waypoints.findIndex(w => w.type === type);
      if (actualIndex !== -1) onRemoveWaypoint(actualIndex);
    }
  };

  return (
    <div className="waypoint-manager">
      <div className="manager-header">
        <h2 className="manager-title">
          <span className="manager-icon">🗺️</span>
          Route Planning
        </h2>
        <div className="waypoint-count">{waypoints.length}</div>
      </div>

      <div className="manager-actions">
        {waypoints.length > 0 && (
          <button 
            className="action-btn danger"
            onClick={onClearWaypoints}
          >
            <span className="btn-icon">🗑️</span>
            Clear All
          </button>
        )}
      </div>

      <div className="waypoints-list">
        {/* Starting Point Section */}
        <div className="route-section">
          <div className="section-label">
            <span className="label-icon">🚩</span>
            Starting Point
          </div>
          
          {!startPoint ? (
            <button 
              className="add-location-btn"
              onClick={() => setShowStartSearch(!showStartSearch)}
            >
              <span className="btn-icon">➕</span>
              Add Start Location
            </button>
          ) : (
            <div className="waypoint-item start-point">
              <div className="waypoint-marker">
                <span className="marker-icon start">🟢</span>
              </div>
              
              <div className="waypoint-info">
                <div className="waypoint-name">{startPoint.name}</div>
                <div className="waypoint-coords">
                  {startPoint.address || `${startPoint.lat.toFixed(4)}, ${startPoint.lng.toFixed(4)}`}
                </div>
              </div>

              <button 
                className="remove-btn"
                onClick={() => removeByType('start')}
                title="Remove starting point"
              >
                ✕
              </button>
            </div>
          )}
          
          {showStartSearch && (
            <div className="search-section">
              <SearchBar onLocationSelect={handleStartSelect} />
            </div>
          )}
        </div>

        {/* Intermediate Waypoints Section */}
        <div className="route-section">
          <div className="section-label">
            <span className="label-icon">📍</span>
            Waypoints (Optional - {intermediateWaypoints.length})
          </div>
          
          <button 
            className="add-location-btn secondary"
            onClick={() => setShowWaypointSearch(!showWaypointSearch)}
          >
            <span className="btn-icon">➕</span>
            Add Waypoint
          </button>
          
          {showWaypointSearch && (
            <div className="search-section">
              <SearchBar onLocationSelect={handleWaypointSelect} />
            </div>
          )}
          
          {intermediateWaypoints.length > 0 && (
            <div className="waypoints-sublist">
              {intermediateWaypoints.map((waypoint, idx) => (
                <div key={idx} className="waypoint-item intermediate-point">
                  <div className="waypoint-marker">
                    <span className="marker-icon waypoint">🟣</span>
                  </div>
                  
                  <div className="waypoint-info">
                    <div className="waypoint-name">{waypoint.name}</div>
                    <div className="waypoint-coords">
                      {waypoint.address || `${waypoint.lat.toFixed(4)}, ${waypoint.lng.toFixed(4)}`}
                    </div>
                  </div>

                  <button 
                    className="remove-btn"
                    onClick={() => removeByType('waypoint', idx)}
                    title="Remove waypoint"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Destination Section */}
        <div className="route-section">
          <div className="section-label">
            <span className="label-icon">🏁</span>
            Destination
          </div>
          
          {!destination ? (
            <button 
              className="add-location-btn"
              onClick={() => setShowDestSearch(!showDestSearch)}
            >
              <span className="btn-icon">➕</span>
              Add Destination
            </button>
          ) : (
            <div className="waypoint-item destination-point">
              <div className="waypoint-marker">
                <span className="marker-icon end">🔴</span>
              </div>
              
              <div className="waypoint-info">
                <div className="waypoint-name">{destination.name}</div>
                <div className="waypoint-coords">
                  {destination.address || `${destination.lat.toFixed(4)}, ${destination.lng.toFixed(4)}`}
                </div>
              </div>

              <button 
                className="remove-btn"
                onClick={() => removeByType('destination')}
                title="Remove destination"
              >
                ✕
              </button>
            </div>
          )}
          
          {showDestSearch && (
            <div className="search-section">
              <SearchBar onLocationSelect={handleDestSelect} />
            </div>
          )}
        </div>
      </div>

      {startPoint && destination && (
        <>
          <div className="route-info-banner">
            {intermediateWaypoints.length === 0 ? (
              <span>🔍 Will find optimized route between start and destination</span>
            ) : (
              <span>🎯 Will optimize route order through {intermediateWaypoints.length} waypoint{intermediateWaypoints.length > 1 ? 's' : ''}</span>
            )}
          </div>
          <button 
            className={`optimize-btn ${isOptimizing ? 'optimizing' : ''}`}
            onClick={onOptimize}
            disabled={isOptimizing}
          >
            {isOptimizing ? (
              <>
                <span className="spinner"></span>
                Finding Optimized Route...
              </>
            ) : (
              <>
                <span className="btn-icon">⚛️</span>
                Find Optimized Route
              </>
            )}
          </button>
        </>
      )}
      
      {(!startPoint || !destination) && (
        <div className="route-info-banner warning">
          ⚠️ Please add both start point and destination to continue
        </div>
      )}
    </div>
  );
}

export default WaypointManager;
