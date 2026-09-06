import React, { useState, useEffect } from 'react';
import { 
  Building2, 
  Camera, 
  CheckCircle2, 
  AlertTriangle, 
  Upload, 
  Wrench, 
  ShieldCheck,
  Plus,
  Lock
} from 'lucide-react';
import { User, Camera as CameraType, MaintenanceTicket } from '../types';

interface DepartmentAdminDashboardProps {
  currentUser: User;
  onNavigate: (tab: string) => void;
}

export const DepartmentAdminDashboard: React.FC<DepartmentAdminDashboardProps> = ({ currentUser, onNavigate }) => {
  const [deptCameras, setDeptCameras] = useState<CameraType[]>([]);
  const [deptTickets, setDeptTickets] = useState<MaintenanceTicket[]>([]);
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [loading, setLoading] = useState(true);

  const deptId = currentUser.departmentId || 'DEPT-01';
  const deptName = currentUser.departmentName || 'Gujarat Police Department';

  const fetchDepartmentData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token') || '';
      const [camRes, tktRes, countRes] = await Promise.all([
        fetch(`/api/cameras?dept_id=${deptId}&limit=100`),
        fetch(`/api/tickets?status=Open`),
        fetch('/api/v1/admin/users/pending/count', {
          headers: { 'Authorization': `Bearer ${token}` }
        }).catch(() => null)
      ]);

      const cData = await camRes.json();
      const tData = await tktRes.json();

      setDeptCameras(cData.cameras || []);
      // Filter tickets strictly for this department
      const filteredTickets = (tData || []).filter((t: any) => t.dept_id === deptId);
      setDeptTickets(filteredTickets);

      if (countRes && countRes.ok) {
        const countData = await countRes.json();
        setPendingCount(countData.pending_count || 0);
      }
    } catch (e) {
      console.error('Failed to load department data', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDepartmentData();
  }, [deptId]);

  const onlineCount = deptCameras.filter((c) => c.is_online).length;
  const offlineCount = deptCameras.length - onlineCount;
  const uptimePercent = deptCameras.length > 0 ? ((onlineCount / deptCameras.length) * 100).toFixed(1) : '100.0';

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="bg-slate-900/90 border border-slate-800 p-5 rounded-xl shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="bg-blue-950 text-blue-400 border border-blue-800 px-2.5 py-0.5 rounded font-mono text-[10px] font-bold uppercase">
              RLS MULTI-TENANT ISOLATED
            </span>
            <span className="text-xs text-slate-400 font-mono">Scope: {deptId}</span>
          </div>
          <h2 className="text-xl font-bold text-white flex items-center mt-1">
            <Building2 className="w-6 h-6 text-blue-400 mr-2.5" />
            {deptName} — Departmental Command Center
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Managing departmental node assets, camera onboarding approvals, and AMC ticket resolutions
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button 
            onClick={() => onNavigate('registry')}
            className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white text-xs font-semibold rounded-lg shadow-lg shadow-blue-500/20 transition"
          >
            <Upload className="w-4 h-4" />
            <span>Onboard Department Camera</span>
          </button>
        </div>
      </div>

      {/* RLS Multi-Tenancy Security Banner */}
      <div className="bg-blue-950/40 border border-blue-800/80 p-3.5 rounded-xl flex items-center justify-between text-xs text-blue-200">
        <div className="flex items-center space-x-2">
          <Lock className="w-4 h-4 text-blue-400" />
          <span>
            <strong>Row-Level Security (RLS) Active:</strong> Your session is strictly scoped to <strong>{deptName}</strong>. Access to external department assets or tickets is prohibited.
          </span>
        </div>
        <span className="font-mono text-[10px] bg-blue-900 px-2 py-0.5 rounded border border-blue-700">WHERE dept_id = '{deptId}'</span>
      </div>

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
                  DEPARTMENT PERSONNEL CLEARANCES REQUIRED
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

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-lg">
          <div className="text-xs text-slate-400 uppercase font-semibold">Department Cameras</div>
          <div className="text-3xl font-extrabold text-white mt-1">{deptCameras.length}</div>
          <p className="text-xs text-slate-400 mt-1">Registered in {deptId}</p>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-lg">
          <div className="text-xs text-slate-400 uppercase font-semibold">Department Telemetry Uptime</div>
          <div className="text-3xl font-extrabold text-emerald-400 mt-1">{uptimePercent}%</div>
          <p className="text-xs text-slate-400 mt-1">{onlineCount} Online / {offlineCount} Offline</p>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-lg">
          <div className="text-xs text-slate-400 uppercase font-semibold">Open Maintenance Tickets</div>
          <div className="text-3xl font-extrabold text-amber-400 mt-1">{deptTickets.length}</div>
          <p className="text-xs text-slate-400 mt-1">Requiring AMC repair</p>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-lg">
          <div className="text-xs text-slate-400 uppercase font-semibold">Nodal Officer Badge</div>
          <div className="text-base font-bold text-cyan-400 mt-1 font-mono">{currentUser.badgeCode}</div>
          <p className="text-xs text-slate-400 mt-1">{currentUser.name}</p>
        </div>
      </div>

      {/* Department Camera Registry Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl shadow-lg overflow-hidden space-y-3">
        <div className="p-4 border-b border-slate-800 flex justify-between items-center text-xs">
          <h3 className="font-bold text-white text-base">Department Camera Node Registry</h3>
          <span className="text-slate-400 font-mono text-[11px]">Showing {deptCameras.length} nodes</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase font-semibold text-[11px] border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Asset Code</th>
                <th className="py-3 px-4">Camera Name</th>
                <th className="py-3 px-4">District</th>
                <th className="py-3 px-4">Hardware Type</th>
                <th className="py-3 px-4">NVR IP / Port</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {deptCameras.map((cam) => (
                <tr key={cam.id} className="hover:bg-slate-800/40 transition">
                  <td className="py-2.5 px-4 font-mono text-cyan-400 font-semibold">{cam.asset_code}</td>
                  <td className="py-2.5 px-4 font-medium text-white">{cam.name}</td>
                  <td className="py-2.5 px-4">{cam.district}</td>
                  <td className="py-2.5 px-4"><span className="bg-slate-800 px-2 py-0.5 rounded text-[11px]">{cam.camera_type}</span></td>
                  <td className="py-2.5 px-4 font-mono text-slate-400">{cam.nvr_ip}:{cam.nvr_port}</td>
                  <td className="py-2.5 px-4">
                    <span className={`font-semibold ${cam.is_online ? 'text-emerald-400' : 'text-red-400'}`}>
                      {cam.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-4 text-right">
                    <button 
                      onClick={() => onNavigate('registry')}
                      className="text-cyan-400 hover:underline text-xs"
                    >
                      Manage Node
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
