import axios from 'axios';

// Define the base URL of your API
const API_URL = process.env.REACT_APP_API_URL || 'https://facility-profiling.onrender.com';

// Create axios instance with base URL
const api = axios.create({
  baseURL: API_URL,
});

// Add request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Authentication API calls
export const loginUser = async (username, password) => {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const response = await api.post('/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  });
  return response.data;
};

export const registerUser = async (username, password) => {
  const response = await api.post('/register', { username, password });
  return response.data;
};

// Inspections API calls
export const getInspections = async () => {
  const response = await api.get('/inspections/');
  return response.data;
};

export const getInspection = async (id) => {
  const response = await api.get(`/inspections/${id}`);
  return response.data;
};

export const createInspection = async (inspectionData) => {
  const response = await api.post('/inspections/', inspectionData);
  return response.data;
};

export const updateInspection = async (id, inspectionData) => {
  const response = await api.put(`/inspections/${id}`, inspectionData);
  return response.data;
};

export const deleteInspection = async (id) => {
  const response = await api.delete(`/inspections/${id}`);
  return response.data;
};

export default api;
