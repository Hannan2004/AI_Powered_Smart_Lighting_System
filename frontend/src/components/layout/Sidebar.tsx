'use client'; // Needed for Zustand hook and onClick handlers

import React from 'react';
import { ShieldCheck, CloudSun, Zap, LayoutDashboard } from 'lucide-react';
import { useDashboardStore, AgentView } from '@/store/useDashboardStore';
import Link from "next/link";

const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col h-full shadow-md">
      {/* Title */}
      <div className="p-6 border-b border-gray-800">
        <h1 className="text-2xl font-bold">Mumbai Smart City</h1>
      </div>
      {/* Navigation */}
      <nav className="flex-1 p-6 space-y-4">
        <Link href="/" className="block px-2 py-2 rounded hover:bg-gray-800 transition-colors">Weather Dashboard</Link>
        <Link href="/cybersecurity" className="block px-2 py-2 rounded hover:bg-gray-800 transition-colors">Cybersecurity</Link>
        <Link href="/blackout" className="block px-2 py-2 rounded hover:bg-gray-800 transition-colors">Blackout Response</Link>
      </nav>
    </aside>
  );
};

export default Sidebar;