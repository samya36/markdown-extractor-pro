export const config = {
  API_BASE_URL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api',
  NODE_ENV: process.env.NODE_ENV || 'development'
};

export default config;