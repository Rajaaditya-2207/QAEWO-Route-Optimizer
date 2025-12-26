import React, { useState, useEffect, useRef } from 'react';
import './SearchBar.css';

// Indian cities database with focus on Tamil Nadu and Union Territories
const INDIAN_CITIES = [
  // Tamil Nadu
  { name: 'Chennai', state: 'Tamil Nadu', lat: 13.0827, lng: 80.2707 },
  { name: 'Coimbatore', state: 'Tamil Nadu', lat: 11.0168, lng: 76.9558 },
  { name: 'Madurai', state: 'Tamil Nadu', lat: 9.9252, lng: 78.1198 },
  { name: 'Tiruchirappalli', state: 'Tamil Nadu', lat: 10.7905, lng: 78.7047 },
  { name: 'Salem', state: 'Tamil Nadu', lat: 11.6643, lng: 78.1460 },
  { name: 'Tirunelveli', state: 'Tamil Nadu', lat: 8.7139, lng: 77.7567 },
  { name: 'Erode', state: 'Tamil Nadu', lat: 11.3410, lng: 77.7172 },
  { name: 'Vellore', state: 'Tamil Nadu', lat: 12.9165, lng: 79.1325 },
  { name: 'Thoothukudi', state: 'Tamil Nadu', lat: 8.7642, lng: 78.1348 },
  { name: 'Dindigul', state: 'Tamil Nadu', lat: 10.3673, lng: 77.9803 },
  { name: 'Thanjavur', state: 'Tamil Nadu', lat: 10.7870, lng: 79.1378 },
  { name: 'Ranipet', state: 'Tamil Nadu', lat: 12.9249, lng: 79.3333 },
  { name: 'Sivakasi', state: 'Tamil Nadu', lat: 9.4523, lng: 77.7906 },
  { name: 'Karur', state: 'Tamil Nadu', lat: 10.9601, lng: 78.0766 },
  { name: 'Kanchipuram', state: 'Tamil Nadu', lat: 12.8342, lng: 79.7036 },
  { name: 'Tiruppur', state: 'Tamil Nadu', lat: 11.1075, lng: 77.3398 },
  { name: 'Nagercoil', state: 'Tamil Nadu', lat: 8.1790, lng: 77.4338 },
  { name: 'Cuddalore', state: 'Tamil Nadu', lat: 11.7480, lng: 79.7714 },
  { name: 'Kumbakonam', state: 'Tamil Nadu', lat: 10.9617, lng: 79.3881 },
  
  // Puducherry Union Territory
  { name: 'Puducherry', state: 'Puducherry UT', lat: 11.9416, lng: 79.8083 },
  { name: 'Karaikal', state: 'Puducherry UT', lat: 10.9254, lng: 79.8380 },
  { name: 'Yanam', state: 'Puducherry UT', lat: 16.7333, lng: 82.2167 },
  { name: 'Mahe', state: 'Puducherry UT', lat: 11.7009, lng: 75.5371 },
  
  // Other major cities
  { name: 'Mumbai', state: 'Maharashtra', lat: 19.0760, lng: 72.8777 },
  { name: 'Delhi', state: 'Delhi', lat: 28.7041, lng: 77.1025 },
  { name: 'Bangalore', state: 'Karnataka', lat: 12.9716, lng: 77.5946 },
  { name: 'Hyderabad', state: 'Telangana', lat: 17.3850, lng: 78.4867 },
  { name: 'Ahmedabad', state: 'Gujarat', lat: 23.0225, lng: 72.5714 },
  { name: 'Pune', state: 'Maharashtra', lat: 18.5204, lng: 73.8567 },
  { name: 'Kolkata', state: 'West Bengal', lat: 22.5726, lng: 88.3639 },
  { name: 'Surat', state: 'Gujarat', lat: 21.1702, lng: 72.8311 },
  { name: 'Jaipur', state: 'Rajasthan', lat: 26.9124, lng: 75.7873 },
  { name: 'Lucknow', state: 'Uttar Pradesh', lat: 26.8467, lng: 80.9462 },
  { name: 'Kanpur', state: 'Uttar Pradesh', lat: 26.4499, lng: 80.3319 },
  { name: 'Nagpur', state: 'Maharashtra', lat: 21.1458, lng: 79.0882 },
  { name: 'Visakhapatnam', state: 'Andhra Pradesh', lat: 17.6868, lng: 83.2185 },
  { name: 'Bhopal', state: 'Madhya Pradesh', lat: 23.2599, lng: 77.4126 },
  { name: 'Patna', state: 'Bihar', lat: 25.5941, lng: 85.1376 },
  { name: 'Vadodara', state: 'Gujarat', lat: 22.3072, lng: 73.1812 },
  { name: 'Ghaziabad', state: 'Uttar Pradesh', lat: 28.6692, lng: 77.4538 },
  { name: 'Ludhiana', state: 'Punjab', lat: 30.9010, lng: 75.8573 },
  { name: 'Agra', state: 'Uttar Pradesh', lat: 27.1767, lng: 78.0081 },
  { name: 'Kochi', state: 'Kerala', lat: 9.9312, lng: 76.2673 },
  { name: 'Thiruvananthapuram', state: 'Kerala', lat: 8.5241, lng: 76.9366 },
  { name: 'Kozhikode', state: 'Kerala', lat: 11.2588, lng: 75.7804 },
];

function SearchBar({ onLocationSelect }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredCities, setFilteredCities] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const searchRef = useRef(null);

  useEffect(() => {
    if (searchTerm.trim().length >= 2) {
      const filtered = INDIAN_CITIES.filter(city =>
        city.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        city.state.toLowerCase().includes(searchTerm.toLowerCase())
      ).slice(0, 8); // Limit to 8 results
      setFilteredCities(filtered);
      setShowResults(true);
    } else {
      setFilteredCities([]);
      setShowResults(false);
    }
  }, [searchTerm]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setShowResults(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleCitySelect = (city) => {
    onLocationSelect({
      name: city.name,
      address: `${city.name}, ${city.state}`,
      lat: city.lat,
      lng: city.lng
    });
    setSearchTerm('');
    setShowResults(false);
  };

  const handleSearchFocus = () => {
    if (searchTerm.trim().length >= 2) {
      setShowResults(true);
    }
  };

  return (
    <div className="search-bar" ref={searchRef}>
      <div className="search-input-container">
        <span className="search-icon">🔍</span>
        <input
          type="text"
          className="search-input"
          placeholder="Search for cities (e.g., Puducherry, Karaikal...)"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onFocus={handleSearchFocus}
        />
        {searchTerm && (
          <button 
            className="clear-search-btn"
            onClick={() => {
              setSearchTerm('');
              setShowResults(false);
            }}
          >
            ✕
          </button>
        )}
      </div>

      {showResults && filteredCities.length > 0 && (
        <div className="search-results">
          {filteredCities.map((city, index) => (
            <div
              key={index}
              className="search-result-item"
              onClick={() => handleCitySelect(city)}
            >
              <div className="result-icon">📍</div>
              <div className="result-info">
                <div className="result-name">{city.name}</div>
                <div className="result-state">{city.state}</div>
              </div>
              <div className="result-coords">
                {city.lat.toFixed(2)}°, {city.lng.toFixed(2)}°
              </div>
            </div>
          ))}
        </div>
      )}

      {showResults && searchTerm.trim().length >= 2 && filteredCities.length === 0 && (
        <div className="search-results">
          <div className="no-results">
            <span className="no-results-icon">🔍</span>
            No cities found matching "{searchTerm}"
          </div>
        </div>
      )}
    </div>
  );
}

export default SearchBar;
