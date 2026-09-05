import React from "react";
import { MapContainer, TileLayer, Marker, Popup, Tooltip } from "react-leaflet";
import L from "leaflet";

const getTierColor = (tier) => {
  switch (tier) {
    case "Healthy": return "#6b9e78";   // Muted Sage Green
    case "Watch": return "#c9a85b";     // Muted Amber
    case "Degraded": return "#c97b4a";  // Muted Burnt Orange
    case "Critical": return "#b85c5c";  // Muted Red
    default: return "#6b9e78";
  }
};

const createCustomIcon = (statusTier, hasAnomaly) => {
  const color = getTierColor(statusTier);
  const strokeColor = hasAnomaly ? "#b85c5c" : "#ffffff";

  const svg = `
    <svg width="34" height="34" viewBox="0 0 34 34" xmlns="http://www.w3.org/2000/svg">
      <circle cx="17" cy="17" r="14" fill="${color}25" />
      <circle cx="17" cy="17" r="7" fill="${color}" stroke="${strokeColor}" stroke-width="2.5"/>
    </svg>
  `;

  return L.divIcon({
    className: "custom-map-marker",
    html: `<div style="display:flex;align-items:center;justify-content:center;">${svg}</div>`,
    iconSize: [34, 34],
    iconAnchor: [17, 17],
    popupAnchor: [0, -17],
  });
};

export default function MapView({ stations = [], selectedStationId, onSelectStation }) {
  const defaultCenter = [18.35, 73.9];
  const defaultZoom = 9;

  return (
    <div style={{
      width: "100%",
      height: "100%",
      borderRadius: "10px",
      overflow: "hidden",
      border: "1px solid #2c2c36",
      position: "relative",
      backgroundColor: "#141419"
    }}>
      <MapContainer
        center={defaultCenter}
        zoom={defaultZoom}
        style={{ width: "100%", height: "100%" }}
        zoomControl={true}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />

        {stations.map((st) => {
          const isSelected = st.station_id === selectedStationId;
          const tier = st.status_tier || "Healthy";
          const score = st.health_score ?? 100.0;
          const icon = createCustomIcon(tier, st.status === "ANOMALY");

          return (
            <Marker
              key={st.station_id}
              position={[st.lat, st.lon]}
              icon={icon}
              eventHandlers={{
                click: () => onSelectStation(st.station_id),
              }}
            >
              <Tooltip direction="top" offset={[0, -10]} opacity={0.95} permanent={isSelected}>
                <div style={{ fontWeight: "700", color: "#141419" }}>
                  {st.name} ({score} / 100)
                </div>
              </Tooltip>
              <Popup>
                <div style={{ minWidth: "220px", color: "#e8e8ea" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                    <h4 style={{ margin: 0, fontSize: "14px", color: "#e8e8ea", fontWeight: "700" }}>{st.name}</h4>
                    <span style={{
                      padding: "2px 8px",
                      borderRadius: "12px",
                      fontSize: "11px",
                      fontWeight: "700",
                      backgroundColor: `${getTierColor(tier)}20`,
                      color: getTierColor(tier),
                      border: `1px solid ${getTierColor(tier)}40`
                    }}>
                      {tier} ({score})
                    </span>
                  </div>

                  <p style={{ margin: "2px 0", fontSize: "12px", color: "#9c9ca4" }}>
                    ID: <strong>{st.station_id}</strong> | Elev: <strong>{st.elevation_m}m</strong>
                  </p>
                  
                  {st.maintenance_recommendation && (
                    <div style={{
                      marginTop: "8px",
                      padding: "6px 8px",
                      backgroundColor: "#24242c",
                      borderRadius: "6px",
                      fontSize: "11px",
                      color: "#9c9ca4",
                      borderLeft: `3px solid ${getTierColor(tier)}`
                    }}>
                      <strong style={{ color: "#e8e8ea" }}>Maintenance:</strong> {st.maintenance_recommendation}
                    </div>
                  )}

                  {st.latest_temperature && (
                    <div style={{ marginTop: "8px", fontSize: "11px", borderTop: "1px solid #2c2c36", paddingTop: "6px", color: "#9c9ca4" }}>
                      Temp: {st.latest_temperature}°C | Hum: {st.latest_humidity}% | Press: {st.latest_pressure} hPa
                    </div>
                  )}
                  
                  <button
                    onClick={() => onSelectStation(st.station_id)}
                    style={{
                      marginTop: "10px",
                      width: "100%",
                      padding: "6px",
                      backgroundColor: "#d98e4a",
                      color: "#ffffff",
                      border: "none",
                      borderRadius: "4px",
                      cursor: "pointer",
                      fontSize: "12px",
                      fontWeight: "600"
                    }}
                  >
                    View Station Analytics
                  </button>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      {/* Map Legend Overlay */}
      <div style={{
        position: "absolute",
        bottom: "16px",
        left: "16px",
        backgroundColor: "#1c1c22e6",
        backdropFilter: "blur(6px)",
        border: "1px solid #2c2c36",
        borderRadius: "8px",
        padding: "10px 14px",
        zIndex: 1000,
        fontSize: "11px",
        color: "#9c9ca4"
      }}>
        <div style={{ fontWeight: "700", marginBottom: "6px", color: "#e8e8ea", fontSize: "12px" }}>
          Sensor Health Tiers
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
          <span style={{ width: "9px", height: "9px", borderRadius: "50%", backgroundColor: "#6b9e78" }}></span>
          <span>Healthy (85 - 100)</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
          <span style={{ width: "9px", height: "9px", borderRadius: "50%", backgroundColor: "#c9a85b" }}></span>
          <span>Watch (70 - 84)</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
          <span style={{ width: "9px", height: "9px", borderRadius: "50%", backgroundColor: "#c97b4a" }}></span>
          <span>Degraded (50 - 69)</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ width: "9px", height: "9px", borderRadius: "50%", backgroundColor: "#b85c5c" }}></span>
          <span>Critical (&lt; 50)</span>
        </div>
      </div>
    </div>
  );
}
