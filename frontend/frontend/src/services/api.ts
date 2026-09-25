import axios from "axios";


const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL
  || "http://127.0.0.1:8000/api"
).replace(/\/$/, "");


const api = axios.create({
  baseURL: API_BASE_URL,
});


api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem("access_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});


export default api;
