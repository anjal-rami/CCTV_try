import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  ShieldCheck, 
  ShieldAlert,
  Eye,
  LayoutDashboard, 
  Camera, 
  Map, 
  Grid, 
  Scan, 
  Wrench, 
  BarChart3, 
  Bell, 
  Activity,
  Building2,
  LogOut,
  User as UserIcon,
  UserCheck,
  GitMerge
} from 'lucide-react';
import { User } from '../types';

interface NavbarProps {
  currentUser: User;
  onLogout: () => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onlineRatio: number;
  totalCameras: number;
  openTickets: number;
  pendingApprovalsCount?: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentUser,
  onLogout,
  activeTab,
  setActiveTab,
  onlineRatio,
  totalCameras,
  openTickets,
  pendingApprovalsCount = 0
}) => {
  const [time, setTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const d = new Date();
      setTime(d.toLocaleTimeString('en-US', { hour12: false }) + ' IST');
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  // Strict Authority-based Navigation Gating
  const getNavItems = () => {
    const role = currentUser.role;
    if (role === 'SUPER_ADMIN') {
      return [
        { id: 'dashboard', label: 'Command Dashboard', icon: LayoutDashboard },
        { 
          id: 'approvals', 
          label: 'User Management & Directory', 
          icon: UserCheck,
          badge: pendingApprovalsCount > 0 ? `Users [ ${pendingApprovalsCount} Pending ]` : 'Users [ 0 Pending ]'
        },
        { id: 'security', label: 'Security & Forensics', icon: ShieldAlert },
        { id: 'vms', label: 'VMS Federation', icon: GitMerge },
        { id: 'dept_admin', label: 'Department Portal', icon: Building2 },
        { id: 'registry', label: 'Camera Registry', icon: Camera },
        { id: 'gis', label: 'GIS Command Map', icon: Map },
        { id: 'videowall', label: 'Video Wall', icon: Grid },
        { id: 'anpr', label: 'AI ANPR & Route Tracker', icon: Scan },
        { id: 'maintenance', label: 'SLA Maintenance', icon: Wrench },
        { id: 'gap', label: 'Gap Analytics', icon: BarChart3 },
      ];
    } else if (role === 'SECURITY_ADMIN') {
      return [
        { id: 'security', label: 'Security & Threat Meter', icon: ShieldAlert },
        { id: 'gap', label: 'Audit Log Forensics', icon: BarChart3 },
      ];
    } else if (role === 'DEPARTMENT_ADMIN') {
      return [
        { id: 'dept_admin', label: 'Department Command', icon: Building2 },
        { 
          id: 'approvals', 
          label: 'User Management & Directory', 
          icon: UserCheck,
          badge: pendingApprovalsCount > 0 ? `Users [ ${pendingApprovalsCount} Pending ]` : undefined
        },
        { id: 'vms', label: 'VMS Federation', icon: GitMerge },
        { id: 'registry', label: 'Department Cameras', icon: Camera },
        { id: 'maintenance', label: 'Department Tickets', icon: Wrench },
      ];
    } else if (role === 'AI_ANALYST') {
      return [
        { id: 'anpr', label: 'AI ANPR & Route Tracker', icon: Scan },
        { id: 'gis', label: 'GIS Command Map', icon: Map },
        { id: 'videowall', label: 'Video Wall Grid', icon: Grid },
        { id: 'dashboard', label: 'Command Overview', icon: LayoutDashboard },
      ];
    } else if (role === 'GIS_OPERATOR') {
      return [
        { id: 'gis', label: 'GIS Command Map & FOV', icon: Map },
        { id: 'gap', label: 'Coverage Density Analysis', icon: BarChart3 },
      ];
    } else if (role === 'MAINTENANCE_OFFICER') {
      return [
        { id: 'maintenance', label: 'SLA Maintenance Kanban', icon: Wrench },
        { id: 'gap', label: 'Aging Infrastructure Radar', icon: BarChart3 },
      ];
    } else if (role === 'TECHNICIAN') {
      return [
        { id: 'technician_tasks', label: 'Assigned Work Orders', icon: Wrench },
      ];
    } else if (role === 'OPERATOR') {
      return [
        { id: 'viewer_live', label: 'Department Monitoring Stream (Operator)', icon: Eye },
      ];
    }
    return [{ id: 'dashboard', label: 'Command Dashboard', icon: LayoutDashboard }];
  };

  const navItems = getNavItems();

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50 shadow-xl">
      {/* Top Banner Bar */}
      <div className="max-w-7xl mx-auto px-4 py-2 flex items-center justify-between border-b border-slate-800/60 text-xs">
        <div className="flex items-center space-x-4">
          <span className="flex items-center text-cyan-400 font-semibold tracking-wide">
            <ShieldCheck className="w-4 h-4 mr-1.5 text-cyan-400" />
            GUJARAT STATE CCTV REGISTRY & FEDERATION
          </span>
          <span className="bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700 font-mono text-[10px]">
            26 SOVEREIGN DEPARTMENTS
          </span>
        </div>

        <div className="flex items-center space-x-5">
          <div className="hidden md:flex items-center space-x-2 text-slate-300">
            <Activity className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
            <span>Telemetry: <strong className="text-emerald-400">{onlineRatio}% Online</strong> ({totalCameras} streams)</span>
          </div>

          {/* User Session Profile Pill */}
          <div className="flex items-center space-x-2 bg-slate-950 border border-slate-800 px-3 py-1 rounded-full text-xs">
            <UserIcon className="w-3.5 h-3.5 text-cyan-400" />
            <span className="font-semibold text-white">{currentUser.name}</span>
            <span className={`px-1.5 py-0.2 rounded font-mono text-[9px] font-bold ${
              currentUser.role === 'SUPER_ADMIN' ? 'bg-cyan-950 text-cyan-400 border border-cyan-800' :
              currentUser.role === 'POLICE_OFFICER' ? 'bg-red-950 text-red-400 border border-red-800' :
              currentUser.role === 'DEPT_NODAL_OFFICER' ? 'bg-blue-950 text-blue-400 border border-blue-800' :
              currentUser.role === 'AMC_TECHNICIAN' ? 'bg-amber-950 text-amber-400 border border-amber-800' :
              'bg-purple-950 text-purple-400 border border-purple-800'
            }`}>
              {currentUser.role}
            </span>
          </div>

          <button 
            onClick={onLogout}
            className="flex items-center space-x-1 bg-red-950/60 hover:bg-red-900 text-red-300 border border-red-800/80 px-2.5 py-1 rounded-full text-xs font-semibold transition"
            title="Log Out of Command Session"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Log Out</span>
          </button>
        </div>
      </div>

      {/* Main Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between">
        <nav className="flex space-x-1 overflow-x-auto py-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-lg shadow-cyan-500/5'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
                {(item as any).badge && (
                  <span className="bg-amber-500/20 text-amber-400 border border-amber-500/40 text-[10px] font-mono font-bold px-2 py-0.5 rounded-full shadow-sm animate-pulse whitespace-nowrap">
                    {(item as any).badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        <div className="hidden lg:flex items-center space-x-2 text-xs text-slate-400">
          <Building2 className="w-4 h-4 text-cyan-400" />
          <span>Integrated Government Cloud</span>
        </div>
      </div>
    </header>
  );
};

export interface TabItem {
  id: string;
  label: string;
  badge?: string;
  alert?: boolean;
}

export interface AnimatedNavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  tabs?: TabItem[];
}

export default function AnimatedNavbar({
  activeTab,
  setActiveTab,
  tabs = [
    { id: 'cameras', label: 'Live Feeds', badge: '3' },
    { id: 'alerts', label: 'Alerts & Rules', badge: '1', alert: true },
    { id: 'analytics', label: 'Telemetry & Stats' },
  ]
}: AnimatedNavbarProps) {
  return (
    <nav className="sticky top-6 z-50 flex justify-center mb-10 px-4">
      <div className="flex items-center gap-1.5 p-1.5 rounded-2xl bg-neutral-900/80 border border-neutral-800/80 backdrop-blur-xl shadow-2xl">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`relative flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-colors duration-200 outline-none select-none cursor-pointer ${
                isActive ? 'text-white' : 'text-neutral-400 hover:text-neutral-200'
              }`}
            >
              {/* Sliding Background Pill */}
              {isActive && (
                <motion.div
                  layoutId="active-pill"
                  className="absolute inset-0 rounded-xl bg-indigo-600/30 border border-indigo-500/50 shadow-inner"
                  transition={{
                    type: 'spring',
                    stiffness: 380,
                    damping: 30,
                  }}
                />
              )}

              {/* Tab Content */}
              <span className="relative z-10">{tab.label}</span>

              {tab.badge && (
                <span
                  className={`relative z-10 px-1.5 py-0.5 text-[10px] font-mono rounded-md ${
                    tab.alert
                      ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30 animate-pulse'
                      : 'bg-neutral-800 text-neutral-300 border border-neutral-700'
                  }`}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
