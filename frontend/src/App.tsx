import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { LoginPage } from './components/LoginPage';
import { RegisterPage } from './components/RegisterPage';
import { Dashboard } from './components/Dashboard';
import { SecurityDashboard } from './components/SecurityDashboard';
import { DepartmentAdminDashboard } from './components/DepartmentAdminDashboard';
import { TechnicianDashboard } from './components/TechnicianDashboard';
import { ViewerDashboard } from './components/ViewerDashboard';
import { CameraRegistry } from './components/CameraRegistry';
import { GisMap } from './components/GisMap';
import { VideoWall } from './components/VideoWall';
import { AnprTracker } from './components/AnprTracker';
import { Maintenance } from './components/Maintenance';
import { GapAnalysis } from './components/GapAnalysis';
import { AdminApprovals } from './components/AdminApprovals';
import { VmsFederation } from './components/VmsFederation';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Department, Camera, DashboardStats, User } from './types';
import { ShieldAlert, CheckCircle2 } from 'lucide-react';

export function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [authRoute, setAuthRoute] = useState<'login' | 'register'>(
    typeof window !== 'undefined' && window.location.pathname === '/register' ? 'register' : 'login'
  );
  const [activeTab, setActiveTab] = useState<string>(() => {
    if (typeof window !== 'undefined' && window.location.pathname === '/admin/approvals') {
      return 'approvals';
    }
    return 'dashboard';
  });
  const [restoringSession, setRestoringSession] = useState<boolean>(true);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [pendingApprovalsCount, setPendingApprovalsCount] = useState<number>(3);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const fetchInitialData = async () => {
    try {
      const token = localStorage.getItem('access_token') || '';
      const [statsRes, deptRes, camsRes, countRes] = await Promise.all([
        fetch('/api/dashboard/stats').catch(() => null),
        fetch('/api/departments').catch(() => null),
        fetch('/api/cameras?limit=520').catch(() => null),
        fetch('/api/v1/admin/users/pending/count', {
          headers: { 'Authorization': `Bearer ${token}` }
        }).catch(() => null)
      ]);

      if (statsRes?.ok) {
        const statsData = await statsRes.json().catch(() => null);
        if (statsData) {
          setStats(statsData);
          if (typeof statsData.pending_approvals_count === 'number') {
            setPendingApprovalsCount(statsData.pending_approvals_count);
          }
        }
      }
      if (deptRes?.ok) {
        const deptData = await deptRes.json().catch(() => []);
        if (deptData) setDepartments(deptData);
      }
      if (camsRes?.ok) {
        const camsData = await camsRes.json().catch(() => ({ cameras: [] }));
        if (camsData?.cameras) setCameras(camsData.cameras);
      }
      if (countRes?.ok) {
        const countData = await countRes.json().catch(() => null);
        if (countData && typeof countData.pending_count === 'number') {
          setPendingApprovalsCount(countData.pending_count);
        }
      }
    } catch (e) {
      console.warn('Failed to load platform telemetry', e);
    } finally {
      setLoading(false);
    }
  };

  // Restore authenticated session from localStorage on application load / refresh
  useEffect(() => {
    const storedToken = localStorage.getItem('access_token');
    const storedUser = localStorage.getItem('auth_user');
    const storedTab = localStorage.getItem('active_tab');

    if (storedToken && storedUser) {
      try {
        const userObj: User = JSON.parse(storedUser);
        setCurrentUser(userObj);
        if (typeof window !== 'undefined' && window.location.pathname === '/admin/approvals') {
          setActiveTab('approvals');
        } else if (storedTab) {
          setActiveTab(storedTab);
        }
      } catch (e) {
        console.warn('Failed to parse stored authentication session:', e);
        localStorage.removeItem('access_token');
        localStorage.removeItem('auth_user');
        localStorage.removeItem('active_tab');
      }
    }
    setRestoringSession(false);
    fetchInitialData();
  }, []);

  const getDefaultTabForRole = (role: string): string => {
    switch (role) {
      case 'SUPER_ADMIN': return 'dashboard';
      case 'SECURITY_ADMIN': return 'security';
      case 'DEPARTMENT_ADMIN': return 'dept_admin';
      case 'AI_ANALYST': return 'anpr';
      case 'GIS_OPERATOR': return 'gis';
      case 'MAINTENANCE_OFFICER': return 'maintenance';
      case 'TECHNICIAN': return 'technician_tasks';
      case 'OPERATOR': return 'viewer_live';
      default: return 'dashboard';
    }
  };

  const isTabAllowedForRole = (tab: string, user: User): boolean => {
    const role = user.role;
    if (role === 'SUPER_ADMIN') return true;

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
  };

  const handleClearanceProcessed = async () => {
    try {
      const token = localStorage.getItem('access_token') || '';
      const countRes = await fetch('/api/v1/admin/users/pending/count', {
        headers: { 'Authorization': `Bearer ${token}` }
      }).catch(() => null);
      if (countRes && countRes.ok) {
        const countData = await countRes.json();
        const updated = countData.pending_count || 0;
        setPendingApprovalsCount(updated);
        setStats(prev => prev ? { ...prev, pending_approvals_count: updated } : null);
      } else {
        setPendingApprovalsCount(prev => Math.max(0, prev - 1));
        setStats(prev => prev ? { ...prev, pending_approvals_count: Math.max(0, (prev.pending_approvals_count || 1) - 1) } : null);
      }
    } catch (e) {
      setPendingApprovalsCount(prev => Math.max(0, prev - 1));
    }
  };

  const handleLoginSuccess = (user: User, token?: string) => {
    setCurrentUser(user);
    const defaultRoute = getDefaultTabForRole(user.role);
    setActiveTab(defaultRoute);
    
    // Save authentication session to localStorage for refresh persistence
    if (token) {
      localStorage.setItem('access_token', token);
    } else {
      localStorage.setItem('access_token', `session_token_${user.id}`);
    }
    localStorage.setItem('auth_user', JSON.stringify(user));
    localStorage.setItem('active_tab', defaultRoute);

    setToastMessage(`Welcome ${user.name} (${user.roleTitle}). Session saved to local storage.`);
    setTimeout(() => setToastMessage(null), 5000);
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('auth_user');
    localStorage.removeItem('active_tab');
    setCurrentUser(null);
  };

  const handleTabChange = (targetTab: string) => {
    if (!currentUser) return;
    if (!isTabAllowedForRole(targetTab, currentUser)) {
      const homeTab = getDefaultTabForRole(currentUser.role);
      setActiveTab(homeTab);
      localStorage.setItem('active_tab', homeTab);
      setToastMessage(`Access Restricted: Role '${currentUser.role}' is not authorized for tab '${targetTab}'. Redirected to home directory.`);
      setTimeout(() => setToastMessage(null), 5000);
    } else {
      setActiveTab(targetTab);
      localStorage.setItem('active_tab', targetTab);
    }
  };

  if (restoringSession) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-slate-950 text-slate-400 space-y-3 font-mono">
        <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-cyan-400"></div>
        <span className="text-xs text-cyan-400 tracking-wider">RESTORING ACTIVE COMMAND SESSION...</span>
      </div>
    );
  }

  if (!currentUser) {
    if (authRoute === 'register') {
      return <RegisterPage onNavigateToLogin={() => setAuthRoute('login')} />;
    }
    return (
      <LoginPage 
        onLoginSuccess={handleLoginSuccess} 
        onNavigateToRegister={() => setAuthRoute('register')} 
      />
    );
  }

  const isTabAuthorized = isTabAllowedForRole(activeTab, currentUser);

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
        currentUser={currentUser}
        onLogout={handleLogout}
        activeTab={activeTab}
        setActiveTab={handleTabChange}
        onlineRatio={stats?.system_uptime_percentage || 0}
        totalCameras={stats?.total_cameras || 0}
        openTickets={stats?.active_maintenance_tickets || 0}
        pendingApprovalsCount={pendingApprovalsCount}
      />

      {/* Main Command Center Body with ErrorBoundary Protection */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6">
        {loading ? (
          <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
            <div className="animate-spin rounded-full h-14 w-14 border-t-2 border-b-2 border-cyan-400"></div>
            <p className="text-sm font-mono text-cyan-400 tracking-wider">
              CONNECTING TO 80,000+ CCTV FEDERATION STREAM NODES...
            </p>
          </div>
        ) : !isTabAuthorized ? (
          <div className="bg-red-950/40 border border-red-800 rounded-xl p-8 text-center space-y-4 shadow-2xl max-w-2xl mx-auto my-12">
            <div className="w-16 h-16 bg-red-900/60 rounded-full flex items-center justify-center mx-auto border border-red-500 text-red-400 animate-pulse">
              <ShieldAlert className="w-8 h-8" />
            </div>
            <h2 className="text-xl font-bold text-white tracking-wide uppercase">
              403 RESTRICTED — DIRECTORY BOUNDARY ENFORCED
            </h2>
            <p className="text-xs text-red-300 font-mono">
              Role '<strong className="text-white">{currentUser.role}</strong>' ({currentUser.roleTitle}) is strictly prohibited from accessing '<strong className="text-white">{activeTab}</strong>'.
            </p>
            <button
              onClick={() => handleTabChange(getDefaultTabForRole(currentUser.role))}
              className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs rounded-lg shadow-lg transition"
            >
              Return to Authorized {currentUser.roleTitle} Directory
            </button>
          </div>
        ) : (
          <ErrorBoundary fallbackTitle={`Panel Error (${activeTab})`}>
            {activeTab === 'dashboard' && <Dashboard stats={stats} onNavigate={handleTabChange} />}
            {activeTab === 'approvals' && (
              <AdminApprovals 
                currentUser={currentUser} 
                onClearanceProcessed={handleClearanceProcessed}
                onNavigateToDashboard={() => handleTabChange('dashboard')}
              />
            )}
            {activeTab === 'security' && <SecurityDashboard />}
            {activeTab === 'vms' && <VmsFederation currentUser={currentUser} />}
            {activeTab === 'dept_admin' && <DepartmentAdminDashboard currentUser={currentUser} onNavigate={handleTabChange} />}
            {activeTab === 'technician_tasks' && <TechnicianDashboard currentUser={currentUser} />}
            {activeTab === 'viewer_live' && <ViewerDashboard cameras={cameras || []} />}
            {activeTab === 'registry' && <CameraRegistry departments={departments || []} />}
            {activeTab === 'gis' && <GisMap departments={departments || []} />}
            {activeTab === 'videowall' && <VideoWall cameras={cameras || []} />}
            {activeTab === 'anpr' && <AnprTracker currentUser={currentUser} />}
            {activeTab === 'maintenance' && <Maintenance cameras={cameras || []} />}
            {activeTab === 'gap' && <GapAnalysis />}
          </ErrorBoundary>
        )}
      </main>

      {/* Footer Status Bar */}
      <footer className="bg-slate-900 border-t border-slate-800 text-xs text-slate-500 py-3 px-4">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-2 font-mono">
          <div>
            Gujarat State CCTV Registry, Federation & Analytics Platform • Active Session: {currentUser.roleTitle}
          </div>
          <div>
            Badge: {currentUser.badgeCode} • 26 Sovereign Departments • Persistent Session & Hardened Auth Engine
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
