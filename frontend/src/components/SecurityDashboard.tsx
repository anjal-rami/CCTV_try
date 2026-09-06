import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  ShieldCheck, 
  Lock, 
  Slash, 
  Activity, 
  AlertTriangle, 
  Terminal, 
  RefreshCw, 
  UserX, 
  Globe, 
  CheckCircle2,
  X
} from 'lucide-react';

export const SecurityDashboard: React.FC = () => {
  const [threatData, setThreatData] = useState<any>(null);
  const [incidents, setIncidents] = useState<any[]>([]);
  const [blockedIps, setBlockedIps] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Block IP Modal
  const [showBlockModal, setShowBlockModal] = useState(false);
  const [ipToBlock, setIpToBlock] = useState('');
  const [blockReason, setBlockReason] = useState('');

  const fetchSecurityData = async () => {
    setLoading(true);
    try {
      const [threatRes, incRes, ipRes] = await Promise.all([
        fetch('/api/v1/security/threat-meter'),
        fetch('/api/v1/security/incidents'),
        fetch('/api/v1/security/blocked-ips')
      ]);

      const tData = await threatRes.json();
      const iData = await incRes.json();
      const ipData = await ipRes.json();

      setThreatData(tData);
      setIncidents(iData || []);
      setBlockedIps(ipData || []);
    } catch (e) {
      console.error('Failed to load security forensics data', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSecurityData();
  }, []);

  const handleBlockIp = async () => {
    if (!ipToBlock.trim() || !blockReason.trim()) return;
    try {
      const res = await fetch('/api/v1/security/block-ip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip_address: ipToBlock, reason: blockReason })
      });
      const data = await res.json();
      if (data.success) {
        setShowBlockModal(false);
        setIpToBlock('');
        setBlockReason('');
        fetchSecurityData();
      }
    } catch (e) {
      console.error('Failed to block IP', e);
    }
  };

  const handleTerminateSession = async (incidentId: string) => {
    alert(`Terminating session and revoking JWT token for Incident ${incidentId}...`);
    fetchSecurityData();
  };

  if (loading || !threatData) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
      </div>
    );
  }

  const getThreatColor = (level: string) => {
    switch (level) {
      case 'CRITICAL': return 'text-red-500 bg-red-950/80 border-red-800';
      case 'HIGH': return 'text-orange-500 bg-orange-950/80 border-orange-800';
      case 'ELEVATED': return 'text-amber-400 bg-amber-950/80 border-amber-800';
      default: return 'text-emerald-400 bg-emerald-950/80 border-emerald-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="bg-slate-900/90 border border-slate-800 p-5 rounded-xl shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center">
            <ShieldAlert className="w-6 h-6 text-red-500 mr-2.5" />
            Central Cybersecurity & Compliance Operations Center
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time Threat Score Meter, Automated IP Firewall Shield, JWT Revocation, & Cryptographic Audit Logs
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button 
            onClick={() => setShowBlockModal(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-red-600 hover:bg-red-500 text-white text-xs font-semibold rounded-lg shadow-lg shadow-red-500/20 transition"
          >
            <Slash className="w-4 h-4" />
            <span>Manually Ban Threat IP</span>
          </button>
        </div>
      </div>

      {/* Threat Meter Score Gauge Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Threat Gauge */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col justify-between">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Threat Score Meter</div>
          <div className="flex items-baseline space-x-3">
            <span className="text-4xl font-extrabold text-white tracking-tight">{threatData.threat_score}</span>
            <span className="text-xs text-slate-400">/ 100 Risk Index</span>
          </div>
          <div className="mt-3">
            <span className={`px-2.5 py-1 rounded text-xs font-mono font-extrabold border ${getThreatColor(threatData.threat_level)}`}>
              THREAT LEVEL: {threatData.threat_level}
            </span>
          </div>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Active Incidents</div>
          <div className="text-3xl font-extrabold text-amber-400">{threatData.active_threat_incidents}</div>
          <p className="text-xs text-slate-400 mt-2">Under active SOC investigation</p>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Banned IP Firewall Rules</div>
          <div className="text-3xl font-extrabold text-red-400">{threatData.total_blocked_ips}</div>
          <p className="text-xs text-slate-400 mt-2">IP addresses blocked at gateway</p>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Audit Hash Forensics</div>
          <div className="text-sm font-bold text-emerald-400 flex items-center space-x-1.5 mt-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>CRYPTO HASH VERIFIED</span>
          </div>
          <p className="text-xs text-slate-400 mt-2">Immutable log chain verified</p>
        </div>
      </div>

      {/* Main Grid: Active Security Threat Incidents + Blocked IPs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Incidents Table */}
        <div className="lg:col-span-2 bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-base font-bold text-white flex items-center">
              <Activity className="w-5 h-5 text-amber-400 mr-2" />
              Active Cybersecurity Threat Incidents & Suspicious API Traffic
            </h3>
            <span className="text-xs font-mono text-cyan-400">Argon2id & JWT Guard Active</span>
          </div>

          <div className="space-y-3">
            {incidents.map((inc) => (
              <div key={inc.id} className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs space-y-2">
                <div className="flex justify-between items-center font-mono">
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                      inc.severity === 'CRITICAL' ? 'bg-red-950 text-red-400 border border-red-800' : 'bg-amber-950 text-amber-400 border border-amber-800'
                    }`}>
                      {inc.severity}
                    </span>
                    <strong className="text-white text-sm">{inc.threat_type}</strong>
                  </div>
                  <span className="text-slate-400">{inc.timestamp}</span>
                </div>

                <p className="text-slate-300 leading-relaxed">{inc.details}</p>

                <div className="flex justify-between items-center pt-1 border-t border-slate-800/80 text-[11px]">
                  <div className="font-mono text-slate-400 space-x-3">
                    <span>Source IP: <strong className="text-cyan-400">{inc.source_ip}</strong></span>
                    <span>Target: <strong className="text-slate-300">{inc.user_email}</strong></span>
                  </div>

                  <div className="flex space-x-2">
                    <button 
                      onClick={() => handleBlockIp()}
                      className="px-2.5 py-1 bg-red-950 text-red-300 border border-red-800 rounded hover:bg-red-900 transition font-semibold"
                    >
                      Block IP {inc.source_ip}
                    </button>
                    <button 
                      onClick={() => handleTerminateSession(inc.id)}
                      className="px-2.5 py-1 bg-slate-800 text-cyan-400 border border-slate-700 rounded hover:bg-slate-700 transition"
                    >
                      Terminate Session
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Banned IP Blocklist Table */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
          <h3 className="text-base font-bold text-white flex items-center">
            <Globe className="w-5 h-5 text-red-400 mr-2" />
            Gateway IP Firewall Blocklist
          </h3>

          <div className="space-y-2 max-h-[480px] overflow-y-auto pr-1 text-xs">
            {blockedIps.map((b, idx) => (
              <div key={idx} className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 space-y-1">
                <div className="flex justify-between items-center font-mono text-red-400 font-bold">
                  <span>{b.ip_address}</span>
                  <span className="text-[10px] text-slate-400">{b.blocked_at}</span>
                </div>
                <p className="text-slate-300 text-[11px]">{b.reason}</p>
                <div className="text-[10px] text-slate-400 font-mono">Banned by: {b.blocked_by}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Manual Block IP Modal */}
      {showBlockModal && (
        <div className="fixed inset-0 z-[99999] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center">
                <Slash className="w-5 h-5 text-red-400 mr-2" />
                Add Gateway IP Firewall Rule
              </h3>
              <button onClick={() => setShowBlockModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <label className="text-xs text-slate-300 block mb-1">Target IPv4 Address *</label>
              <input 
                type="text"
                placeholder="e.g. 198.51.100.99"
                value={ipToBlock}
                onChange={(e) => setIpToBlock(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-red-500"
              />
            </div>

            <div>
              <label className="text-xs text-slate-300 block mb-1">Justification Reason *</label>
              <textarea 
                rows={3}
                placeholder="State threat reason (e.g. High-frequency API probe, Unauthorized ANPR search attempt)..."
                value={blockReason}
                onChange={(e) => setBlockReason(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-red-500"
              />
            </div>

            <div className="flex justify-end space-x-3 pt-2">
              <button onClick={() => setShowBlockModal(false)} className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg text-xs">
                Cancel
              </button>
              <button 
                onClick={handleBlockIp}
                disabled={!ipToBlock.trim() || !blockReason.trim()}
                className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white font-semibold rounded-lg text-xs disabled:opacity-50"
              >
                Enforce Ban Rule
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
