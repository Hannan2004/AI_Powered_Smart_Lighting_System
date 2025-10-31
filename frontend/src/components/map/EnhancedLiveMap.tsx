'use client';

import React, { useState, useEffect, useMemo } from 'react';
import dynamic from 'next/dynamic';
import { useDashboardStore } from '@/store/useDashboardStore';
import { generatePowerGridTopology, PowerGridTopology, updateGridState, StreetLight } from '@/utils/streetLightGenerator';
import toast from 'react-hot-toast';
import 'leaflet/dist/leaflet.css';
import { Incident } from './IncidentMarkers';

const MapContainer = dynamic(() => import('react-leaflet').then((m) => m.MapContainer), { ssr: false });
const TileLayer = dynamic(() => import('react-leaflet').then((m) => m.TileLayer), { ssr: false });
const Polygon = dynamic(() => import('react-leaflet').then((m) => m.Polygon), { ssr: false });
const Tooltip = dynamic(() => import('react-leaflet').then((m) => m.Tooltip), { ssr: false });
const LiveStreetLightMarkers = dynamic(() => import('./LiveStreetLightMarkers').then(m => m.LiveStreetLightMarkers), { ssr: false });
const IncidentMarkers = dynamic(() => import('./IncidentMarkers').then(m => m.IncidentMarkers), { ssr: false });

interface EnhancedLiveMapProps {
  height?: string;
  showControls?: boolean;
}

