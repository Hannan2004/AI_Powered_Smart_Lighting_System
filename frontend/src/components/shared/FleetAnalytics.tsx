import React from "react";

const FleetAnalytics: React.FC = () => (
  <div className="bg-gray-800 rounded-xl shadow p-6 flex flex-col items-center w-full">
    <div className="w-full h-32 bg-gray-700 rounded flex items-center justify-center text-gray-400 mb-4">
      Analytics chart placeholder
    </div>
    <div className="flex gap-8">
      <div className="flex flex-col items-center">
        <span className="text-2xl text-blue-400 font-bold">252</span>
        <span className="text-xs text-gray-300">Fleet Vehicles</span>
      </div>
      <div className="flex flex-col items-center">
        <span className="text-2xl text-yellow-300 font-bold">96%</span>
        <span className="text-xs text-gray-300">Uptime</span>
      </div>
    </div>
  </div>
);

export default FleetAnalytics;
