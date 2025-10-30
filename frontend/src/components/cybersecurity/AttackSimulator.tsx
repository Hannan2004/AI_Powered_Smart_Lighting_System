import React from "react";

const AttackSimulator: React.FC = () => (
  <div className="bg-gray-800 rounded-xl p-6 shadow w-full">
    <h3 className="font-bold text-lg text-gray-100 mb-2">Attack Simulator</h3>
    <button className="w-full px-4 py-2 rounded bg-red-600 text-white font-bold hover:bg-red-700 transition mb-2">Simulate Attack</button>
    <div className="text-xs text-gray-400">No simulated attack yet</div>
  </div>
);

export default AttackSimulator;
