import React from "react";
import { TrendingUp, Globe, Smartphone, ShieldCheck, Sparkles, CheckCircle } from "lucide-react";

export default function FutureVisionView() {
  return (
    <div style={{
      padding: "20px 24px",
      backgroundColor: "#141419",
      color: "#e8e8ea",
      minHeight: "calc(100vh - 64px)",
      display: "flex",
      flexDirection: "column",
      gap: "20px"
    }}>
      {/* Hero Header */}
      <div style={{
        backgroundColor: "#1c1c22",
        border: "1px solid #2c2c36",
        borderRadius: "10px",
        padding: "20px 24px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center"
      }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
            <span style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "3px 10px",
              borderRadius: "16px",
              backgroundColor: "rgba(217, 142, 74, 0.14)",
              color: "#d98e4a",
              fontSize: "11px",
              fontWeight: "700",
              border: "1px solid rgba(217, 142, 74, 0.3)"
            }}>
              <Sparkles size={13} /> PHASE 4 & BEYOND ROADMAP
            </span>
            <span style={{ fontSize: "11px", color: "#6c6c74" }}>| SIH Problem Statement 26073 Vision</span>
          </div>
          <h1 style={{ fontSize: "22px", fontWeight: "700", letterSpacing: "0.5px", color: "#e8e8ea" }}>
            AETHERIX SENTINEL — Technical Roadmap & Strategic Vision
          </h1>
          <p style={{ fontSize: "13px", color: "#9c9ca4", marginTop: "4px", maxWidth: "820px", lineHeight: "1.5" }}>
            Scaling from AWS Quality Control to National Climate Data Infrastructure, Satellite Fusion, and Predictive Atmospheric Intelligence.
          </p>
        </div>

        <div style={{
          backgroundColor: "#141419",
          padding: "12px 18px",
          borderRadius: "8px",
          border: "1px solid #2c2c36",
          textAlign: "right"
        }}>
          <div style={{ fontSize: "11px", color: "#6c6c74", fontWeight: "600", textTransform: "uppercase" }}>Architecture Status</div>
          <div style={{ fontSize: "14px", fontWeight: "700", color: "#6b9e78", marginTop: "2px", display: "flex", alignItems: "center", gap: "6px", justifyContent: "flex-end" }}>
            <CheckCircle size={15} /> Phases 1-3 Verified
          </div>
        </div>
      </div>

      {/* 4 Strategic Pillar Cards Grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: "16px"
      }}>
        {/* Pillar 1: Predictive Forecasting */}
        <div style={{
          backgroundColor: "#1c1c22",
          border: "1px solid #2c2c36",
          borderTop: "3px solid #d98e4a",
          borderRadius: "10px",
          padding: "18px",
          display: "flex",
          flexDirection: "column",
          gap: "12px"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{ padding: "8px", backgroundColor: "rgba(217, 142, 74, 0.14)", color: "#d98e4a", borderRadius: "6px", display: "flex" }}>
              <TrendingUp size={20} />
            </div>
            <div>
              <h3 style={{ fontSize: "15px", fontWeight: "700", color: "#e8e8ea" }}>1. Predictive Intelligence & Failure Forecasting</h3>
              <span style={{ fontSize: "11px", color: "#9c9ca4" }}>Solving "Garbage In, Garbage Out" in Weather ML</span>
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "12px", color: "#9c9ca4", lineHeight: "1.5" }}>
            <div style={{ backgroundColor: "#141419", padding: "10px 12px", borderRadius: "6px", border: "1px solid #2c2c36" }}>
              <strong style={{ color: "#d98e4a", display: "block", marginBottom: "3px" }}>Near-Term Weather Forecasting (1–6 Hours):</strong>
              Uses cleaned, trust-scored telemetry as input to LSTM and Prophet sequence models — eliminating forecast distortion caused by undetected raw sensor anomalies.
            </div>

            <div style={{ backgroundColor: "#141419", padding: "10px 12px", borderRadius: "6px", border: "1px solid #2c2c36" }}>
              <strong style={{ color: "#d98e4a", display: "block", marginBottom: "3px" }}>Predictive Hardware Degradation:</strong>
              Extrapolates 30-day health score trends to flag sensors likely to fail before catastrophic lockup or drift occurs.
            </div>
          </div>
        </div>

        {/* Pillar 2: National Scale Deployment */}
        <div style={{
          backgroundColor: "#1c1c22",
          border: "1px solid #2c2c36",
          borderTop: "3px solid #c9a85b",
          borderRadius: "10px",
          padding: "18px",
          display: "flex",
          flexDirection: "column",
          gap: "12px"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{ padding: "8px", backgroundColor: "rgba(201, 168, 91, 0.14)", color: "#c9a85b", borderRadius: "6px", display: "flex" }}>
              <Globe size={20} />
            </div>
            <div>
              <h3 style={{ fontSize: "15px", fontWeight: "700", color: "#e8e8ea" }}>2. National-Scale Network Integration</h3>
              <span style={{ fontSize: "11px", color: "#9c9ca4" }}>IMD, ISRO & Regional Hub Architecture</span>
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "12px", color: "#9c9ca4", lineHeight: "1.5" }}>
            <div style={{ backgroundColor: "#141419", padding: "10px 12px", borderRadius: "6px", border: "1px solid #2c2c36" }}>
              <strong style={{ color: "#c9a85b", display: "block", marginBottom: "3px" }}>Multi-Source Verification (IMD & ISRO INSAT-3D):</strong>
              Cross-checks AWS ground telemetry with ISRO INSAT-3D/3DR satellite imagery and IMD radar grids for multi-layer synoptic verification.
            </div>

            <div style={{ backgroundColor: "#141419", padding: "10px 12px", borderRadius: "6px", border: "1px solid #2c2c36" }}>
              <strong style={{ color: "#c9a85b", display: "block", marginBottom: "3px" }}>Federated Hub & Spoke & Edge IoT:</strong>
              Allows State Agricultural Universities & regional centers to run local detection hubs, with low-power LoRaWAN/NB-IoT micro-controllers processing anomalies on remote mountain nodes.
            </div>
          </div>
        </div>

        {/* Pillar 3: Accessibility & Reach */}
        <div style={{
          backgroundColor: "#1c1c22",
          border: "1px solid #2c2c36",
          borderTop: "3px solid #c97b4a",
          borderRadius: "10px",
          padding: "18px",
          display: "flex",
          flexDirection: "column",
          gap: "12px"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{ padding: "8px", backgroundColor: "rgba(201, 123, 74, 0.14)", color: "#c97b4a", borderRadius: "6px", display: "flex" }}>
              <Smartphone size={20} />
            </div>
            <div>
              <h3 style={{ fontSize: "15px", fontWeight: "700", color: "#e8e8ea" }}>3. Accessibility & Grassroots Reach</h3>
              <span style={{ fontSize: "11px", color: "#9c9ca4" }}>Field Technician Dispatches & Multi-Lingual XAI</span>
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "12px", color: "#9c9ca4", lineHeight: "1.5" }}>
            <div style={{ backgroundColor: "#141419", padding: "10px 12px", borderRadius: "6px", border: "1px solid #2c2c36" }}>
              <strong style={{ color: "#c97b4a", display: "block", marginBottom: "3px" }}>SMS & WhatsApp Technician Dispatch:</strong>
              Dispatches automated fault alerts directly to field crews without requiring smartphone app or desktop dashboard access.
            </div>

            <div style={{ backgroundColor: "#141419", padding: "10px 12px", borderRadius: "6px", border: "1px solid #2c2c36" }}>
              <strong style={{ color: "#c97b4a", display: "block", marginBottom: "3px" }}>Multi-Language Regional XAI:</strong>
              Native translation of XAI explanations into Marathi, Hindi, Tamil, and regional languages — achieved seamlessly because narratives are template-based.
            </div>
          </div>
        </div>

        {/* Pillar 4: Real-World Policy & Impact */}
        <div style={{
          backgroundColor: "#1c1c22",
          border: "1px solid #2c2c36",
          borderTop: "3px solid #6b9e78",
          borderRadius: "10px",
          padding: "18px",
          display: "flex",
          flexDirection: "column",
          gap: "12px"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{ padding: "8px", backgroundColor: "rgba(107, 158, 120, 0.14)", color: "#6b9e78", borderRadius: "6px", display: "flex" }}>
              <ShieldCheck size={20} />
            </div>
            <div>
              <h3 style={{ fontSize: "15px", fontWeight: "700", color: "#e8e8ea" }}>4. Real-World Economic & Policy Impact</h3>
              <span style={{ fontSize: "11px", color: "#9c9ca4" }}>Parametric Crop Insurance & Open Public Infrastructure</span>
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "12px", color: "#9c9ca4", lineHeight: "1.5" }}>
            <div style={{ backgroundColor: "#141419", padding: "10px 12px", borderRadius: "6px", border: "1px solid #2c2c36" }}>
              <strong style={{ color: "#6b9e78", display: "block", marginBottom: "3px" }}>PMFBY Crop Insurance & Disaster Triggers:</strong>
              Provides disputable-proof, lineage-tracked weather evidence to settle Pradhan Mantri Fasal Bima Yojana (PMFBY) agricultural claims fairly.
            </div>

            <div style={{ backgroundColor: "#141419", padding: "10px 12px", borderRadius: "6px", border: "1px solid #2c2c36" }}>
              <strong style={{ color: "#6b9e78", display: "block", marginBottom: "3px" }}>Open Climate Research API Infrastructure:</strong>
              Exposes public REST APIs for climate researchers, universities, and agtech startups to consume verified, cleaned meteorological data.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
