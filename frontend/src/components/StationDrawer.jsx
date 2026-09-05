import React, { useState, useEffect } from "react";
import { X, Thermometer, Droplets, Gauge, AlertTriangle, CheckCircle, Calendar, ShieldCheck, Zap, Info } from "lucide-react";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { fetchStationHistory } from "../api";

export default function StationDrawer({ station, onClose }) {
  const [activeTab, setActiveTab] = useState("temperature");
  const [telemetryMode, setTelemetryMode] = useState("healed"); // "raw", "healed", "overlay"
  const [historyData, setHistoryData] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!station) return;
    setLoading(true);
    fetchStationHistory(station.station_id, 7)
      .then((data) => {
        const formatted = data.map((d) => ({
          ...d,
          timeLabel: new Date(d.timestamp).toLocaleDateString([], { month: "short", day: "numeric" }) +
                     " " + new Date(d.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          rawVal: d[activeTab],
          healedVal: d[`${activeTab}_estimated`],
          isFlagged: d[`${activeTab}_flagged`],
          faultType: d[`${activeTab}_fault_type`],
          statusLabel: d[`${activeTab}_status_label`],
          conf: d[`${activeTab}_imputed_conf`]
        }));
        setHistoryData(formatted);
      })
      .catch((err) => console.error("Error fetching station history:", err))
      .finally(() => setLoading(false));
  }, [station, activeTab]);

  if (!station) return null;

  const tier = station.status_tier || "Healthy";
  const score = station.health_score ?? 100.0;

  const anomalyPoints = historyData.filter((d) => d.isFlagged);

  const getTierColor = (t) => {
    switch (t) {
      case "Healthy": return "#6b9e78";
      case "Watch": return "#c9a85b";
      case "Degraded": return "#c97b4a";
      case "Critical": return "#b85c5c";
      default: return "#6b9e78";
    }
  };

  return (
    <div style={{
      position: "fixed",
      top: 0,
      right: 0,
      width: "520px",
      height: "100vh",
      backgroundColor: "#1c1c22",
      borderLeft: "1px solid #2c2c36",
      boxShadow: "-10px 0 30px rgba(0,0,0,0.6)",
      zIndex: 2000,
      display: "flex",
      flexDirection: "column",
      padding: "20px",
      overflowY: "auto"
    }}>
      {/* Drawer Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "14px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h2 style={{ fontSize: "18px", fontWeight: "700", color: "#e8e8ea" }}>{station.name}</h2>
            <span style={{
              fontSize: "11px",
              fontWeight: "700",
              padding: "2px 8px",
              borderRadius: "12px",
              backgroundColor: `${getTierColor(tier)}20`,
              color: getTierColor(tier),
              border: `1px solid ${getTierColor(tier)}40`
            }}>
              {tier} ({score}/100)
            </span>
          </div>
          <p style={{ fontSize: "12px", color: "#9c9ca4", marginTop: "4px" }}>
            ID: {station.station_id} | Coords: {station.lat.toFixed(4)}°N, {station.lon.toFixed(4)}°E | Elev: {station.elevation_m}m
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

      {/* Sensor Maintenance Recommendation Alert Box */}
      {station.maintenance_recommendation && (
        <div style={{
          marginBottom: "16px",
          padding: "10px 14px",
          backgroundColor: "#24242c",
          borderRadius: "6px",
          borderLeft: `3px solid ${getTierColor(tier)}`,
          fontSize: "12px",
          color: "#9c9ca4"
        }}>
          <strong style={{ color: "#e8e8ea" }}>Maintenance Advisory:</strong> {station.maintenance_recommendation}
        </div>
      )}

      {/* Live Reading Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "10px", marginBottom: "16px" }}>
        <div style={{ backgroundColor: "#141419", padding: "12px", borderRadius: "8px", border: "1px solid #2c2c36" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#b85c5c", fontSize: "11px", fontWeight: "600" }}>
            <Thermometer size={15} /> Temperature
          </div>
          <div style={{ fontSize: "17px", fontWeight: "700", color: "#e8e8ea", marginTop: "4px" }}>
            {station.latest_temperature !== null ? `${station.latest_temperature}°C` : "N/A"}
          </div>
        </div>

        <div style={{ backgroundColor: "#141419", padding: "12px", borderRadius: "8px", border: "1px solid #2c2c36" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#d98e4a", fontSize: "11px", fontWeight: "600" }}>
            <Droplets size={15} /> Humidity
          </div>
          <div style={{ fontSize: "17px", fontWeight: "700", color: "#e8e8ea", marginTop: "4px" }}>
            {station.latest_humidity !== null ? `${station.latest_humidity}%` : "N/A"}
          </div>
        </div>

        <div style={{ backgroundColor: "#141419", padding: "12px", borderRadius: "8px", border: "1px solid #2c2c36" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#c9a85b", fontSize: "11px", fontWeight: "600" }}>
            <Gauge size={15} /> Pressure
          </div>
          <div style={{ fontSize: "17px", fontWeight: "700", color: "#e8e8ea", marginTop: "4px" }}>
            {station.latest_pressure !== null ? `${station.latest_pressure} hPa` : "N/A"}
          </div>
        </div>
      </div>

      {/* Telemetry Display Mode Selector (Raw vs Healed vs Overlay) */}
      <div style={{
        display: "flex",
        justify: "space-between",
        alignItems: "center",
        backgroundColor: "#141419",
        padding: "6px 10px",
        borderRadius: "8px",
        border: "1px solid #2c2c36",
        marginBottom: "14px"
      }}>
        <span style={{ fontSize: "12px", fontWeight: "600", color: "#d98e4a", display: "flex", alignItems: "center", gap: "6px" }}>
          <Zap size={14} /> Telemetry Mode:
        </span>
        <div style={{ display: "flex", gap: "4px" }}>
          {[
            { id: "healed", label: "AI-Healed" },
            { id: "raw", label: "Raw Telemetry" },
            { id: "overlay", label: "Overlay Both" },
          ].map((mode) => (
            <button
              key={mode.id}
              onClick={() => setTelemetryMode(mode.id)}
              style={{
                padding: "4px 10px",
                fontSize: "11px",
                fontWeight: "600",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
                backgroundColor: telemetryMode === mode.id ? "#d98e4a" : "#24242c",
                color: telemetryMode === mode.id ? "#ffffff" : "#9c9ca4",
                transition: "all 0.2s"
              }}
            >
              {mode.label}
            </button>
          ))}
        </div>
      </div>

      {/* Variable Tabs & History Header */}
      <div style={{ marginBottom: "12px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
          <h3 style={{ fontSize: "13px", fontWeight: "700", color: "#e8e8ea", display: "flex", alignItems: "center", gap: "6px" }}>
            <Calendar size={14} /> 7-Day Historical Data ({activeTab.toUpperCase()})
          </h3>
          <span style={{ fontSize: "11px", color: "#9c9ca4" }}>
            {anomalyPoints.length} anomalies flagged
          </span>
        </div>

        <div style={{ display: "flex", backgroundColor: "#141419", padding: "3px", borderRadius: "6px", border: "1px solid #2c2c36" }}>
          {["temperature", "humidity", "pressure"].map((varName) => (
            <button
              key={varName}
              onClick={() => setActiveTab(varName)}
              style={{
                flex: 1,
                padding: "6px 0",
                fontSize: "12px",
                fontWeight: "600",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
                backgroundColor: activeTab === varName ? "#d98e4a" : "transparent",
                color: activeTab === varName ? "#ffffff" : "#9c9ca4",
                textTransform: "capitalize"
              }}
            >
              {varName}
            </button>
          ))}
        </div>
      </div>

      {/* Time Series Chart */}
      <div style={{
        height: "220px",
        backgroundColor: "#141419",
        borderRadius: "8px",
        border: "1px solid #2c2c36",
        padding: "12px",
        marginBottom: "16px"
      }}>
        {loading ? (
          <div style={{ height: "100%", display: "flex", alignItems: "center", justifyContent: "center", color: "#9c9ca4", fontSize: "12px" }}>
            Loading sensor history...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={historyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2c2c36" />
              <XAxis dataKey="timeLabel" stroke="#6c6c74" tick={{ fontSize: 10 }} interval={24} />
              <YAxis stroke="#6c6c74" tick={{ fontSize: 10 }} domain={['auto', 'auto']} />
              <Tooltip
                contentStyle={{ backgroundColor: "#1c1c22", borderColor: "#2c2c36", borderRadius: "6px", color: "#e8e8ea", fontSize: "12px" }}
              />
              {(telemetryMode === "raw" || telemetryMode === "overlay") && (
                <Line
                  type="monotone"
                  dataKey="rawVal"
                  name="Raw Value"
                  stroke="#b85c5c"
                  strokeWidth={1.5}
                  strokeDasharray={telemetryMode === "overlay" ? "4 4" : undefined}
                  dot={(props) => {
                    const { cx, cy, payload } = props;
                    if (payload.isFlagged) {
                      return (
                        <circle
                          key={props.index}
                          cx={cx}
                          cy={cy}
                          r={4}
                          fill="#b85c5c"
                          stroke="#ffffff"
                          strokeWidth={1.5}
                        />
                      );
                    }
                    return null;
                  }}
                />
              )}
              {(telemetryMode === "healed" || telemetryMode === "overlay") && (
                <Line
                  type="monotone"
                  dataKey="healedVal"
                  name="AI-Healed Value"
                  stroke="#6b9e78"
                  strokeWidth={2}
                  dot={false}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Flagged Anomaly XAI Narrative Inspector */}
      <div style={{ flex: 1 }}>
        <h3 style={{ fontSize: "13px", fontWeight: "700", color: "#e8e8ea", marginBottom: "10px", display: "flex", alignItems: "center", gap: "6px" }}>
          <ShieldCheck size={15} color="#d98e4a" /> Flagged Anomalies & XAI Explanations
        </h3>
        
        {anomalyPoints.length === 0 ? (
          <div style={{ padding: "16px", backgroundColor: "#141419", borderRadius: "6px", border: "1px solid #2c2c36", textAlign: "center", color: "#9c9ca4", fontSize: "12px" }}>
            <CheckCircle size={18} color="#6b9e78" style={{ margin: "0 auto 6px auto" }} />
            No sensor anomalies flagged for {activeTab} in the past 7 days.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {anomalyPoints.slice(0, 6).map((pt, idx) => (
              <div key={idx} style={{
                backgroundColor: "#141419",
                borderLeft: `3px solid ${pt.faultType === "none" ? "#6b9e78" : "#b85c5c"}`,
                padding: "10px 12px",
                borderRadius: "6px",
                border: "1px solid #2c2c36"
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                  <div style={{ fontSize: "12px", fontWeight: "700", color: "#e8e8ea" }}>
                    {activeTab.toUpperCase()} {pt.faultType.toUpperCase()} Fault
                  </div>
                  <span style={{
                    fontSize: "10px",
                    fontWeight: "600",
                    padding: "2px 6px",
                    borderRadius: "4px",
                    backgroundColor: "rgba(217, 142, 74, 0.14)",
                    color: "#d98e4a",
                    border: "1px solid rgba(217, 142, 74, 0.3)"
                  }}>
                    {pt.statusLabel}
                  </span>
                </div>
                
                <div style={{ fontSize: "11px", color: "#9c9ca4", marginBottom: "6px" }}>
                  Timestamp: <strong>{new Date(pt.timestamp).toLocaleString()}</strong>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px", fontSize: "11px", backgroundColor: "#24242c", padding: "6px 8px", borderRadius: "4px", marginBottom: "6px" }}>
                  <div>Raw: <strong style={{ color: "#b85c5c" }}>{pt.rawVal !== null ? pt.rawVal : "NULL"}</strong></div>
                  <div>AI-Healed: <strong style={{ color: "#6b9e78" }}>{pt.healedVal}</strong></div>
                </div>

                <div style={{ fontSize: "11px", color: "#9c9ca4", lineHeight: "1.4" }}>
                  <Info size={12} color="#d98e4a" style={{ display: "inline", marginRight: "4px" }} />
                  {pt.faultType === "drift" && `Flagged as sensor drift: raw value deviated from baseline while neighbor agreement remained low. Imputed using pre-onset trajectory extrapolation.`}
                  {pt.faultType === "spike" && `Flagged as impulse spike: single-reading jump detected and smoothed via spatial-temporal IDW interpolation.`}
                  {pt.faultType === "frozen" && `Flagged as frozen sensor: flat line detected over trailing window. Replaced with neighbor IDW blended estimate.`}
                  {pt.faultType === "missing" && `Flagged as missing telemetry dropout: filled using spatial-temporal gap interpolation.`}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
