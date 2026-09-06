import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  ShieldAlert, 
  CheckCircle2, 
  XCircle, 
  Building2, 
  Clock, 
  Search, 
  RefreshCw, 
  UserCheck, 
  UserX,
  AlertTriangle,
  ChevronRight,
  Filter
} from 'lucide-react';
import { User, PendingUser } from '../types';

interface AdminApprovalsProps {
  currentUser: User;
  onClearanceProcessed?: () => void;
  onNavigateToDashboard?: () => void;
}

export const AdminApprovals: React.FC<AdminApprovalsProps> = ({
  currentUser,
  onClearanceProcessed,
  onNavigateToDashboard
}) => {
  const [pendingUsers, setPendingUsers] = useState<PendingUser[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedDeptFilter, setSelectedDeptFilter] = useState<string>('ALL');
  const [selectedRoles, setSelectedRoles] = useState<Record<string, string>>({});
  const [rejectionModalUser, setRejectionModalUser] = useState<PendingUser | null>(null);
  const [rejectionReason, setRejectionReason] = useState<string>('Credentials verification failed / invalid badge id');
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const isSuperAdmin = currentUser.role === 'SUPER_ADMIN';
  const isDeptAdmin = currentUser.role === 'DEPARTMENT_ADMIN';
  const adminDepartment = currentUser.departmentName || '';

  const fetchPendingApprovals = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token') || '';
      const response = await fetch('/api/v1/admin/users/pending', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPendingUsers(data || []);
      } else if (response.status === 403) {
        setNotification({
          type: 'error',
          message: 'Access Forbidden: Only Super Admins and Department Admins may access user approvals.'
        });
      } else {
        setPendingUsers([]);
      }
    } catch (e) {
      console.error('Failed to fetch pending user approvals:', e);
      setNotification({
        type: 'error',
        message: 'Network error communicating with clearance authority service.'
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPendingApprovals();
  }, [currentUser]);

  const handleRoleChange = (userId: string, role: string) => {
    setSelectedRoles(prev => ({ ...prev, [userId]: role }));
  };

  const handleApproveClearance = async (user: PendingUser) => {
    setActionLoading(user.id);
    const assignedRole = selectedRoles[user.id] || 'OPERATOR';
    const token = localStorage.getItem('access_token') || '';

    try {
      const response = await fetch(`/api/v1/admin/users/${user.id}/clearance`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          action: 'APPROVE',
          assigned_role: assignedRole
        })
      });

      if (response.ok) {
        // Instantly remove approved user from local pending list
        setPendingUsers(prev => prev.filter(u => u.id !== user.id));
        setNotification({
          type: 'success',
          message: `Clearance Granted: ${user.full_name} (${user.email}) approved as ${assignedRole}. User can now log in immediately.`
        });
        if (onClearanceProcessed) onClearanceProcessed();
      } else {
        const errData = await response.json().catch(() => ({ detail: 'Failed to approve clearance.' }));
        setNotification({
          type: 'error',
          message: `Approval failed: ${errData.detail || 'Authorization refused.'}`
        });
      }
    } catch (e) {
      setNotification({
        type: 'error',
        message: 'Network error processing user clearance.'
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleRejectClearance = async () => {
    if (!rejectionModalUser) return;
    const user = rejectionModalUser;
    setActionLoading(user.id);
    const token = localStorage.getItem('access_token') || '';

    try {
      const response = await fetch(`/api/v1/admin/users/${user.id}/clearance`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          action: 'REJECT',
          rejection_reason: rejectionReason
        })
      });

      if (response.ok) {
        // Instantly remove rejected user from local pending list
        setPendingUsers(prev => prev.filter(u => u.id !== user.id));
        setNotification({
          type: 'success',
          message: `Clearance Denied: ${user.full_name}'s registration was rejected.`
        });
        setRejectionModalUser(null);
        if (onClearanceProcessed) onClearanceProcessed();
      } else {
        const errData = await response.json().catch(() => ({ detail: 'Failed to reject clearance.' }));
        setNotification({
          type: 'error',
          message: `Rejection failed: ${errData.detail || 'Request rejected.'}`
        });
      }
    } catch (e) {
      setNotification({
        type: 'error',
        message: 'Network error submitting clearance rejection.'
      });
    } finally {
      setActionLoading(null);
    }
  };

  // Filter pending users by search term and department
  const filteredUsers = pendingUsers.filter(u => {
    const matchesSearch = 
      (u.full_name && u.full_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (u.email && u.email.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (u.username && u.username.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (u.employee_id && u.employee_id.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (u.department && u.department.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesDept = 
      selectedDeptFilter === 'ALL' || 
      (u.department && u.department.toLowerCase() === selectedDeptFilter.toLowerCase());

    return matchesSearch && matchesDept;
  });

  // Distinct departments in pending users for filtering
  const distinctDepartments = Array.from(new Set(pendingUsers.map(u => u.department).filter(Boolean)));

  return (
    <div className="space-y-6">
      {/* Top Notification Banner */}
      {notification && (
        <div className={`p-4 rounded-xl border flex items-center justify-between shadow-lg transition-all font-mono text-xs ${
          notification.type === 'success' 
            ? 'bg-emerald-950/90 border-emerald-700 text-emerald-200' 
            : 'bg-red-950/90 border-red-700 text-red-200'
        }`}>
          <div className="flex items-center space-x-2.5">
            {notification.type === 'success' ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
            )}
            <span>{notification.message}</span>
          </div>
          <button 
            onClick={() => setNotification(null)}
            className="text-slate-400 hover:text-white px-2 py-0.5 font-bold"
          >
            ✕
          </button>
        </div>
      )}

      {/* Header Panel */}
      <div className="bg-slate-900/90 border border-slate-800 p-6 rounded-2xl shadow-xl backdrop-blur flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2.5">
            <span className="bg-amber-500/10 text-amber-400 border border-amber-500/30 px-3 py-1 rounded-full font-mono text-xs font-bold uppercase tracking-wider flex items-center">
              <ShieldAlert className="w-3.5 h-3.5 mr-1.5 text-amber-400" />
              CLEARANCE VERIFICATION PORTAL
            </span>
            <span className="bg-slate-800 text-slate-300 px-2.5 py-1 rounded-full border border-slate-700 font-mono text-xs">
              {isSuperAdmin ? 'SUPER ADMIN: STATE-WIDE JURISDICTION' : `DEPT ADMIN: ${adminDepartment}`}
            </span>
          </div>
          <h1 className="text-2xl font-black text-white flex items-center mt-2 tracking-tight">
            <UserCheck className="w-7 h-7 text-amber-400 mr-2.5" />
            Administrative Personnel Approval Workflow
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-3xl">
            Review incoming government operator credentials, badge identifiers, and grant official departmental clearance. Approved accounts immediately gain login authorization.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="bg-slate-950 border border-slate-800 px-4 py-2.5 rounded-xl text-center">
            <div className="text-[10px] uppercase font-mono text-slate-400 tracking-wider">Awaiting Verification</div>
            <div className="text-2xl font-black text-amber-400 font-mono">{pendingUsers.length}</div>
          </div>
          <button
            onClick={fetchPendingApprovals}
            disabled={loading}
            className="flex items-center space-x-2 px-3.5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition"
            title="Refresh Pending List"
          >
            <RefreshCw className={`w-4 h-4 text-cyan-400 ${loading ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl flex flex-col md:flex-row items-center justify-between gap-3 shadow-md">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search by name, email, badge ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 transition font-mono"
          />
        </div>

        {isSuperAdmin && distinctDepartments.length > 0 && (
          <div className="flex items-center space-x-2 w-full md:w-auto">
            <Filter className="w-4 h-4 text-slate-400" />
            <span className="text-xs text-slate-400">Department:</span>
            <select
              value={selectedDeptFilter}
              onChange={(e) => setSelectedDeptFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-amber-500 font-mono"
            >
              <option value="ALL">All Departments ({pendingUsers.length})</option>
              {distinctDepartments.map(dept => (
                <option key={dept} value={dept}>{dept}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Table of Pending Personnel */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl shadow-xl overflow-hidden">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 space-y-3">
            <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-amber-400"></div>
            <span className="text-xs font-mono text-amber-400 tracking-wider">RETRIEVING PENDING REGISTRATIONS...</span>
          </div>
        ) : filteredUsers.length === 0 ? (
          <div className="py-16 text-center space-y-3">
            <div className="w-14 h-14 bg-emerald-500/10 border border-emerald-500/30 rounded-full flex items-center justify-center mx-auto text-emerald-400">
              <CheckCircle2 className="w-7 h-7" />
            </div>
            <h3 className="text-lg font-bold text-white tracking-wide">All Personnel Cleared</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              There are currently no government operators waiting for administrative clearance in your jurisdiction.
            </p>
            {onNavigateToDashboard && (
              <button
                onClick={onNavigateToDashboard}
                className="mt-2 inline-flex items-center space-x-1 text-xs text-cyan-400 hover:text-cyan-300 font-semibold"
              >
                <span>Return to Command Dashboard</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-mono uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="py-3.5 px-4 font-semibold">Full Name & Official Email</th>
                  <th className="py-3.5 px-4 font-semibold">Employee / Badge ID</th>
                  <th className="py-3.5 px-4 font-semibold">Requested Department</th>
                  <th className="py-3.5 px-4 font-semibold">Submission Timestamp</th>
                  <th className="py-3.5 px-4 font-semibold">Assigned Role</th>
                  <th className="py-3.5 px-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {filteredUsers.map((user) => {
                  const isProcessing = actionLoading === user.id;
                  const currentRoleChoice = selectedRoles[user.id] || 'OPERATOR';

                  return (
                    <tr key={user.id} className="hover:bg-slate-800/30 transition-colors">
                      {/* Full Name & Official Email */}
                      <td className="py-4 px-4">
                        <div className="flex items-center space-x-3">
                          <div className="w-9 h-9 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-amber-400 font-bold text-sm">
                            {user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
                          </div>
                          <div>
                            <div className="font-bold text-white text-sm flex items-center space-x-2">
                              <span>{user.full_name}</span>
                              <span className="font-mono text-[10px] bg-amber-950 text-amber-300 border border-amber-800/80 px-1.5 py-0.2 rounded">
                                PENDING
                              </span>
                            </div>
                            <div className="text-slate-400 text-xs font-mono">{user.email}</div>
                            {user.username && (
                              <div className="text-slate-500 text-[10px] font-mono">@{user.username}</div>
                            )}
                          </div>
                        </div>
                      </td>

                      {/* Employee / Badge ID */}
                      <td className="py-4 px-4">
                        <span className="inline-flex items-center px-2.5 py-1 rounded-md bg-slate-950 border border-slate-700 font-mono text-cyan-300 font-semibold text-xs">
                          <ShieldCheck className="w-3.5 h-3.5 mr-1.5 text-cyan-400" />
                          {user.employee_id || 'GJ-PENDING'}
                        </span>
                      </td>

                      {/* Requested Department */}
                      <td className="py-4 px-4">
                        <div className="flex items-center space-x-1.5 text-slate-200">
                          <Building2 className="w-4 h-4 text-blue-400 flex-shrink-0" />
                          <span className="font-medium">{user.department || 'Gujarat State Administration'}</span>
                        </div>
                      </td>

                      {/* Submission Timestamp */}
                      <td className="py-4 px-4 font-mono text-slate-400 text-xs">
                        <div className="flex items-center space-x-1.5">
                          <Clock className="w-3.5 h-3.5 text-slate-500" />
                          <span>{user.created_at || '2026-09-05 10:00:00'}</span>
                        </div>
                      </td>

                      {/* Role Elevation Option */}
                      <td className="py-4 px-4">
                        <select
                          value={currentRoleChoice}
                          onChange={(e) => handleRoleChange(user.id, e.target.value)}
                          disabled={isProcessing}
                          className="bg-slate-950 border border-slate-700 text-xs text-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-amber-500 font-mono"
                        >
                          <option value="OPERATOR">OPERATOR (Default)</option>
                          <option value="AI_ANALYST">AI_ANALYST</option>
                          <option value="GIS_OPERATOR">GIS_OPERATOR</option>
                          <option value="MAINTENANCE_OFFICER">MAINTENANCE_OFFICER</option>
                          <option value="TECHNICIAN">TECHNICIAN</option>
                          {isSuperAdmin && <option value="DEPARTMENT_ADMIN">DEPARTMENT_ADMIN</option>}
                        </select>
                      </td>

                      {/* Actions */}
                      <td className="py-4 px-4 text-right">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            onClick={() => handleApproveClearance(user)}
                            disabled={isProcessing}
                            className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold text-xs rounded-lg shadow-md shadow-emerald-950 transition"
                            title="Approve clearance and grant immediate system login access"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>{isProcessing ? 'Processing...' : 'Approve Clearance'}</span>
                          </button>

                          <button
                            onClick={() => setRejectionModalUser(user)}
                            disabled={isProcessing}
                            className="inline-flex items-center space-x-1.5 px-2.5 py-1.5 bg-red-950/60 hover:bg-red-900 border border-red-800 text-red-300 font-semibold text-xs rounded-lg transition"
                            title="Reject this registration"
                          >
                            <XCircle className="w-3.5 h-3.5" />
                            <span>Reject</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Rejection Modal */}
      {rejectionModalUser && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-red-800/80 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center space-x-3 text-red-400">
              <div className="w-10 h-10 rounded-full bg-red-950 border border-red-800 flex items-center justify-center">
                <UserX className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Deny Administrative Clearance</h3>
                <p className="text-xs text-red-300">Reject {rejectionModalUser.full_name} ({rejectionModalUser.email})</p>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-mono text-slate-300 block">
                Official Rejection Reason (Security Audit Log):
              </label>
              <textarea
                rows={3}
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-red-500 font-mono"
                placeholder="Specify reason for credential rejection..."
              />
            </div>

            <div className="flex items-center justify-end space-x-3 pt-2">
              <button
                type="button"
                onClick={() => setRejectionModalUser(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleRejectClearance}
                disabled={actionLoading === rejectionModalUser.id}
                className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white text-xs font-semibold rounded-lg shadow-lg"
              >
                {actionLoading === rejectionModalUser.id ? 'Rejecting...' : 'Confirm Rejection'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
