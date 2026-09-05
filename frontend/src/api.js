import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

export const fetchStations = async () => {
  const response = await api.get("/stations");
  return response.data;
};

export const fetchStationHistory = async (stationId, days = 7) => {
  const response = await api.get(`/stations/${stationId}/history`, {
    params: { days },
  });
  return response.data;
};

export const fetchAlerts = async (limit = 50) => {
  const response = await api.get("/alerts", {
    params: { limit },
  });
  return response.data;
};

export const fetchMetrics = async () => {
  const response = await api.get("/metrics/evaluation");
  return response.data;
};

export default api;
