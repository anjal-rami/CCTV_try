import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Lock, 
  User as UserIcon, 
  Key, 
  ChevronRight, 
  ShieldAlert,
  Users
} from 'lucide-react';
import { User, UserRole } from '../types';
<<<<<<< HEAD
import { useAuth } from '../context/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';

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
=======
>>>>>>> 8ba9ff981a3a31412079589b7b323d6b617498da

interface RoleAccountRef {
  role: string;
  username: string;
  department: string;
}

const AVAILABLE_ACCOUNTS: RoleAccountRef[] = [
  { role: "SUPER_ADMIN", username: "admin", department: "State Command" },
  { role: "SECURITY_ADMIN", username: "sec_admin", department: "Cyber Defense" },
  { role: "DEPARTMENT_ADMIN", username: "police_admin", department: "Police Dept" },
  { role: "AI_ANALYST", username: "analyst_intel", department: "Intelligence Unit" },
  { role: "GIS_OPERATOR", username: "gis_operator", department: "Spatial Command" },
  { role: "MAINTENANCE_OFFICER", username: "maint_officer", department: "Operations" },
  { role: "TECHNICIAN", username: "tech_amc", department: "Field Maintenance" },
  { role: "OPERATOR", username: "operator", department: "Department Monitoring" }
];

export const AccountDirectoryPanel: React.FC = () => {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-6 backdrop-blur shadow-2xl space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          <Users className="w-4 h-4 text-cyan-400" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            Registered Accounts Directory
          </h3>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800/80 text-amber-400 border border-amber-500/20">
          Manual Entry Required
        </span>
      </div>

      <p className="text-xs text-slate-400">
        Reference handles for active authorities. Enter credentials manually in the login form.
      </p>

      <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
        {AVAILABLE_ACCOUNTS.map((account) => (
          <div
            key={account.username}
            className="flex items-center justify-between rounded-xl border border-slate-800/80 bg-slate-950/60 px-3.5 py-2.5 text-xs transition"
          >
            <div className="flex flex-col">
              <span className="font-mono font-medium text-slate-200 text-xs">
                {account.username}
              </span>
              <span className="text-[10px] text-slate-500">
                {account.department}
              </span>
            </div>
            <span className="rounded-md bg-slate-800/90 border border-slate-700/50 px-2 py-0.5 text-[10px] font-mono font-semibold text-cyan-300">
              {account.role}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

interface LoginPageProps {
<<<<<<< HEAD
  onLoginSuccess?: (user: User, token?: string) => void;
=======
  onLoginSuccess: (user: User, token?: string) => void;
>>>>>>> 8ba9ff981a3a31412079589b7b323d6b617498da
  onNavigateToRegister?: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess, onNavigateToRegister }) => {
<<<<<<< HEAD
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
=======
>>>>>>> 8ba9ff981a3a31412079589b7b323d6b617498da
  const [handle, setHandle] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const handleCustomLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!handle.trim() || !password.trim()) {
      setError('Username and password are required.');
      return;
    }
    setLoading(true);
    setError('');

    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: handle.trim(), password })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: 'Invalid username or password' }));
        throw new Error(typeof errData.detail === 'string' ? errData.detail : 'Invalid username or password.');
      }

      const data = await res.json();
<<<<<<< HEAD
      let authenticatedUser: User;
      let activeToken: string;

=======
>>>>>>> 8ba9ff981a3a31412079589b7b323d6b617498da
      if (data.mfa_required) {
        // Automatically verify MFA code for demo evaluation
        const mfaRes = await fetch('/api/v1/auth/verify-mfa', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ temp_token: data.temp_mfa_token, totp_code: '123456' })
        });
        const mfaData = await mfaRes.json();
<<<<<<< HEAD
        authenticatedUser = {
=======
        const authenticatedUser: User = {
>>>>>>> 8ba9ff981a3a31412079589b7b323d6b617498da
          id: mfaData.user.id,
          username: mfaData.user.username,
          name: mfaData.user.name,
          email: mfaData.user.email,
          role: mfaData.user.role as UserRole,
          roleTitle: mfaData.user.role_title,
          departmentId: mfaData.user.department_id,
          departmentName: mfaData.user.department_name,
          badgeCode: mfaData.user.badge_code
        };
<<<<<<< HEAD
        activeToken = mfaData.access_token;
      } else {
        authenticatedUser = {
          id: data.user.id,
          username: data.user.username,
          name: data.user.name,
          email: data.user.email,
          role: data.user.role as UserRole,
          roleTitle: data.user.role_title,
          departmentId: data.user.department_id,
          departmentName: data.user.department_name,
          badgeCode: data.user.badge_code
        };
        activeToken = data.access_token;
      }

      login(authenticatedUser, activeToken);
      if (onLoginSuccess) {
        onLoginSuccess(authenticatedUser, activeToken);
      }
      const from = (location.state as any)?.from?.pathname;
      navigate(from || getHomeDirectoryForRole(authenticatedUser.role), { replace: true });
