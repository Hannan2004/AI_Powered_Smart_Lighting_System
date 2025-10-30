"use client";
import React from "react";
import CybersecurityDashboard from "@/components/cybersecurity/CybersecurityDashboard";
import ZoneStatusPanel from "@/components/shared/ZoneStatusPanel";
import AttackSimulator from "@/components/shared/AttackSimulator";
import MapAndControls from "@/components/shared/MapAndControls";

export default function CybersecurityDashboardPage() {
  return (
    <div className="flex gap-6 h-full w-full p-8">
      {/* Main content on the left */}
      <div className="flex-1 flex flex-col gap-6">
        <CybersecurityDashboard />
        <MapAndControls />
      </div>
      {/* Right sidebar */}
      <div className="w-[400px] flex flex-col gap-6">
        <ZoneStatusPanel />
        <AttackSimulator />
      </div>
    </div>
  );
}
