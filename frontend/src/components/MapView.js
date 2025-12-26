import React, { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './MapView.css';

// Fix for default marker icons in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// Custom marker icons
const startIcon = new L.Icon({
  iconUrl: 'data:image/svg+xml;base64,' + btoa(`
    <svg width="25" height="41" viewBox="0 0 25 41" xmlns="http://www.w3.org/2000/svg">
      <path d="M12.5 0C5.596 0 0 5.596 0 12.5c0 9.375 12.5 28.125 12.5 28.125S25 21.875 25 12.5C25 5.596 19.404 0 12.5 0z" fill="#10b981"/>
      <circle cx="12.5" cy="12.5" r="6" fill="white"/>
    </svg>
  `),
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

const endIcon = new L.Icon({
  iconUrl: 'data:image/svg+xml;base64,' + btoa(`
    <svg width="25" height="41" viewBox="0 0 25 41" xmlns="http://www.w3.org/2000/svg">
      <path d="M12.5 0C5.596 0 0 5.596 0 12.5c0 9.375 12.5 28.125 12.5 28.125S25 21.875 25 12.5C25 5.596 19.404 0 12.5 0z" fill="#ef4444"/>
      <circle cx="12.5" cy="12.5" r="6" fill="white"/>
    </svg>
  `),
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

const waypointIcon = new L.Icon({
  iconUrl: 'data:image/svg+xml;base64,' + btoa(`
    <svg width="25" height="41" viewBox="0 0 25 41" xmlns="http://www.w3.org/2000/svg">
      <path d="M12.5 0C5.596 0 0 5.596 0 12.5c0 9.375 12.5 28.125 12.5 28.125S25 21.875 25 12.5C25 5.596 19.404 0 12.5 0z" fill="#8b5cf6"/>
      <circle cx="12.5" cy="12.5" r="6" fill="white"/>
    </svg>
  `),
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

// Component to fit map bounds to markers
function MapBounds({ waypoints, optimizedRoute }) {
  const map = useMap();

  useEffect(() => {
    if (waypoints.length > 0) {
      const bounds = L.latLngBounds(waypoints.map(wp => [wp.lat, wp.lng]));
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [waypoints, optimizedRoute, map]);

  return null;
}

function MapView({ waypoints, optimizedRoute, onMapClick, isDarkTheme }) {
  const [clickMode, setClickMode] = useState(false);
  const [showAlternatives, setShowAlternatives] = useState(false);
  const [selectedRoutes, setSelectedRoutes] = useState(new Set()); // Track which routes are selected/visible
  const mapRef = useRef();

  // Toggle route visibility
  const toggleRouteVisibility = (routeIndex) => {
    setSelectedRoutes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(routeIndex)) {
        newSet.delete(routeIndex); // Unselect - hide this route
      } else {
        newSet.add(routeIndex); // Select - show only this route
      }
      return newSet;
    });
  };

  // Check if a route should be shown
  const shouldShowRoute = (routeIndex) => {
    if (selectedRoutes.size === 0) return true; // Show all if none selected
    return selectedRoutes.has(routeIndex); // Show only if selected
  };

  const handleMapClick = (e) => {
    if (clickMode) {
      const newWaypoint = {
        lat: e.latlng.lat,
        lng: e.latlng.lng,
        name: `Point ${waypoints.length + 1}`,
        address: `${e.latlng.lat.toFixed(4)}, ${e.latlng.lng.toFixed(4)}`
      };
      onMapClick(newWaypoint);
    }
  };

  const getMarkerIcon = (index, total) => {
    if (index === 0) return startIcon;
    if (index === total - 1) return endIcon;
    return waypointIcon;
  };

  // Get route polyline for optimized route
  const getRoutePolyline = () => {
    if (!optimizedRoute) return [];

    // Main optimized route with geometry
    if (optimizedRoute.route_geometry && optimizedRoute.route_geometry.length > 0) {
      return optimizedRoute.route_geometry;
    }
    
    // Fallback to waypoint order
    if (optimizedRoute.optimized_order) {
      return optimizedRoute.optimized_order.map(idx => [waypoints[idx].lat, waypoints[idx].lng]);
    }

    return [];
  };

  // Get alternative routes
  const getAlternativeRoutes = () => {
    if (!optimizedRoute || !optimizedRoute.alternative_routes) return [];
    return optimizedRoute.alternative_routes;
  };

  const routePolyline = getRoutePolyline();
  const alternativeRoutes = getAlternativeRoutes();

  return (
    <div className="map-container">
      <div className="map-controls">
          <button 
          className={`map-control-btn ${clickMode ? 'active' : ''}`}
          onClick={() => setClickMode(!clickMode)}
          title={clickMode ? 'Click mode: ON' : 'Click mode: OFF'}
        >
          <span className="control-icon">{clickMode ? '📍' : '🗺️'}</span>
          {clickMode ? 'Click to Add Points' : 'Enable Click Mode'}
        </button>
        
        {optimizedRoute && alternativeRoutes.length > 0 && (
          <button 
            className={`map-control-btn ${showAlternatives ? 'active' : ''}`}
            onClick={() => setShowAlternatives(!showAlternatives)}
            title="Show alternative routes"
          >
            <span className="control-icon">🔀</span>
            {showAlternatives ? 'Hide Alternatives' : `Show ${alternativeRoutes.length} Routes`}
          </button>
        )}
      </div>

      {/* Route Legend */}
      {showAlternatives && alternativeRoutes.length > 0 && (
        <div className="route-legend">
          <div className="legend-title">Route Options (Click to toggle)</div>
          {alternativeRoutes.map((altRoute, index) => {
            const isSelected = selectedRoutes.has(index);
            const isVisible = shouldShowRoute(index);
            return (
              <div 
                key={index} 
                className={`legend-item ${isSelected ? 'selected' : ''} ${!isVisible ? 'hidden-route' : ''}`}
                onClick={() => toggleRouteVisibility(index)}
                style={{ cursor: 'pointer' }}
              >
                <div 
                  className="legend-color" 
                  style={{ 
                    background: altRoute.color || ['#f59e0b', '#10b981', '#ef4444'][index % 3],
                    borderStyle: 'dashed',
                    opacity: isVisible ? 1 : 0.3
                  }}
                ></div>
                <div className="legend-info">
                  <div className="legend-name">
                    {altRoute.name} {isSelected && '✓'}
                  </div>
                  <div className="legend-stats">
                    {altRoute.distance.toFixed(1)} km · {(altRoute.duration / 60).toFixed(1)} hrs
                  </div>
                </div>
              </div>
            );
          })}
          <div 
            className={`legend-item best-route-legend ${selectedRoutes.has('best') ? 'selected' : ''} ${!shouldShowRoute('best') ? 'hidden-route' : ''}`}
            onClick={() => toggleRouteVisibility('best')}
            style={{ cursor: 'pointer' }}
          >
            <div 
              className="legend-color" 
              style={{ 
                background: '#8b5cf6',
                opacity: shouldShowRoute('best') ? 1 : 0.3
              }}
            ></div>
            <div className="legend-info">
              <div className="legend-name">
                🏆 Best Route {selectedRoutes.has('best') && '✓'}
              </div>
              <div className="legend-stats">
                {optimizedRoute.total_distance.toFixed(1)} km · {(optimizedRoute.total_duration / 60).toFixed(1)} hrs
              </div>
            </div>
          </div>
        </div>
      )}

      <MapContainer
        center={[11.9416, 79.8083]} // Default: Puducherry
        zoom={8}
        style={{ height: '100%', width: '100%' }}
        ref={mapRef}
        onClick={handleMapClick}
      >
        <TileLayer
          key={isDarkTheme ? 'dark' : 'light'}
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url={isDarkTheme 
            ? "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            : "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          }
        />

        {/* Display optimized route polyline */}
        {routePolyline.length > 0 && shouldShowRoute('best') && (
          <Polyline
            positions={routePolyline}
            color="#8b5cf6"
            weight={selectedRoutes.has('best') ? 7 : 5}
            opacity={selectedRoutes.has('best') ? 1 : 0.9}
            dashArray="0"
          >
            <Popup>
              <div className="route-popup">
                <strong>🏆 Best Route</strong>
                {optimizedRoute && (
                  <>
                    <div>📏 Distance: {optimizedRoute.total_distance?.toFixed(1)} km</div>
                    {optimizedRoute.total_duration && (
                      <div>⏱️ Duration: {(optimizedRoute.total_duration / 60).toFixed(1)} hrs ({optimizedRoute.total_duration.toFixed(0)} min)</div>
                    )}
                    <div>🔬 Method: {optimizedRoute.optimization_method === 'hybrid' ? 'Hybrid QA+WOA' : 'Quantum'}</div>
                  </>
                )}
              </div>
            </Popup>
          </Polyline>
        )}

        {/* Display alternative routes if enabled */}
        {showAlternatives && alternativeRoutes.map((altRoute, index) => {
          // Use color from backend or fallback to default colors
          const color = altRoute.color || ['#f59e0b', '#10b981', '#ef4444'][index % 3];
          const isVisible = shouldShowRoute(index);
          const isHighlighted = selectedRoutes.has(index);
          
          if (!altRoute.geometry || altRoute.geometry.length === 0 || !isVisible) return null;
          
          return (
            <Polyline
              key={`alt-route-${index}`}
              positions={altRoute.geometry}
              color={color}
              weight={isHighlighted ? 6 : 4}
              opacity={isHighlighted ? 1 : 0.7}
              dashArray={isHighlighted ? "0" : "10, 5"}
              eventHandlers={{
                mouseover: (e) => {
                  e.target.setStyle({ weight: 6, opacity: 1 });
                },
                mouseout: (e) => {
                  e.target.setStyle({ weight: isHighlighted ? 6 : 4, opacity: isHighlighted ? 1 : 0.7 });
                }
              }}
            >
              <Popup>
                <div className="route-popup">
                  <strong>{altRoute.name}</strong>
                  <div>📏 Distance: {altRoute.distance.toFixed(1)} km</div>
                  {altRoute.duration && (
                    <div>⏱️ Duration: {(altRoute.duration / 60).toFixed(1)} hrs ({altRoute.duration.toFixed(0)} min)</div>
                  )}
                  <div style={{ marginTop: '0.5rem', padding: '0.25rem 0.5rem', background: color, color: 'white', borderRadius: '4px', fontSize: '0.75rem', textAlign: 'center' }}>
                    Route Option {index + 1}
                  </div>
                </div>
              </Popup>
            </Polyline>
          );
        })}
        
        {/* Display segment markers with distance/time info */}
        {optimizedRoute && optimizedRoute.segments && optimizedRoute.segments.map((segment, index) => {
          const midLat = (segment.from.coordinates.lat + segment.to.coordinates.lat) / 2;
          const midLng = (segment.from.coordinates.lng + segment.to.coordinates.lng) / 2;
          
          return (
            <Marker
              key={`segment-${index}`}
              position={[midLat, midLng]}
              icon={new L.DivIcon({
                className: 'segment-label',
                html: `<div class="segment-info">
                  <div class="segment-number">${index + 1}</div>
                  <div class="segment-details">
                    ${segment.distance_km.toFixed(1)}km<br/>
                    ${segment.duration_minutes.toFixed(0)}min
                  </div>
                </div>`,
                iconSize: [60, 40]
              })}
            />
          );
        })}

        {/* Display waypoint markers */}
        {waypoints.map((waypoint, index) => {
          // Find the position in optimized order
          let orderIndex = index;
          if (optimizedRoute && optimizedRoute.optimized_order) {
            orderIndex = optimizedRoute.optimized_order.indexOf(index);
          }

          return (
            <Marker
              key={index}
              position={[waypoint.lat, waypoint.lng]}
              icon={getMarkerIcon(orderIndex, waypoints.length)}
            >
              <Popup>
                <div className="waypoint-popup">
                  <strong>{waypoint.name}</strong>
                  <div className="waypoint-address">{waypoint.address}</div>
                  {optimizedRoute && (
                    <div className="waypoint-order">
                      Order: #{orderIndex + 1}
                    </div>
                  )}
                </div>
              </Popup>
            </Marker>
          );
        })}

        <MapBounds waypoints={waypoints} optimizedRoute={optimizedRoute} />
      </MapContainer>
    </div>
  );
}

export default MapView;
