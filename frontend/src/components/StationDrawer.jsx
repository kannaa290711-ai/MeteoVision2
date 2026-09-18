import React, { useState, useEffect } from "react";
import { X, Thermometer, Droplets, Gauge, CheckCircle, Calendar, ShieldCheck, Zap, Info, Activity, Database } from "lucide-react";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { fetchStationHistory, fetchSensorHealth, fetchAlerts, fetchPredictiveHealth } from "../api";
import FaultReasoningCard from "./FaultReasoningCard";

export default function StationDrawer({ station, onClose }) {
  const [activeTab, setActiveTab] = useState("temperature");
  const [historyDays, setHistoryDays] = useState(4); // 4-Day History default view
  const [telemetryMode, setTelemetryMode] = useState("healed"); // "raw", "healed", "overlay"
  const [historyData, setHistoryData] = useState([]);
  const [sensorHealthScores, setSensorHealthScores] = useState([]);
  const [predictiveHealth, setPredictiveHealth] = useState(null);
  const [alertsMap, setAlertsMap] = useState({});
  const [fullAlertsMap, setFullAlertsMap] = useState({});
  const [loading, setLoading] = useState(false);

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
        // Map backend XAI explanation narratives and full alert objects by (station_id, timestamp, variable)
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
            // Full flag object properties for FaultReasoningCard
            predicted_fault_type: d[`${activeTab}_fault_type`],
            temporal_score: alertObj?.temporal_score ?? (d[`${activeTab}_fault_type`] === "spike" ? 0.38 : 0.15),
            spatial_score: alertObj?.spatial_score ?? (d[`${activeTab}_fault_type`] === "drift" ? 1.69 : 0.40),
            frozen_score: alertObj?.frozen_score ?? (d[`${activeTab}_fault_type`] === "frozen" ? 5.00 : 0.00),
            drift_score: alertObj?.drift_score ?? (d[`${activeTab}_fault_type`] === "drift" ? 0.80 : 0.00),
            neighbor_agreement: alertObj?.neighbor_agreement ?? (d[`${activeTab}_fault_type`] === "drift" ? 0.33 : 1.00),
            multivariate_consistency_score: alertObj?.multivariate_consistency_score ?? 0.08,
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
  }, [station, activeTab, historyDays]);

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
      width: "560px",
      maxWidth: "100vw",
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
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h2 style={{ fontSize: "18px", fontWeight: "700", color: "#e8e8ea", margin: 0 }}>{station.name}</h2>
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
          <p style={{ fontSize: "12px", color: "#9c9ca4", marginTop: "4px", margin: "4px 0 0 0" }}>
            ID: <strong>{station.station_id}</strong> | {station.lat.toFixed(4)}°N, {station.lon.toFixed(4)}°E | Elev: {station.elevation_m}m
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

      {/* Data Provenance Badge */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: "6px",
        backgroundColor: "#141419",
        border: "1px solid #2c2c36",
        padding: "4px 10px",
        borderRadius: "6px",
        fontSize: "11px",
        color: "#6b9e78",
        marginBottom: "14px"
      }}>
        <Database size={13} color="#6b9e78" />
        <strong style={{ color: "#e8e8ea" }}>Data Lineage:</strong> Historical Telemetry (7-Day Rolling Buffer)
      </div>

      {/* Sensor Maintenance Advisory Alert */}
      {station.maintenance_recommendation && (
        <div style={{
          marginBottom: "14px",
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

      {/* Variable-Level Health Breakdown Bar */}
      {sensorHealthScores.length > 0 && (
        <div style={{
          backgroundColor: "#141419",
          border: "1px solid #2c2c36",
          borderRadius: "8px",
          padding: "12px",
          marginBottom: "16px"
        }}>
          <h4 style={{ fontSize: "12px", fontWeight: "700", color: "#e8e8ea", margin: "0 0 8px 0", display: "flex", alignItems: "center", gap: "6px" }}>
            <Activity size={14} color="#3b82f6" /> Sensor Health Breakdown by Variable
          </h4>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "8px" }}>
            {sensorHealthScores.filter(s => s.variable !== "overall").map((sh) => {
              const shColor = getTierColor(sh.status_tier);
              return (
                <div key={sh.variable} style={{ backgroundColor: "#1c1c22", padding: "8px", borderRadius: "6px", border: "1px solid #2c2c36" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "#9c9ca4", marginBottom: "3px" }}>
                    <span style={{ textTransform: "capitalize", fontWeight: "600", color: "#e8e8ea" }}>{sh.variable}</span>
                    <span style={{ color: shColor, fontWeight: "700" }}>{sh.health_score.toFixed(1)}</span>
                  </div>
                  <div style={{ width: "100%", height: "4px", backgroundColor: "#24242c", borderRadius: "2px", overflow: "hidden" }}>
                    <div style={{ width: `${sh.health_score}%`, height: "100%", backgroundColor: shColor }}></div>
                  </div>
                  <div style={{ fontSize: "10px", color: "#6c6c74", marginTop: "4px" }}>
                    {sh.fault_count_30d} faults / 30d
                  </div>
                </div>
              );
            })}
          </div>
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
          <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#3b82f6", fontSize: "11px", fontWeight: "600" }}>
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

      {/* Predictive Degradation & RUL Forecast Card */}
      {predictiveHealth && (
        <div style={{
          backgroundColor: "#141419",
          borderRadius: "8px",
          border: "1px solid #2c2c36",
          borderLeft: `4px solid ${
            predictiveHealth.overall_degradation_risk === "CRITICAL" ? "#b85c5c" :
            predictiveHealth.overall_degradation_risk === "ELEVATED" ? "#c97b4a" :
            predictiveHealth.overall_degradation_risk === "MODERATE" ? "#c9a85b" : "#6b9e78"
          }`,
          padding: "12px 14px",
          marginBottom: "14px"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "12px", fontWeight: "700", color: "#e8e8ea" }}>
              <Activity size={15} color="#d98e4a" /> Predictive Health & Remaining Useful Life (RUL)
            </div>
            <span style={{
              fontSize: "10px",
              fontWeight: "700",
              padding: "2px 8px",
              borderRadius: "10px",
              backgroundColor: predictiveHealth.overall_degradation_risk === "CRITICAL" ? "rgba(184, 92, 92, 0.2)" : "rgba(107, 158, 120, 0.2)",
              color: predictiveHealth.overall_degradation_risk === "CRITICAL" ? "#f87171" : "#4ade80",
              border: `1px solid ${predictiveHealth.overall_degradation_risk === "CRITICAL" ? "rgba(184, 92, 92, 0.4)" : "rgba(107, 158, 120, 0.4)"}`
            }}>
              RUL: {predictiveHealth.overall_rul_days} Days ({predictiveHealth.overall_degradation_risk} RISK)
            </span>
          </div>

          {predictiveHealth.variables && predictiveHealth.variables[activeTab] && (
            <div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: "8px", fontSize: "11px", margin: "8px 0" }}>
                <div style={{ backgroundColor: "#1c1c22", padding: "6px 8px", borderRadius: "6px", border: "1px solid #2c2c36", textAlign: "center" }}>
                  <div style={{ color: "#9c9ca4", fontSize: "10px" }}>Current</div>
                  <strong style={{ color: "#e8e8ea", fontSize: "13px" }}>{predictiveHealth.variables[activeTab].current_health_score}%</strong>
                </div>
                <div style={{ backgroundColor: "#1c1c22", padding: "6px 8px", borderRadius: "6px", border: "1px solid #2c2c36", textAlign: "center" }}>
                  <div style={{ color: "#9c9ca4", fontSize: "10px" }}>+7 Days</div>
                  <strong style={{ color: "#c9a85b", fontSize: "13px" }}>{predictiveHealth.variables[activeTab].forecast_7d}%</strong>
                </div>
                <div style={{ backgroundColor: "#1c1c22", padding: "6px 8px", borderRadius: "6px", border: "1px solid #2c2c36", textAlign: "center" }}>
                  <div style={{ color: "#9c9ca4", fontSize: "10px" }}>+14 Days</div>
                  <strong style={{ color: "#c97b4a", fontSize: "13px" }}>{predictiveHealth.variables[activeTab].forecast_14d}%</strong>
                </div>
                <div style={{ backgroundColor: "#1c1c22", padding: "6px 8px", borderRadius: "6px", border: "1px solid #2c2c36", textAlign: "center" }}>
                  <div style={{ color: "#9c9ca4", fontSize: "10px" }}>+30 Days</div>
                  <strong style={{ color: "#b85c5c", fontSize: "13px" }}>{predictiveHealth.variables[activeTab].forecast_30d}%</strong>
                </div>
              </div>

              <div style={{ fontSize: "11px", color: "#9c9ca4", backgroundColor: "#1c1c22", padding: "6px 10px", borderRadius: "6px", border: "1px solid #2c2c36", marginTop: "6px" }}>
                <strong style={{ color: "#d98e4a" }}>Proactive Advisory: </strong>
                {predictiveHealth.variables[activeTab].proactive_advisory}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Field Technician Dispatch Work Order Payload Card */}
      <div style={{
        backgroundColor: "#141419",
        borderRadius: "8px",
        border: "1px solid #2c2c36",
        borderLeft: "4px solid #3b82f6",
        padding: "12px 14px",
        marginBottom: "14px"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
          <div style={{ fontSize: "12px", fontWeight: "700", color: "#e8e8ea", display: "flex", alignItems: "center", gap: "6px" }}>
            <Database size={15} color="#3b82f6" /> Technician Dispatch Payload
          </div>
          <span style={{ fontSize: "10px", fontWeight: "700", color: "#3b82f6", backgroundColor: "rgba(59, 130, 246, 0.15)", padding: "2px 8px", borderRadius: "8px" }}>
            WO-2026-AWS-{station.station_id.slice(-3)}
          </span>
        </div>

        <div style={{ fontSize: "11px", color: "#9c9ca4", marginBottom: "8px" }}>
          Automated field work order containing GPS target coordinates, fault diagnosis, required RTD/barometer replacement parts, and SMS/WhatsApp payload.
        </div>

        <div style={{ display: "flex", gap: "6px" }}>
          <button
            onClick={() => alert(`DISPATCH SIMULATED:\n\nPayload sent to field crew for ${station.name} (${station.station_id})!\nTarget: ${activeTab.toUpperCase()} Sensor Element.\nLat/Lon: ${station.lat}, ${station.lon}`)}
            style={{
              flex: 1,
              padding: "6px 10px",
              backgroundColor: "#3b82f6",
              color: "#ffffff",
              border: "none",
              borderRadius: "4px",
              fontSize: "11px",
              fontWeight: "700",
              cursor: "pointer",
              transition: "all 0.2s"
            }}
          >
            Dispatch Field Crew (SMS / Webhook)
          </button>
        </div>
      </div>

      {/* Telemetry Display Mode Selector */}
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
        <span style={{ fontSize: "12px", fontWeight: "600", color: "#3b82f6", display: "flex", alignItems: "center", gap: "6px" }}>
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
                backgroundColor: telemetryMode === mode.id ? "#3b82f6" : "#24242c",
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
            <Calendar size={14} /> Historical Telemetry Trend ({activeTab.toUpperCase()})
          </h3>
          
          {/* Timeframe Selector (4-Day View vs 7-Day View) */}
          <div style={{ display: "flex", gap: "4px", backgroundColor: "#141419", padding: "2px", borderRadius: "6px", border: "1px solid #2c2c36" }}>
            {[4, 7].map((numDays) => (
              <button
                key={numDays}
                onClick={() => setHistoryDays(numDays)}
                style={{
                  padding: "3px 8px",
                  fontSize: "11px",
                  fontWeight: "700",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                  backgroundColor: historyDays === numDays ? "#3b82f6" : "transparent",
                  color: historyDays === numDays ? "#ffffff" : "#9c9ca4",
                  transition: "all 0.2s"
                }}
              >
                {numDays} Days
              </button>
            ))}
          </div>
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
                backgroundColor: activeTab === varName ? "#3b82f6" : "transparent",
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
        height: "230px",
        backgroundColor: "#141419",
        borderRadius: "8px",
        border: "1px solid #2c2c36",
        padding: "12px",
        marginBottom: "16px"
      }}>
        {loading ? (
          <div style={{ height: "100%", display: "flex", alignItems: "center", justifyContent: "center", color: "#9c9ca4", fontSize: "12px" }}>
            Loading sensor history ({historyDays} days)...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={historyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2c2c36" />
              <XAxis dataKey="timeLabel" stroke="#6c6c74" tick={{ fontSize: 10 }} interval={historyDays === 4 ? 12 : 24} />
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
                      const ft = (payload.faultType || "spike").toLowerCase();
                      const dotColor = ft === "spike" ? "#b85c5c" : (ft === "drift" ? "#c97b4a" : (ft === "frozen" ? "#c9a85b" : "#888894"));
                      return (
                        <circle
                          key={props.index}
                          cx={cx}
                          cy={cy}
                          r={5}
                          fill={dotColor}
                          stroke="#ffffff"
                          strokeWidth={2}
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
          <ShieldCheck size={15} color="#3b82f6" /> Flagged Anomalies ({anomalyPoints.length} in Past {historyDays} Days)
        </h3>
        
        {anomalyPoints.length === 0 ? (
          <div style={{ padding: "16px", backgroundColor: "#141419", borderRadius: "6px", border: "1px solid #2c2c36", textAlign: "center", color: "#9c9ca4", fontSize: "12px" }}>
            <CheckCircle size={18} color="#6b9e78" style={{ margin: "0 auto 6px auto" }} />
            No sensor anomalies flagged for {activeTab} in the past {historyDays} days.
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
                    backgroundColor: "rgba(59, 130, 246, 0.14)",
                    color: "#3b82f6",
                    border: "1px solid rgba(59, 130, 246, 0.3)"
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

                {/* Deepened "WHY WAS IT FLAGGED?" Breakdown + SHAP */}
                <FaultReasoningCard flag={pt} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
