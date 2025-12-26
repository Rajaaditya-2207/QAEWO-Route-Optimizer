import React from 'react';
import './Dashboard.css';

function Dashboard({ optimizedRoute, waypointCount, waypoints = [] }) {
  if (!optimizedRoute) {
    return (
      <div className="dashboard">
        <div className="dashboard-header">
          <h2 className="dashboard-title">
            <span className="dashboard-icon">📊</span>
            Optimization Dashboard
          </h2>
        </div>
        <div className="dashboard-empty">
          <div className="empty-icon">🚀</div>
          <p>Add waypoints and click optimize to see results</p>
        </div>
      </div>
    );
  }

  const {
    total_distance,
    total_duration,
    optimization_method,
    optimization_time,
    quantum_iterations,
    woa_iterations,
    optimized_order
  } = optimizedRoute;

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2 className="dashboard-title">
          <span className="dashboard-icon">📊</span>
          Optimization Results
        </h2>
        <div className="optimization-badge">
          {optimization_method === 'quantum_annealing' ? '⚛️ Quantum' : 
           optimization_method === 'hybrid' ? '🔬 Hybrid QA+WOA' : '🐋 WOA'}
        </div>
      </div>

      <div className="dashboard-content">
        {/* Main Metrics */}
        <div className="metrics-grid">
          <div className="metric-card primary">
            <div className="metric-icon">🛣️</div>
            <div className="metric-content">
              <div className="metric-label">Total Distance</div>
              <div className="metric-value">
                {total_distance?.toFixed(2) || 'N/A'}
                <span className="metric-unit">km</span>
              </div>
            </div>
          </div>

          <div className="metric-card primary">
            <div className="metric-icon">⏱️</div>
            <div className="metric-content">
              <div className="metric-label">Estimated Time</div>
              <div className="metric-value">
                {total_duration ? 
                  total_duration.toFixed(0) : 'N/A'}
                <span className="metric-unit">min</span>
              </div>
            </div>
          </div>
        </div>

        {/* Optimization Details */}
        <div className="details-section">
          <h3 className="section-title">Optimization Details</h3>
          <div className="details-grid">
            <div className="detail-item">
              <span className="detail-label">Method</span>
              <span className="detail-value">
                {optimization_method === 'quantum_annealing' ? 'Quantum Annealing' :
                 optimization_method === 'hybrid' ? 'Hybrid QA+WOA' : 
                 'Whale Optimization'}
              </span>
            </div>

            <div className="detail-item">
              <span className="detail-label">Computation Time</span>
              <span className="detail-value">
                {optimization_time?.toFixed(3) || 'N/A'}s
              </span>
            </div>

            {quantum_iterations && (
              <div className="detail-item">
                <span className="detail-label">Quantum Iterations</span>
                <span className="detail-value">{quantum_iterations}</span>
              </div>
            )}

            {woa_iterations && (
              <div className="detail-item">
                <span className="detail-label">WOA Iterations</span>
                <span className="detail-value">{woa_iterations}</span>
              </div>
            )}

            <div className="detail-item">
              <span className="detail-label">Waypoints</span>
              <span className="detail-value">{waypointCount}</span>
            </div>
          </div>
        </div>

        {/* Route Order */}
        {optimized_order && optimized_order.length > 0 && (
          <div className="route-order-section">
            <h3 className="section-title">Optimized Route Order</h3>
            <div className="route-order-list">
              {optimized_order.map((waypointIndex, position) => {
                const waypoint = waypoints[waypointIndex];
                const waypointName = waypoint ? waypoint.name : `Point ${waypointIndex + 1}`;
                return (
                  <div key={position} className="route-order-item">
                    <div className="order-number">{position + 1}</div>
                    <div className="order-arrow">→</div>
                    <div className="order-waypoint">{waypointName}</div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Route Segments with Distance and Time */}
        {optimizedRoute.segments && optimizedRoute.segments.length > 0 && (
          <div className="segments-section">
            <h3 className="section-title">Route Segments</h3>
            <div className="segments-list">
              {optimizedRoute.segments.map((segment, index) => (
                <div key={index} className="segment-card">
                  <div className="segment-header">
                    <span className="segment-number-badge">{index + 1}</span>
                    <div className="segment-route">
                      <span className="segment-from">{segment.from.name}</span>
                      <span className="segment-arrow">→</span>
                      <span className="segment-to">{segment.to.name}</span>
                    </div>
                  </div>
                  <div className="segment-metrics">
                    <div className="segment-metric">
                      <span className="metric-icon">📏</span>
                      <span className="metric-value">{segment.distance_km.toFixed(2)} km</span>
                    </div>
                    <div className="segment-metric">
                      <span className="metric-icon">⏱️</span>
                      <span className="metric-value">{segment.duration_minutes.toFixed(0)} min</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Alternative Routes Comparison */}
        {optimizedRoute.alternative_routes && optimizedRoute.alternative_routes.length > 0 && (
          <div className="alternatives-section">
            <h3 className="section-title">🔀 Route Comparison ({optimizedRoute.alternative_routes.length} Options)</h3>
            <div className="alternatives-list">
              {optimizedRoute.alternative_routes.map((route, index) => {
                const isOptimal = index === 0; // First route is shortest/best since sorted by distance
                const longestRoute = optimizedRoute.alternative_routes[optimizedRoute.alternative_routes.length - 1];
                const savings = isOptimal && longestRoute ? 
                  ((longestRoute.distance - route.distance) / longestRoute.distance * 100) : 0;
                
                return (
                  <div key={index} className={`alternative-card ${isOptimal ? 'optimal' : ''}`}>
                    <div 
                      className="route-color-indicator" 
                      style={{ background: route.color || '#6b7280' }}
                    ></div>
                    <div className="alternative-content">
                      <div className="alternative-header">
                        <div className="alternative-header-left">
                          <span className="alternative-icon">
                            {isOptimal ? '🏆' : '🗺️'}
                          </span>
                          <span className="alternative-name">{isOptimal ? 'Best Route' : route.name}</span>
                        </div>
                        {isOptimal && savings > 0 && (
                          <span className="savings-badge">-{savings.toFixed(0)}%</span>
                        )}
                      </div>
                      <div className="alternative-metrics">
                        <div className="alt-metric">
                          <span className="alt-metric-icon">📏</span>
                          <span className="alt-metric-value">{route.distance.toFixed(1)} km</span>
                        </div>
                        {route.duration && (
                          <div className="alt-metric">
                            <span className="alt-metric-icon">⏱️</span>
                            <span className="alt-metric-value">{(route.duration / 60).toFixed(1)} hrs</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Performance Indicator */}
        <div className="performance-indicator">
          <div className="performance-header">
            <span className="performance-label">Optimization Quality</span>
            <span className="performance-score">
              {optimization_method === 'hybrid' ? 'Excellent' :
               optimization_method === 'quantum_annealing' ? 'Very Good' : 'Good'}
            </span>
          </div>
          <div className="performance-bar">
            <div 
              className={`performance-fill ${optimization_method}`}
              style={{
                width: optimization_method === 'hybrid' ? '95%' :
                       optimization_method === 'quantum_annealing' ? '85%' : '75%'
              }}
            ></div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
