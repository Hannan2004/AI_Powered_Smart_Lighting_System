import React, { useState } from "react";

const zones = [
  { id: 'airport', name: 'Airport' },
  { id: 'midtown', name: 'Midtown' }
];

const ZoneControlPanel: React.FC = () => {
  const [selectedZone, setSelectedZone] = useState(zones[0].id);
  return (
    <div className="bg-gray-800 rounded-xl p-6 shadow flex flex-col gap-4 w-full">
      <h3 className="font-bold text-lg text-gray-100">Zone Controls</h3>
      <label className="text-gray-300 text-sm mb-1" htmlFor="zone-select">Select Zone:</label>
      <select
        id="zone-select"
        value={selectedZone}
        className="rounded px-3 py-2 bg-gray-700 text-gray-100"
        onChange={e => setSelectedZone(e.target.value)}
      >
        {zones.map(z => (<option key={z.id} value={z.id}>{z.name}</option>))}
      </select>
      <div className="flex gap-2 mt-3">
        <button className="flex-1 px-3 py-2 rounded bg-yellow-500 hover:bg-yellow-600 text-white font-semibold">Simulate Heatwave</button>
        <button className="flex-1 px-3 py-2 rounded bg-blue-500 hover:bg-blue-600 text-white font-semibold">Simulate Heavy Rain</button>
      </div>
    </div>
  );
};

export default ZoneControlPanel;
