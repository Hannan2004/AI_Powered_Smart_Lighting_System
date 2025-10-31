/**
 * Street Light Data Generator
 * Generates realistic street light infrastructure with zones, substations, and grid topology
 */

export interface Coordinates {
  lat: number;
  lng: number;
}

export interface StreetLight {
  id: string;
  coordinates: Coordinates;
  zoneId: string;
  substationId: string;
  circuitId: string;
  status: 'ONLINE' | 'OFFLINE' | 'MAINTENANCE' | 'WARNING';
  brightness: number; // 0-100
  powerRating: number; // watts
  voltage: number; // volts
  current: number; // amps
  temperature: number; // celsius
  lastCommunication: Date;
  securityLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  firmwareVersion: string;
  uptime: number; // hours
  connectedLights: string[]; // IDs of adjacent lights in network
}

export interface Zone {
  id: string;
  name: string;
  type: 'RESIDENTIAL' | 'COMMERCIAL' | 'INDUSTRIAL' | 'DOWNTOWN' | 'AIRPORT' | 'HIGHWAY';
  center: Coordinates;
  bounds: Coordinates[];
  totalLights: number;
  onlineLights: number;
  powerConsumption: number; // kW
  securityState: 'GREEN' | 'YELLOW' | 'RED';
  weatherCondition: string;
  temperature: number;
  humidity: number;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

export interface Substation {
  id: string;
  name: string;
  coordinates: Coordinates;
  capacity: number; // kW
  currentLoad: number; // kW
  zones: string[];
  status: 'OPERATIONAL' | 'OVERLOAD' | 'OFFLINE';
  circuits: Circuit[];
}

export interface Circuit {
  id: string;
  substationId: string;
  capacity: number; // amps
  currentLoad: number; // amps
  streetLights: string[];
  status: 'NORMAL' | 'WARNING' | 'OVERLOAD' | 'TRIPPED';
}

export interface PowerGridTopology {
  substations: Substation[];
  zones: Zone[];
  streetLights: StreetLight[];
  totalCapacity: number;
  totalLoad: number;
}

/**
 * Generate random coordinate within bounds
 */
function randomCoordinate(center: Coordinates, radiusKm: number): Coordinates {
  const radiusInDegrees = radiusKm / 111; // 1 degree ≈ 111 km
  const angle = Math.random() * 2 * Math.PI;
  const distance = Math.random() * radiusInDegrees;

  return {
    lat: center.lat + distance * Math.cos(angle),
    lng: center.lng + distance * Math.sin(angle),
  };
}

/**
 * Generate zone boundary polygon
 */
function generateZoneBounds(center: Coordinates, radiusKm: number, sides: number = 6): Coordinates[] {
  const radiusInDegrees = radiusKm / 111;
  const bounds: Coordinates[] = [];

  for (let i = 0; i < sides; i++) {
    const angle = (i / sides) * 2 * Math.PI;
    bounds.push({
      lat: center.lat + radiusInDegrees * Math.cos(angle),
      lng: center.lng + radiusInDegrees * Math.sin(angle),
    });
  }

  return bounds;
}

/**
 * Calculate distance between two coordinates (in km)
 */
function calculateDistance(coord1: Coordinates, coord2: Coordinates): number {
  const R = 6371; // Earth's radius in km
  const dLat = (coord2.lat - coord1.lat) * Math.PI / 180;
  const dLng = (coord2.lng - coord1.lng) * Math.PI / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(coord1.lat * Math.PI / 180) * Math.cos(coord2.lat * Math.PI / 180) *
    Math.sin(dLng / 2) * Math.sin(dLng / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/**
 * Find nearest street lights for network connectivity
 */
function findNearestLights(light: StreetLight, allLights: StreetLight[], maxDistance: number = 0.5): string[] {
  const distances = allLights
    .filter(l => l.id !== light.id && l.zoneId === light.zoneId)
    .map(l => ({
      id: l.id,
      distance: calculateDistance(light.coordinates, l.coordinates),
    }))
    .filter(d => d.distance <= maxDistance)
    .sort((a, b) => a.distance - b.distance)
    .slice(0, 4); // Connect to max 4 nearest lights

  return distances.map(d => d.id);
}

/**
 * Generate realistic street lights for a zone
 */
function generateStreetLightsForZone(
  zone: Zone,
  zoneIndex: number,
  lightsPerZone: number,
  substationId: string
): StreetLight[] {
  const lights: StreetLight[] = [];
  const circuitCapacity = 40; // amps per circuit
  const lightsPerCircuit = 25; // lights per circuit
  const numCircuits = Math.ceil(lightsPerZone / lightsPerCircuit);

  for (let i = 0; i < lightsPerZone; i++) {
    const circuitNum = Math.floor(i / lightsPerCircuit);
    const circuitId = `${substationId}-C${circuitNum + 1}`;

    const status: StreetLight['status'] =
      Math.random() < 0.92 ? 'ONLINE' :
      Math.random() < 0.5 ? 'OFFLINE' :
      Math.random() < 0.7 ? 'MAINTENANCE' : 'WARNING';

    const brightness = status === 'ONLINE' ? 70 + Math.random() * 30 : 0;
    const powerRating = 50 + Math.random() * 100; // 50-150W
    const voltage = status === 'ONLINE' ? 220 + (Math.random() - 0.5) * 20 : 0;
    const current = status === 'ONLINE' ? powerRating / voltage : 0;

    lights.push({
      id: `LIGHT-${zoneIndex}-${i.toString().padStart(4, '0')}`,
      coordinates: randomCoordinate(zone.center, 2), // Within 2km of zone center
      zoneId: zone.id,
      substationId,
      circuitId,
      status,
      brightness,
      powerRating,
      voltage,
      current,
      temperature: 35 + Math.random() * 20,
      lastCommunication: new Date(Date.now() - Math.random() * 300000), // Last 5 min
      securityLevel: zone.priority === 'CRITICAL' ? 'HIGH' : zone.priority === 'HIGH' ? 'MEDIUM' : 'LOW',
      firmwareVersion: `v${Math.floor(Math.random() * 3) + 2}.${Math.floor(Math.random() * 10)}.${Math.floor(Math.random() * 20)}`,
      uptime: Math.random() * 8760, // Up to 1 year
      connectedLights: [], // Will be populated later
    });
  }

  return lights;
}

/**
 * Generate complete power grid topology with zones, substations, and street lights
 */
export function generatePowerGridTopology(totalLights: number = 500): PowerGridTopology {
  const cityCenter: Coordinates = { lat: 19.092, lng: 72.886 }; // Mumbai coordinates

  // Define zones
  const zoneConfigs: Array<{name: string; type: Zone['type']; offset: Coordinates; priority: Zone['priority']}> = [
    { name: 'Downtown Central', type: 'DOWNTOWN', offset: { lat: 0, lng: 0 }, priority: 'CRITICAL' },
    { name: 'Financial District', type: 'COMMERCIAL', offset: { lat: 0.015, lng: 0.015 }, priority: 'HIGH' },
    { name: 'Airport Zone', type: 'AIRPORT', offset: { lat: -0.01, lng: 0.02 }, priority: 'CRITICAL' },
    { name: 'Industrial Park', type: 'INDUSTRIAL', offset: { lat: 0.02, lng: -0.01 }, priority: 'MEDIUM' },
    { name: 'Residential North', type: 'RESIDENTIAL', offset: { lat: 0.025, lng: 0 }, priority: 'MEDIUM' },
    { name: 'Residential South', type: 'RESIDENTIAL', offset: { lat: -0.025, lng: 0 }, priority: 'MEDIUM' },
    { name: 'Residential East', type: 'RESIDENTIAL', offset: { lat: 0, lng: 0.03 }, priority: 'LOW' },
    { name: 'Residential West', type: 'RESIDENTIAL', offset: { lat: 0, lng: -0.03 }, priority: 'LOW' },
    { name: 'Shopping District', type: 'COMMERCIAL', offset: { lat: 0.01, lng: -0.02 }, priority: 'HIGH' },
    { name: 'Tech Park', type: 'COMMERCIAL', offset: { lat: -0.015, lng: 0.015 }, priority: 'HIGH' },
    { name: 'Highway Corridor', type: 'HIGHWAY', offset: { lat: 0.03, lng: 0.02 }, priority: 'MEDIUM' },
    { name: 'Port Area', type: 'INDUSTRIAL', offset: { lat: -0.02, lng: -0.025 }, priority: 'MEDIUM' },
  ];

  const lightsPerZone = Math.floor(totalLights / zoneConfigs.length);
  const zones: Zone[] = [];
  const substations: Substation[] = [];
  const allStreetLights: StreetLight[] = [];

  // Generate zones, substations, and street lights
  zoneConfigs.forEach((config, index) => {
    const center: Coordinates = {
      lat: cityCenter.lat + config.offset.lat,
      lng: cityCenter.lng + config.offset.lng,
    };

    const zoneId = `ZONE-${(index + 1).toString().padStart(2, '0')}`;
    const substationId = `SUB-${(index + 1).toString().padStart(2, '0')}`;

    // Create zone
    const zone: Zone = {
      id: zoneId,
      name: config.name,
      type: config.type,
      center,
      bounds: generateZoneBounds(center, 2.5), // 2.5 km radius
      totalLights: lightsPerZone,
      onlineLights: Math.floor(lightsPerZone * 0.92),
      powerConsumption: (lightsPerZone * 100) / 1000, // Assume 100W per light
      securityState: 'GREEN',
      weatherCondition: 'Clear',
      temperature: 25 + Math.random() * 8,
      humidity: 60 + Math.random() * 20,
      priority: config.priority,
    };
    zones.push(zone);

    // Generate street lights for this zone
    const zoneLights = generateStreetLightsForZone(zone, index, lightsPerZone, substationId);
    allStreetLights.push(...zoneLights);

    // Create circuits for this zone
    const numCircuits = Math.ceil(lightsPerZone / 25);
    const circuits: Circuit[] = [];

    for (let c = 0; c < numCircuits; c++) {
      const circuitId = `${substationId}-C${c + 1}`;
      const circuitLights = zoneLights
        .filter(l => l.circuitId === circuitId)
        .map(l => l.id);
      const circuitLoad = circuitLights
        .map(lid => zoneLights.find(l => l.id === lid)!)
        .reduce((sum, l) => sum + l.current, 0);

      circuits.push({
        id: circuitId,
        substationId,
        capacity: 40, // amps
        currentLoad: circuitLoad,
        streetLights: circuitLights,
        status: circuitLoad > 38 ? 'WARNING' : circuitLoad > 40 ? 'OVERLOAD' : 'NORMAL',
      });
    }

    // Create substation
    const substationCapacity = lightsPerZone * 150 / 1000; // kW
    const substationLoad = zoneLights
      .filter(l => l.status === 'ONLINE')
      .reduce((sum, l) => sum + (l.powerRating / 1000), 0);

    substations.push({
      id: substationId,
      name: `${config.name} Substation`,
      coordinates: {
        lat: center.lat + (Math.random() - 0.5) * 0.005,
        lng: center.lng + (Math.random() - 0.5) * 0.005,
      },
      capacity: substationCapacity,
      currentLoad: substationLoad,
      zones: [zoneId],
      status: substationLoad > substationCapacity * 0.9 ? 'OVERLOAD' : 'OPERATIONAL',
      circuits,
    });
  });

  // Build network connectivity between street lights
  allStreetLights.forEach(light => {
    light.connectedLights = findNearestLights(light, allStreetLights);
  });

  const totalCapacity = substations.reduce((sum, s) => sum + s.capacity, 0);
  const totalLoad = substations.reduce((sum, s) => sum + s.currentLoad, 0);

  return {
    substations,
    zones,
    streetLights: allStreetLights,
    totalCapacity,
    totalLoad,
  };
}

/**
 * Simulate real-time updates to the grid
 */
export function updateGridState(
  grid: PowerGridTopology,
  updates: {
    zoneId?: string;
    lightId?: string;
    status?: StreetLight['status'];
    brightness?: number;
    incident?: 'POWER_OUTAGE' | 'CYBER_ATTACK' | 'WEATHER_EVENT' | 'EQUIPMENT_FAILURE';
  }
): PowerGridTopology {
  const updatedGrid = JSON.parse(JSON.stringify(grid)) as PowerGridTopology;

  if (updates.incident) {
    // Apply incident effects
    switch (updates.incident) {
      case 'POWER_OUTAGE':
        // Take down entire zone or substation
        if (updates.zoneId) {
          updatedGrid.streetLights
            .filter(l => l.zoneId === updates.zoneId)
            .forEach(l => {
              l.status = 'OFFLINE';
              l.brightness = 0;
              l.voltage = 0;
              l.current = 0;
            });
        }
        break;

      case 'CYBER_ATTACK':
        // Random lights compromised
        if (updates.zoneId) {
          const zoneLights = updatedGrid.streetLights.filter(l => l.zoneId === updates.zoneId);
          const compromisedCount = Math.floor(zoneLights.length * 0.3);

          for (let i = 0; i < compromisedCount; i++) {
            const randomLight = zoneLights[Math.floor(Math.random() * zoneLights.length)];
            randomLight.status = 'WARNING';
            randomLight.brightness = Math.random() * 100;
          }
        }
        break;

      case 'WEATHER_EVENT':
        // Reduce brightness, some failures
        if (updates.zoneId) {
          updatedGrid.streetLights
            .filter(l => l.zoneId === updates.zoneId)
            .forEach(l => {
              if (Math.random() < 0.15) {
                l.status = 'OFFLINE';
                l.brightness = 0;
              } else {
                l.brightness = 100; // Max brightness for visibility
              }
            });
        }
        break;

      case 'EQUIPMENT_FAILURE':
        // Circuit failure affects multiple lights
        if (updates.zoneId) {
          const substation = updatedGrid.substations.find(s =>
            s.zones.includes(updates.zoneId!)
          );
          if (substation && substation.circuits.length > 0) {
            const failedCircuit = substation.circuits[0];
            failedCircuit.status = 'TRIPPED';

            updatedGrid.streetLights
              .filter(l => l.circuitId === failedCircuit.id)
              .forEach(l => {
                l.status = 'OFFLINE';
                l.brightness = 0;
              });
          }
        }
        break;
    }
  } else if (updates.lightId) {
    // Single light update
    const light = updatedGrid.streetLights.find(l => l.id === updates.lightId);
    if (light) {
      if (updates.status) light.status = updates.status;
      if (updates.brightness !== undefined) light.brightness = updates.brightness;
      light.lastCommunication = new Date();
    }
  }

  // Recalculate zone and substation metrics
  updatedGrid.zones.forEach(zone => {
    const zoneLights = updatedGrid.streetLights.filter(l => l.zoneId === zone.id);
    zone.onlineLights = zoneLights.filter(l => l.status === 'ONLINE').length;
    zone.powerConsumption = zoneLights
      .filter(l => l.status === 'ONLINE')
      .reduce((sum, l) => sum + l.powerRating, 0) / 1000;
  });

  updatedGrid.substations.forEach(substation => {
    const substationLights = updatedGrid.streetLights.filter(l => l.substationId === substation.id);
    substation.currentLoad = substationLights
      .filter(l => l.status === 'ONLINE')
      .reduce((sum, l) => sum + l.powerRating, 0) / 1000;
    substation.status = substation.currentLoad > substation.capacity * 0.9 ? 'OVERLOAD' : 'OPERATIONAL';
  });

  updatedGrid.totalLoad = updatedGrid.substations.reduce((sum, s) => sum + s.currentLoad, 0);

  return updatedGrid;
}

/**
 * Get lights affected by cascading failure
 */
export function getCascadingFailure(
  grid: PowerGridTopology,
  originLightId: string,
  maxDepth: number = 3
): string[] {
  const affected = new Set<string>([originLightId]);
  const queue: Array<{ id: string; depth: number }> = [{ id: originLightId, depth: 0 }];

  while (queue.length > 0) {
    const current = queue.shift()!;

    if (current.depth >= maxDepth) continue;

    const light = grid.streetLights.find(l => l.id === current.id);
    if (!light) continue;

    light.connectedLights.forEach(connectedId => {
      if (!affected.has(connectedId) && Math.random() < 0.6) { // 60% chance to propagate
        affected.add(connectedId);
        queue.push({ id: connectedId, depth: current.depth + 1 });
      }
    });
  }

  return Array.from(affected);
}
