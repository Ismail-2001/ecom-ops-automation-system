import axios from 'axios';

const getBaseUrl = () => {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (envUrl) return envUrl;
  
  // If we are running in Vite dev server (port 5173), we point to the FastAPI dev server (port 8000)
  if (typeof window !== 'undefined' && window.location.port === '5173') {
    return 'http://localhost:8000';
  }
  
  // In production, serve from same origin
  return '';
};

export const apiClient = axios.create({
  baseURL: getBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getWsUrl = () => {
  const base = getBaseUrl();
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  
  if (base) {
    // base can be http://localhost:8000
    const url = new URL(base);
    return `${url.protocol === 'https:' ? 'wss:' : 'ws:'}//${url.host}/ws/queue`;
  }
  
  return `${protocol}//${window.location.host}/ws/queue`;
};
export default apiClient;
