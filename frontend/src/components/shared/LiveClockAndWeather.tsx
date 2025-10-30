import React, { useEffect, useState } from "react";

const LiveClockAndWeather: React.FC = () => {
  const [time, setTime] = useState<string>("");

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col gap-2 items-center justify-center py-8 bg-gray-800 rounded-xl shadow-md">
      <div className="text-4xl font-mono font-bold text-blue-400" data-testid="local-time">{time}</div>
      <div className="text-md text-gray-300">Mumbai, Maharashtra</div>
      <div className="mt-2 px-4 py-2 bg-gray-700 rounded text-lg text-gray-200">Weather summary: --°C • ---</div>
    </div>
  );
};

export default LiveClockAndWeather;
