import React from "react";

const metrics = [
  { label: "Active Sensors", value: 1281, color: "text-blue-400" },
  { label: "Total Alerts (24h)", value: 13, color: "text-yellow-300" },
  { label: "Power Uptime (%)", value: "99.985", color: "text-green-400" },
];

const DashboardMetrics: React.FC = () => (
  <div className="flex flex-wrap gap-6 justify-center">
    {metrics.map((m, idx) => (
      <div key={m.label} className="flex flex-col bg-gray-800 rounded-xl p-6 shadow w-64 items-center">
        <span className={`text-3xl font-bold font-mono ${m.color}`}>{m.value}</span>
        <span className="text-gray-300 mt-2 text-md text-center">{m.label}</span>
      </div>
    ))}
  </div>
);

export default DashboardMetrics;
