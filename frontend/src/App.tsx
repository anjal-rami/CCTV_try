import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { ReactLenis } from 'lenis/react';
import Waves from './components/reactbits/Waves';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AppLayout, getHomeDirectoryForRole } from './components/AppLayout';

// Public Auth Pages
import { LoginPage } from './components/LoginPage';
import { RegisterPage } from './components/RegisterPage';

// Protected Command Panels
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
import CamerasPage from './pages/CamerasPage';
import AlertsPage from './pages/AlertsPage';
import AnalyticsPage from './pages/AnalyticsPage';
import VisionPortal from './components/VisionPortal';

import { Department, Camera, DashboardStats } from './types';

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

export const AppRoutes: React.FC = () => {
  const { user, token, isLoading } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [pendingApprovalsCount, setPendingApprovalsCount] = useState<number>(3);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);

  const fetchInitialData = async () => {
    if (!token) return;
    try {
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
    }
  };

  useEffect(() => {
    if (token) {
      fetchInitialData();
    }
  }, [token]);

  const handleClearanceProcessed = async () => {
    if (!token) return;
    try {
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
      }
    } catch (e) {
      setPendingApprovalsCount(prev => Math.max(0, prev - 1));
    }
  };

  const handleNavigation = (tab: string) => {
    const path = TAB_TO_PATH[tab] || '/dashboard';
    navigate(path);
  };

  if (isLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-slate-950 text-slate-400">
        <div className="flex flex-col items-center space-y-3 font-mono">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-cyan-400"></div>
          <span className="text-xs text-cyan-400 tracking-wider">Verifying security state...</span>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      {/* 1. ROOT PATH LOGIC: Default to /login if not authenticated */}
      <Route
        path="/"
        element={
          user && token ? (
            <Navigate to={getHomeDirectoryForRole(user.role)} replace />
          ) : (
            // DEFAULT: Always send unauthenticated visitors to login
            <Navigate to="/login" replace />
          )
        }
      />

      {/* 2. PUBLIC AUTHENTICATION ROUTES */}
      <Route
        path="/login"
        element={
          user && token ? (
            <Navigate to={getHomeDirectoryForRole(user.role)} replace />
          ) : (
            <LoginPage />
          )
        }
      />
      <Route
        path="/register"
        element={
          user && token ? (
            <Navigate to={getHomeDirectoryForRole(user.role)} replace />
          ) : (
            <RegisterPage />
          )
        }
      />

      {/* 3. STRICTLY PROTECTED DIRECTORIES */}
      <Route element={<ProtectedRoute />}>
        <Route
          element={
            <AppLayout
              stats={stats}
              departments={departments}
              cameras={cameras}
              pendingApprovalsCount={pendingApprovalsCount}
              onClearanceProcessed={handleClearanceProcessed}
            />
          }
        >
          <Route path="/dashboard" element={<Dashboard stats={stats} onNavigate={handleNavigation} />} />
          <Route
            path="/admin/users"
            element={
              user ? (
                <AdminApprovals
                  currentUser={user}
                  onClearanceProcessed={handleClearanceProcessed}
                  onNavigateToDashboard={() => navigate('/dashboard')}
                />
              ) : null
            }
          />
          <Route
            path="/admin/approvals"
            element={
              user ? (
                <AdminApprovals
                  currentUser={user}
                  onClearanceProcessed={handleClearanceProcessed}
                  onNavigateToDashboard={() => navigate('/dashboard')}
                />
              ) : null
            }
          />
          <Route path="/security" element={<SecurityDashboard />} />
          <Route path="/vms" element={user ? <VmsFederation currentUser={user} /> : null} />
          <Route
            path="/dept_admin"
            element={
              user ? (
                <DepartmentAdminDashboard
                  currentUser={user}
                  onNavigate={handleNavigation}
                />
              ) : null
            }
          />
          <Route path="/technician" element={user ? <TechnicianDashboard currentUser={user} /> : null} />
          <Route path="/control-room" element={<ViewerDashboard cameras={cameras} />} />
          <Route path="/viewer_live" element={<ViewerDashboard cameras={cameras} />} />
          <Route path="/registry" element={<CameraRegistry departments={departments} />} />
          <Route path="/gis" element={<GisMap departments={departments} />} />
          <Route path="/gis/map" element={<GisMap departments={departments} />} />
          <Route path="/videowall" element={<VideoWall cameras={cameras} />} />
          <Route path="/anpr" element={user ? <AnprTracker currentUser={user} /> : null} />
          <Route path="/ai/analytics" element={user ? <AnprTracker currentUser={user} /> : null} />
          <Route path="/maintenance" element={<Maintenance cameras={cameras} />} />
          <Route path="/gap" element={<GapAnalysis />} />
          <Route path="/cameras" element={<CamerasPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/portal" element={<VisionPortal />} />
          <Route path="/vision" element={<VisionPortal />} />
        </Route>
      </Route>

      {/* 4. WILDCARD FALLBACK: Send all unknown/unauthenticated visits to /login */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
};

export function App() {
  return (
    <ReactLenis root options={{ lerp: 0.08, duration: 1.2, smoothWheel: true }}>
      <div className="relative min-h-screen bg-neutral-950 text-neutral-100 overflow-x-hidden">
        {/* Background WebGL Waves Container */}
        <div className="fixed inset-0 z-0 opacity-40 pointer-events-none">
          <Waves />
        </div>

        {/* Foreground Content */}
        <div className="relative z-10">
          <AuthProvider>
            <BrowserRouter>
              <AppRoutes />
            </BrowserRouter>
          </AuthProvider>
        </div>
      </div>
    </ReactLenis>
  );
}

export default App;
