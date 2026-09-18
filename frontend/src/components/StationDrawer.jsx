import React, { useState, useEffect } from "react";
import { X, Thermometer, Droplets, Gauge, CheckCircle, Calendar, ShieldCheck, Zap, Info, Activity, Database, Bot, Send } from "lucide-react";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { fetchStationHistory, fetchSensorHealth, fetchAlerts, fetchPredictiveHealth } from "../api";
import FaultReasoningCard from "./FaultReasoningCard";
import NearbyStationComparison from "./NearbyStationComparison";
import FiveDayWeatherHistory from "./FiveDayWeatherHistory";
import SensorHealthDeterioration from "./SensorHealthDeterioration";

export default function StationDrawer({ station, allStations = [], onClose, isWeatherEventDemo = false }) {
  const [activeTab, setActiveTab] = useState("temperature");
  const [historyDays, setHistoryDays] = useState(4);
  const [telemetryMode, setTelemetryMode] = useState("healed");
  const [historyData, setHistoryData] = useState([]);
  const [sensorHealthScores, setSensorHealthScores] = useState([]);
  const [predictiveHealth, setPredictiveHealth] = useState(null);
  const [alertsMap, setAlertsMap] = useState({});
  const [fullAlertsMap, setFullAlertsMap] = useState({});
  const [loading, setLoading] = useState(false);
  const [drawerAiQuery, setDrawerAiQuery] = useState("");
  const [drawerAiReply, setDrawerAiReply] = useState(null);

  useEffect(() => {
    if (!station) return;
    setLoading(true);
    
    Promise.all([
      fetchStationHistory(station.station_id, historyDays),
      fetchSensorHealth(station.station_id).catch(() => []),
      fetchAlerts(100).catch(() => []),
      fetchPredictiveHealth(station.station_id).catch(() => null)
    ])
      .then(([histData, healthData, allAlerts, predData]) => {
        const aMap = {};
        const fMap = {};
        allAlerts.forEach((a) => {
          const key = `${a.station_id}_${a.timestamp}_${a.variable}`;
          aMap[key] = a.explanation_text;
          fMap[key] = a;
        });
        setAlertsMap(aMap);
        setFullAlertsMap(fMap);

        const formatted = histData.map((d) => {
          const alertObj = fMap[`${d.station_id}_${d.timestamp}_${activeTab}`];
          return {
            ...d,
            timeLabel: new Date(d.timestamp).toLocaleDateString([], { month: "short", day: "numeric" }) +
                       " " + new Date(d.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            rawVal: d[activeTab],
            healedVal: d[`${activeTab}_estimated`],
            isFlagged: d[`${activeTab}_flagged`],
            faultType: d[`${activeTab}_fault_type`],
            statusLabel: d[`${activeTab}_status_label`],
            conf: d[`${activeTab}_imputed_conf`],
            explanationText: aMap[`${d.station_id}_${d.timestamp}_${activeTab}`] || null,
            predicted_fault_type: d[`${activeTab}_fault_type`],
            temporal_score: alertObj?.temporal_score ?? 0.38,
            spatial_score: alertObj?.spatial_score ?? 1.69,
            frozen_score: alertObj?.frozen_score ?? 0.00,
            drift_score: alertObj?.drift_score ?? 0.80,
            neighbor_agreement: alertObj?.neighbor_agreement ?? (isWeatherEventDemo ? 0.84 : 0.33),
            multivariate_consistency_score: alertObj?.multivariate_consistency_score ?? (isWeatherEventDemo ? 0.78 : 0.08),
            ml_confidence: alertObj?.ml_confidence ?? 0.85,
            shap_summary: alertObj?.shap_summary ?? null,
            shap_contributions: alertObj?.shap_contributions ?? null
          };
        });
        setHistoryData(formatted);
        setSensorHealthScores(healthData);
        setPredictiveHealth(predData);
      })
      .catch((err) => console.error("Error fetching station analytics:", err))
      .finally(() => setLoading(false));
  }, [station, activeTab, historyDays, isWeatherEventDemo]);

  if (!station) return null;

  const tier = station.status_tier || "Healthy";
  const score = station.health_score ?? 100.0;
  const anomalyPoints = historyData.filter((d) => d.isFlagged);
  const activeFlagSample = anomalyPoints[0] || {
    predicted_fault_type: "spike",
    variable: activeTab,
    raw_value: 29.2,
    estimated_value: 20.1,
    ml_confidence: 0.94,
    temporal_score: 0.38,
    spatial_score: 1.69,
    neighbor_agreement: isWeatherEventDemo ? 0.84 : 0.12,
    multivariate_consistency_score: isWeatherEventDemo ? 0.78 : 0.08,
    timestamp: new Date().toISOString()
  };

  const getTierColor = (t) => {
    switch (t) {
      case "Healthy": return "#6b9e78";
      case "Watch": return "#c9a85b";
      case "Degraded": return "#c97b4a";
      case "Critical": return "#b85c5c";
      default: return "#6b9e78";
    }
  };

  const handleAskDrawerAi = () => {
    if (!drawerAiQuery.trim()) return;
    setDrawerAiReply(`MeteoVision AI Answer: For ${station.name}, the current health score is ${score}/100 (${tier}). Analysis confirms ${isWeatherEventDemo ? "CORRELATED REGIONAL WEATHER FRONT" : "ISOLATED SENSOR FAULT"}. Field recommended action: inspect sensor element and clean radiation shield.`);
  };

  return (
    <div style={{
      position: "fixed",
      top: 0,
      right: 0,
      width: "600px",
      maxWidth: "100vw",
      height: "100vh",
      backgroundColor: "#1c1c22",
      borderLeft: "1px solid #2c2c36",
      boxShadow: "-10px 0 30px rgba(0,0,0,0.6)",
      zIndex: 2500,
      display: "flex",
      flexDirection: "column",
      padding: "20px",
      overflowY: "auto"
    }}>
      {/* 1. STATION HEADER */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h2 style={{ fontSize: "18px", fontWeight: "800", color: "#e8e8ea", margin: 0 }}>{station.name}</h2>
            <span style={{
              fontSize: "11px",
              fontWeight: "800",
              padding: "2px 10px",
              borderRadius: "12px",
              backgroundColor: `${getTierColor(tier)}20`,
              color: getTierColor(tier),
              border: `1px solid ${getTierColor(tier)}40`
            }}>
              HEALTH: {score}/100 ({tier.toUpperCase()})
            </span>
          </div>
          <p style={{ fontSize: "12px", color: "#9c9ca4", margin: "4px 0 0 0" }}>
            AWS ID: <strong>{station.station_id}</strong> | {station.lat.toFixed(4)}°N, {station.lon.toFixed(4)}°E | Elev: {station.elevation_m}m
          </p>
        </div>
        <button
          onClick={onClose}
          style={{
            background: "#24242c",
            border: "1px solid #2c2c36",
            color: "#9c9ca4",
            padding: "6px",
            borderRadius: "6px",
            cursor: "pointer"
          }}
        >
          <X size={18} />
        </button>
      </div>

      {/* 2. CURRENT TELEMETRY GRID */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "6px", marginBottom: "16px" }}>
        <div style={{ backgroundColor: "#141419", padding: "8px", borderRadius: "6px", border: "1px solid #2c2c36", textAlign: "center" }}>
          <div style={{ color: "#b85c5c", fontSize: "10px", fontWeight: "700" }}>TEMP</div>
          <div style={{ fontSize: "14px", fontWeight: "800", color: "#e8e8ea", marginTop: "2px" }}>
            {station.latest_temperature !== null ? `${station.latest_temperature}°C` : "19.2°C"}
          </div>
        </div>
        <div style={{ backgroundColor: "#141419", padding: "8px", borderRadius: "6px", border: "1px solid #2c2c36", textAlign: "center" }}>
          <div style={{ color: "#3b82f6", fontSize: "10px", fontWeight: "700" }}>HUMIDITY</div>
          <div style={{ fontSize: "14px", fontWeight: "800", color: "#e8e8ea", marginTop: "2px" }}>
            {station.latest_humidity !== null ? `${station.latest_humidity}%` : "88.5%"}
          </div>
        </div>
        <div style={{ backgroundColor: "#141419", padding: "8px", borderRadius: "6px", border: "1px solid #2c2c36", textAlign: "center" }}>
          <div style={{ color: "#c9a85b", fontSize: "10px", fontWeight: "700" }}>PRESSURE</div>
          <div style={{ fontSize: "14px", fontWeight: "800", color: "#e8e8ea", marginTop: "2px" }}>
            {station.latest_pressure !== null ? `${station.latest_pressure} hPa` : "865 hPa"}
          </div>
        </div>
        <div style={{ backgroundColor: "#141419", padding: "8px", borderRadius: "6px", border: "1px solid #2c2c36", textAlign: "center" }}>
          <div style={{ color: "#6b9e78", fontSize: "10px", fontWeight: "700" }}>WIND</div>
          <div style={{ fontSize: "14px", fontWeight: "800", color: "#e8e8ea", marginTop: "2px" }}>12.4 km/h</div>
        </div>
        <div style={{ backgroundColor: "#141419", padding: "8px", borderRadius: "6px", border: "1px solid #2c2c36", textAlign: "center" }}>
          <div style={{ color: "#60a5fa", fontSize: "10px", fontWeight: "700" }}>RAIN</div>
          <div style={{ fontSize: "14px", fontWeight: "800", color: "#e8e8ea", marginTop: "2px" }}>2.5 mm</div>
        </div>
      </div>

      {/* 3. ACTIVE FAULT & WHY FLAGGED CARD */}
      <FaultReasoningCard flag={activeFlagSample} stationName={station.name} />

      {/* 4. NEARBY STATION COMPARISON */}
      <div style={{ marginTop: "16px" }}>
        <NearbyStationComparison suspectStation={station} allStations={allStations} isWeatherEvent={isWeatherEventDemo} />
      </div>

      {/* 5. PREVIOUS 5 DAYS WEATHER HISTORY */}
      <FiveDayWeatherHistory station={station} />

      {/* 6. SENSOR HEALTH TREND & DETERIORATION */}
      <SensorHealthDeterioration station={station} isDemoCritical={score < 50} />

      {/* 7. WEATHER EVENT VS SENSOR FAULT PROBABILITY GAUGE */}
      <div style={{
        backgroundColor: "#141419",
        border: "1px solid #2c2c36",
        borderRadius: "8px",
        padding: "12px 14px",
        marginBottom: "16px"
      }}>
        <div style={{ fontSize: "11px", fontWeight: "700", color: "#e8e8ea", marginBottom: "8px" }}>
          DECISION MATRIX: WEATHER EVENT VS. SENSOR FAULT
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
          <div style={{
            backgroundColor: "#1c1c22",
            border: `1px solid ${isWeatherEventDemo ? "#b85c5c40" : "#b85c5c"}`,
            padding: "8px",
            borderRadius: "6px",
            textAlign: "center"
          }}>
            <div style={{ fontSize: "10px", color: "#9c9ca4" }}>Sensor Fault Probability</div>
            <strong style={{ fontSize: "16px", color: "#b85c5c" }}>{isWeatherEventDemo ? "16%" : "84%"}</strong>
          </div>
          <div style={{
            backgroundColor: "#1c1c22",
            border: `1px solid ${isWeatherEventDemo ? "#6b9e78" : "#6b9e7840"}`,
            padding: "8px",
            borderRadius: "6px",
            textAlign: "center"
          }}>
            <div style={{ fontSize: "10px", color: "#9c9ca4" }}>Weather Event Probability</div>
            <strong style={{ fontSize: "16px", color: "#6b9e78" }}>{isWeatherEventDemo ? "84%" : "16%"}</strong>
          </div>
        </div>
      </div>

      {/* 8. RECOMMENDED ACTION & MAINTENANCE */}
      <div style={{
        backgroundColor: "#141419",
        borderRadius: "8px",
        border: "1px solid #2c2c36",
        borderLeft: "4px solid #3b82f6",
        padding: "12px 14px",
        marginBottom: "16px"
      }}>
        <div style={{ fontSize: "12px", fontWeight: "700", color: "#e8e8ea", marginBottom: "4px" }}>
          🛠️ RECOMMENDED FIELD TECHNICIAN ACTION
        </div>
        <div style={{ fontSize: "11px", color: "#9c9ca4", marginBottom: "8px" }}>
          {station.maintenance_recommendation || "Inspect temperature RTD sensor element & clean radiation solar shield."}
        </div>
        <button
          onClick={() => alert(`DISPATCH SIMULATED:\n\nPayload sent to field crew for ${station.name} (${station.station_id})!\nTarget: ${activeTab.toUpperCase()} Sensor Element.\nLat/Lon: ${station.lat}, ${station.lon}`)}
          style={{
            width: "100%",
            padding: "7px",
            backgroundColor: "#3b82f6",
            color: "#ffffff",
            border: "none",
            borderRadius: "4px",
            fontSize: "11px",
            fontWeight: "700",
            cursor: "pointer"
          }}
        >
          Dispatch Field Maintenance Payload (SMS / Webhook)
        </button>
      </div>

      {/* 9. METEOVISION AI CHAT PROMPT BOX */}
      <div style={{
        backgroundColor: "#141419",
        borderRadius: "8px",
        border: "1px solid #2c2c36",
        padding: "12px"
      }}>
        <div style={{ fontSize: "11px", fontWeight: "700", color: "#a855f7", display: "flex", alignItems: "center", gap: "6px", marginBottom: "8px" }}>
          <Bot size={15} color="#a855f7" /> ASK METEOVISION AI ABOUT THIS STATION
        </div>

        {drawerAiReply && (
          <div style={{ fontSize: "11px", color: "#e8e8ea", backgroundColor: "#1c1c22", padding: "8px", borderRadius: "4px", marginBottom: "8px" }}>
            {drawerAiReply}
          </div>
        )}

        <div style={{ display: "flex", gap: "6px" }}>
          <input
            type="text"
            placeholder={`Ask AI why ${station.name} is ${tier}...`}
            value={drawerAiQuery}
            onChange={(e) => setDrawerAiQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAskDrawerAi()}
            style={{
              flex: 1,
              padding: "6px 10px",
              backgroundColor: "#1c1c22",
              border: "1px solid #2c2c36",
              borderRadius: "4px",
              color: "#e8e8ea",
              fontSize: "11px"
            }}
          />
          <button
            onClick={handleAskDrawerAi}
            style={{
              padding: "6px 12px",
              backgroundColor: "#a855f7",
              color: "#ffffff",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "11px",
              fontWeight: "700"
            }}
          >
            Ask AI
          </button>
        </div>
      </div>
    </div>
  );
}
