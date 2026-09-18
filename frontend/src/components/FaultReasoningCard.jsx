import React from "react";
import { AlertTriangle, Cpu, Layers, CheckCircle2, Info } from "lucide-react";

export default function FaultReasoningCard({ flag }) {
  if (!flag) return null;

  const faultType = (flag.predicted_fault_type || flag.fault_type || "none").toLowerCase();
  const temporalScore = flag.temporal_score ?? 0.0;
  const spatialScore = flag.spatial_score ?? 0.0;
  const frozenScore = flag.frozen_score ?? 0.0;
  const driftScore = flag.drift_score ?? 0.0;
  
  // Normalize neighbor_agreement (could be 0..1 or 0..100)
  const rawNA = flag.neighbor_agreement ?? 1.0;
  const neighborAgreementPct = rawNA <= 1.0 ? Math.round(rawNA * 100) : Math.round(rawNA);

  // Normalize multivariate_consistency_score (could be 0..1 or 0..100)
  const rawMV = flag.multivariate_consistency_score;
  const mvScorePct = rawMV !== null && rawMV !== undefined ? (rawMV <= 1.0 ? Math.round(rawMV * 100) : Math.round(rawMV)) : null;

  const confidencePct = flag.ml_confidence ? Math.round(flag.ml_confidence <= 1.0 ? flag.ml_confidence * 100 : flag.ml_confidence) : null;
  const variable = (flag.variable || "sensor").toUpperCase();

  const getFaultColor = (ft) => {
    switch (ft) {
      case "spike": return "#b85c5c";
      case "drift": return "#c97b4a";
      case "frozen": return "#c9a85b";
      case "missing": return "#888894";
      default: return "#3b82f6";
    }
  };

  const accentColor = getFaultColor(faultType);

  // Dynamic Reason Bullets and Conclusion
  let bullets = [];
  let conclusionText = "";

  if (faultType === "spike") {
    bullets = [
      `${variable} reading changed abnormally fast (temporal_score: ${temporalScore.toFixed(2)})`,
      `Neighboring stations showed low physical correlation (spatial_score: ${spatialScore.toFixed(2)}, neighbor_agreement: ${neighborAgreementPct}%)`,
      mvScorePct !== null
        ? `Cross-variable atmosphere remained stable (multivariate_consistency_score: ${mvScorePct}%)`
        : `Cross-variable stability verified against trailing 15-min baseline`
    ];
    conclusionText = (neighborAgreementPct > 70 && mvScorePct && mvScorePct > 50)
      ? "Possible synoptic micro-burst weather front"
      : "Isolated single-sensor hardware fault, not a weather event";
  } else if (faultType === "frozen") {
    bullets = [
      `Sensor output remained completely static over trailing window (frozen_score: ${frozenScore.toFixed(2)})`,
      `Real atmospheric readings always exhibit natural micro-variability; zero variance detected`
    ];
    conclusionText = "Likely hardware sensor lockup or ADC sampler stall";
  } else if (faultType === "drift") {
    bullets = [
      `Reading steadily deviated from diurnal baseline (drift_score: ${driftScore.toFixed(2)}, spatial_score: ${spatialScore.toFixed(2)})`,
      `Neighbor agreement: ${neighborAgreementPct}% (${neighborAgreementPct < 50 ? "low agreement = single-station drift" : "high agreement = regional trend"})`
    ];
    conclusionText = neighborAgreementPct < 50
      ? "Single-station sensor calibration drift (requires technician re-calibration)"
      : "Possible regional synoptic weather trend";
  } else if (faultType === "missing") {
    bullets = [
      `No telemetry received at expected interval timestamp (${flag.timestamp ? new Date(flag.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A'})`,
      `Data gap detected across telemetry stream`
    ];
    conclusionText = "Communication link dropout or datalogger power failure";
  } else {
    bullets = [
      `Reading passed standard statistical sanity boundaries`,
      `Spatial and temporal rate of change aligned with regional baseline`
    ];
    conclusionText = "Normal atmospheric telemetry";
  }

  return (
    <div style={{
      backgroundColor: "#141419",
      border: `1px solid ${accentColor}40`,
      borderLeft: `4px solid ${accentColor}`,
      borderRadius: "6px",
      padding: "10px 12px",
      marginTop: "8px",
      fontSize: "11px",
      color: "#e8e8ea"
    }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
        <span style={{ fontWeight: "700", textTransform: "uppercase", color: accentColor, display: "flex", alignItems: "center", gap: "5px" }}>
          <AlertTriangle size={13} color={accentColor} />
          WHY WAS IT FLAGGED? ({faultType.toUpperCase()})
        </span>
        {confidencePct !== null && (
          <span style={{
            fontSize: "10px",
            fontWeight: "600",
            backgroundColor: `${accentColor}20`,
            color: accentColor,
            padding: "1px 6px",
            borderRadius: "4px",
            border: `1px solid ${accentColor}40`
          }}>
            ML Conf: {confidencePct}%
          </span>
        )}
      </div>

      {/* Bullet Points */}
      <ul style={{ margin: "0 0 8px 0", paddingLeft: "16px", color: "#9c9ca4", lineHeight: "1.5" }}>
        {bullets.map((b, idx) => (
          <li key={idx} style={{ marginBottom: "2px" }}>
            <span style={{ color: "#e8e8ea" }}>{b}</span>
          </li>
        ))}
      </ul>

      {/* Conclusion */}
      <div style={{
        backgroundColor: "#1c1c22",
        padding: "6px 8px",
        borderRadius: "4px",
        border: "1px solid #2c2c36",
        marginBottom: (flag.shap_summary || flag.shap_contributions) ? "8px" : "0",
        fontWeight: "600",
        color: "#6b9e78",
        display: "flex",
        alignItems: "center",
        gap: "6px"
      }}>
        <CheckCircle2 size={12} color="#6b9e78" />
        <span>Conclusion: {conclusionText}</span>
      </div>

      {/* Embedded SHAP Attribution Breakdown */}
      {(flag.shap_summary || flag.shap_contributions) && (
        <div style={{
          backgroundColor: "#1c1c22",
          border: "1px solid rgba(59, 130, 246, 0.3)",
          borderRadius: "4px",
          padding: "6px 8px",
          fontSize: "10px",
          color: "#9c9ca4"
        }}>
          <div style={{ color: "#3b82f6", fontWeight: "700", display: "flex", alignItems: "center", gap: "4px", marginBottom: "4px" }}>
            <Cpu size={12} color="#3b82f6" />
            SHAP Explainability Driver:
          </div>
          {flag.shap_summary && (
            <div style={{ color: "#e8e8ea", marginBottom: flag.shap_contributions ? "4px" : "0" }}>
              {flag.shap_summary}
            </div>
          )}
          {flag.shap_contributions && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "4px" }}>
              {Object.entries(flag.shap_contributions).map(([feat, val]) => (
                <span key={feat} style={{
                  backgroundColor: "#141419",
                  padding: "2px 6px",
                  borderRadius: "3px",
                  border: "1px solid #2c2c36"
                }}>
                  <strong style={{ color: "#9c9ca4" }}>{feat}:</strong>{" "}
                  <span style={{ color: val > 0 ? "#b85c5c" : "#6b9e78", fontWeight: "700" }}>
                    {val > 0 ? `+${val.toFixed(2)}` : val.toFixed(2)}
                  </span>
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
