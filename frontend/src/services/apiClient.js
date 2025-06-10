// Enhanced API client with correlation ID support and performance monitoring
import axios from 'axios';

// Utility functions
const generateCorrelationId = () => {
  return Math.random().toString(36).substring(2, 15) + 
         Math.random().toString(36).substring(2, 15);
};

const getCurrentTimestamp = () => new Date().toISOString();

// Performance tracking
class PerformanceTracker {
  constructor() {
    this.metrics = [];
    this.maxMetrics = 100; // Keep last 100 API calls
  }

  track(method, url, startTime, endTime, status, correlationId) {
    const metric = {
      method,
      url,
      duration: endTime - startTime,
      status,
      correlationId,
      timestamp: getCurrentTimestamp()
    };

    this.metrics.unshift(metric);
    if (this.metrics.length > this.maxMetrics) {
      this.metrics.pop();
    }

    // Log slow requests
    if (metric.duration > 1000) {
      console.warn(`Slow API request: ${method} ${url} took ${metric.duration}ms`, {
        correlationId,
        metric
      });
    }
  }

  getMetrics() {
    return this.metrics;
  }

  getAverageResponseTime() {
    if (this.metrics.length === 0) return 0;
    const total = this.metrics.reduce((sum, metric) => sum + metric.duration, 0);
    return total / this.metrics.length;
  }

  getSlowRequests(threshold = 1000) {
    return this.metrics.filter(metric => metric.duration > threshold);
  }
}

// Global performance tracker instance
const performanceTracker = new PerformanceTracker();

// Error handling utilities
class ApiError extends Error {
  constructor(message, status, correlationId, response) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.correlationId = correlationId;
    this.response = response;
    this.timestamp = getCurrentTimestamp();
  }

  toJSON() {
    return {
      name: this.name,
      message: this.message,
      status: this.status,
      correlationId: this.correlationId,
      timestamp: this.timestamp
    };
  }
}

// Create axios instance with enhanced configuration
const createApiClient = () => {
  const client = axios.create({
    baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8080',
    timeout: 30000, // 30 second timeout
    headers: {
      'Content-Type': 'application/json',
    }
  });

  // Request interceptor
  client.interceptors.request.use(
    (config) => {
      // Generate correlation ID for each request
      const correlationId = generateCorrelationId();
      config.headers['X-Correlation-ID'] = correlationId;
      
      // Add timestamp for performance tracking
      config.metadata = {
        startTime: Date.now(),
        correlationId
      };

      // Add authentication token if available
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers['X-API-Key'] = token;
      }

      // Log request for debugging
      if (process.env.NODE_ENV === 'development') {
        console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
          correlationId,
          headers: config.headers,
          data: config.data
        });
      }

      return config;
    },
    (error) => {
      console.error('[API Request Error]', error);
      return Promise.reject(error);
    }
  );

  // Response interceptor
  client.interceptors.response.use(
    (response) => {
      const config = response.config;
      const endTime = Date.now();
      const { startTime, correlationId } = config.metadata || {};

      // Track performance
      if (startTime && correlationId) {
        performanceTracker.track(
          config.method?.toUpperCase(),
          config.url,
          startTime,
          endTime,
          response.status,
          correlationId
        );
      }

      // Log successful response for debugging
      if (process.env.NODE_ENV === 'development') {
        const duration = endTime - startTime;
        console.log(`[API Response] ${config.method?.toUpperCase()} ${config.url} (${duration}ms)`, {
          correlationId,
          status: response.status,
          data: response.data
        });
      }

      return response;
    },
    (error) => {
      const config = error.config;
      const endTime = Date.now();
      const { startTime, correlationId } = config?.metadata || {};

      // Track failed request performance
      if (startTime && correlationId) {
        performanceTracker.track(
          config?.method?.toUpperCase(),
          config?.url,
          startTime,
          endTime,
          error.response?.status || 0,
          correlationId
        );
      }

      // Enhanced error handling
      const status = error.response?.status;
      const errorMessage = error.response?.data?.message || error.message;
      const responseCorrelationId = error.response?.headers['x-correlation-id'] || correlationId;

      // Create enhanced error object
      const apiError = new ApiError(
        errorMessage,
        status,
        responseCorrelationId,
        error.response
      );

      // Log error with context
      console.error(`[API Error] ${config?.method?.toUpperCase()} ${config?.url}`, {
        correlationId: responseCorrelationId,
        status,
        message: errorMessage,
        error: error.response?.data
      });

      // Handle specific error cases
      if (status === 401) {
        // Clear invalid token
        localStorage.removeItem('auth_token');
        // Redirect to login or show auth modal
        window.dispatchEvent(new CustomEvent('auth:required'));
      } else if (status === 429) {
        // Rate limiting - show user-friendly message
        apiError.message = 'Too many requests. Please wait a moment and try again.';
      } else if (status >= 500) {
        // Server error - show generic message
        apiError.message = 'Server error. Please try again later.';
      }

      return Promise.reject(apiError);
    }
  );

  return client;
};

