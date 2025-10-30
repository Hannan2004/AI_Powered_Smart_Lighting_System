"use client";
import React from "react";
import PowerDashboard from "@/components/power/PowerDashboard";
import ZonePowerPanel from "@/components/shared/ZonePowerPanel";
import IncidentPanel from "@/components/shared/IncidentPanel";
import BlackoutSimulator from "@/components/shared/BlackoutSimulator";
import MapAndControls from "@/components/shared/MapAndControls";

export default function BlackoutDashboardPage() {
  return (
    <div className="flex gap-6 h-full w-full p-8">
      <div className="flex-1 flex flex-col gap-6">
        <PowerDashboard />
        <MapAndControls />
      </div>
      <div className="w-[400px] flex flex-col gap-6">
        <ZonePowerPanel />
        <IncidentPanel />
        <BlackoutSimulator />
      </div>
    </div>
  );
}