export const EnhancedLiveMap: React.FC<EnhancedLiveMapProps> = ({
  height = '600px',
  showControls = true,
}) => {
  const selectedAgentView = useDashboardStore((state) => state.selectedAgentView);
  const weatherScenario = useDashboardStore((s) => s.weatherScenario);
  const cyberAttackType = useDashboardStore((s) => s.cyberAttackType);
  const cyberTargetZone = useDashboardStore((s) => s.cyberTargetZone);
  const blackoutScenario = useDashboardStore((s) => s.blackoutScenario);

  const [isClient, setIsClient] = useState(false);
  const [gridTopology, setGridTopology] = useState<PowerGridTopology | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedZone, setSelectedZone] = useState<string | null>(null);
  const [selectedLight, setSelectedLight] = useState<StreetLight | null>(null);
  const [zoomLevel, setZoomLevel] = useState(13);
  const [showAllLights, setShowAllLights] = useState(false);

  // Initialize grid topology
  useEffect(() => {
    setIsClient(true);
    const grid = generatePowerGridTopology(600); // Generate 600 street lights
    setGridTopology(grid);
  }, []);

  // React to scenario changes
  useEffect(() => {
    if (!gridTopology) return;

    let updatedGrid = gridTopology;
    const newIncidents: Incident[] = [];

    // Handle weather scenarios
    if (weatherScenario !== 'clear') {
      const affectedZone = gridTopology.zones[Math.floor(Math.random() * gridTopology.zones.length)];

      updatedGrid = updateGridState(gridTopology, {
        zoneId: affectedZone.id,
        incident: 'WEATHER_EVENT',
      });

      newIncidents.push({
        id: `weather-${Date.now()}`,
        type: 'WEATHER_EVENT',
        severity: weatherScenario === 'cyclone' ? 'CRITICAL' : weatherScenario === 'heavy-rain' ? 'HIGH' : 'MEDIUM',
        location: affectedZone.center,
        affectedRadius: 2.5,
        timestamp: new Date(),
        description: `${weatherScenario.replace('-', ' ')} affecting street lighting in ${affectedZone.name}`,
        affectedLights: Math.floor(affectedZone.totalLights * 0.3),
        status: 'ACTIVE',
      });
    }

    // Handle cyber attacks
    if (cyberAttackType && cyberTargetZone) {
      const targetZone = gridTopology.zones.find(z => z.id.toLowerCase().includes(cyberTargetZone.toLowerCase()));

      if (targetZone) {
        updatedGrid = updateGridState(updatedGrid, {
          zoneId: targetZone.id,
          incident: 'CYBER_ATTACK',
        });

        newIncidents.push({
          id: `cyber-${Date.now()}`,
          type: 'CYBER_ATTACK',
          severity: cyberAttackType === 'ransomware' ? 'CRITICAL' : 'HIGH',
          location: targetZone.center,
          affectedRadius: 1.5,
          timestamp: new Date(),
          description: `${cyberAttackType} attack detected in ${targetZone.name}`,
          affectedLights: Math.floor(targetZone.totalLights * 0.4),
          status: 'ACTIVE',
        });
      }
    }

    // Handle blackout scenarios
    if (blackoutScenario) {
      const affectedZone = gridTopology.zones[Math.floor(Math.random() * gridTopology.zones.length)];

      updatedGrid = updateGridState(updatedGrid, {
        zoneId: affectedZone.id,
        incident: 'POWER_OUTAGE',
      });

      newIncidents.push({
        id: `power-${Date.now()}`,
        type: 'POWER_OUTAGE',
        severity: blackoutScenario === 'weather-catastrophe' ? 'CRITICAL' : blackoutScenario === 'cyber-major' ? 'HIGH' : 'MEDIUM',
        location: affectedZone.center,
        affectedRadius: 3.0,
        timestamp: new Date(),
        description: `Power outage in ${affectedZone.name} due to ${blackoutScenario.replace(/-/g, ' ')}`,
        affectedLights: Math.floor(affectedZone.totalLights * 0.8),
        status: 'ACTIVE',
      });
    }

    setGridTopology(updatedGrid);
    setIncidents(prev => [...prev.filter(i => i.status !== 'RESOLVED'), ...newIncidents]);

  }, [weatherScenario, cyberAttackType, cyberTargetZone, blackoutScenario]);

  // Filter zones based on selected agent view
  const visibleZones = useMemo(() => {
    if (!gridTopology) return [];

    if (selectedAgentView === 'overview') {
      return gridTopology.zones;
    }

    // Filter zones by type based on agent view
    return gridTopology.zones.filter(zone => {
      if (selectedAgentView === 'weather') {
        return true; // Show all zones for weather
      } else if (selectedAgentView === 'cybersecurity') {
        return zone.type === 'COMMERCIAL' || zone.type === 'DOWNTOWN' || zone.type === 'INDUSTRIAL';
      } else if (selectedAgentView === 'power') {
        return zone.type === 'INDUSTRIAL' || zone.type === 'COMMERCIAL' || zone.type === 'DOWNTOWN';
      }
      return true;
    });
  }, [gridTopology, selectedAgentView]);

  // Get zone color based on current view and status
  const getZoneColor = (zone: any) => {
    if (selectedAgentView === 'cybersecurity') {
      const hasIncident = incidents.some(
        i => i.type === 'CYBER_ATTACK' && i.status === 'ACTIVE' &&
        Math.abs(i.location.lat - zone.center.lat) < 0.01 && Math.abs(i.location.lng - zone.center.lng) < 0.01
      );
      return hasIncident ? '#ef4444' : zone.securityState === 'RED' ? '#dc2626' : zone.securityState === 'YELLOW' ? '#eab308' : '#10b981';
    } else if (selectedAgentView === 'power') {
      const hasOutage = incidents.some(
        i => i.type === 'POWER_OUTAGE' && i.status === 'ACTIVE' &&
        Math.abs(i.location.lat - zone.center.lat) < 0.01 && Math.abs(i.location.lng - zone.center.lng) < 0.01
      );
      return hasOutage ? '#dc2626' : '#10b981';
    } else {
      // Weather view
      const hasWeatherIncident = incidents.some(
        i => i.type === 'WEATHER_EVENT' && i.status === 'ACTIVE' &&
        Math.abs(i.location.lat - zone.center.lat) < 0.01 && Math.abs(i.location.lng - zone.center.lng) < 0.01
      );
      return hasWeatherIncident ? '#3b82f6' : '#6366f1';
    }
  };

  const handleZoneClick = (zoneId: string, zoneName: string) => {
    setSelectedZone(zoneId);
    toast.success(`Selected ${zoneName}`, { icon: '📍', duration: 2000 });
  };

  const handleLightClick = (light: StreetLight) => {
    setSelectedLight(light);
    toast(`Light ${light.id} - ${light.status}`, { icon: '💡', duration: 2000 });
  };

  const handleIncidentClick = (incident: Incident) => {
    toast.error(`${incident.type}: ${incident.description}`, { duration: 4000 });
  };

  if (!isClient || !gridTopology) {
    return (
      <div style={{ width: '100%', height }} className="rounded-xl overflow-hidden shadow-lg bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
        <p className="text-gray-500 dark:text-gray-400">Loading enhanced map...</p>
      </div>
    );
  }

  // Stats panel
  const stats = {
    totalLights: gridTopology.streetLights.length,
    onlineLights: gridTopology.streetLights.filter(l => l.status === 'ONLINE').length,
    offlineLights: gridTopology.streetLights.filter(l => l.status === 'OFFLINE').length,
    warningLights: gridTopology.streetLights.filter(l => l.status === 'WARNING').length,
    totalPower: gridTopology.totalLoad.toFixed(2),
    activeIncidents: incidents.filter(i => i.status === 'ACTIVE').length,
  };

  return (
    <div className="relative w-full" style={{ height }}>
      <MapContainer
        center={[19.092, 72.886]}
        zoom={zoomLevel}
        scrollWheelZoom={true}
        style={{ height: '100%', width: '100%' }}
        className="rounded-xl overflow-hidden shadow-lg"
        whenCreated={(map) => {
          map.on('zoomend', () => {
            setZoomLevel(map.getZoom());
          });
        }}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
        />

        {/* Zone Polygons */}
        {visibleZones.map(zone => (
          <Polygon
            key={zone.id}
            positions={zone.bounds.map(b => [b.lat, b.lng])}
            pathOptions={{
              color: getZoneColor(zone),
              fillColor: getZoneColor(zone),
              fillOpacity: selectedZone === zone.id ? 0.4 : 0.2,
              weight: selectedZone === zone.id ? 3 : 1.5,
            }}
            eventHandlers={{
              click: () => handleZoneClick(zone.id, zone.name),
            }}
          >
            <Tooltip direction="top" offset={[0, -10]} opacity={0.9}>
              <div className="text-xs space-y-1">
                <strong className="text-sm">{zone.name}</strong>
                <br />
                Type: {zone.type}
                <br />
                Lights: {zone.onlineLights}/{zone.totalLights} online
                <br />
                Power: {zone.powerConsumption.toFixed(2)} kW
                <br />
                Temp: {zone.temperature.toFixed(1)}°C
                <br />
                Humidity: {zone.humidity.toFixed(0)}%
                <br />
                Priority: {zone.priority}
              </div>
            </Tooltip>
          </Polygon>
        ))}

        {/* Street Light Markers */}
        <LiveStreetLightMarkers
          streetLights={gridTopology.streetLights.filter(l =>
            visibleZones.some(z => z.id === l.zoneId)
          )}
          onLightClick={handleLightClick}
          showAll={showAllLights}
          zoomLevel={zoomLevel}
        />

        {/* Incident Markers */}
        <IncidentMarkers incidents={incidents} onIncidentClick={handleIncidentClick} />
      </MapContainer>

      {/* Stats Overlay */}
      {showControls && (
        <div className="absolute top-3 right-3 bg-[#0d1b2e]/95 border border-gray-700 rounded-lg p-3 text-xs text-gray-300 space-y-2 shadow-lg backdrop-blur">
          <div className="font-bold text-sm border-b border-gray-700 pb-2 mb-2">
            System Overview
          </div>

          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
            <span className="text-gray-400">Total Lights:</span>
            <span className="font-semibold text-right">{stats.totalLights}</span>

            <span className="text-gray-400">Online:</span>
            <span className="font-semibold text-green-400 text-right">{stats.onlineLights}</span>

            <span className="text-gray-400">Offline:</span>
            <span className="font-semibold text-red-400 text-right">{stats.offlineLights}</span>

            <span className="text-gray-400">Warning:</span>
            <span className="font-semibold text-yellow-400 text-right">{stats.warningLights}</span>

            <span className="text-gray-400">Power Load:</span>
            <span className="font-semibold text-right">{stats.totalPower} kW</span>

            <span className="text-gray-400">Incidents:</span>
            <span className="font-semibold text-red-400 text-right">{stats.activeIncidents}</span>
          </div>

          <div className="pt-2 border-t border-gray-700">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showAllLights}
                onChange={(e) => setShowAllLights(e.target.checked)}
                className="rounded"
              />
              <span className="text-xs">Show all lights</span>
            </label>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-3 left-3 bg-[#0d1b2e]/95 border border-gray-700 rounded-lg p-3 text-xs text-gray-300 shadow-lg backdrop-blur">
        <div className="font-semibold mb-2">Legend</div>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span>Online</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <span>Offline</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
            <span>Warning</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
            <span>Maintenance</span>
          </div>
        </div>
      </div>

      {/* Zoom level indicator */}
      <div className="absolute bottom-3 right-3 bg-[#0d1b2e]/80 border border-gray-700 rounded px-2 py-1 text-xs text-gray-400">
        Zoom: {zoomLevel}
      </div>
    </div>
  );
};

export default EnhancedLiveMap;
