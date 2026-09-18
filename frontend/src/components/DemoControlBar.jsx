import React from "react";
import { Sparkles, Zap, AlertTriangle, ShieldCheck, Activity, CloudRain, RefreshCw } from "lucide-react";

export default function DemoControlBar({ activeScenario, onSelectScenario, onResetDemo }) {
  const scenarios = [
    { id: "spike", name: "1. Sudden Spike", label: "Sensor Spike (Fault)", icon: Zap, color: "#b85c5c" },
    { id: "drift", name: "2. Drift", label: "Calibration Drift", icon: Activity, color: "#c97b4a" },
    { id: "frozen", name: "3. Frozen Sensor", label: "Stuck Sensor Lockup", icon: AlertTriangle, color: "#c9a85b" },
    { id: "missing", name: "4. Missing Data", label: "Data Gap & AI Healing", icon: ShieldCheck, color: "#888894" },
    { id: "weather-event", name: "5. Real Weather Event", label: "Multi-Station Correlated Shift", icon: CloudRain, color: "#6b9e78" },
    { id: "cyclone", name: "6. Cyclone / Severe Weather", label: "Severe Storm Depression", icon: Sparkles, color: "#a855f7" },
  ];

  return (
    <div style={{
      backgroundColor: "#1c1c22",
      borderBottom: "1px solid #2c2c36",
      padding: "10px 18px",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      gap: "12px",
      flexWrap: "wrap",
      zIndex: 2000
    }}>
      {/* Title */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <div style={{
          backgroundColor: "rgba(168, 85, 247, 0.2)",
          color: "#a855f7",
          padding: "5px 8px",
          borderRadius: "6px",
          fontSize: "11px",
          fontWeight: "800",
          display: "flex",
          alignItems: "center",
          gap: "6px"
        }}>
          <Sparkles size={14} /> SIH 2026 DEMO MODE ACTIVE
        </div>
        <span style={{ fontSize: "11px", color: "#9c9ca4" }}>
          Select pre-configured SIH presentation scenario:
        </span>
      </div>

      {/* Scenario Buttons */}
      <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
        {scenarios.map((s) => {
          const Icon = s.icon;
          const isSelected = activeScenario === s.id;
          return (
            <button
              key={s.id}
              onClick={() => onSelectScenario(s.id)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "5px",
                padding: "6px 10px",
                fontSize: "11px",
                fontWeight: "700",
                backgroundColor: isSelected ? s.color : "#141419",
                color: isSelected ? "#ffffff" : s.color,
                border: `1px solid ${isSelected ? s.color : "#2c2c36"}`,
                borderRadius: "6px",
                cursor: "pointer",
                transition: "all 0.15s ease-in-out"
              }}
            >
              <Icon size={13} />
              <span>{s.name}</span>
            </button>
          );
        })}

        <button
          onClick={onResetDemo}
          style={{
            padding: "6px 10px",
            fontSize: "11px",
            fontWeight: "600",
            backgroundColor: "#24242c",
            color: "#9c9ca4",
            border: "1px solid #2c2c36",
            borderRadius: "6px",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "4px"
          }}
          title="Reset to Live Stream"
        >
          <RefreshCw size={12} /> Reset
        </button>
      </div>
    </div>
  );
}
