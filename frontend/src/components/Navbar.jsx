import React, { useState, useEffect } from "react";
import { Activity, ShieldAlert, CheckCircle2, Clock, Sparkles, LayoutDashboard, CloudRain } from "lucide-react";

export default function Navbar({ activeAnomaliesCount = 0, activeTab = "dashboard", onSelectTab }) {
  const [timeStr, setTimeStr] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeStr(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header style={{
      height: "64px",
      backgroundColor: "#1c1c22",
      borderBottom: "1px solid #2c2c36",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "0 24px"
    }}>
      {/* Brand Title */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <div style={{
          backgroundColor: "rgba(59, 130, 246, 0.14)",
          color: "#3b82f6",
          padding: "8px",
          borderRadius: "8px",
          display: "flex"
        }}>
          <Activity size={22} />
        </div>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ fontSize: "17px", fontWeight: "700", letterSpacing: "0.5px", color: "#e8e8ea" }}>
              AETHERIX SENTINEL
            </h1>
            <span style={{
              fontSize: "11px",
              padding: "2px 8px",
              borderRadius: "12px",
              backgroundColor: "rgba(59, 130, 246, 0.12)",
              color: "#3b82f6",
              fontWeight: "600",
              border: "1px solid rgba(59, 130, 246, 0.3)"
            }}>
              Phases 1-3 Verified | SIH PS-26073
            </span>
          </div>
          <p style={{ fontSize: "12px", color: "#9c9ca4" }}>
            AWS Anomaly Detection, Self-Healing & Health Scoring Platform
          </p>
        </div>
      </div>



      {/* System Status Indicators */}
      <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
        {/* Status Pill */}
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          padding: "6px 14px",
          borderRadius: "20px",
          backgroundColor: activeAnomaliesCount > 0 ? "rgba(184, 92, 92, 0.15)" : "rgba(107, 158, 120, 0.15)",
          border: `1px solid ${activeAnomaliesCount > 0 ? "rgba(184, 92, 92, 0.35)" : "rgba(107, 158, 120, 0.35)"}`,
          color: activeAnomaliesCount > 0 ? "#b85c5c" : "#6b9e78",
          fontSize: "12px",
          fontWeight: "600"
        }}>
          {activeAnomaliesCount > 0 ? (
            <>
              <ShieldAlert size={15} />
              <span>{activeAnomaliesCount} STATIONS WITH ACTIVE ANOMALIES</span>
            </>
          ) : (
            <>
              <CheckCircle2 size={15} />
              <span>ALL 12 STATIONS NORMAL</span>
            </>
          )}
        </div>

        {/* Live Clock */}
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: "6px",
          fontSize: "12px",
          color: "#9c9ca4",
          fontFamily: "monospace"
        }}>
          <Clock size={14} />
          <span>{timeStr}</span>
        </div>
      </div>
    </header>
  );
}
