import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const chemistryAPI = {
  // Process a chemistry query
  processQuery: async (query, explainMode = false) => {
    try {
      const response = await api.post('/query', {
        query,
        explain_mode: explainMode
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Failed to process query');
    }
  },

  // Get conversation history
  getHistory: async () => {
    try {
      const response = await api.get('/history');
      return response.data;
    } catch (error) {
      throw new Error('Failed to fetch conversation history');
    }
  },

  // Get specific conversation
  getConversation: async (id) => {
    try {
      const response = await api.get(`/history/${id}`);
      return response.data;
    } catch (error) {
      throw new Error('Failed to fetch conversation');
    }
  },

  // Clear conversation history
  clearHistory: async () => {
    try {
      const response = await api.post('/clear-history');
      return response.data;
    } catch (error) {
      throw new Error('Failed to clear history');
    }
  },

  // Get demo queries
  getDemoQueries: async () => {
    try {
      const response = await api.get('/demo-queries');
      return response.data;
    } catch (error) {
      throw new Error('Failed to fetch demo queries');
    }
  },

  // Download automation script
  downloadScript: async (script, filename) => {
    try {
      const response = await api.post('/download-script', {
        script,
        filename
      });
      return response.data;
    } catch (error) {
      throw new Error('Failed to generate download');
    }
  },

  // Health check
  healthCheck: async () => {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      throw new Error('API is not available');
    }
  }
};

export default api;
