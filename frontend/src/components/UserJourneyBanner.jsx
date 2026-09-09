import React from "react";
import { MapPin, MousePointerClick, Activity, AlertTriangle, Cpu, ShieldCheck } from "lucide-react";

export default function UserJourneyBanner() {
  const steps = [
    { num: 1, label: "MAP", desc: "12 AWS Stations", icon: MapPin, color: "#d98e4a" },
    { num: 2, label: "SELECT STATION", desc: "Click Marker", icon: MousePointerClick, color: "#6b9e78" },
    { num: 3, label: "VIEW READINGS", desc: "Temp / Hum / Press", icon: Activity, color: "#c9a85b" },
    { num: 4, label: "DETECT ANOMALY", desc: "Spike / Drift / Frozen", icon: AlertTriangle, color: "#b85c5c" },
    { num: 5, label: "ANALYZE", desc: "XAI & Imputation", icon: Cpu, color: "#9c9ca4" },
    { num: 6, label: "ALERT", desc: "Trust Score & Action", icon: ShieldCheck, color: "#6b9e78" },
  ];

  return (
    <div style={{
      backgroundColor: "#1c1c22",
      border: "1px solid #2c2c36",
      borderRadius: "10px",
      padding: "14px 18px",
      marginBottom: "16px",
      display: "flex",
      flexDirection: "column",
      gap: "10px"
    }}>
      {/* Purpose Banner */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
        <div>
          <h1 style={{ fontSize: "16px", fontWeight: "700", color: "#e8e8ea", margin: 0 }}>
            AETHERIX SENTINEL — <span style={{ color: "#d98e4a" }}>Intelligent AWS Monitoring & Anomaly Detection</span>
          </h1>
          <p style={{ fontSize: "12px", color: "#9c9ca4", margin: "3px 0 0 0" }}>
            An AI-powered platform for intelligent monitoring of Automatic Weather Stations, sensor anomalies, and weather patterns.
          </p>
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
          color: "#6b9e78"
        }}>
          <span style={{ width: "7px", height: "7px", borderRadius: "50%", backgroundColor: "#6b9e78" }}></span>
          <strong style={{ color: "#e8e8ea" }}>Data Provenance:</strong> Live API / Real Telemetry
        </div>
      </div>

      {/* Visual User Journey Workflow Steps */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
        gap: "8px",
        paddingTop: "6px",
        borderTop: "1px solid #2c2c36"
      }}>
        {steps.map((step, idx) => {
          const IconComp = step.icon;
          return (
            <div key={idx} style={{
              backgroundColor: "#141419",
              border: "1px solid #2c2c36",
              borderRadius: "6px",
              padding: "8px 10px",
              display: "flex",
              alignItems: "center",
              gap: "8px"
            }}>
              <div style={{
                width: "24px",
                height: "24px",
                borderRadius: "50%",
                backgroundColor: `${step.color}20`,
                color: step.color,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "11px",
                fontWeight: "700",
                flexShrink: 0
              }}>
                {step.num}
              </div>
              <div style={{ overflow: "hidden" }}>
                <div style={{ fontSize: "11px", fontWeight: "700", color: "#e8e8ea", whiteSpace: "nowrap" }}>
                  {step.label}
                </div>
                <div style={{ fontSize: "10px", color: "#9c9ca4", whiteSpace: "nowrap" }}>
                  {step.desc}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