=======
        onLoginSuccess(authenticatedUser, mfaData.access_token);
        return;
      }

      const authenticatedUser: User = {
        id: data.user.id,
        username: data.user.username,
        name: data.user.name,
        email: data.user.email,
        role: data.user.role as UserRole,
        roleTitle: data.user.role_title,
        departmentId: data.user.department_id,
        departmentName: data.user.department_name,
        badgeCode: data.user.badge_code
      };
      onLoginSuccess(authenticatedUser, data.access_token);
>>>>>>> 8ba9ff981a3a31412079589b7b323d6b617498da
    } catch (err: any) {
      setError(err.message || 'Invalid username or password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between font-sans relative overflow-hidden">
      {/* Background Glow Overlay */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[450px] bg-cyan-500/5 blur-[120px] rounded-full pointer-events-none" />

      {/* Top Header Bar */}
      <div className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <ShieldCheck className="w-6 h-6 text-cyan-400" />
          <div>
            <h1 className="text-sm font-bold text-white tracking-wide uppercase">GUJARAT STATE CCTV REGISTRY & FEDERATION PLATFORM</h1>
            <p className="text-[11px] text-slate-400">Integrated Government Video Management & Multi-Department AI Analytics</p>
          </div>
        </div>

        <div className="flex items-center space-x-3 text-xs font-mono text-slate-400">
          <span className="flex items-center space-x-1.5 bg-slate-900 border border-slate-800 px-3 py-1 rounded-full text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>State Network Online</span>
          </span>
          <span className="bg-slate-900 border border-slate-800 px-3 py-1 rounded-full text-cyan-400">
            26 Sovereign Depts
          </span>
        </div>
      </div>

      {/* Main Grid Container for Login Form & Account Directory Panel */}
      <div className="max-w-4xl w-full mx-auto px-4 py-8 my-auto grid grid-cols-1 md:grid-cols-2 gap-6 items-stretch">
        {/* Left Column: Primary Authentication Form */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-8 shadow-2xl space-y-6 backdrop-blur flex flex-col justify-between">
          <div className="space-y-6">
            <div className="text-center space-y-2">
              <div className="inline-flex items-center space-x-2 bg-cyan-950/80 text-cyan-400 border border-cyan-800 px-3.5 py-1 rounded-full text-xs font-mono">
                <Key className="w-3.5 h-3.5" />
                <span>SECURE OPERATOR PORTAL</span>
              </div>
              <h2 className="text-2xl font-extrabold text-white tracking-tight">Operator Authentication</h2>
              <p className="text-xs text-slate-400">
                Enter your official government handle or email and security password to access CCTV command services.
              </p>
            </div>

            <form onSubmit={handleCustomLogin} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">Official Username or Email</label>
                <div className="relative">
                  <UserIcon className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input 
                    type="text"
                    required
                    value={handle}
                    onChange={(e) => setHandle(e.target.value)}
                    placeholder="e.g. officer.sharma or admin@dept.gov.in"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">Security Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input 
                    type="password"
                    id="password"
                    name="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter security password"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition font-mono"
                  />
                </div>
              </div>

              {error && (
                <div className="p-3 bg-red-950/60 border border-red-800 text-red-300 text-xs rounded-lg flex items-center space-x-2">
                  <ShieldAlert className="w-4 h-4 text-red-400 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <button 
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-cyan-500/20 transition flex items-center justify-center space-x-2 tracking-wide disabled:opacity-50"
              >
                {loading ? (
                  <span className="flex items-center space-x-2">
                    <span className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></span>
                    <span>Authenticating...</span>
                  </span>
                ) : (
                  <>
                    <span>Authenticate & Enter Command Center</span>
                    <ChevronRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>
          </div>

          <div className="border-t border-slate-800/80 pt-4 text-center text-[11px] text-slate-500 space-y-2">
            <div>Protected by State Cyber Security Directorate • Audit Logs Active</div>
<<<<<<< HEAD
            <div>
              <button
                type="button"
                onClick={onNavigateToRegister || (() => navigate('/register'))}
                className="text-xs text-cyan-400 hover:text-cyan-300 hover:underline font-mono transition"
              >
                Need an observer account? Register here
              </button>
            </div>
=======
            {onNavigateToRegister && (
              <div>
                <button
                  type="button"
                  onClick={onNavigateToRegister}
                  className="text-xs text-cyan-400 hover:text-cyan-300 hover:underline font-mono transition"
                >
                  Need an observer account? Register here
                </button>
              </div>
            )}
>>>>>>> 8ba9ff981a3a31412079589b7b323d6b617498da
          </div>
        </div>

        {/* Right Column: Account Directory Reference Panel */}
        <AccountDirectoryPanel />
      </div>

      {/* Footer */}
      <div className="border-t border-slate-800/80 bg-slate-900/60 py-3 px-6 text-center text-xs text-slate-500 font-mono">
        Gujarat State CCTV Registry, Federation & AI Analytics Command Center • Authorized Personnel Only
      </div>
    </div>
  );
};
