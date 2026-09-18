import React, { useState } from "react";
import { ShieldAlert, AlertCircle, Wind, CloudRain, Flame, Radio, CheckCircle2, Info, BellRing, Sparkles } from "lucide-react";

export default function DisasterAlertCenter({ stations = [] }) {
  const [filterType, setFilterType] = useState("ALL");

  const alertsList = [
    {
      id: "cyclone-01",
      type: "CYCLONE",
      title: "🌪️ POTENTIAL CYCLONIC DEPRESSION ALERT",
      region: "Coastal Maharashtra & Konkan Belt",
      riskLevel: "HIGH",
      riskScore: 82,
      isSimulated: true,
      affectedStations: ["AWS_003 (Mumbai)", "AWS_009 (Ratnagiri)"],
      evidence: [
        "Rapid barometric pressure fall (-14.2 hPa / 3 hours)",
        "Sustained wind speed acceleration (> 64 km/h)",
        "Relative humidity jump to 98% across coastal stations",
        "Synoptic front confirmed by ISRO INSAT-3D thermal infrared concordance"
      ],
      recommendedAction: "Increase observation frequency to 5-minute telemetry intervals and verify IMD synoptic warning feeds."
    },
    {
      id: "flood-02",
      type: "FLOOD",
      title: "🌊 HEAVY MONSOON DELUGE & FLOOD RISK",
      region: "Mahabaleshwar High-Altitude Catchment",
      riskLevel: "HIGH",
      riskScore: 88,
      isSimulated: true,
      affectedStations: ["AWS_002 (Mahabaleshwar)", "AWS_005 (Satara)"],
      evidence: [
        "Precipitation accumulation exceeded 145 mm in trailing 24 hours",
        "Sustained 100% relative humidity with low cloud-top temperature",
        "Neighboring valley stations (Satara, Pune) showing correlated runoff increase"
      ],
      recommendedAction: "Notify local district disaster management authority and field hydraulic gauge operators."
    },
    {
      id: "heat-03",
      type: "HEATWAVE",
      title: "🔥 EXTREME HEATWAVE WARNING",
      region: "Solapur & Marathwada Semi-Arid Zone",
      riskLevel: "MODERATE",
      riskScore: 76,
      isSimulated: true,
      affectedStations: ["AWS_007 (Solapur)", "AWS_008 (Aurangabad)"],
      evidence: [
        "Ambient temperature sustained > 42.5°C over 6 consecutive hours",
        "Relative humidity dropped below 22% causing extreme vapor pressure deficit",
        "No spatial discrepancy detected among neighbor AWS cluster"
      ],
      recommendedAction: "Issue agricultural advisory for crop irrigation and heat exposure warnings."
    },
    {
      id: "wind-04",
      type: "WIND",
      title: "💨 SEVERE THUNDERSTORM & WIND GUST ALERT",
      region: "Pune & Lonavala Plateau",
      riskLevel: "MODERATE",
      riskScore: 71,
      isSimulated: true,
      affectedStations: ["AWS_001 (Pune)", "AWS_012 (Lonavala)"],
      evidence: [
        "Peak wind gusts recorded at 78 km/h during squall passage",
        "Rapid temperature drop (-6.8°C / 15 min) indicative of cold pool downdraft"
      ],
      recommendedAction: "Verify AWS anemometer mechanical integrity and check wind mast guy wire tension."
    }
  ];

  const filteredAlerts = filterType === "ALL" ? alertsList : alertsList.filter(a => a.type === filterType);

  const handleSimulateDispatch = (alertItem) => {
    alert(`DISASTER ALERT DISPATCH SIMULATED:\n\nAlert: ${alertItem.title}\nRegion: ${alertItem.region}\nRisk Score: ${alertItem.riskScore}/100\nAction: ${alertItem.recommendedAction}\n\nBroadcast sent to regional emergency control center!`);
  };

  return (
    <div style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px", color: "#e8e8ea" }}>
      {/* Page Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <h2 style={{ fontSize: "20px", fontWeight: "800", color: "#e8e8ea", margin: 0, display: "flex", alignItems: "center", gap: "8px" }}>
            <ShieldAlert size={22} color="#b85c5c" /> WEATHER & NATURAL DISASTER ALERT CENTER
          </h2>
          <p style={{ fontSize: "12px", color: "#9c9ca4", margin: "4px 0 0 0" }}>
            Real-time multi-AWS synoptic hazard monitoring for Cyclones, Monsoon Floods, Heatwaves, and Severe Squalls.
          </p>
        </div>

        {/* Filter Chips */}
        <div style={{ display: "flex", gap: "6px" }}>
          {["ALL", "CYCLONE", "FLOOD", "HEATWAVE", "WIND"].map((type) => (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              style={{
                padding: "6px 12px",
                fontSize: "11px",
                fontWeight: "700",
                backgroundColor: filterType === type ? "#3b82f6" : "#1c1c22",
                color: filterType === type ? "#ffffff" : "#9c9ca4",
                border: "1px solid #2c2c36",
                borderRadius: "6px",
                cursor: "pointer"
              }}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Alert Feed Cards */}
      <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
        {filteredAlerts.map((alertItem) => (
          <div key={alertItem.id} style={{
            backgroundColor: "#1c1c22",
            border: "1px solid #2c2c36",
            borderLeft: `4px solid ${alertItem.riskScore > 80 ? "#b85c5c" : "#c97b4a"}`,
            borderRadius: "8px",
            padding: "16px"
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <h3 style={{ fontSize: "15px", fontWeight: "800", color: "#e8e8ea", margin: 0 }}>
                    {alertItem.title}
                  </h3>
                  {alertItem.isSimulated && (
                    <span style={{
                      fontSize: "10px",
                      fontWeight: "700",
                      backgroundColor: "rgba(168, 85, 247, 0.2)",
                      color: "#a855f7",
                      padding: "2px 8px",
                      borderRadius: "10px",
                      border: "1px solid rgba(168, 85, 247, 0.4)"
                    }}>
                      DEMO ALERT — SIMULATED
                    </span>
                  )}
                </div>
                <div style={{ fontSize: "12px", color: "#9c9ca4", marginTop: "4px" }}>
                  Region: <strong style={{ color: "#e8e8ea" }}>{alertItem.region}</strong> | Affected AWS: <strong style={{ color: "#3b82f6" }}>{alertItem.affectedStations.join(", ")}</strong>
                </div>
              </div>

              <div style={{
                backgroundColor: alertItem.riskScore > 80 ? "rgba(184, 92, 92, 0.2)" : "rgba(201, 123, 74, 0.2)",
                color: alertItem.riskScore > 80 ? "#f87171" : "#fb923c",
                border: `1px solid ${alertItem.riskScore > 80 ? "rgba(184, 92, 92, 0.4)" : "rgba(201, 123, 74, 0.4)"}`,
                padding: "6px 14px",
                borderRadius: "8px",
                textAlign: "center"
              }}>
                <div style={{ fontSize: "10px", fontWeight: "700" }}>RISK SCORE</div>
                <div style={{ fontSize: "18px", fontWeight: "900" }}>{alertItem.riskScore} / 100</div>
              </div>
            </div>

            {/* Evidence Checklist */}
            <div style={{
              backgroundColor: "#141419",
              border: "1px solid #2c2c36",
              borderRadius: "6px",
              padding: "10px 12px",
              marginBottom: "12px"
            }}>
              <div style={{ fontSize: "11px", fontWeight: "700", color: "#6b9e78", marginBottom: "6px", display: "flex", alignItems: "center", gap: "5px" }}>
                <CheckCircle2 size={13} color="#6b9e78" /> Multi-AWS Correlated Evidence:
              </div>
              <ul style={{ margin: 0, paddingLeft: "18px", fontSize: "11px", color: "#9c9ca4", lineHeight: "1.5" }}>
                {alertItem.evidence.map((ev, idx) => (
                  <li key={idx} style={{ color: "#e8e8ea" }}>{ev}</li>
                ))}
              </ul>
            </div>

            {/* Recommended Action Footer */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
              <div style={{ fontSize: "11px", color: "#9c9ca4" }}>
                <strong style={{ color: "#3b82f6" }}>Recommended Operator Action: </strong>
                {alertItem.recommendedAction}
              </div>
              <button
                onClick={() => handleSimulateDispatch(alertItem)}
                style={{
                  padding: "6px 14px",
                  backgroundColor: "#3b82f6",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "6px",
                  fontSize: "11px",
                  fontWeight: "700",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px"
                }}
              >
                <BellRing size={13} /> Broadcast Emergency Advisory
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
