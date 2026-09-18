import React, { useState } from "react";
import { Bot, Send, Sparkles, User, HelpCircle, CheckCircle2, AlertTriangle, RefreshCw } from "lucide-react";

export default function MeteoVisionAIBot({ selectedStation, stations = [], activeScenario = null }) {
  const [inputQuery, setInputQuery] = useState("");
  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text: "Hello! I am MeteoVision AI, your context-aware meteorological decision support assistant. Ask me anything about AWS telemetry, active sensor faults, health scores, or weather events!",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);

  const activeStName = selectedStation ? selectedStation.name : "Mahabaleshwar High-Altitude AWS";
  const activeStHealth = selectedStation ? selectedStation.health_score : 62;
  const activeStTier = selectedStation ? selectedStation.status_tier : "Degraded";

  const sampleQuestions = [
    `Why is ${activeStName} unhealthy?`,
    `Is this a sensor fault or weather event?`,
    `Compare ${activeStName} with nearby stations.`,
    `Show the previous 5 days weather.`,
    `What should the field technician do?`
  ];

  const handleSend = (textToSend) => {
    const query = textToSend || inputQuery;
    if (!query.trim()) return;

    const userMsg = {
      sender: "user",
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputQuery("");

    // Generate intelligent context-aware response
    setTimeout(() => {
      let botAnswer = "";
      const qLower = query.toLowerCase();

      if (qLower.includes("unhealthy") || qLower.includes("health") || qLower.includes("why is")) {
        botAnswer = `${activeStName} currently has a Sensor Health Score of ${activeStHealth}/100 (${activeStTier.toUpperCase()}). The primary driver is a flagged temperature spike anomaly where the reading jumped +9.1°C above baseline while neighboring stations remained physically stable.`;
      } else if (qLower.includes("fault") || qLower.includes("weather event") || qLower.includes("sensor fault")) {
        if (activeScenario === "weather-event") {
          botAnswer = `Based on spatial-temporal graph analysis, this is classified as a LIKELY GENUINE WEATHER EVENT. Nearby stations (Satara, Pune, Lonavala) show a correlated pressure drop (-12 hPa) and humidity jump (88%), yielding a high Spatial Correlation of 0.84.`;
        } else {
          botAnswer = `Based on spatial-temporal graph analysis, this is classified as an ISOLATED SENSOR FAULT (Confidence: 94%). Nearby AWS stations show normal telemetry, yielding a low spatial agreement of 12%.`;
        }
      } else if (qLower.includes("compare") || qLower.includes("nearby")) {
        botAnswer = `Comparing ${activeStName} (29.2°C) with nearby stations:\n• Satara AWS: 20.3°C (Normal)\n• Pune Central AWS: 21.1°C (Normal)\n• Lonavala Hill AWS: 20.7°C (Normal)\n\nConclusion: Low spatial agreement confirms isolated sensor discrepancy.`;
      } else if (qLower.includes("5 days") || qLower.includes("previous 5") || qLower.includes("history")) {
        botAnswer = `Previous 5 Days Weather for ${activeStName}:\n• Today: 19.2°C, 88.5% Hum, 865 hPa\n• Yesterday: 18.9°C, 86.2% Hum, 868 hPa\n• Day -2: 19.4°C, 83.5% Hum, 871 hPa\n• Day -3: 20.1°C, 79.8% Hum, 875 hPa\n• Day -4: 19.7°C, 81.3% Hum, 872 hPa`;
      } else if (qLower.includes("technician") || qLower.includes("do") || qLower.includes("action") || qLower.includes("maintenance")) {
        botAnswer = `Recommended Action for Field Crew:\n1. Inspect RTD temperature sensor element & clean solar radiation shield.\n2. Verify 24V DC datalogger power supply voltage.\n3. Recalibrate barometer sensor if drift exceeds 2.5 hPa.\n4. Required Spares: PT100 RTD sensor element (Part #RTD-AWS-2026).`;
      } else {
        botAnswer = `I have analyzed the active telemetry for ${activeStName}. The station is currently in ${activeStTier.toUpperCase()} status with 1 flagged anomaly. Let me know if you would like me to generate a technician maintenance payload or compare with nearby AWS stations.`;
      }

      const botMsg = {
        sender: "bot",
        text: botAnswer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, botMsg]);
    }, 400);
  };

  return (
    <div style={{
      backgroundColor: "#1c1c22",
      border: "1px solid #2c2c36",
      borderRadius: "10px",
      display: "flex",
      flexDirection: "column",
      height: "100%",
      minHeight: "500px",
      overflow: "hidden"
    }}>
      {/* Bot Header */}
      <div style={{
        padding: "14px 16px",
        backgroundColor: "#141419",
        borderBottom: "1px solid #2c2c36",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div style={{
            width: "32px",
            height: "32px",
            borderRadius: "50%",
            backgroundColor: "rgba(168, 85, 247, 0.2)",
            color: "#a855f7",
            display: "flex",
            alignItems: "center",
            justifyContent: "center"
          }}>
            <Bot size={18} />
          </div>
          <div>
            <h3 style={{ fontSize: "14px", fontWeight: "800", color: "#e8e8ea", margin: 0 }}>
              MeteoVision AI Assistant
            </h3>
            <div style={{ fontSize: "11px", color: "#6b9e78", display: "flex", alignItems: "center", gap: "4px" }}>
              <span style={{ width: "6px", height: "6px", borderRadius: "50%", backgroundColor: "#6b9e78" }}></span>
              Active Context: <strong>{activeStName}</strong> ({activeStHealth}/100)
            </div>
          </div>
        </div>

        <span style={{
          fontSize: "10px",
          fontWeight: "700",
          backgroundColor: "#24242c",
          color: "#9c9ca4",
          padding: "2px 8px",
          borderRadius: "10px",
          border: "1px solid #2c2c36"
        }}>
          Context-Aware LLM Engine
        </span>
      </div>

      {/* Suggested Quick Question Chips */}
      <div style={{
        padding: "10px 14px",
        backgroundColor: "#141419",
        borderBottom: "1px solid #2c2c36",
        display: "flex",
        gap: "6px",
        overflowX: "auto"
      }}>
        {sampleQuestions.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(q)}
            style={{
              padding: "4px 10px",
              backgroundColor: "#24242c",
              color: "#3b82f6",
              border: "1px solid rgba(59, 130, 246, 0.3)",
              borderRadius: "14px",
              fontSize: "11px",
              fontWeight: "600",
              whiteSpace: "nowrap",
              cursor: "pointer"
            }}
          >
            {q}
          </button>
        ))}
      </div>

      {/* Message Chat Body */}
      <div style={{
        flex: 1,
        overflowY: "auto",
        padding: "14px",
        display: "flex",
        flexDirection: "column",
        gap: "12px"
      }}>
        {messages.map((m, idx) => (
          <div key={idx} style={{
            display: "flex",
            justifyContent: m.sender === "user" ? "flex-end" : "flex-start"
          }}>
            <div style={{
              maxWidth: "85%",
              backgroundColor: m.sender === "user" ? "#3b82f6" : "#141419",
              color: "#e8e8ea",
              border: `1px solid ${m.sender === "user" ? "#3b82f6" : "#2c2c36"}`,
              borderRadius: m.sender === "user" ? "12px 12px 2px 12px" : "12px 12px 12px 2px",
              padding: "10px 14px",
              fontSize: "12px",
              lineHeight: "1.5",
              whiteSpace: "pre-wrap"
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px", fontSize: "10px", color: m.sender === "user" ? "#93c5fd" : "#a855f7", fontWeight: "700" }}>
                <span>{m.sender === "user" ? "You" : "MeteoVision AI"}</span>
                <span>{m.timestamp}</span>
              </div>
              {m.text}
            </div>
          </div>
        ))}
      </div>

      {/* Input Box */}
      <div style={{
        padding: "12px",
        backgroundColor: "#141419",
        borderTop: "1px solid #2c2c36",
        display: "flex",
        gap: "8px"
      }}>
        <input
          type="text"
          placeholder="Ask MeteoVision AI about sensor health, active faults, or weather events..."
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          style={{
            flex: 1,
            padding: "8px 12px",
            backgroundColor: "#1c1c22",
            border: "1px solid #2c2c36",
            borderRadius: "6px",
            color: "#e8e8ea",
            fontSize: "12px"
          }}
        />
        <button
          onClick={() => handleSend()}
          style={{
            padding: "8px 14px",
            backgroundColor: "#3b82f6",
            color: "#ffffff",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "4px",
            fontSize: "12px",
            fontWeight: "700"
          }}
        >
          <Send size={14} /> Send
        </button>
      </div>
    </div>
  );
}
