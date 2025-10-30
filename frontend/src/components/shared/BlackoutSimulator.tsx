import React, { useState } from 'react';

const BlackoutSimulator: React.FC = () => {
  const [status, setStatus] = useState('No blackout simulated yet');

  return (
    <div className="bg-gray-800 rounded-xl p-6 shadow w-full flex flex-col items-center">
      <h3 className="font-bold text-lg text-gray-100 mb-4">Blackout Simulator</h3>
      <button
        className="px-5 py-2 rounded bg-yellow-600 text-white hover:bg-yellow-700 font-semibold mb-3"
        onClick={() => setStatus('Blackout simulated at ' + new Date().toLocaleTimeString())}
      >
        Simulate Blackout
      </button>
      <div className="text-xs text-gray-300 mt-1">{status}</div>
    </div>
  );
};

export default BlackoutSimulator;
