import React, { useState, useEffect } from 'react';
import { 
  Wrench, 
  Clock, 
  CheckCircle2, 
  Camera as CameraIcon, 
  Upload, 
  AlertTriangle, 
  Check, 
  UserCheck,
  FileText
} from 'lucide-react';
import { User, MaintenanceTicket } from '../types';

interface TechnicianDashboardProps {
  currentUser: User;
}

export const TechnicianDashboard: React.FC<TechnicianDashboardProps> = ({ currentUser }) => {
  const [tasks, setTasks] = useState<MaintenanceTicket[]>([]);
  const [loading, setLoading] = useState(true);

  // Selected Task to update
  const [selectedTask, setSelectedTask] = useState<MaintenanceTicket | null>(null);
  const [status, setStatus] = useState<string>('In Progress');
  const [notes, setNotes] = useState<string>('');
  const [photoUrl, setPhotoUrl] = useState<string>('https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=400&q=80');

  const fetchAssignedTasks = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/technician/tasks?tech_email=${encodeURIComponent(currentUser.email)}`);
      const data = await res.json();
      setTasks(data || []);
    } catch (e) {
      console.error('Failed to load technician tasks', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssignedTasks();
  }, [currentUser]);

  const handleUpdateTask = async () => {
    if (!selectedTask) return;
    try {
      const res = await fetch(`/api/tickets/${selectedTask.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: status,
          resolution_summary: notes || 'Field repair completed and verified by engineer.',
          photo_evidence_url: photoUrl
        })
      });
      const data = await res.json();
      if (data.success) {
        setSelectedTask(null);
        setNotes('');
        fetchAssignedTasks();
      }
    } catch (e) {
      console.error('Failed to update task', e);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-400"></div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Mobile-Responsive Header */}
      <div className="bg-slate-900/90 border border-slate-800 p-5 rounded-2xl shadow-lg space-y-2">
        <div className="flex justify-between items-center">
          <div className="inline-flex items-center space-x-1.5 bg-amber-950/80 text-amber-400 border border-amber-800/80 px-2.5 py-0.5 rounded-full text-xs font-mono font-bold">
            <UserCheck className="w-3.5 h-3.5" />
            <span>TECHNICIAN FIELD WORK ORDERS</span>
          </div>
          <span className="text-xs font-mono text-slate-400">Badge: {currentUser.badgeCode}</span>
        </div>

        <h2 className="text-xl font-extrabold text-white">{currentUser.name} — Service Queue</h2>
        <p className="text-xs text-slate-400">
          Showing assigned service checklists for <strong className="text-amber-400">{currentUser.email}</strong>
        </p>
      </div>

      {/* Task Cards List */}
      <div className="space-y-4">
        {tasks.length > 0 ? (
          tasks.map((task) => (
            <div 
              key={task.id} 
              className={`bg-slate-900/90 border rounded-2xl p-5 shadow-xl space-y-3 transition ${
                task.status === 'Resolved' || task.status === 'Closed' 
                  ? 'border-emerald-800/60 bg-slate-900/40 opacity-75' 
                  : 'border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex justify-between items-start">
                <div>
                  <span className="font-mono text-xs text-amber-400 font-bold">{task.ticket_code}</span>
                  <h3 className="text-base font-bold text-white mt-0.5">{task.camera_name}</h3>
                  <p className="text-xs text-slate-400">{task.dept_name} • {task.vendor_name}</p>
                </div>
                <span className={`px-2.5 py-1 rounded text-xs font-semibold ${
                  task.status === 'Resolved' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' :
                  task.status === 'In Progress' ? 'bg-amber-950 text-amber-400 border border-amber-800' :
                  'bg-slate-800 text-slate-300 border border-slate-700'
                }`}>
                  {task.status}
                </span>
              </div>

              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-xs space-y-1">
                <div className="text-slate-300 font-medium">Issue: <strong className="text-white">{task.issue_type}</strong></div>
                <div className="text-slate-400 font-mono">SLA Due: <span className="text-amber-300">{task.sla_due_at}</span></div>
                <div className="text-slate-400">Repair Cost Est: ₹{task.repair_cost_inr}</div>
              </div>

              {task.resolution_summary && (
                <div className="text-xs bg-slate-950/80 p-2.5 rounded-lg border border-slate-800 text-slate-300">
                  <strong className="text-emerald-400">Resolution Notes:</strong> {task.resolution_summary}
                </div>
              )}

              <div className="flex justify-end pt-1">
                <button 
                  onClick={() => {
                    setSelectedTask(task);
                    setStatus(task.status);
                    setNotes(task.resolution_summary || '');
                  }}
                  className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white font-semibold rounded-xl text-xs shadow-lg shadow-amber-600/20 transition flex items-center space-x-1.5"
                >
                  <Wrench className="w-3.5 h-3.5" />
                  <span>Update Service Status</span>
                </button>
              </div>
            </div>
          ))
        ) : (
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-8 text-center text-xs text-slate-400">
            No active work orders assigned to your account.
          </div>
        )}
      </div>

      {/* Task Update Modal */}
      {selectedTask && (
        <div className="fixed inset-0 z-[99999] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white flex items-center">
              <Wrench className="w-5 h-5 text-amber-400 mr-2" />
              Update Work Order: {selectedTask.ticket_code}
            </h3>

            <div>
              <label className="text-xs text-slate-300 block mb-1">Work Order Status</label>
              <select 
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
              >
                <option value="In Progress">In Progress</option>
                <option value="Awaiting Parts">Awaiting Parts</option>
                <option value="Resolved">Resolved (Field Verified)</option>
              </select>
            </div>

            <div>
              <label className="text-xs text-slate-300 block mb-1">Field Service & Parts Replaced Notes *</label>
              <textarea 
                rows={3}
                placeholder="Document replaced components, cable splicing, PTZ motor fix..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-amber-500"
              />
            </div>

            <div>
              <label className="text-xs text-slate-300 block mb-1">Proof-of-Work Photo Evidence URL</label>
              <input 
                type="text"
                value={photoUrl}
                onChange={(e) => setPhotoUrl(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-amber-500"
              />
            </div>

            <div className="flex justify-end space-x-3 pt-2">
              <button onClick={() => setSelectedTask(null)} className="px-4 py-2 bg-slate-800 text-slate-300 rounded-xl text-xs">
                Cancel
              </button>
              <button 
                onClick={handleUpdateTask}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-xl text-xs shadow-lg shadow-emerald-600/20"
              >
                Commit Field Resolution
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
