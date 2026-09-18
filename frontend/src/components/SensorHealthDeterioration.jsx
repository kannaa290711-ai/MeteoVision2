import React from "react";
import { HeartPulse, AlertTriangle, ShieldAlert, CheckCircle2, TrendingDown, BellRing } from "lucide-react";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

export default function SensorHealthDeterioration({ station, isDemoCritical = false }) {
  if (!station) return null;

  const currentScore = isDemoCritical ? 48.0 : (station.health_score ?? 62.0);
  const statusTier = isDemoCritical ? "Critical" : (station.status_tier || (currentScore < 50 ? "Critical" : (currentScore < 70 ? "Degraded" : (currentScore < 85 ? "Watch" : "Healthy"))));

  const getTierColor = (tier) => {
    switch (tier) {
      case "Healthy": return "#6b9e78";
      case "Watch": return "#c9a85b";
      case "Degraded": return "#c97b4a";
      case "Critical": return "#b85c5c";
      default: return "#6b9e78";
    }
  };

  const accentColor = getTierColor(statusTier);

  // 5-Day Health History Deterioration Trend Data
  const healthTrendData = isDemoCritical ? [
    { day: "Day 1", score: 92, label: "Healthy" },
    { day: "Day 2", score: 84, label: "Watch" },
    { day: "Day 3", score: 71, label: "Watch" },
    { day: "Day 4", score: 58, label: "Degraded" },
    { day: "Day 5", score: 48, label: "Critical" },
  ] : [
    { day: "Day 1", score: 94, label: "Healthy" },
    { day: "Day 2", score: 91, label: "Healthy" },
    { day: "Day 3", score: 86, label: "Healthy" },
    { day: "Day 4", score: 77, label: "Watch" },
    { day: "Day 5", score: Math.round(currentScore), label: statusTier },
  ];

  const handleSendDemoAlert = () => {
    alert(`DEMO NOTIFICATION ALERT TRIGGERED:\n\n[CRITICAL SENSOR HEALTH WARNING]\nStation: ${station.name} (${station.station_id})\nHealth Score: ${currentScore}/100 (CRITICAL)\nRecommended Action: Immediate sensor inspection required.\n\nSMS & Datalogger Maintenance Dispatch Payload Sent!`);
  };

  return (
    <div style={{
      backgroundColor: "#141419",
      border: `1px solid ${accentColor}40`,
      borderRadius: "8px",
      padding: "14px",
      marginBottom: "16px"
    }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
        <h4 style={{ fontSize: "13px", fontWeight: "700", color: "#e8e8ea", margin: 0, display: "flex", alignItems: "center", gap: "6px" }}>
          <HeartPulse size={15} color={accentColor} /> SENSOR HEALTH SCORE & 5-DAY TREND
        </h4>
        <span style={{
          fontSize: "11px",
          fontWeight: "800",
          padding: "2px 10px",
          borderRadius: "12px",
          backgroundColor: `${accentColor}20`,
          color: accentColor,
          border: `1px solid ${accentColor}40`
        }}>
          {currentScore.toFixed(1)} / 100 ({statusTier.toUpperCase()})
        </span>
      </div>

      {/* Prominent Critical Warning Banner if score < 50 */}
      {(currentScore < 50 || isDemoCritical) && (
        <div style={{
          backgroundColor: "rgba(184, 92, 92, 0.2)",
          border: "1px solid #b85c5c",
          borderRadius: "6px",
          padding: "10px 14px",
          marginBottom: "12px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <ShieldAlert size={22} color="#b85c5c" />
            <div>
              <div style={{ fontSize: "12px", fontWeight: "800", color: "#f87171" }}>
                ⚠ SENSOR HEALTH CRITICAL — IMMEDIATE ACTION REQUIRED
              </div>
              <div style={{ fontSize: "11px", color: "#9c9ca4", marginTop: "2px" }}>
                Station: <strong>{station.name}</strong> | Sensor: <strong>Temperature</strong> | Health: <strong style={{ color: "#b85c5c" }}>{currentScore} / 100</strong>
              </div>
            </div>
          </div>
          <button
            onClick={handleSendDemoAlert}
            style={{
              padding: "6px 12px",
              backgroundColor: "#b85c5c",
              color: "#ffffff",
              border: "none",
              borderRadius: "4px",
              fontSize: "11px",
              fontWeight: "700",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "5px"
            }}
          >
            <BellRing size={13} /> Trigger Demo Alert
          </button>
        </div>
      )}

      {/* Health Deterioration Trend Chart */}
      <div style={{
        height: "120px",
        backgroundColor: "#1c1c22",
        borderRadius: "6px",
        border: "1px solid #2c2c36",
        padding: "8px",
        marginBottom: "10px"
      }}>
        <div style={{ fontSize: "10px", color: "#9c9ca4", marginBottom: "4px", fontWeight: "700", display: "flex", alignItems: "center", gap: "4px" }}>
          <TrendingDown size={12} color="#d98e4a" /> 5-Day Health Deterioration Sequence:
        </div>
        <ResponsiveContainer width="100%" height="80%">
          <LineChart data={healthTrendData}>
            <CartesianGrid strokeDasharray="2 2" stroke="#2c2c36" />
            <XAxis dataKey="day" stroke="#6c6c74" tick={{ fontSize: 10 }} />
            <YAxis stroke="#6c6c74" tick={{ fontSize: 10 }} domain={[0, 100]} />
            <Tooltip contentStyle={{ backgroundColor: "#1c1c22", borderColor: "#2c2c36", fontSize: "11px" }} />
            <Line type="monotone" dataKey="score" stroke={accentColor} strokeWidth={2.5} dot={{ r: 4, fill: accentColor }} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* 5-Day Horizontal Step Indicator */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "6px", fontSize: "10px" }}>
        {healthTrendData.map((h, idx) => (
          <div key={idx} style={{
            backgroundColor: "#1c1c22",
            padding: "6px",
            borderRadius: "4px",
            textAlign: "center",
            border: "1px solid #2c2c36"
          }}>
            <div style={{ color: "#9c9ca4" }}>{h.day}</div>
            <strong style={{ color: getTierColor(h.label), fontSize: "12px" }}>{h.score}</strong>
            <div style={{ color: "#6c6c74", fontSize: "9px" }}>{h.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
