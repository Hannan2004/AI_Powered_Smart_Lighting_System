'use client'; // Needed for Zustand hook

import AgentViewDisplay from "@/components/dashboard/AgentViewDisplay";
import OverviewDashboard from "@/components/overview/OverviewDashboard"; // Create this component
import { useDashboardStore } from "@/store/useDashboardStore";

export default function DashboardPage() {
  const selectedAgentView = useDashboardStore((state) => state.selectedAgentView);

  return (
    <div className="container mx-auto">
       {/* Conditionally render Overview or AgentViewDisplay */}
       {selectedAgentView === 'overview' ? (
        <OverviewDashboard />
      ) : (
        <AgentViewDisplay />
      )}
    </div>
  );
}
