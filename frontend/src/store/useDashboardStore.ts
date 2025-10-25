import { create } from 'zustand';

// Define the types for the agent views
export type AgentView = 'cybersecurity' | 'power' | 'weather' | 'overview';

// Define the store state and actions
interface DashboardState {
  selectedAgentView: AgentView;
  setSelectedAgentView: (view: AgentView) => void;
}

// Create the Zustand store
export const useDashboardStore = create<DashboardState>((set) => ({
  selectedAgentView: 'overview', // Default view
  setSelectedAgentView: (view) => set({ selectedAgentView: view }),
}));
