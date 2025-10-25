'use client'; // Needed for Zustand hook and onClick handlers

import React from 'react';
import { ShieldCheck, CloudSun, Zap, LayoutDashboard } from 'lucide-react';
import { useDashboardStore, AgentView } from '@/store/useDashboardStore';

const Sidebar: React.FC = () => {
  const { selectedAgentView, setSelectedAgentView } = useDashboardStore();

  const navItems: { name: string; view: AgentView; icon: React.ElementType }[] = [
    { name: 'Overview', view: 'overview', icon: LayoutDashboard },
    { name: 'Cybersecurity', view: 'cybersecurity', icon: ShieldCheck },
    { name: 'Weather', view: 'weather', icon: CloudSun },
    { name: 'Power Grid', view: 'power', icon: Zap },
  ];

  return (
    <aside className="w-64 bg-white dark:bg-gray-800 shadow-md flex flex-col">
      <div className="p-4 border-b dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Agent Views</h2>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isSelected = selectedAgentView === item.view;
          return (
            <button
              key={item.view}
              onClick={() => setSelectedAgentView(item.view)}
              className={`w-full flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors duration-150 ease-in-out
                          ${
                            isSelected
                              ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-100'
                              : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                          }`}
            >
              <Icon className="h-5 w-5 mr-3" />
              {item.name}
            </button>
          );
        })}
      </nav>
      {/* Optional: Add footer or user info here */}
    </aside>
  );
};

export default Sidebar;