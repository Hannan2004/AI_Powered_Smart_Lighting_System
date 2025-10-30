'use client'; // Needed for Zustand hook

import React from "react";
import WeatherDashboard from "@/components/weather/WeatherDashboard";
import LiveClockAndWeather from "@/components/shared/LiveClockAndWeather";
import DashboardMetrics from "@/components/shared/DashboardMetrics";
import MapAndControls from "@/components/shared/MapAndControls";
import FleetAnalytics from "@/components/shared/FleetAnalytics";
import Footer from "@/components/shared/Footer";

export default function WeatherDashboardPage() {
  return (
    <div className="flex flex-col gap-0 px-8 py-8 max-w-4xl mx-auto">
      <LiveClockAndWeather />
      <div className="my-6 border-t border-gray-700" />
      <DashboardMetrics />
      <div className="my-6 border-t border-gray-700" />
      {/* Backend-connected weather data */}
      <WeatherDashboard />
      <div className="my-6 border-t border-gray-700" />
      <MapAndControls />
      <div className="my-6 border-t border-gray-700" />
      <FleetAnalytics />
      <div className="my-6 border-t border-gray-700" />
      <Footer />
    </div>
  );
}
