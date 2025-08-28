// Frontend environment configuration
const config = {
  // API Configuration
  API_BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  
  // Environment
  ENVIRONMENT: process.env.REACT_APP_ENVIRONMENT || 'development',
  
  // Feature flags
  FEATURES: {
    CHATBOT: true,
    MAP_INTEGRATION: true,
    USER_ANALYTICS: true,
  },
  
  // API Endpoints
  ENDPOINTS: {
    AUTH: {
      LOGIN: '/users/login',
      REGISTER: '/users/register',
      LOGOUT: '/users/logout',
      PROFILE: '/users/profile',
    },
    STATIONS: {
      ALL: '/stations/',
      NEARBY: '/stations/nearby',
      COUNT: '/stations/count',
      SEARCH: '/stations/search',
    },
    SESSIONS: {
      LOG: '/sessions/',
      USER_SESSIONS: '/sessions/',
      STATISTICS: '/sessions/statistics',
      RECENT: '/sessions/recent',
    },
  },
  
  // Default settings
  DEFAULTS: {
    MAP_CENTER: { lat: 40.7128, lng: -74.0060 }, // New York
    SEARCH_RADIUS: 10, // km
    MAX_STATIONS: 50,
    SESSION_LIMIT: 20,
  },
};

export default config;
