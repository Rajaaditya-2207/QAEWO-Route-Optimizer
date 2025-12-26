import axios from 'axios';

// Backend API base URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 seconds timeout for optimization requests
});

/**
 * Check backend health status
 */
export const checkBackendHealth = () => {
  return api.get('/health');
};

/**
 * Optimize route using quantum annealing and whale optimization
 * @param {Array} waypoints - Array of waypoint objects with lat, lng, name, address
 * @returns {Promise} - Promise with optimization results
 */
export const optimizeRoute = (waypoints) => {
  return api.post('/optimize-route', {
    waypoints: waypoints.map(wp => ({
      lat: wp.lat,
      lng: wp.lng,
      name: wp.name,
      address: wp.address
    }))
  });
};

/**
 * Calculate distance between two points using real roads
 * @param {Object} point1 - First point with lat, lng
 * @param {Object} point2 - Second point with lat, lng
 * @returns {Promise} - Promise with distance and route info
 */
export const calculateDistance = (point1, point2) => {
  return api.post('/api/calculate-distance', {
    point1,
    point2
  });
};

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.config.url}`, response.data);
    return response;
  },
  (error) => {
    if (error.response) {
      // Server responded with error status
      console.error('API Response Error:', {
        status: error.response.status,
        data: error.response.data,
        url: error.config.url
      });
    } else if (error.request) {
      // Request made but no response received
      console.error('API No Response:', error.request);
    } else {
      // Error in request setup
      console.error('API Request Setup Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default api;
