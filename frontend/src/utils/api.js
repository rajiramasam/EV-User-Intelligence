// API utility functions for consistent communication with backend
import config from '../env.config.js';

const API_BASE_URL = config.API_BASE_URL;

// Helper function to make API calls
export const apiCall = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    credentials: 'include', // Include cookies for JWT refresh
  };

  try {
    const response = await fetch(url, { ...defaultOptions, ...options });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API call failed:', error);
    throw error;
  }
};

// User authentication API calls
export const authAPI = {
  // Register a new user
  register: async (userData) => {
    return apiCall(config.ENDPOINTS.AUTH.REGISTER, {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  },

  // Login user
  login: async (credentials) => {
    return apiCall(config.ENDPOINTS.AUTH.LOGIN, {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  },

  // Logout user
  logout: async () => {
    return apiCall(config.ENDPOINTS.AUTH.LOGOUT, {
      method: 'POST',
    });
  },

  // Get user profile
  getProfile: async () => {
    return apiCall(config.ENDPOINTS.AUTH.PROFILE, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
    });
  },

  // Update user profile
  updateProfile: async (profileData) => {
    return apiCall(config.ENDPOINTS.AUTH.PROFILE, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
      body: JSON.stringify(profileData),
    });
  },
};

// Stations API calls
export const stationsAPI = {
  // Get all stations
  getAll: async () => {
    return apiCall(config.ENDPOINTS.STATIONS.ALL);
  },

  // Get nearby stations
  getNearby: async (lat, lon, radius = config.DEFAULTS.SEARCH_RADIUS) => {
    return apiCall(`${config.ENDPOINTS.STATIONS.NEARBY}?lat=${lat}&lon=${lon}&radius=${radius}`);
  },

  // Get station count
  getCount: async () => {
    return apiCall(config.ENDPOINTS.STATIONS.COUNT);
  },

  // Search stations
  search: async (query, limit = config.DEFAULTS.MAX_STATIONS) => {
    return apiCall(`${config.ENDPOINTS.STATIONS.SEARCH}?query=${encodeURIComponent(query)}&limit=${limit}`);
  },
};

// Sessions API calls
export const sessionsAPI = {
  // Log a charging session
  logSession: async (sessionData) => {
    return apiCall(config.ENDPOINTS.SESSIONS.LOG, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
      body: JSON.stringify(sessionData),
    });
  },

  // Get user sessions
  getUserSessions: async (limit = config.DEFAULTS.SESSION_LIMIT, offset = 0) => {
    return apiCall(`${config.ENDPOINTS.SESSIONS.USER_SESSIONS}?limit=${limit}&offset=${offset}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
    });
  },

  // Get session statistics
  getStatistics: async () => {
    return apiCall(config.ENDPOINTS.SESSIONS.STATISTICS, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
    });
  },

  // Get recent sessions
  getRecent: async (count = 5) => {
    return apiCall(`${config.ENDPOINTS.SESSIONS.RECENT}?count=${count}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
    });
  },
};

// Health check
export const healthCheck = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.ok;
  } catch (error) {
    console.error('Health check failed:', error);
    return false;
  }
};

export default {
  authAPI,
  stationsAPI,
  sessionsAPI,
  healthCheck,
};
