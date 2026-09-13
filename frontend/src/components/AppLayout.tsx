import React, { useState, useEffect } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Navbar } from './Navbar';
import { ErrorBoundary } from './ErrorBoundary';
import { useAuth } from '../context/AuthContext';
import { Department, Camera, DashboardStats, User } from '../types';
import { ShieldAlert, CheckCircle2 } from 'lucide-react';

const TAB_TO_PATH: Record<string, string> = {
  dashboard: '/dashboard',
  approvals: '/admin/users',
  security: '/security',
  vms: '/vms',
  dept_admin: '/dept_admin',
  registry: '/registry',
  gis: '/gis/map',
  videowall: '/videowall',
  anpr: '/ai/analytics',
  maintenance: '/maintenance',
  technician_tasks: '/technician',
  viewer_live: '/control-room',
  gap: '/gap'
};

const PATH_TO_TAB: Record<string, string> = {
  '/dashboard': 'dashboard',
  '/admin/users': 'approvals',
  '/admin/approvals': 'approvals',
  '/security': 'security',
  '/vms': 'vms',
  '/dept_admin': 'dept_admin',
  '/registry': 'registry',
  '/gis': 'gis',
  '/gis/map': 'gis',
  '/videowall': 'videowall',
  '/anpr': 'anpr',
  '/ai/analytics': 'anpr',
  '/maintenance': 'maintenance',
  '/technician': 'technician_tasks',
  '/control-room': 'viewer_live',
  '/viewer_live': 'viewer_live',
  '/gap': 'gap',
  '/cameras': 'cameras',
  '/alerts': 'alerts',
  '/analytics': 'analytics',
  '/portal': 'portal',
  '/vision': 'portal'
};

export function getHomeDirectoryForRole(role: string): string {
  switch (role) {
    case "SUPER_ADMIN":
      return "/dashboard";
    case "SECURITY_ADMIN":
      return "/security";
    case "DEPARTMENT_ADMIN":
      return "/dept_admin";
    case "AI_ANALYST":
      return "/ai/analytics";
    case "GIS_OPERATOR":
      return "/gis/map";
    case "MAINTENANCE_OFFICER":
      return "/maintenance";
    case "TECHNICIAN":
      return "/technician";
    case "OPERATOR":
      return "/control-room";
    default:
      return "/dashboard";
  }
}

export function isTabAllowedForRole(tab: string, user: User): boolean {
  const role = user.role;
  if (role === 'SUPER_ADMIN') return true;
  if (['cameras', 'alerts', 'analytics', 'portal'].includes(tab)) return true;

  if (role === 'TECHNICIAN') return tab === 'technician_tasks';
  if (role === 'SECURITY_ADMIN') return ['security', 'dashboard', 'gap'].includes(tab);
  if (role === 'OPERATOR') return ['viewer_live', 'videowall', 'gis'].includes(tab);
  if (role === 'GIS_OPERATOR') return ['gis', 'registry', 'gap'].includes(tab);
  if (role === 'MAINTENANCE_OFFICER') return ['maintenance', 'registry', 'gis', 'gap'].includes(tab);
  if (role === 'AI_ANALYST') return ['anpr', 'gis', 'videowall', 'dashboard', 'gap'].includes(tab);
  if (role === 'DEPARTMENT_ADMIN') {
    const dept = (user.departmentName || '').toLowerCase();
    const isLawEnforcement = dept.includes('police') || dept.includes('home') || dept.includes('rto') || dept.includes('transport');
    const allowed = ['dept_admin', 'approvals', 'vms', 'registry', 'maintenance', 'videowall', 'gis', 'gap'];
    if (isLawEnforcement) allowed.push('anpr');
    return allowed.includes(tab);
  }

  return true;
}

export const AppLayout: React.FC<{
  stats: DashboardStats | null;
  departments: Department[];
  cameras: Camera[];
  pendingApprovalsCount: number;
  onClearanceProcessed: () => void;
}> = ({ stats, departments, cameras, pendingApprovalsCount }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  if (!user) return null;

  const currentTab = PATH_TO_TAB[location.pathname] || 'dashboard';
  const isAuthorized = isTabAllowedForRole(currentTab, user);

  const handleTabChange = (targetTab: string) => {
    if (!isTabAllowedForRole(targetTab, user)) {
      const homePath = getHomeDirectoryForRole(user.role);
      navigate(homePath);
      setToastMessage(`Access Restricted: Role '${user.role}' is not authorized for '${targetTab}'. Redirected to home directory.`);
      setTimeout(() => setToastMessage(null), 5000);
    } else {
      const targetPath = TAB_TO_PATH[targetTab] || '/dashboard';
      navigate(targetPath);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Toast Notification Banner */}
      {toastMessage && (
        <div className="bg-cyan-950/95 border-b border-cyan-700/80 px-4 py-2.5 text-xs text-cyan-200 flex items-center justify-between shadow-xl transition-all font-mono">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-cyan-400 flex-shrink-0" />
            <span>{toastMessage}</span>
          </div>
          <button 
            onClick={() => setToastMessage(null)} 
            className="text-cyan-400 hover:text-white text-xs font-bold px-2 py-0.5"
          >
            ✕
          </button>
        </div>
      )}

      {/* Global Command Header Navbar */}
      <Navbar
        currentUser={user}
        onLogout={handleLogout}
        activeTab={currentTab}
        setActiveTab={handleTabChange}
        onlineRatio={stats?.system_uptime_percentage || 0}
        totalCameras={stats?.total_cameras || 0}
        openTickets={stats?.active_maintenance_tickets || 0}
        pendingApprovalsCount={pendingApprovalsCount}
      />

      {/* Main Command Center Body with ErrorBoundary Protection */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6">
        {!isAuthorized ? (
          <div className="bg-red-950/40 border border-red-800 rounded-xl p-8 text-center space-y-4 shadow-2xl max-w-2xl mx-auto my-12">
            <div className="w-16 h-16 bg-red-900/60 rounded-full flex items-center justify-center mx-auto border border-red-500 text-red-400 animate-pulse">
              <ShieldAlert className="w-8 h-8" />
            </div>
            <h2 className="text-xl font-bold text-white tracking-wide uppercase">
              403 RESTRICTED — DIRECTORY BOUNDARY ENFORCED
            </h2>
            <p className="text-xs text-red-300 font-mono">
              Role '<strong className="text-white">{user.role}</strong>' ({user.roleTitle}) is strictly prohibited from accessing '<strong className="text-white">{location.pathname}</strong>'.
            </p>
            <button
              onClick={() => navigate(getHomeDirectoryForRole(user.role))}
              className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs rounded-lg shadow-lg transition"
            >
              Return to Authorized {user.roleTitle} Directory
            </button>
          </div>
        ) : (
          <ErrorBoundary fallbackTitle={`Panel Error (${location.pathname})`}>
            <Outlet />
          </ErrorBoundary>
        )}
      </main>

      {/* Footer Status Bar */}
      <footer className="bg-slate-900 border-t border-slate-800 text-xs text-slate-500 py-3 px-4">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-2 font-mono">
          <div>
            Gujarat State CCTV Registry, Federation & Analytics Platform • Active Session: {user.roleTitle}
          </div>
          <div>
            Badge: {user.badgeCode} • 26 Sovereign Departments • Persistent Session & Hardened Auth Engine
          </div>
        </div>
      </footer>
    </div>
  );
};

export default AppLayout;