// Create the main API client instance
const apiClient = createApiClient();

// Authentication utilities
export const auth = {
  setToken: (token) => {
    localStorage.setItem('auth_token', token);
  },
  
  getToken: () => {
    return localStorage.getItem('auth_token');
  },
  
  clearToken: () => {
    localStorage.removeItem('auth_token');
  },
  
  isAuthenticated: () => {
    return !!localStorage.getItem('auth_token');
  }
};

// Game API endpoints
export const gameApi = {
  // Player management
  createPlayer: async (playerData) => {
    const response = await apiClient.post('/api/v1/players', playerData);
    return response.data;
  },

  // Game management
  createGame: async (gameConfig) => {
    const response = await apiClient.post('/api/v1/games', gameConfig);
    return response.data;
  },

  getGameState: async (gameId, playerId) => {
    const response = await apiClient.get(`/api/v1/games/${gameId}`, {
      params: { player_id: playerId }
    });
    return response.data;
  },

  submitAction: async (gameId, playerId, action) => {
    const response = await apiClient.post(`/api/v1/games/${gameId}/actions`, {
      player_id: playerId,
      ...action
    });
    return response.data;
  },

  nextHand: async (gameId, playerId) => {
    const response = await apiClient.post(`/api/v1/games/${gameId}/next-hand`, {
      player_id: playerId
    });
    return response.data;
  },

  getShowdown: async (gameId, playerId) => {
    const response = await apiClient.get(`/api/v1/games/${gameId}/showdown`, {
      params: { player_id: playerId }
    });
    return response.data;
  }
};

// Learning API endpoints
export const learningApi = {
  getFeedback: async (playerId, handId) => {
    const response = await apiClient.get('/api/v1/learning/feedback', {
      params: { player_id: playerId, hand_id: handId }
    });
    return response.data;
  },

  getStats: async (playerId) => {
    const response = await apiClient.get('/api/v1/learning/stats', {
      params: { player_id: playerId }
    });
    return response.data;
  },

  getProgress: async (playerId) => {
    const response = await apiClient.get('/api/v1/learning/progress', {
      params: { player_id: playerId }
    });
    return response.data;
  }
};

// Debug API endpoints
export const debugApi = {
  getLogs: async (logType = 'main', lines = 100) => {
    const response = await apiClient.get('/api/v1/debug/logs', {
      params: { log_type: logType, lines }
    });
    return response.data;
  },

  searchLogs: async (query, logType = 'main', hours = 24) => {
    const response = await apiClient.get('/api/v1/debug/logs/search', {
      params: { query, log_type: logType, hours }
    });
    return response.data;
  },

  getLogsByCorrelationId: async (correlationId) => {
    const response = await apiClient.get(`/api/v1/debug/logs/correlation/${correlationId}`);
    return response.data;
  },

  getSystemInfo: async () => {
    const response = await apiClient.get('/api/v1/debug/system/info');
    return response.data;
  },

  testLogging: async (message, level = 'info') => {
    const response = await apiClient.post('/api/v1/debug/logs/test', null, {
      params: { message, level }
    });
    return response.data;
  },

  getPerformanceStats: async () => {
    const response = await apiClient.get('/api/v1/debug/performance/stats');
    return response.data;
  },

  clearPerformanceCache: async () => {
    const response = await apiClient.post('/api/v1/debug/performance/clear-cache');
    return response.data;
  }
};

// Performance monitoring utilities
export const performance = {
  getMetrics: () => performanceTracker.getMetrics(),
  getAverageResponseTime: () => performanceTracker.getAverageResponseTime(),
  getSlowRequests: (threshold) => performanceTracker.getSlowRequests(threshold),
  
  // Client-side performance tracking
  trackPageLoad: (pageName) => {
    const loadTime = performance.navigation ? 
      performance.timing.loadEventEnd - performance.timing.navigationStart : 
      0;
    
    console.log(`[Performance] Page Load: ${pageName} took ${loadTime}ms`);
    return loadTime;
  },

  trackRender: (componentName, renderTime) => {
    if (renderTime > 100) {
      console.warn(`[Performance] Slow Render: ${componentName} took ${renderTime}ms`);
    }
  }
};

// Utility functions for correlation tracking
export const correlation = {
  getCurrentId: () => {
    // Get correlation ID from the most recent request
    const metrics = performanceTracker.getMetrics();
    return metrics.length > 0 ? metrics[0].correlationId : null;
  },

  trackUserAction: (action, data = {}) => {
    const correlationId = generateCorrelationId();
    console.log(`[User Action] ${action}`, {
      correlationId,
      timestamp: getCurrentTimestamp(),
      data
    });
    return correlationId;
  }
};

// Export the main API client and utilities
export default apiClient;
export { ApiError, performanceTracker };