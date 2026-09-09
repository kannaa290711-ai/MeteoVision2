import React, { useState, useEffect } from "react";
import Navbar from "./components/Navbar";
import UserJourneyBanner from "./components/UserJourneyBanner";
import MetricsCard from "./components/MetricsCard";
import MapView from "./components/MapView";
import StationDrawer from "./components/StationDrawer";
import AlertFeed from "./components/AlertFeed";
import WeatherPatternView from "./components/WeatherPatternView";
import FutureVisionView from "./components/FutureVisionView";
import { fetchStations, fetchAlerts, fetchMetrics, subscribeTelemetryStream } from "./api";

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard"); // "dashboard", "weather-risk", "roadmap"
  const [stations, setStations] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [selectedStationId, setSelectedStationId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isStreaming, setIsStreaming] = useState(true);

  const loadDashboardData = async () => {
    try {
      const [stData, alertData, metricsData] = await Promise.all([
        fetchStations(),
        fetchAlerts(50),
        fetchMetrics()
      ]);
      setStations(stData);
      setAlerts(alertData);
      setMetrics(metricsData);
    } catch (err) {
      console.error("Error loading AETHERIX dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 12000);

    // Live Telemetry SSE Stream Subscription
    let unsubscribeStream = null;
    try {
      unsubscribeStream = subscribeTelemetryStream((newStreamItem) => {
        setIsStreaming(true);
        if (newStreamItem.flagged) {
          setAlerts((prevAlerts) => [
            {
              id: Date.now(),
              station_id: newStreamItem.station_id,
              station_name: newStreamItem.station_name,
              variable: "temperature",
              timestamp: newStreamItem.timestamp,
              raw_value: newStreamItem.temperature,
              predicted_fault_type: newStreamItem.fault_type,
              shap_summary: newStreamItem.shap_summary,
              multivariate_consistency_score: newStreamItem.multivariate_consistency_score
            },
            ...prevAlerts.slice(0, 49)
          ]);
        }
      });
    } catch (err) {
      console.warn("Real-time SSE stream unavailable, relying on interval polling:", err);
    }

    return () => {
      clearInterval(interval);
      if (unsubscribeStream) unsubscribeStream();
    };
  }, []);

  const activeAnomaliesCount = stations.filter((s) => s.status === "ANOMALY").length;
  const selectedStation = stations.find((s) => s.station_id === selectedStationId);

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#141419", display: "flex", flexDirection: "column" }}>
      {/* Top Navigation Bar with View Switcher */}
      <Navbar
        activeAnomaliesCount={activeAnomaliesCount}
        activeTab={activeTab}
        onSelectTab={(tab) => setActiveTab(tab)}
      />

      {/* Conditional View Rendering */}
      {activeTab === "roadmap" ? (
        <FutureVisionView />
      ) : activeTab === "weather-risk" ? (
        <WeatherPatternView stations={stations} />
      ) : (
        /* Main Dashboard Workspace */
        <div style={{ flex: 1, padding: "16px", display: "flex", flexDirection: "column" }}>
          {/* User Journey & Purpose Banner */}
          <UserJourneyBanner />

          {/* Model Performance Banner */}
          <MetricsCard metrics={metrics} />

          {/* Core Layout: Map + Alert Ticker */}
          <div style={{
            flex: 1,
            display: "grid",
            gridTemplateColumns: "1fr 360px",
            gap: "16px",
            minHeight: "580px"
          }}>
            {/* Leaflet Map Area */}
            <MapView
              stations={stations}
              selectedStationId={selectedStationId}
              onSelectStation={(id) => setSelectedStationId(id)}
            />

            {/* Real-time Alerts Ticker */}
            <AlertFeed
              alerts={alerts}
              onSelectStation={(id) => setSelectedStationId(id)}
            />
          </div>
        </div>
      )}

      {/* Station Analytics Side Drawer */}
      {selectedStation && activeTab === "dashboard" && (
        <StationDrawer
          station={selectedStation}
          onClose={() => setSelectedStationId(null)}
        />
      )}
    </div>
  );
}
