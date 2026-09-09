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

export const fetchSensorHealth = async (stationId) => {
  const response = await api.get(`/sensor-health/${stationId}`);
  return response.data;
};

export const fetchAlerts = async (limit = 50) => {
  const response = await api.get("/alerts", {
    params: { limit },
  });
  return response.data;
};

export const fetchDataLineage = async (flagId) => {
  const response = await api.get(`/lineage/${flagId}`);
  return response.data;
};

export const fetchMetrics = async () => {
  const response = await api.get("/metrics/evaluation");
  return response.data;
};

export const subscribeTelemetryStream = (onData, onError) => {
  const streamUrl = `${API_BASE_URL}/stream/telemetry`;
  const eventSource = new EventSource(streamUrl);
  
  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (onData) onData(data);
    } catch (err) {
      console.error("Failed to parse telemetry stream event:", err);
    }
  };

  eventSource.onerror = (err) => {
    console.warn("SSE telemetry stream warning/reconnecting:", err);
    if (onError) onError(err);
  };

  return () => eventSource.close();
};

export default api;
