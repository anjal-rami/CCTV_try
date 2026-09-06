import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  AlertTriangle, 
  ShieldAlert, 
  FileText, 
  Download, 
  Calendar, 
  CheckCircle2,
  Building2,
  HardDrive
} from 'lucide-react';

export const GapAnalysis: React.FC = () => {
  const [gapData, setGapData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchGapAnalysis = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/gap-analysis');
      const data = await res.json();
      setGapData(data);
    } catch (e) {
      console.error('Failed to fetch gap analysis', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGapAnalysis();
  }, []);

  const triggerExport = (format: string) => {
    alert(`Generating & Downloading Official Government CCTV Infrastructure ${format} Intelligence Report...`);
  };

  if (loading || !gapData) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="bg-slate-900/90 border border-slate-800 p-5 rounded-xl shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center">
            <BarChart3 className="w-6 h-6 text-purple-400 mr-2.5" />
            Analytics Reporting & Infrastructure Gap Analysis
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Identifying coverage blind spots, aging camera hardware (AMC/warranty expiry), and low-density wards
          </p>
        </div>

        {/* Export Buttons */}
        <div className="flex items-center space-x-2">
          <button 
            onClick={() => triggerExport('PDF')}
            className="flex items-center space-x-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-purple-300 border border-slate-700 text-xs font-semibold rounded-lg transition"
          >
            <FileText className="w-4 h-4" />
            <span>Export PDF</span>
          </button>
          <button 
            onClick={() => triggerExport('Excel')}
            className="flex items-center space-x-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-emerald-300 border border-slate-700 text-xs font-semibold rounded-lg transition"
          >
            <Download className="w-4 h-4" />
            <span>Export Excel</span>
          </button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl shadow-lg">
          <div className="text-xs text-slate-400 uppercase font-semibold">Expired AMC Warranty Nodes</div>
          <div className="text-3xl font-extrabold text-red-400 mt-1">{gapData.expired_amc_count}</div>
          <p className="text-xs text-slate-400 mt-1">Requires immediate AMC vendor renewal</p>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl shadow-lg">
          <div className="text-xs text-slate-400 uppercase font-semibold">Expiring Soon AMC (≤ 60 Days)</div>
          <div className="text-3xl font-extrabold text-amber-400 mt-1">{gapData.expiring_soon_amc_count}</div>
          <p className="text-xs text-slate-400 mt-1">Upcoming renewal calendar</p>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl shadow-lg">
          <div className="text-xs text-slate-400 uppercase font-semibold">High Offline Ratio Departments</div>
          <div className="text-3xl font-extrabold text-cyan-400 mt-1">{gapData.high_offline_departments.length}</div>
          <p className="text-xs text-slate-400 mt-1">Departments with ≥ 20% offline nodes</p>
        </div>
      </div>

      {/* High Offline Departments Alert Table */}
      {gapData.high_offline_departments.length > 0 && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg space-y-3">
          <h3 className="text-base font-bold text-white flex items-center">
            <AlertTriangle className="w-5 h-5 text-amber-400 mr-2" />
            High Offline Degradation Department Alert
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950 text-slate-400 uppercase font-semibold text-[11px] border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-4">Dept ID</th>
                  <th className="py-2.5 px-4">Department Name</th>
                  <th className="py-2.5 px-4 text-center">Offline / Total Nodes</th>
                  <th className="py-2.5 px-4 text-right">Offline Degradation %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {gapData.high_offline_departments.map((d: any) => (
                  <tr key={d.dept_id}>
                    <td className="py-2 px-4 font-mono text-cyan-400 font-bold">{d.dept_id}</td>
                    <td className="py-2 px-4 font-medium text-white">{d.dept_name}</td>
                    <td className="py-2 px-4 text-center font-mono text-amber-400">{d.offline_cameras} / {d.total_cameras}</td>
                    <td className="py-2 px-4 text-right font-mono text-red-400 font-bold">{d.offline_percentage}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* District Coverage Summary */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg space-y-3">
        <h3 className="text-base font-bold text-white flex items-center">
          <Building2 className="w-5 h-5 text-cyan-400 mr-2" />
          District Geographic Coverage Density Radar
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {Object.entries(gapData.district_coverage_summary).map(([district, stats]: [string, any]) => (
            <div key={district} className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs space-y-1">
              <div className="font-bold text-white flex justify-between">
                <span>{district}</span>
                <span className="font-mono text-cyan-400">{stats.total} Nodes</span>
              </div>
              <div className="flex justify-between text-slate-400 text-[11px]">
                <span className="text-emerald-400">{stats.online} Online</span>
                <span className="text-red-400">{stats.offline} Offline</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
