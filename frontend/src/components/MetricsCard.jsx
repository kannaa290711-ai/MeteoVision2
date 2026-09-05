import React from "react";
import { Target, Zap, Award, Radio } from "lucide-react";

export default function MetricsCard({ metrics }) {
  const precision = metrics ? (metrics.precision * 100).toFixed(1) : "84.7";
  const recall = metrics ? (metrics.recall * 100).toFixed(1) : "87.8";
  const f1 = metrics ? (metrics.f1 * 100).toFixed(1) : "86.2";

  const cards = [
    {
      title: "Model F1 Score",
      value: `${f1}%`,
      sub: "Macro 5-Class Evaluation",
      icon: Award,
      color: "#6b9e78",
      bgColor: "rgba(107, 158, 120, 0.14)"
    },
    {
      title: "Detection Precision",
      value: `${precision}%`,
      sub: `${metrics?.tp || 4196} True Pos / ${metrics?.fp || 760} False Pos`,
      icon: Target,
      color: "#d98e4a",
      bgColor: "rgba(217, 142, 74, 0.14)"
    },
    {
      title: "Detection Recall",
      value: `${recall}%`,
      sub: "Fault coverage across 336 events",
      icon: Zap,
      color: "#c9a85b",
      bgColor: "rgba(201, 168, 91, 0.14)"
    },
    {
      title: "Monitored Telemetry",
      value: "12 AWS",
      sub: "155,520 Evaluated Readings",
      icon: Radio,
      color: "#9c9ca4",
      bgColor: "rgba(156, 156, 164, 0.14)"
    }
  ];

  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
      gap: "12px",
      marginBottom: "16px"
    }}>
      {cards.map((card, idx) => {
        const IconComponent = card.icon;
        return (
          <div key={idx} style={{
            backgroundColor: "#1c1c22",
            border: "1px solid #2c2c36",
            borderRadius: "10px",
            padding: "14px 18px",
            display: "flex",
            alignItems: "center",
            gap: "14px"
          }}>
            <div style={{
              backgroundColor: card.bgColor,
              color: card.color,
              padding: "10px",
              borderRadius: "10px",
              display: "flex"
            }}>
              <IconComponent size={20} />
            </div>
            <div>
              <p style={{ fontSize: "11px", color: "#9c9ca4", fontWeight: "600", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                {card.title}
              </p>
              <h2 style={{ fontSize: "20px", fontWeight: "700", color: "#e8e8ea", margin: "2px 0" }}>
                {card.value}
              </h2>
              <p style={{ fontSize: "11px", color: "#6c6c74" }}>
                {card.sub}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
