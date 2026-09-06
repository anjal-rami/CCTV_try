import React, { useState } from 'react';
<<<<<<< HEAD
import { useNavigate } from 'react-router-dom';
=======
>>>>>>> 8ba9ff981a3a31412079589b7b323d6b617498da
import { 
  ShieldCheck, 
  User as UserIcon, 
  Mail, 
  Lock, 
  Building2, 
  CheckCircle2, 
  ShieldAlert, 
  ArrowLeft,
  UserPlus
} from 'lucide-react';

const DEPARTMENTS_LIST = [
  "Gujarat Police Department",
  "Gujarat State Transport Corp (GSRTC)",
  "Regional Transport Office Gujarat (RTO)",
  "Food, Civil Supplies & Consumer Affairs",
  "Ahmedabad & Surat Municipal Corps",
  "Health & Family Welfare Dept Gujarat",
  "Gujarat State Disaster Management Authority",
  "Forest & Environment Dept (Gir & Parks)",
  "State Prohibition & Excise Department",
  "Public Works Department Gujarat (PWD)",
  "Revenue & Land Records Dept",
  "Gujarat Maritime Board (GMB Ports)",
  "Urban Development & Urban Housing",
  "School Education & Samagra Shiksha",
  "Higher & Technical Education Dept",
  "Social Justice & Empowerment",
  "Women & Child Development Dept",
  "Tourism Corporation of Gujarat (TCGL)",
  "Industries & Mines Dept (GIDC)",
  "Agriculture, Farmers Welfare & Co-operation",
  "Water Resources & Narmada Water",
  "Energy & Petrochemicals Dept (GETCO)",
  "Science & Technology Dept (DST)",
  "Prisons & Correctional Services Gujarat",
  "Labour, Skill Development & Employment",
  "Finance Department Gujarat"
];

interface RegisterPageProps {
<<<<<<< HEAD
  onNavigateToLogin?: () => void;
}

export const RegisterPage: React.FC<RegisterPageProps> = ({ onNavigateToLogin }) => {
  const navigate = useNavigate();
=======
  onNavigateToLogin: () => void;
}

