import React, { useEffect, useState } from "react";
import axios from "axios";

export interface ApprovedUser {
  id: number | string;
  username: string;
  email: string;
  full_name: string;
  employee_id: string;
  department: string;
  role: string;
  verification_status: string;
  is_active: boolean;
  created_at?: string;
  approved_at?: string;
}

interface ApprovedUsersPanelProps {
  refreshTrigger?: number;
  onRefreshRequested?: () => void;
}

export const ApprovedUsersPanel: React.FC<ApprovedUsersPanelProps> = ({ refreshTrigger }) => {
  const [users, setUsers] = useState<ApprovedUser[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>("");

  const fetchApprovedUsers = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem("access_token");
      const res = await axios.get<ApprovedUser[]>("/api/v1/admin/users/approved", {
        headers: { Authorization: `Bearer ${token}` },
      });
      // Rule 3: Defensive fallback to prevent runtime crashes
      setUsers(res.data || []);
      setError(null);
    } catch (err: any) {
      console.error("Failed to load approved users", err);
      setError(err?.response?.data?.detail || "Failed to load approved staff registry.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovedUsers();
  }, [refreshTrigger]);

  const filteredUsers = (users || []).filter((u) => {
    const q = searchTerm.toLowerCase();
    return (
      (u.username || "").toLowerCase().includes(q) ||
      (u.full_name || "").toLowerCase().includes(q) ||
      (u.email || "").toLowerCase().includes(q) ||
      (u.department || "").toLowerCase().includes(q) ||
      (u.employee_id || "").toLowerCase().includes(q) ||
      (u.role || "").toLowerCase().includes(q)
    );
  });

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 backdrop-blur-md">
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
            Approved Government Personnel Directory
            <span className="text-xs font-mono font-normal bg-cyan-950 text-cyan-400 border border-cyan-800/60 px-2 py-0.5 rounded-full">
              {(users || []).length} Verified Staff
            </span>
          </h2>
          <p className="text-xs text-slate-400">
            Active staff verified and cleared for CCTV Command access.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <input
            type="text"
            placeholder="Filter by name, badge ID, or handle..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 w-64"
          />
          <button
            onClick={fetchApprovedUsers}
            className="rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700 transition-colors flex items-center gap-1.5"
          >
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {loading ? (
        <div className="py-12 text-center text-xs text-slate-500 font-mono">
          <div className="inline-block animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-cyan-400 mb-2"></div>
          <div>Loading approved personnel directory...</div>
        </div>
      ) : error ? (
        <div className="rounded-lg border border-red-500/30 bg-red-950/20 p-3 text-xs text-red-400 font-mono">
          {error}
        </div>
      ) : filteredUsers.length === 0 ? (
        <div className="py-12 text-center text-xs text-slate-500 font-mono">
          No approved users match the current criteria.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="border-b border-slate-800 bg-slate-950/60 uppercase text-[11px] font-semibold text-slate-400">
              <tr>
                <th className="px-4 py-3">Official Handle</th>
                <th className="px-4 py-3">Full Name & Email</th>
                <th className="px-4 py-3">Badge / Gov ID</th>
                <th className="px-4 py-3">Department</th>
                <th className="px-4 py-3">Role Assigned</th>
                <th className="px-4 py-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredUsers.map((u) => (
                <tr key={u.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3 font-mono font-medium text-cyan-400">
                    @{u.username}
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-medium text-slate-200">{u.full_name}</div>
                    <div className="text-[11px] text-slate-500">{u.email}</div>
                  </td>
                  <td className="px-4 py-3 font-mono text-slate-400">
                    {u.employee_id}
                  </td>
                  <td className="px-4 py-3 text-slate-300">
                    {u.department}
                  </td>
                  <td className="px-4 py-3">
                    <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-semibold tracking-wide text-slate-300 border border-slate-700/60">
                      {u.role}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-950/60 border border-emerald-500/40 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-400">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      Active / Verified
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default ApprovedUsersPanel;
