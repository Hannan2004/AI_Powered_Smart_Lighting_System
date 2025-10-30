import React from "react";
import { MapContainer, TileLayer, Polygon, CircleMarker } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { useDashboardStore } from '@/store/useDashboardStore';

// Example static data for each service (replace with Redux or API data as needed)
const weatherZones = [
  { id: 'air', name: 'Airport', color: 'orange', positions: [[19.09, 72.86],[19.10, 72.86],[19.10, 72.88],[19.09, 72.88]] },
];
const weatherPoles = [
  { id: 1, lat: 19.095, lng: 72.87, status: 'ONLINE', brightness: 80 },
  { id: 2, lat: 19.098, lng: 72.865, status: 'OFFLINE', brightness: 0 },
];
const getPoleColor = (status, brightness) => {
  if(status === "OFFLINE") return "red";
  if(status === "MAINTENANCE") return "yellow";
  return `rgba(16, 185, 129, ${brightness / 100})`;
};

const cyberZones = [
  { id: 'downtown', name: 'Downtown', security_state: "GREEN", positions: [[19.08, 72.85],[19.085, 72.85],[19.085, 72.865],[19.08, 72.865]] },
  { id: 'midtown', name: 'Midtown', security_state: "RED", positions: [[19.09, 72.86],[19.094, 72.86],[19.094, 72.87],[19.09, 72.87]] },
];
const getStateColor = (state) => {
  if(state === "GREEN") return "green";
  if(state === "YELLOW") return "yellow";
  if(state === "RED") return "red";
  return "gray";
};

const blackoutZones = [
  { id: 'z1', name: 'Zone 1', status: 'ONLINE', positions: [[19.091, 72.881],[19.094, 72.881],[19.094, 72.886],[19.091, 72.886]] },
  { id: 'z2', name: 'Zone 2', status: 'OFFLINE', positions: [[19.089, 72.889],[19.092, 72.889],[19.092, 72.894],[19.089, 72.894]] },
];
const getPowerStateColor = (status) => {
  if(status === 'ONLINE') return 'green';
  if(status === 'OFFLINE') return 'red';
  if(status === 'WARNING') return 'yellow';
  if(status === 'CRITICAL') return 'darkred';
  return 'gray';
};

const UnifiedMap: React.FC = () => {
  const selectedAgentView = useDashboardStore((state) => state.selectedAgentView);

  let polygons = [];
  let markers = [];

  if (selectedAgentView === 'weather') {
    polygons = weatherZones.map(zone => (
      <Polygon key={zone.id} positions={zone.positions} pathOptions={{ color: zone.color, fillOpacity: 0.4 }} />
    ));
    markers = weatherPoles.map(pole => (
      <CircleMarker
        key={pole.id}
        center={[pole.lat, pole.lng]}
        radius={10}
        pathOptions={{ color: getPoleColor(pole.status, pole.brightness), fillColor: getPoleColor(pole.status, pole.brightness), fillOpacity: 0.65 }}
      />
    ));
  } else if (selectedAgentView === 'cybersecurity') {
    polygons = cyberZones.map(zone => (
      <Polygon key={zone.id} positions={zone.positions} pathOptions={{ color: getStateColor(zone.security_state), fillOpacity: 0.4 }} />
    ));
    markers = [];
  } else if (selectedAgentView === 'power') {
    polygons = blackoutZones.map(zone => (
      <Polygon key={zone.id} positions={zone.positions} pathOptions={{ color: getPowerStateColor(zone.status), fillOpacity: 0.4 }} />
    ));
    markers = [];
  }

  return (
    <div className="w-full h-[350px] rounded-xl overflow-hidden shadow-lg">
      <MapContainer center={[19.092, 72.886]} zoom={15} scrollWheelZoom={false} style={{ height: '100%', width: '100%' }}>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        {polygons}
        {markers}
      </MapContainer>
    </div>
  );
};

export default UnifiedMap;
