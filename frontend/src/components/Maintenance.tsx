import React, { useState, useEffect } from 'react';
import { 
  Wrench, 
  Plus, 
  Clock, 
  AlertTriangle, 
  CheckCircle2, 
  UserCheck, 
  Image, 
  ShieldCheck,
  Search,
  Filter,
  DollarSign,
  X
} from 'lucide-react';
import { MaintenanceTicket, Camera } from '../types';

interface MaintenanceProps {
  cameras: Camera[];
}

export const Maintenance: React.FC<MaintenanceProps> = ({ cameras }) => {
  const [tickets, setTickets] = useState<MaintenanceTicket[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [loading, setLoading] = useState(false);

  // New Ticket Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedCamId, setSelectedCamId] = useState('');
  const [issueType, setIssueType] = useState('No Video Stream Signal');
  const [severity, setSeverity] = useState<'Critical' | 'High' | 'Medium' | 'Low'>('High');
  const [technician, setTechnician] = useState('Tech. Aniket Shinde');

  // Update Status Modal
  const [updatingTicket, setUpdatingTicket] = useState<MaintenanceTicket | null>(null);
  const [newStatus, setNewStatus] = useState<string>('In Progress');
  const [resolutionSummary, setResolutionSummary] = useState<string>('');

  const fetchTickets = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      if (severityFilter) params.append('severity', severityFilter);

      const res = await fetch(`/api/tickets?${params.toString()}`);
      const data = await res.json();
      setTickets(data || []);
    } catch (e) {
      console.error('Failed to fetch tickets', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, [statusFilter, severityFilter]);

  const handleCreateTicket = async () => {
    if (!selectedCamId) return;
    try {
      const res = await fetch('/api/tickets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          camera_id: selectedCamId,
          issue_type: issueType,
          severity: severity,
          assigned_technician: technician,
          repair_cost_inr: 4500.0
        })
      });
      const data = await res.json();
      if (data.success) {
        setShowCreateModal(false);
        fetchTickets();
      }
    } catch (e) {
      console.error('Failed to create ticket', e);
    }
  };

  const handleUpdateStatus = async () => {
    if (!updatingTicket) return;
    try {
      const res = await fetch(`/api/tickets/${updatingTicket.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: newStatus,
          resolution_summary: resolutionSummary
        })
      });
      const data = await res.json();
      if (data.success) {
        setUpdatingTicket(null);
        setResolutionSummary('');
        fetchTickets();
      }
    } catch (e) {
      console.error('Failed to update ticket', e);
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'Critical':
        return <span className="bg-red-950 text-red-400 border border-red-800 px-2 py-0.5 rounded font-mono text-[10px] font-bold">CRITICAL (SLA 2H)</span>;
      case 'High':
        return <span className="bg-amber-950 text-amber-400 border border-amber-800 px-2 py-0.5 rounded font-mono text-[10px] font-bold">HIGH (SLA 6H)</span>;
      case 'Medium':
        return <span className="bg-blue-950 text-blue-400 border border-blue-800 px-2 py-0.5 rounded font-mono text-[10px] font-bold">MEDIUM (SLA 24H)</span>;
      default:
        return <span className="bg-slate-800 text-slate-300 border border-slate-700 px-2 py-0.5 rounded font-mono text-[10px]">LOW (SLA 48H)</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="bg-slate-900/90 border border-slate-800 p-5 rounded-xl shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center">
            <Wrench className="w-6 h-6 text-amber-400 mr-2.5" />
            Maintenance Management & SLA Ticketing Engine
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Automated ticket escalation for offline nodes, technician dispatch matrix, and AMC repair logs
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button 
            onClick={() => {
              if (cameras.length > 0) setSelectedCamId(cameras[0].id);
              setShowCreateModal(true);
            }}
            className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white text-xs font-semibold rounded-lg shadow-lg shadow-amber-500/20 transition"
          >
            <Plus className="w-4 h-4" />
            <span>Create Inspection Ticket</span>
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl shadow-lg flex flex-wrap gap-4 items-center">
        <div>
          <select 
            value={statusFilter} 
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
          >
            <option value="">All Ticket Statuses</option>
            <option value="Open">Open</option>
            <option value="Assigned">Assigned</option>
            <option value="In Progress">In Progress</option>
            <option value="Resolved">Resolved</option>
            <option value="Closed">Closed</option>
          </select>
        </div>

        <div>
          <select 
            value={severityFilter} 
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
          >
            <option value="">All Severity SLAs</option>
            <option value="Critical">Critical (2h)</option>
            <option value="High">High (6h)</option>
            <option value="Medium">Medium (24h)</option>
            <option value="Low">Low (48h)</option>
          </select>
        </div>
      </div>

      {/* Tickets Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl shadow-lg overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex justify-between items-center text-xs text-slate-400">
          <span>Active Tickets: <strong className="text-white">{tickets.length}</strong></span>
          <span className="font-mono text-amber-400">AMC Vendor SLA Engine Active</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase font-semibold text-[11px] border-b border-slate-800">
              <tr>
                <th className="py-3.5 px-4">Ticket Code</th>
                <th className="py-3.5 px-4">Camera Node</th>
                <th className="py-3.5 px-4">Department Owner</th>
                <th className="py-3.5 px-4">Issue Description</th>
                <th className="py-3.5 px-4">Severity SLA</th>
                <th className="py-3.5 px-4">Assigned Technician</th>
                <th className="py-3.5 px-4">AMC Vendor</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {tickets.map((t) => (
                <tr key={t.id} className="hover:bg-slate-800/50 transition">
                  <td className="py-3 px-4 font-mono text-amber-400 font-bold">{t.ticket_code}</td>
                  <td className="py-3 px-4 font-medium text-white">{t.camera_name}</td>
                  <td className="py-3 px-4">{t.dept_name}</td>
                  <td className="py-3 px-4 text-slate-300">{t.issue_type}</td>
                  <td className="py-3 px-4">{getSeverityBadge(t.severity)}</td>
                  <td className="py-3 px-4 font-mono text-slate-300">{t.assigned_technician}</td>
                  <td className="py-3 px-4">{t.vendor_name}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${t.status === 'Resolved' || t.status === 'Closed' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-amber-950 text-amber-400 border border-amber-800'}`}>
                      {t.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button 
                      onClick={() => {
                        setUpdatingTicket(t);
                        setNewStatus(t.status);
                      }}
                      className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-amber-400 rounded text-[11px] transition"
                    >
                      Update Status
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Ticket Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white flex items-center">
              <Wrench className="w-5 h-5 text-amber-400 mr-2" />
              Create Maintenance Inspection Ticket
            </h3>

            <div>
              <label className="text-xs text-slate-300 block mb-1">Target Camera Node *</label>
              <select 
                value={selectedCamId}
                onChange={(e) => setSelectedCamId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
              >
                {cameras.map((c) => (
                  <option key={c.id} value={c.id}>{c.asset_code} - {c.name} ({c.dept_name})</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs text-slate-300 block mb-1">Issue Classification</label>
              <select 
                value={issueType}
                onChange={(e) => setIssueType(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
              >
                <option value="No Video Stream Signal">No Video Stream Signal</option>
                <option value="Network Loss / High Latency">Network Loss / High Latency</option>
                <option value="PTZ Motor Failure">PTZ Motor Failure</option>
                <option value="IR Illuminator Fault">IR Illuminator Fault</option>
                <option value="Power Surge Issue">Power Surge Issue</option>
              </select>
            </div>

            <div>
              <label className="text-xs text-slate-300 block mb-1">Severity SLA Level</label>
              <select 
                value={severity}
                onChange={(e) => setSeverity(e.target.value as any)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
              >
                <option value="Critical">Critical (2 Hours SLA)</option>
                <option value="High">High (6 Hours SLA)</option>
                <option value="Medium">Medium (24 Hours SLA)</option>
                <option value="Low">Low (48 Hours SLA)</option>
              </select>
            </div>

            <div>
              <label className="text-xs text-slate-300 block mb-1">Assigned Technician</label>
              <input 
                type="text"
                value={technician}
                onChange={(e) => setTechnician(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
              />
            </div>

            <div className="flex justify-end space-x-3 pt-2">
              <button onClick={() => setShowCreateModal(false)} className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg text-xs">
                Cancel
              </button>
              <button 
                onClick={handleCreateTicket}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white font-semibold rounded-lg text-xs"
              >
                Dispatch Ticket
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Update Ticket Modal */}
      {updatingTicket && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white flex items-center">
              <Wrench className="w-5 h-5 text-amber-400 mr-2" />
              Update Ticket Workflow State
            </h3>
            <p className="text-xs text-slate-400">Code: <strong className="text-white font-mono">{updatingTicket.ticket_code}</strong></p>

            <div>
              <label className="text-xs text-slate-300 block mb-1">Workflow Status</label>
              <select 
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
              >
                <option value="Open">Open</option>
                <option value="Assigned">Assigned</option>
                <option value="In Progress">In Progress</option>
                <option value="Resolved">Resolved</option>
                <option value="Closed">Closed</option>
              </select>
            </div>

            <div>
              <label className="text-xs text-slate-300 block mb-1">Resolution / AMC Action Notes</label>
              <textarea 
                rows={3}
                placeholder="Log repair summary or parts replaced..."
                value={resolutionSummary}
                onChange={(e) => setResolutionSummary(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-amber-500"
              />
            </div>

            <div className="flex justify-end space-x-3 pt-2">
              <button onClick={() => setUpdatingTicket(null)} className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg text-xs">
                Cancel
              </button>
              <button 
                onClick={handleUpdateStatus}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-lg text-xs"
              >
                Save Resolution
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