export const RegisterPage: React.FC<RegisterPageProps> = ({ onNavigateToLogin }) => {
>>>>>>> 8ba9ff981a3a31412079589b7b323d6b617498da
  const [fullName, setFullName] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [department, setDepartment] = useState(DEPARTMENTS_LIST[0]);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [honeypot, setHoneypot] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Password evaluation criteria
  const hasMinLength = password.length >= 12;
  const hasUppercase = /[A-Z]/.test(password);
  const hasLowercase = /[a-z]/.test(password);
  const hasNumber = /[0-9]/.test(password);
  const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);

  const calculateStrengthScore = () => {
    let score = 0;
    if (hasMinLength) score += 25;
    if (hasUppercase) score += 20;
    if (hasLowercase) score += 15;
    if (hasNumber) score += 20;
    if (hasSpecial) score += 20;
    return score;
  };

  const strengthScore = calculateStrengthScore();
  const getStrengthLabel = () => {
    if (strengthScore < 40) return { label: 'Weak', color: 'bg-red-500', text: 'text-red-400' };
    if (strengthScore < 80) return { label: 'Moderate', color: 'bg-amber-500', text: 'text-amber-400' };
    return { label: 'Strong & Compliant', color: 'bg-emerald-500', text: 'text-emerald-400' };
  };

  const isUsernameValid = /^[a-z0-9_-]{4,32}$/.test(username.trim().toLowerCase());
  const passwordsMatch = password.length > 0 && confirmPassword.length > 0 && password === confirmPassword;

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');

    // Frontend validations before API payload dispatch
    if (!fullName.trim()) {
      setError('Full Name is required.');
      return;
    }
    if (!isUsernameValid) {
      setError('Username must be 4-32 characters, lowercase alphanumeric (letters, numbers, _, -).');
      return;
    }
    if (!email.trim() || !email.includes('@')) {
      setError('Valid official email address is required.');
      return;
    }
    if (strengthScore < 100) {
      setError('Password must meet all complexity requirements (12+ chars, uppercase, lowercase, number, symbol).');
      return;
    }
    if (!passwordsMatch) {
      setError('Password and confirmation password do not match.');
      return;
    }

    setLoading(true);

    try {
      const res = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: fullName.trim(),
          username: username.trim().toLowerCase(),
          email: email.trim().toLowerCase(),
          department: department,
          password: password,
          confirm_password: confirmPassword,
          honeypot: honeypot || undefined
        })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: 'Registration failed' }));
        throw new Error(typeof errData.detail === 'string' ? errData.detail : 'Registration failed.');
      }

      const data = await res.json();
      setSuccessMessage('Account created successfully under role OPERATOR (PENDING_APPROVAL)! Awaiting administrative verification by Department Admin or Super Admin. Redirecting to login...');
      
      // Wipe password state immediately from memory
      setPassword('');
      setConfirmPassword('');

      setTimeout(() => {
<<<<<<< HEAD
        if (onNavigateToLogin) {
          onNavigateToLogin();
        } else {
          navigate('/login');
        }
=======
        onNavigateToLogin();
>>>>>>> 8ba9ff981a3a31412079589b7b323d6b617498da
      }, 2000);
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please check your details.');
    } finally {
      setLoading(false);
    }
  };

  const strengthMeta = getStrengthLabel();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between font-sans relative overflow-hidden">
      {/* Background Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[750px] h-[500px] bg-cyan-500/5 blur-[140px] rounded-full pointer-events-none" />

      {/* Header Bar */}
      <div className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <ShieldCheck className="w-6 h-6 text-cyan-400" />
          <div>
            <h1 className="text-sm font-bold text-white tracking-wide uppercase">GUJARAT STATE CCTV REGISTRY & FEDERATION PLATFORM</h1>
            <p className="text-[11px] text-slate-400">Manual User Registration & Multi-Department Observer Onboarding</p>
          </div>
        </div>

        <button 
          onClick={onNavigateToLogin}
          className="flex items-center space-x-2 text-xs font-mono text-cyan-400 hover:text-cyan-300 bg-slate-900 border border-slate-800 px-3.5 py-1.5 rounded-full transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Login</span>
        </button>
      </div>

      {/* Main Registration Card Container */}
      <div className="max-w-xl w-full mx-auto px-4 py-8 my-auto">
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-8 shadow-2xl space-y-6 backdrop-blur">
          
          <div className="text-center space-y-2">
            <div className="inline-flex items-center space-x-2 bg-cyan-950/80 text-cyan-400 border border-cyan-800 px-3.5 py-1 rounded-full text-xs font-mono">
              <UserPlus className="w-3.5 h-3.5" />
              <span>OFFICIAL REGISTRATION ENGINE</span>
            </div>
            <h2 className="text-2xl font-extrabold text-white tracking-tight">Create Observer Account</h2>
            <p className="text-xs text-slate-400">
              Submit your credentials to register as an authorized departmental operator. Default role: <strong className="text-cyan-300">OPERATOR (Pending Approval)</strong>.
            </p>
          </div>

          {successMessage ? (
            <div className="p-5 bg-emerald-950/80 border border-emerald-700 text-emerald-300 text-xs rounded-xl flex items-center space-x-3 shadow-lg animate-pulse">
              <CheckCircle2 className="w-6 h-6 text-emerald-400 flex-shrink-0" />
              <div>
                <p className="font-bold text-sm text-white mb-1">Registration Successful!</p>
                <p>{successMessage}</p>
              </div>
            </div>
          ) : (
            <form onSubmit={handleRegister} className="space-y-4">
              
              {/* Full Name */}
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Full Official Name</label>
                <div className="relative">
                  <UserIcon className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input 
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Inspector Rajesh Patel"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition font-sans"
                  />
                </div>
              </div>

              {/* Username & Live Criteria */}
              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className="text-xs font-semibold text-slate-300">Username Handle</label>
                  <span className="text-[10px] text-slate-500 font-mono">4-32 lowercase alphanumeric</span>
                </div>
                <div className="relative">
                  <span className="text-slate-500 absolute left-3.5 top-2.5 font-mono text-xs">@</span>
                  <input 
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="officer_sharma"
                    className={`w-full bg-slate-950 border rounded-xl pl-8 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none transition font-mono ${
                      username ? (isUsernameValid ? 'border-emerald-500/80' : 'border-red-500/80') : 'border-slate-800 focus:border-cyan-500'
                    }`}
                  />
                </div>
                {username && !isUsernameValid && (
                  <p className="text-[10px] text-red-400 mt-1 font-mono">
                    Must be 4-32 characters, lowercase letters, numbers, _, -
                  </p>
                )}
              </div>

              {/* Official Email */}
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Official Email Address</label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input 
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="officer.sharma@gujarat.gov.in"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition font-mono"
                  />
                </div>
              </div>

              {/* Department Dropdown */}
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Assigned Department Scope (26 Available)</label>
                <div className="relative">
                  <Building2 className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <select
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white focus:outline-none focus:border-cyan-500 transition appearance-none"
                  >
                    {DEPARTMENTS_LIST.map((dept) => (
                      <option key={dept} value={dept} className="bg-slate-900 text-white">
                        {dept}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Password & Strength Meter */}
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Security Password</label>
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

                {/* Password Strength Meter */}
                {password.length > 0 && (
                  <div className="mt-2 space-y-1.5">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-slate-400">Password Strength:</span>
                      <span className={`font-semibold ${strengthMeta.text}`}>{strengthMeta.label} ({strengthScore}%)</span>
                    </div>
                    <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                      <div 
                        className={`h-full ${strengthMeta.color} transition-all duration-300`} 
                        style={{ width: `${strengthScore}%` }} 
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-1 text-[10px] text-slate-400 pt-1 font-mono">
                      <span className={hasMinLength ? 'text-emerald-400' : 'text-slate-500'}>✓ Min 12 Characters</span>
                      <span className={hasUppercase ? 'text-emerald-400' : 'text-slate-500'}>✓ Uppercase Letter</span>
                      <span className={hasNumber ? 'text-emerald-400' : 'text-slate-500'}>✓ Number (0-9)</span>
                      <span className={hasSpecial ? 'text-emerald-400' : 'text-slate-500'}>✓ Special Symbol</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Confirm Password */}
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Confirm Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input 
                    type="password"
                    id="confirm_password"
                    name="confirm_password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm security password"
                    className={`w-full bg-slate-950 border rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none transition font-mono ${
                      confirmPassword ? (passwordsMatch ? 'border-emerald-500/80' : 'border-red-500/80') : 'border-slate-800 focus:border-cyan-500'
                    }`}
                  />
                </div>
                {confirmPassword.length > 0 && (
                  <p className={`text-[10px] mt-1 font-mono ${passwordsMatch ? 'text-emerald-400' : 'text-red-400'}`}>
                    {passwordsMatch ? '✓ Passwords match' : '✕ Passwords do not match'}
                  </p>
                )}
              </div>

              {/* Hidden Honeypot Field for Bot Trap */}
              <input
                type="text"
                name="honeypot"
                value={honeypot}
                onChange={(e) => setHoneypot(e.target.value)}
                style={{ display: 'none' }}
                tabIndex={-1}
                autoComplete="off"
              />

              {error && (
                <div className="p-3 bg-red-950/60 border border-red-800 text-red-300 text-xs rounded-lg flex items-center space-x-2">
                  <ShieldAlert className="w-4 h-4 text-red-400 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <button 
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-cyan-500/20 transition flex items-center justify-center space-x-2 tracking-wide disabled:opacity-50 mt-4"
              >
                {loading ? (
                  <span className="flex items-center space-x-2">
                    <span className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></span>
                    <span>Creating Account...</span>
                  </span>
                ) : (
                  <span>Create Account</span>
                )}
              </button>
            </form>
          )}

          <div className="border-t border-slate-800/80 pt-4 text-center">
            <button
              type="button"
<<<<<<< HEAD
              onClick={onNavigateToLogin || (() => navigate('/login'))}
=======
              onClick={onNavigateToLogin}
>>>>>>> 8ba9ff981a3a31412079589b7b323d6b617498da
              className="text-xs text-cyan-400 hover:text-cyan-300 hover:underline transition font-mono"
            >
              Already registered? Log in here
            </button>
          </div>

        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-slate-800/80 bg-slate-900/60 py-3 px-6 text-center text-xs text-slate-500 font-mono">
        Gujarat State CCTV Registry, Federation & AI Analytics Command Center • Observer Registration Portal
      </div>
    </div>
  );
};
