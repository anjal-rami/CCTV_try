import React from 'react';
import { 
  Camera, 
  CheckCircle2, 
  AlertTriangle, 
  HardDrive, 
  Building2, 
  TrendingUp, 
  ShieldAlert, 
  Activity,
  Zap
} from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { DashboardStats } from '../types';
import { SurveillanceHero } from './SurveillanceHero';

interface DashboardProps {
  stats: DashboardStats | null;
  onNavigate: (tab: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ stats, onNavigate }) => {
  if (!stats) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400"></div>
      </div>
    );
  }

  const pendingCount = stats.pending_approvals_count ?? 0;

  return (
    <div className="space-y-6">
      {/* React Bits Animated Surveillance AI Vision Engine Hero */}
      <SurveillanceHero />

      {/* High-Visibility Admin Clearance Alert Banner */}
      {pendingCount > 0 && (
        <div className="bg-gradient-to-r from-amber-950/90 via-amber-900/60 to-orange-950/90 border-2 border-amber-500/70 rounded-2xl p-4.5 shadow-2xl flex flex-col md:flex-row items-center justify-between gap-4 text-amber-200">
          <div className="flex items-center space-x-3.5">
            <div className="w-11 h-11 rounded-full bg-amber-500/20 border border-amber-400/60 flex items-center justify-center text-amber-300 text-xl flex-shrink-0 animate-bounce">
              ⚠️
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h4 className="text-sm font-black text-white uppercase tracking-wider">
                  GOVERNMENT CLEARANCE VERIFICATION REQUIRED
                </h4>
                <span className="bg-amber-500 text-slate-950 text-[10px] font-mono font-bold px-2 py-0.5 rounded-full">
                  ACTION REQUIRED
                </span>
              </div>
              <p className="text-xs text-amber-200 font-mono mt-1">
                ⚠️ {pendingCount} government {pendingCount === 1 ? 'operator is' : 'operators are'} waiting for clearance verification.
              </p>
            </div>
          </div>
          <button
            onClick={() => onNavigate('approvals')}
            className="px-5 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-amber-950 flex items-center space-x-2 transition cursor-pointer flex-shrink-0"
          >
            <span>Review Clearances ({pendingCount})</span>
            <span>→</span>
          </button>
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Cameras */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-lg backdrop-blur hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium uppercase tracking-wider mb-2">
            <span>Total Cameras</span>
            <Camera className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-extrabold text-white tracking-tight">{stats.total_cameras}</div>
          <div className="text-xs text-slate-400 mt-2 flex items-center">
            <span className="text-emerald-400 font-semibold mr-1">520+ Nodes</span> Across 10 Districts
          </div>
        </div>

        {/* Online Uptime Ratio */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-lg backdrop-blur hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium uppercase tracking-wider mb-2">
            <span>System Telemetry</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-emerald-400 tracking-tight">
            {stats.system_uptime_percentage}%
          </div>
          <div className="text-xs text-slate-400 mt-2 flex items-center">
            <span className="text-emerald-400 font-semibold mr-1">{stats.online_cameras} Online</span> / {stats.offline_cameras} Offline
          </div>
        </div>

        {/* Active SLA Tickets */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-lg backdrop-blur hover:border-slate-700 transition cursor-pointer" onClick={() => onNavigate('maintenance')}>
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium uppercase tracking-wider mb-2">
            <span>Active Tickets</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-extrabold text-amber-400 tracking-tight">
            {stats.active_maintenance_tickets}
          </div>
          <div className="text-xs text-slate-400 mt-2 flex items-center">
            <span className="text-amber-400 font-semibold mr-1">SLA Tracked</span> Click to Manage
          </div>
        </div>

        {/* Storage Capacity */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-lg backdrop-blur hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium uppercase tracking-wider mb-2">
            <span>Storage Capacity</span>
            <HardDrive className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-3xl font-extrabold text-purple-400 tracking-tight">
            {stats.total_storage_capacity_tb} TB
          </div>
          <div className="text-xs text-slate-400 mt-2">
            7 to 90 Days Retention Policy
          </div>
        </div>

        {/* Sovereign Departments */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-lg backdrop-blur hover:border-slate-700 transition cursor-pointer" onClick={() => onNavigate('registry')}>
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium uppercase tracking-wider mb-2">
            <span>Departments</span>
            <Building2 className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-3xl font-extrabold text-blue-400 tracking-tight">
            {stats.total_departments}
          </div>
          <div className="text-xs text-slate-400 mt-2">
            100% Federation Mapped
          </div>
        </div>
      </div>

      {/* Main Charts & Analytics Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* AI Detections & Alert Trend Chart */}
        <div className="lg:col-span-2 bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-semibold text-white flex items-center">
                <TrendingUp className="w-5 h-5 text-cyan-400 mr-2" />
                AI Computer Vision Detections & Incident Trends (7 Days)
              </h3>
              <p className="text-xs text-slate-400">Real-time telemetry aggregated across ANPR, Intrusion, and Node status</p>
            </div>
            <span className="text-xs bg-cyan-950 text-cyan-400 border border-cyan-800 px-2.5 py-1 rounded-full font-mono">
              Live Stream Broker
            </span>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={stats.alert_trends_7days} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="anprColor" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="intrusionColor" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }}
                />
                <Area type="monotone" dataKey="anpr_hits" name="ANPR Plate Matches" stroke="#06b6d4" fillOpacity={1} fill="url(#anprColor)" />
                <Area type="monotone" dataKey="intrusion_alerts" name="Restricted Zone Intrusions" stroke="#f59e0b" fillOpacity={1} fill="url(#intrusionColor)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Live System Alerts Feed */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-semibold text-white flex items-center">
                <ShieldAlert className="w-5 h-5 text-amber-400 mr-2" />
                Real-Time Watchlist & Alert Feed
              </h3>
              <span className="flex h-2 w-2 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
              </span>
            </div>

            <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
              <div className="p-3 bg-red-950/40 border border-red-800/60 rounded-lg text-xs">
                <div className="flex justify-between items-center text-red-300 font-semibold mb-1">
                  <span>WATCHLIST HIT: MH-12-AB-1234</span>
                  <span className="font-mono text-[10px] bg-red-900 text-red-200 px-1.5 py-0.5 rounded">CRITICAL</span>
                </div>
                <p className="text-slate-300">Stolen Black SUV detected at Highway Junction Cam #042</p>
                <div className="text-slate-400 mt-1 font-mono text-[10px]">2 mins ago • Police Department</div>
              </div>

              <div className="p-3 bg-amber-950/40 border border-amber-800/60 rounded-lg text-xs">
                <div className="flex justify-between items-center text-amber-300 font-semibold mb-1">
                  <span>RESTRICTED INTRUSION DETECTED</span>
                  <span className="font-mono text-[10px] bg-amber-900 text-amber-200 px-1.5 py-0.5 rounded">HIGH</span>
                </div>
                <p className="text-slate-300">Zone perimeter crossed at Food Supply Godown Gate 3</p>
                <div className="text-slate-400 mt-1 font-mono text-[10px]">14 mins ago • Food & Civil Supplies</div>
              </div>

              <div className="p-3 bg-slate-800/60 border border-slate-700 rounded-lg text-xs">
                <div className="flex justify-between items-center text-slate-200 font-semibold mb-1">
                  <span>CAMERA OFFLINE TRIGGER</span>
                  <span className="font-mono text-[10px] bg-slate-700 text-slate-300 px-1.5 py-0.5 rounded">AUTO-TICKET</span>
                </div>
                <p className="text-slate-300">RTO Node #018 loss of RTSP stream heartbeat signal</p>
                <div className="text-slate-400 mt-1 font-mono text-[10px]">35 mins ago • RTO Dept</div>
              </div>
            </div>
          </div>

          <button 
            onClick={() => onNavigate('anpr')}
            className="w-full mt-4 py-2 bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs font-semibold rounded-lg border border-slate-700 transition"
          >
            Launch ANPR Route Reconstruction & AI Hub →
          </button>
        </div>
      </div>

      {/* 26 Sovereign Department Breakdown Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-semibold text-white flex items-center">
              <Building2 className="w-5 h-5 text-blue-400 mr-2" />
              Sovereign Department Federation Matrix (26 Sovereign Entities)
            </h3>
            <p className="text-xs text-slate-400">Departmental node distribution, active telemetry ratio, and purpose taxonomy</p>
          </div>
          <button 
            onClick={() => onNavigate('registry')}
            className="text-xs bg-blue-950 text-blue-300 border border-blue-800 px-3 py-1.5 rounded-lg hover:bg-blue-900 transition"
          >
            View Camera Registry & Bulk Import →
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase font-semibold text-[11px] border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Dept ID</th>
                <th className="py-3 px-4">Department Name</th>
                <th className="py-3 px-4">Code</th>
                <th className="py-3 px-4 text-center">Active / Total Nodes</th>
                <th className="py-3 px-4">Telemetry Health</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {stats.department_breakdown.map((dept) => (
                <tr key={dept.dept_id} className="hover:bg-slate-800/40 transition">
                  <td className="py-2.5 px-4 font-mono text-cyan-400 font-semibold">{dept.dept_id}</td>
                  <td className="py-2.5 px-4 font-medium text-white">{dept.dept_name}</td>
                  <td className="py-2.5 px-4"><span className="bg-slate-800 px-2 py-0.5 rounded font-mono">{dept.dept_code}</span></td>
                  <td className="py-2.5 px-4 text-center font-mono">{dept.active_cameras} / {dept.total_cameras}</td>
                  <td className="py-2.5 px-4">
                    <div className="flex items-center space-x-2">
                      <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full ${dept.uptime_percent >= 90 ? 'bg-emerald-400' : dept.uptime_percent >= 75 ? 'bg-amber-400' : 'bg-red-400'}`}
                          style={{ width: `${dept.uptime_percent}%` }}
                        />
                      </div>
                      <span className="font-mono text-[11px] text-slate-400 w-12 text-right">{dept.uptime_percent}%</span>
                    </div>
                  </td>
                  <td className="py-2.5 px-4 text-right">
                    <button 
                      onClick={() => onNavigate('registry')}
                      className="text-cyan-400 hover:underline text-xs"
                    >
                      Filter Nodes
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
