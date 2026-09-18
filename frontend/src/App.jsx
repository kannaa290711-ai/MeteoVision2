import React, { useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import DemoControlBar from "./components/DemoControlBar";
import Navbar from "./components/Navbar";
import UserJourneyBanner from "./components/UserJourneyBanner";
import MetricsCard from "./components/MetricsCard";
import MapView from "./components/MapView";
import StationDrawer from "./components/StationDrawer";
import AlertFeed from "./components/AlertFeed";
import WeatherPatternView from "./components/WeatherPatternView";
import FutureVisionView from "./components/FutureVisionView";
import DisasterAlertCenter from "./components/DisasterAlertCenter";
import MeteoVisionAIBot from "./components/MeteoVisionAIBot";
import NearbyStationComparison from "./components/NearbyStationComparison";
import FiveDayWeatherHistory from "./components/FiveDayWeatherHistory";
import SensorHealthDeterioration from "./components/SensorHealthDeterioration";
import { fetchStations, fetchAlerts, fetchMetrics, subscribeTelemetryStream } from "./api";

const FALLBACK_STATIONS = [
  { station_id: "AWS_001", name: "Pune Central AWS", lat: 18.5204, lon: 73.8567, elevation_m: 560, latest_temperature: 28.4, latest_humidity: 62.0, latest_pressure: 954.2, health_score: 98.5, status_tier: "Healthy", status: "NORMAL" },
  { station_id: "AWS_002", name: "Mahabaleshwar High-Altitude AWS", lat: 17.9237, lon: 73.6586, elevation_m: 1353, latest_temperature: 19.2, latest_humidity: 88.5, latest_pressure: 865.0, health_score: 62.4, status_tier: "Degraded", status: "ANOMALY", maintenance_recommendation: "Inspect RTD temperature element & clean solar shield." },
  { station_id: "AWS_003", name: "Mumbai Colaba Coastal AWS", lat: 18.9067, lon: 72.8147, elevation_m: 11, latest_temperature: 31.8, latest_humidity: 79.4, latest_pressure: 1010.5, health_score: 95.0, status_tier: "Healthy", status: "NORMAL" },
  { station_id: "AWS_004", name: "Nashik Agricultural AWS", lat: 19.9975, lon: 73.7898, elevation_m: 600, latest_temperature: 29.1, latest_humidity: 54.2, latest_pressure: 948.1, health_score: 78.0, status_tier: "Watch", status: "NORMAL" },
  { station_id: "AWS_005", name: "Satara Valley AWS", lat: 17.6805, lon: 74.0183, elevation_m: 742, latest_temperature: 26.5, latest_humidity: 68.0, latest_pressure: 932.0, health_score: 42.1, status_tier: "Critical", status: "ANOMALY", maintenance_recommendation: "Barometer calibration required immediately." },
  { station_id: "AWS_006", name: "Kolhapur Plateau AWS", lat: 16.7050, lon: 74.2433, elevation_m: 569, latest_temperature: 27.8, latest_humidity: 71.3, latest_pressure: 950.4, health_score: 99.0, status_tier: "Healthy", status: "NORMAL" },
  { station_id: "AWS_007", name: "Solapur Semi-Arid AWS", lat: 17.6599, lon: 75.9064, elevation_m: 458, latest_temperature: 34.2, latest_humidity: 38.5, latest_pressure: 960.8, health_score: 91.2, status_tier: "Healthy", status: "NORMAL" },
  { station_id: "AWS_008", name: "Aurangabad AWS", lat: 19.8762, lon: 75.3433, elevation_m: 568, latest_temperature: 32.0, latest_humidity: 45.0, latest_pressure: 951.0, health_score: 82.5, status_tier: "Watch", status: "NORMAL" },
  { station_id: "AWS_009", name: "Ratnagiri Coastal AWS", lat: 16.9902, lon: 73.3120, elevation_m: 84, latest_temperature: 30.5, latest_humidity: 82.1, latest_pressure: 1008.2, health_score: 96.4, status_tier: "Healthy", status: "NORMAL" },
  { station_id: "AWS_010", name: "Ahmednagar AWS", lat: 19.0952, lon: 74.7480, elevation_m: 649, latest_temperature: 30.1, latest_humidity: 50.0, latest_pressure: 942.5, health_score: 94.0, status_tier: "Healthy", status: "NORMAL" },
  { station_id: "AWS_011", name: "Sangli Agricultural AWS", lat: 16.8524, lon: 74.5815, elevation_m: 553, latest_temperature: 28.9, latest_humidity: 63.4, latest_pressure: 952.1, health_score: 89.0, status_tier: "Healthy", status: "NORMAL" },
  { station_id: "AWS_012", name: "Lonavala Hill AWS", lat: 18.7557, lon: 73.4091, elevation_m: 622, latest_temperature: 22.1, latest_humidity: 85.0, latest_pressure: 940.0, health_score: 97.5, status_tier: "Healthy", status: "NORMAL" },
];

const FALLBACK_ALERTS = [
  {
    id: 1,
    station_id: "AWS_002",
    station_name: "Mahabaleshwar High-Altitude AWS",
    variable: "temperature",
    timestamp: new Date().toISOString(),
    raw_value: 29.2,
    estimated_value: 20.1,
    predicted_fault_type: "spike",
    ml_confidence: 0.94,
    imputation_method: "Spatial-Temporal IDW",
    physics_check_passed: true,
    shap_summary: "High positive attribution from trailing 15-min derivative (+0.42)",
    multivariate_consistency_score: 0.08,
    explanation_text: "Impulse spike anomaly detected: temperature jumped +9.1°C in single reading while humidity & pressure remained constant. Healed using IDW spatial interpolation."
  },
  {
    id: 2,
    station_id: "AWS_005",
    station_name: "Satara Valley AWS",
    variable: "pressure",
    timestamp: new Date(Date.now() - 15 * 60000).toISOString(),
    raw_value: 810.0,
    estimated_value: 932.0,
    predicted_fault_type: "drift",
    ml_confidence: 0.89,
    imputation_method: "Pre-Onset Extrapolation",
    physics_check_passed: true,
    shap_summary: "Cumulative negative drift gradient over 6 hours",
    multivariate_consistency_score: 0.88,
    explanation_text: "Sensor drift detected: barometer reading gradually drifted -122 hPa below regional baseline. Healed via baseline trend correction."
  }
];

const FALLBACK_METRICS = { precision: 0.847, recall: 0.878, f1: 0.862, tp: 4196, fp: 760 };

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [stations, setStations] = useState(FALLBACK_STATIONS);
  const [alerts, setAlerts] = useState(FALLBACK_ALERTS);
  const [metrics, setMetrics] = useState(FALLBACK_METRICS);
  const [selectedStationId, setSelectedStationId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isDemoActive, setIsDemoActive] = useState(true);
  const [activeScenario, setActiveScenario] = useState("spike");
  const [isWeatherEventDemo, setIsWeatherEventDemo] = useState(false);

  const loadDashboardData = async () => {
    try {
      const results = await Promise.allSettled([
        fetchStations(),
        fetchAlerts(50),
        fetchMetrics()
      ]);
      if (results[0].status === "fulfilled" && Array.isArray(results[0].value) && results[0].value.length > 0) setStations(results[0].value);
      if (results[1].status === "fulfilled" && Array.isArray(results[1].value) && results[1].value.length > 0) setAlerts(results[1].value);
      if (results[2].status === "fulfilled" && results[2].value) setMetrics(results[2].value);
    } catch (err) {
      console.warn("Using fallback telemetry data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 12000);
    let unsubscribeStream = null;
    try {
      unsubscribeStream = subscribeTelemetryStream((newStreamItem) => {
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
      console.warn("SSE stream warning:", err);
    }
    return () => {
      clearInterval(interval);
      if (unsubscribeStream) unsubscribeStream();
    };
  }, []);

  // Handler for SIH Demo Scenario selection
  const handleSelectScenario = (scenarioId) => {
    setActiveScenario(scenarioId);
    if (scenarioId === "spike") {
      setSelectedStationId("AWS_002");
      setIsWeatherEventDemo(false);
      setActiveTab("dashboard");
    } else if (scenarioId === "drift") {
      setSelectedStationId("AWS_005");
      setIsWeatherEventDemo(false);
      setActiveTab("dashboard");
    } else if (scenarioId === "frozen") {
      setSelectedStationId("AWS_001");
      setIsWeatherEventDemo(false);
      setActiveTab("dashboard");
    } else if (scenarioId === "missing") {
      setSelectedStationId("AWS_003");
      setIsWeatherEventDemo(false);
      setActiveTab("dashboard");
    } else if (scenarioId === "weather-event") {
      setSelectedStationId("AWS_002");
      setIsWeatherEventDemo(true);
      setActiveTab("nearby-analysis");
    } else if (scenarioId === "cyclone") {
      setIsWeatherEventDemo(false);
      setActiveTab("alerts-center");
    }
  };

  const handleResetDemo = () => {
    setActiveScenario(null);
    setIsWeatherEventDemo(false);
    setSelectedStationId(null);
  };

  const activeAnomaliesCount = stations.filter((s) => s.status === "ANOMALY").length;
  const selectedStation = stations.find((s) => s.station_id === selectedStationId) || stations[1];

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#141419", display: "flex", color: "#e8e8ea" }}>
      {/* 1. Left Collapsible Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={(tab) => setActiveTab(tab)}
        isDemoActive={isDemoActive}
        onToggleDemo={() => setIsDemoActive(!isDemoActive)}
      />

      {/* Main Workspace Right Area */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0, overflowX: "hidden" }}>
        {/* Top Navbar */}
        <Navbar
          activeAnomaliesCount={activeAnomaliesCount}
          activeTab={activeTab}
          onSelectTab={(tab) => setActiveTab(tab)}
        />

        {/* SIH Demo Mode Control Header */}
        {isDemoActive && (
          <DemoControlBar
            activeScenario={activeScenario}
            onSelectScenario={handleSelectScenario}
            onResetDemo={handleResetDemo}
          />
        )}

        {/* View Switcher Router */}
        <main style={{ flex: 1, padding: "16px", display: "flex", flexDirection: "column", overflowY: "auto" }}>
          {activeTab === "alerts-center" ? (
            <DisasterAlertCenter stations={stations} />
          ) : activeTab === "ai-bot" ? (
            <MeteoVisionAIBot selectedStation={selectedStation} stations={stations} activeScenario={activeScenario} />
          ) : activeTab === "nearby-analysis" ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <NearbyStationComparison suspectStation={selectedStation} allStations={stations} isWeatherEvent={isWeatherEventDemo} />
              <FiveDayWeatherHistory station={selectedStation} />
            </div>
          ) : activeTab === "sensor-health" ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <SensorHealthDeterioration station={selectedStation} isDemoCritical={selectedStation.health_score < 50} />
              <MetricsCard metrics={metrics} />
            </div>
          ) : activeTab === "analytics" ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <FiveDayWeatherHistory station={selectedStation} />
              <MetricsCard metrics={metrics} />
            </div>
          ) : activeTab === "weather-risk" ? (
            <WeatherPatternView stations={stations} />
          ) : activeTab === "roadmap" || activeTab === "settings-demo" ? (
            <FutureVisionView />
          ) : (
            /* Live Dashboard & Map Default Workspace */
            <div style={{ display: "flex", flexDirection: "column", gap: "16px", flex: 1 }}>
              <UserJourneyBanner />
              <MetricsCard metrics={metrics} />

              <div style={{
                flex: 1,
                display: "grid",
                gridTemplateColumns: "1fr 360px",
                gap: "16px",
                minHeight: "560px"
              }}>
                <MapView
                  stations={stations}
                  selectedStationId={selectedStationId}
                  onSelectStation={(id) => setSelectedStationId(id)}
                />
                <AlertFeed
                  alerts={alerts}
                  onSelectStation={(id) => setSelectedStationId(id)}
                />
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Station Analytics Side Drawer */}
      {selectedStation && (activeTab === "dashboard" || activeTab === "map" || activeTab === "stations" || activeTab === "anomalies") && (
        <StationDrawer
          station={selectedStation}
          allStations={stations}
          onClose={() => setSelectedStationId(null)}
          isWeatherEventDemo={isWeatherEventDemo}
        />
      )}
    </div>
  );
}
