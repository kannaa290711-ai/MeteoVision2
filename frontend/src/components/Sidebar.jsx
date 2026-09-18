import React, { useState } from "react";
import {
  LayoutDashboard, Map, Radio, AlertTriangle, HeartPulse, BarChart3,
  GitCompare, CloudRain, ShieldAlert, Bot, Wrench, Activity, Settings,
  ChevronLeft, ChevronRight, Menu, X, Sparkles
} from "lucide-react";

export default function Sidebar({ activeTab, onSelectTab, isDemoActive, onToggleDemo }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const menuItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "map", label: "AWS Live Map", icon: Map },
    { id: "stations", label: "AWS Stations", icon: Radio },
    { id: "anomalies", label: "Anomaly Detection", icon: AlertTriangle },
    { id: "sensor-health", label: "Sensor Health", icon: HeartPulse },
    { id: "analytics", label: "Historical Analytics", icon: BarChart3 },
    { id: "nearby-analysis", label: "Nearby Comparison", icon: GitCompare },
    { id: "weather-risk", label: "Weather Risk", icon: CloudRain },
    { id: "alerts-center", label: "Disaster Alert Center", icon: ShieldAlert },
    { id: "ai-bot", label: "MeteoVision AI Bot", icon: Bot },
    { id: "maintenance", label: "Maintenance & Spares", icon: Wrench },
    { id: "metrics", label: "Model Performance", icon: Activity },
    { id: "settings-demo", label: "SIH Demo & Settings", icon: Settings },
  ];

  const handleSelect = (id) => {
    onSelectTab(id);
    setMobileOpen(false);
  };

  return (
    <>
      {/* Mobile Hamburger Toggle */}
      <div style={{
        display: "none",
        position: "fixed",
        top: "14px",
        left: "14px",
        zIndex: 3000,
        backgroundColor: "#1c1c22",
        border: "1px solid #2c2c36",
        borderRadius: "6px",
        padding: "8px",
        color: "#e8e8ea",
        cursor: "pointer"
      }} className="mobile-hamburger-btn" onClick={() => setMobileOpen(!mobileOpen)}>
        {mobileOpen ? <X size={20} /> : <Menu size={20} />}
      </div>

      {/* Main Left Sidebar */}
      <aside style={{
        width: collapsed ? "68px" : "240px",
        height: "100vh",
        backgroundColor: "#1c1c22",
        borderRight: "1px solid #2c2c36",
        display: "flex",
        flexDirection: "column",
        transition: "width 0.2s ease-in-out",
        zIndex: 2500,
        position: "relative",
        flexShrink: 0
      }} className={`sidebar-container ${mobileOpen ? "mobile-open" : ""}`}>

        {/* Sidebar Header Brand */}
        <div style={{
          height: "64px",
          display: "flex",
          alignItems: "center",
          justifyContent: collapsed ? "center" : "space-between",
          padding: collapsed ? "0" : "0 16px",
          borderBottom: "1px solid #2c2c36"
        }}>
          {!collapsed && (
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <div style={{
                width: "32px",
                height: "32px",
                borderRadius: "8px",
                backgroundColor: "rgba(59, 130, 246, 0.15)",
                color: "#3b82f6",
                display: "flex",
                alignItems: "center",
                justifyContent: "center"
              }}>
                <Radio size={18} />
              </div>
              <div>
                <h1 style={{ fontSize: "15px", fontWeight: "800", color: "#e8e8ea", margin: 0, letterSpacing: "0.5px" }}>
                  METEO<span style={{ color: "#3b82f6" }}>VISION</span>
                </h1>
                <span style={{ fontSize: "10px", color: "#6b9e78", fontWeight: "700" }}>
                  SIH 2026 | PS 26073
                </span>
              </div>
            </div>
          )}
          {collapsed && (
            <div style={{
              width: "32px",
              height: "32px",
              borderRadius: "8px",
              backgroundColor: "rgba(59, 130, 246, 0.15)",
              color: "#3b82f6",
              display: "flex",
              alignItems: "center",
              justifyContent: "center"
            }}>
              <Radio size={18} />
            </div>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            style={{
              backgroundColor: "#141419",
              border: "1px solid #2c2c36",
              color: "#9c9ca4",
              borderRadius: "6px",
              padding: "4px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center"
            }}
            title={collapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          >
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>

        {/* SIH Demo Mode Trigger Button */}
        <div style={{ padding: collapsed ? "8px 4px" : "10px 12px", borderBottom: "1px solid #2c2c36" }}>
          <button
            onClick={onToggleDemo}
            style={{
              width: "100%",
              padding: collapsed ? "8px 0" : "8px 12px",
              backgroundColor: isDemoActive ? "rgba(184, 92, 92, 0.2)" : "rgba(59, 130, 246, 0.15)",
              color: isDemoActive ? "#f87171" : "#3b82f6",
              border: `1px solid ${isDemoActive ? "rgba(184, 92, 92, 0.4)" : "rgba(59, 130, 246, 0.3)"}`,
              borderRadius: "6px",
              fontSize: "11px",
              fontWeight: "700",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: collapsed ? "center" : "flex-start",
              gap: "8px"
            }}
          >
            <Sparkles size={15} />
            {!collapsed && <span>{isDemoActive ? "EXIT SIH DEMO MODE" : "SIH PRESENTATION DEMO"}</span>}
          </button>
        </div>

        {/* Navigation Item List */}
        <nav style={{ flex: 1, overflowY: "auto", padding: "10px 8px", display: "flex", flexDirection: "column", gap: "4px" }}>
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleSelect(item.id)}
                style={{
                  width: "100%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: collapsed ? "center" : "flex-start",
                  gap: "10px",
                  padding: collapsed ? "10px 0" : "9px 12px",
                  backgroundColor: isActive ? "#3b82f6" : "transparent",
                  color: isActive ? "#ffffff" : "#9c9ca4",
                  border: "none",
                  borderRadius: "6px",
                  cursor: "pointer",
                  fontSize: "12px",
                  fontWeight: isActive ? "700" : "500",
                  transition: "all 0.15s ease-in-out",
                  textAlign: "left"
                }}
                title={collapsed ? item.label : undefined}
              >
                <Icon size={17} color={isActive ? "#ffffff" : (item.id === "alerts-center" ? "#b85c5c" : (item.id === "ai-bot" ? "#a855f7" : "#9c9ca4"))} />
                {!collapsed && <span>{item.label}</span>}
              </button>
            );
          })}
        </nav>

        {/* Sidebar Footer Data Transparency Badge */}
        {!collapsed && (
          <div style={{
            padding: "12px",
            borderTop: "1px solid #2c2c36",
            backgroundColor: "#141419",
            fontSize: "10px",
            color: "#6c6c74"
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#6b9e78", fontWeight: "700" }}>
              <span style={{ width: "6px", height: "6px", borderRadius: "50%", backgroundColor: "#6b9e78" }}></span>
              SYSTEM ONLINE
            </div>
            <div style={{ marginTop: "4px" }}>
              12 AWS Monitored | 155,520 Records
            </div>
          </div>
        )}
      </aside>
    </>
  );
}
