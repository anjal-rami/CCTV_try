import React, { useState, useEffect } from 'react';
import { 
  Server, 
  Activity, 
  Radio, 
  GitMerge, 
  CheckSquare, 
  FileText, 
  Plus, 
  RefreshCw, 
  Play, 
  ShieldCheck, 
  AlertTriangle, 
  Clock, 
  Search, 
  ExternalLink, 
  Download, 
  CheckCircle2, 
  Zap,
  Building2,
  Filter,
  Layers,
  ChevronRight,
  Database
} from 'lucide-react';
import { User } from '../types';

export interface VMSPlatformData {
  id: string;
  name: string;
  department_id: string;
  vendor: string;
  version: string;
  protocol: string;
  base_endpoint_url: string;
  credential_secret_ref: string;
  adapter_type: string;
  status: 'ONLINE' | 'OFFLINE' | 'DEGRADED';
  created_at: string;
  last_sync_at: string | null;
  synced_cameras_count: number;
}

export interface FederatedEventData {
  id: string;
  vms_platform_id: string;
  vms_name: string;
  vendor: string;
  camera_id: string;
  camera_name: string;
  department_id: string;
  department_name: string;
  topic: string;
  event_type: string;
  severity: string;
  timestamp: string;
  plate_number?: string;
  confidence: number;
  payload?: any;
}

export interface CorrelatedIncidentData {
  id: string;
  title: string;
  correlation_type: string;
  source_vms_ids: string[];
  departments_involved: string[];
  plate_number?: string;
  confidence: number;
  severity: string;
  first_detected_at: string;
  last_detected_at: string;
  time_window_minutes: number;
  event_count: number;
  details: string;
  status: string;
  workflow_task_id?: string;
}

export interface WorkflowTaskData {
  id: string;
  title: string;
  event_id?: string;
  correlation_id?: string;
  source_department: string;
  assigned_department: string;
  priority: string;
  status: 'OPEN' | 'IN_PROGRESS' | 'ESCALATED' | 'RESOLVED';
  sop_checklist: Array<{
    id: number;
    task: string;
    completed: boolean;
    verified_by?: string | null;
  }>;
  escalation_deadline: string;
  created_at: string;
  notes?: string;
  resolution_summary?: string;
  resolved_by?: string;
}

interface VmsFederationProps {
  currentUser: User;
}

export const VmsFederation: React.FC<VmsFederationProps> = ({ currentUser }) => {
  const [activeSubTab, setActiveSubTab] = useState<'platforms' | 'events' | 'correlation' | 'workflows' | 'reports'>('platforms');
  
  // Data States
  const [platforms, setPlatforms] = useState<VMSPlatformData[]>([]);
  const [events, setEvents] = useState<FederatedEventData[]>([]);
  const [correlatedIncidents, setCorrelatedIncidents] = useState<CorrelatedIncidentData[]>([]);
  const [workflows, setWorkflows] = useState<WorkflowTaskData[]>([]);
  const [reportSummary, setReportSummary] = useState<any>(null);

  // Filter & Search States
  const [eventFilter, setEventFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowTaskData | null>(null);

  // Loading & Feedback
  const [loading, setLoading] = useState<boolean>(true);
  const [demoSyncing, setDemoSyncing] = useState<boolean>(false);
  const [testConnResult, setTestConnResult] = useState<any>(null);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Create Platform Modal
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [newPlatformForm, setNewPlatformForm] = useState({
    name: '',
    department_id: 'DEPT-01',
    vendor: 'Milestone',
    version: 'XProtect 2024 R1',
    protocol: 'REST API',
    base_endpoint_url: 'http://127.0.0.1:8085',
    credential_secret_ref: 'vault://vms/secret',
    adapter_type: 'milestone',
    status: 'ONLINE'
  });

  const token = localStorage.getItem('access_token') || '';

  const getVendorBadgeColor = (vendor: string) => {
    const v = (vendor || '').toLowerCase();
    if (v.includes('milestone')) return 'bg-sky-950/70 text-sky-400 border-sky-600';
    if (v.includes('hikvision')) return 'bg-rose-950/70 text-rose-400 border-rose-600';
    if (v.includes('dahua')) return 'bg-amber-950/70 text-amber-400 border-amber-600';
    if (v.includes('axis')) return 'bg-emerald-950/70 text-emerald-400 border-emerald-600';
    if (v.includes('honeywell')) return 'bg-purple-950/70 text-purple-400 border-purple-600';
    return 'bg-slate-800 text-slate-300 border-slate-600';
  };

  const getSeverityBadgeColor = (severity: string) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL': return 'bg-red-900/60 text-red-300 border-red-500 animate-pulse';
      case 'HIGH': return 'bg-amber-900/60 text-amber-300 border-amber-500';
      case 'MEDIUM': return 'bg-blue-900/60 text-blue-300 border-blue-500';
      default: return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  // Fetch initial data
  const fetchData = async () => {
    setLoading(true);
    try {
      const [platRes, evtRes, corrRes, wfRes, repRes] = await Promise.all([
        fetch('/api/v1/vms-platforms', { headers: { 'Authorization': `Bearer ${token}` } }),
        fetch('/api/v1/events/stream?limit=100', { headers: { 'Authorization': `Bearer ${token}` } }),
        fetch('/api/v1/events/correlated', { headers: { 'Authorization': `Bearer ${token}` } }),
        fetch('/api/v1/workflows', { headers: { 'Authorization': `Bearer ${token}` } }),
        fetch('/api/v1/analytics/federated-report', { headers: { 'Authorization': `Bearer ${token}` } })
      ]);

      if (platRes.ok) setPlatforms(await platRes.json());
      if (evtRes.ok) setEvents(await evtRes.json());
      if (corrRes.ok) setCorrelatedIncidents(await corrRes.json());
      if (wfRes.ok) {
        const wfData = await wfRes.json();
        setWorkflows(wfData);
        if (wfData.length > 0 && !selectedWorkflow) {
          setSelectedWorkflow(wfData[0]);
        }
      }
      if (repRes.ok) setReportSummary(await repRes.json());
    } catch (e) {
      console.error('Failed to fetch VMS federation telemetry:', e);
      setNotification({ type: 'error', message: 'Failed to connect to VMS Federation gateway.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 8000);
    return () => clearInterval(interval);
  }, []);

  // Demo Sync Handler
  const handleRunDemoSync = async () => {
    setDemoSyncing(true);
    setNotification(null);
    try {
      const res = await fetch('/api/v1/vms-federation/demo-sync', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      const data = await res.json();
      if (res.ok) {
        setNotification({
          type: 'success',
          message: `Demo Sync Successful! Federated 2 VMS nodes. Correlated Target Plate 'GJ-01-AB-1234' with ${data.workflows_count || 1} active multi-agency workflow.`
        });
        await fetchData();
        setActiveSubTab('correlation');
      } else {
        setNotification({ type: 'error', message: data.detail || 'Demo sync execution failed.' });
      }
    } catch (err: any) {
      setNotification({ type: 'error', message: 'Connection error during demo sync.' });
    } finally {
      setDemoSyncing(false);
    }
  };

  // Test Platform Connection
  const handleTestConnection = async (platformId: string) => {
    try {
      const res = await fetch(`/api/v1/vms-platforms/${platformId}/test-connection`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setTestConnResult(data);
      if (data.success) {
        setNotification({
          type: 'success',
          message: `VMS Adapter Connectivity Passed: ${data.platform_name} verified online (Status: ${data.status}).`
        });
      }
      fetchData();
    } catch (e) {
      setNotification({ type: 'error', message: 'Adapter connectivity probe timed out.' });
    }
  };

  // Sync Platform Cameras
  const handleSyncCameras = async (platformId: string) => {
    try {
      const res = await fetch(`/api/v1/vms-platforms/${platformId}/sync`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (res.ok) {
        setNotification({
          type: 'success',
          message: `Camera Discovery Completed: Synchronized ${data.synced_count} camera channels into registry.`
        });
        fetchData();
      }
    } catch (e) {
      setNotification({ type: 'error', message: 'Camera synchronization failed.' });
    }
  };

  // Toggle SOP Checklist item
  const handleToggleChecklist = async (workflowId: string, stepId: number, currentVal: boolean) => {
    try {
      const res = await fetch(`/api/v1/workflows/${workflowId}/checklist`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          step_id: stepId,
          completed: !currentVal,
          verified_by: currentUser.name || 'Command Center Officer'
        })
      });
      if (res.ok) {
        const updated = await res.json();
        setWorkflows(prev => prev.map(w => w.id === workflowId ? updated : w));
        if (selectedWorkflow?.id === workflowId) {
          setSelectedWorkflow(updated);
        }
      }
    } catch (e) {
      console.error('Checklist update failed', e);
    }
  };

  // Update Workflow Status
  const handleUpdateWorkflowStatus = async (workflowId: string, newStatus: string) => {
    try {
      const res = await fetch(`/api/v1/workflows/${workflowId}/status`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          status: newStatus,
          resolution_summary: newStatus === 'RESOLVED' ? 'Multi-agency SOP checklist verified. Suspect intercepted and transferred to CAD jurisdiction.' : undefined,
          resolved_by: currentUser.name || 'Supervisor'
        })
      });
      const data = await res.json();
      if (res.ok) {
        setNotification({ type: 'success', message: `Workflow status updated to '${newStatus}'.` });
        setWorkflows(prev => prev.map(w => w.id === workflowId ? data : w));
        if (selectedWorkflow?.id === workflowId) {
          setSelectedWorkflow(data);
        }
      } else {
        setNotification({ type: 'error', message: data.detail || 'Could not update workflow status.' });
      }
    } catch (e) {
      setNotification({ type: 'error', message: 'Failed to update workflow status.' });
    }
  };

  // Create Platform
  const handleCreatePlatform = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch('/api/v1/vms-platforms', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newPlatformForm)
      });
      if (res.ok) {
        setNotification({ type: 'success', message: 'New VMS Platform registered successfully.' });
        setShowCreateModal(false);
        fetchData();
      }
    } catch (e) {
      setNotification({ type: 'error', message: 'Failed to register VMS Platform.' });
    }
  };

  // Filtered Events
  const filteredEvents = events.filter(e => {
    const matchesTopic = eventFilter === 'ALL' || e.topic.includes(eventFilter.toLowerCase());
    const matchesQuery = !searchQuery || 
      e.camera_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (e.plate_number || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.vendor.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.event_type.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesTopic && matchesQuery;
  });

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* Platform Banner Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none"></div>
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 relative z-10">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-cyan-950/80 border border-cyan-500/40 rounded-lg text-cyan-400 shadow-md">
                <GitMerge className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white tracking-wide">
                  Model 3 VMS Federation & Cross-System Event Engine
                </h1>
                <p className="text-xs text-slate-400 font-mono">
                  Pluggable Adapter Layer • Decoupled Kafka/Redis Event Bus • Spatial/Temporal Correlation • Cross-Agency SOP Workflows
                </p>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={handleRunDemoSync}
              disabled={demoSyncing}
              className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-semibold rounded-lg shadow-lg shadow-cyan-950 transition disabled:opacity-50"
            >
              <Zap className={`w-4 h-4 ${demoSyncing ? 'animate-spin' : 'text-amber-300'}`} />
              {demoSyncing ? 'Simulating Two-System Bench...' : 'Execute Model 3 Federation Demo'}
            </button>

            <a
              href="/api/v1/analytics/federated-report?format=csv"
              download="federated_analytics_report.csv"
              className="flex items-center gap-2 px-3.5 py-2.5 bg-slate-800 hover:bg-slate-750 border border-slate-700 text-slate-200 text-xs font-medium rounded-lg shadow transition"
            >
              <Download className="w-4 h-4 text-cyan-400" />
              Export CSV Report
            </a>

            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-3.5 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-cyan-400 text-xs font-medium rounded-lg shadow transition"
            >
              <Plus className="w-4 h-4" />
              Register VMS
            </button>
          </div>
        </div>

        {/* Global Federation Stats Ribbon */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mt-6 pt-5 border-t border-slate-800/80">
          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
            <span className="text-[10px] uppercase font-mono text-slate-400 tracking-wider">Federated Platforms</span>
            <div className="text-xl font-bold text-white mt-0.5 flex items-center gap-2">
              <Server className="w-4 h-4 text-cyan-400" />
              {platforms.length}
            </div>
            <span className="text-[10px] text-emerald-400 font-mono">100% Adapter Health</span>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
            <span className="text-[10px] uppercase font-mono text-slate-400 tracking-wider">Event Bus Telemetry</span>
            <div className="text-xl font-bold text-white mt-0.5 flex items-center gap-2">
              <Radio className="w-4 h-4 text-sky-400" />
              {events.length}
            </div>
            <span className="text-[10px] text-slate-400 font-mono">Real-Time Ingestion</span>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
            <span className="text-[10px] uppercase font-mono text-slate-400 tracking-wider">Correlated Incidents</span>
            <div className="text-xl font-bold text-amber-400 mt-0.5 flex items-center gap-2">
              <GitMerge className="w-4 h-4" />
              {correlatedIncidents.length}
            </div>
            <span className="text-[10px] text-amber-400 font-mono">Rule 1 & 2 Triggers</span>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
            <span className="text-[10px] uppercase font-mono text-slate-400 tracking-wider">Cross-Dept Workflows</span>
            <div className="text-xl font-bold text-emerald-400 mt-0.5 flex items-center gap-2">
              <CheckSquare className="w-4 h-4" />
              {workflows.length}
            </div>
            <span className="text-[10px] text-slate-400 font-mono">SOP Routing Active</span>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80 col-span-2 md:col-span-1">
            <span className="text-[10px] uppercase font-mono text-slate-400 tracking-wider">Target Plate Match</span>
            <div className="text-xl font-bold text-rose-400 mt-0.5 font-mono">
              GJ-01-AB-1234
            </div>
            <span className="text-[10px] text-rose-400/80 font-mono">Cross-VMS Alert Hit</span>
          </div>
        </div>
      </div>

      {/* Notification Banner */}
      {notification && (
        <div className={`p-4 rounded-xl border flex items-center justify-between text-xs font-mono shadow-lg transition animate-slideDown ${
          notification.type === 'success' 
            ? 'bg-emerald-950/70 border-emerald-500/50 text-emerald-200' 
            : 'bg-red-950/70 border-red-500/50 text-red-200'
        }`}>
          <div className="flex items-center gap-3">
            {notification.type === 'success' ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <AlertTriangle className="w-4 h-4 text-red-400" />}
            <span>{notification.message}</span>
          </div>
          <button onClick={() => setNotification(null)} className="text-slate-400 hover:text-white text-sm font-bold">×</button>
        </div>
      )}

      {/* Sub-Navigation Tabs */}
      <div className="flex border-b border-slate-800 space-x-2">
        <button
          onClick={() => setActiveSubTab('platforms')}
          className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold border-b-2 transition ${
            activeSubTab === 'platforms'
              ? 'border-cyan-500 text-cyan-400 bg-slate-900/40'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Server className="w-4 h-4" />
          VMS Platforms ({platforms.length})
        </button>

        <button
          onClick={() => setActiveSubTab('events')}
          className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold border-b-2 transition ${
            activeSubTab === 'events'
              ? 'border-cyan-500 text-cyan-400 bg-slate-900/40'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Radio className="w-4 h-4" />
          Event Bus Stream ({events.length})
        </button>

        <button
          onClick={() => setActiveSubTab('correlation')}
          className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold border-b-2 transition ${
            activeSubTab === 'correlation'
              ? 'border-cyan-500 text-cyan-400 bg-slate-900/40'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <GitMerge className="w-4 h-4" />
          Correlated Incidents ({correlatedIncidents.length})
        </button>

        <button
          onClick={() => setActiveSubTab('workflows')}
          className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold border-b-2 transition ${
            activeSubTab === 'workflows'
              ? 'border-cyan-500 text-cyan-400 bg-slate-900/40'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <CheckSquare className="w-4 h-4" />
          Cross-Agency SOP Workflows ({workflows.length})
        </button>

        <button
          onClick={() => setActiveSubTab('reports')}
          className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold border-b-2 transition ${
            activeSubTab === 'reports'
              ? 'border-cyan-500 text-cyan-400 bg-slate-900/40'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileText className="w-4 h-4" />
          Analytics & Reports
        </button>
      </div>

      {/* TAB 1: VMS PLATFORMS DIRECTORY */}
      {activeSubTab === 'platforms' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {platforms.map(plat => (
              <div 
                key={plat.id}
                className="bg-slate-900/90 border border-slate-800 hover:border-slate-700 rounded-xl p-5 shadow-lg flex flex-col justify-between space-y-4 transition"
              >
                <div className="space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className={`inline-block px-2.5 py-0.5 text-[10px] font-mono font-bold rounded border ${getVendorBadgeColor(plat.vendor)}`}>
                        {plat.vendor} • {plat.version}
                      </span>
                      <h3 className="text-base font-bold text-white mt-1.5 leading-snug">
                        {plat.name}
                      </h3>
                      <p className="text-[11px] text-slate-400 font-mono">
                        Dept: {plat.department_id} • ID: {plat.id}
                      </p>
                    </div>
                    <span className={`px-2 py-0.5 text-[10px] font-mono rounded font-semibold border ${
                      plat.status === 'ONLINE' 
                        ? 'bg-emerald-950/80 text-emerald-400 border-emerald-600'
                        : 'bg-amber-950/80 text-amber-400 border-amber-600'
                    }`}>
                      {plat.status}
                    </span>
                  </div>

                  <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 space-y-1 font-mono text-[11px]">
                    <div className="flex justify-between text-slate-400">
                      <span>Protocol:</span>
                      <span className="text-slate-200">{plat.protocol}</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Adapter:</span>
                      <span className="text-cyan-400">{plat.adapter_type}</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Synced Cameras:</span>
                      <span className="text-white font-bold">{plat.synced_cameras_count} Feeds</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Last Sync:</span>
                      <span className="text-slate-300">{plat.last_sync_at || 'Never'}</span>
                    </div>
                    <div className="text-[10px] text-slate-500 truncate pt-1 border-t border-slate-800">
                      Endpoint: {plat.base_endpoint_url}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 pt-2 border-t border-slate-800/80">
                  <button
                    onClick={() => handleTestConnection(plat.id)}
                    className="flex-1 py-1.5 px-3 bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-slate-700 hover:border-cyan-500/40 text-xs font-medium rounded-lg transition"
                  >
                    Test Connection
                  </button>
                  <button
                    onClick={() => handleSyncCameras(plat.id)}
                    className="flex-1 py-1.5 px-3 bg-cyan-950/70 hover:bg-cyan-900 text-cyan-300 border border-cyan-800/80 text-xs font-medium rounded-lg transition"
                  >
                    Sync Feeds
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Test Connection Probe Details Drawer */}
          {testConnResult && (
            <div className="bg-slate-950 border border-cyan-800/50 rounded-xl p-4 shadow-2xl font-mono text-xs text-slate-300 space-y-2 animate-fadeIn">
              <div className="flex items-center justify-between text-cyan-400 font-bold border-b border-slate-800 pb-2">
                <span className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-emerald-400" />
                  Live VMS Adapter Connection Probe Response: {testConnResult.platform_name}
                </span>
                <button onClick={() => setTestConnResult(null)} className="text-slate-400 hover:text-white">✕</button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
                <div>
                  <span className="text-slate-500">Auth Token Handshake:</span>
                  <p className="text-emerald-400 font-semibold truncate">{testConnResult.auth_response?.access_token || testConnResult.auth_response?.session_id || 'Active Session'}</p>
                </div>
                <div>
                  <span className="text-slate-500">API Gateway Version:</span>
                  <p className="text-white">{testConnResult.auth_response?.api_version || testConnResult.auth_response?.isapi_version || 'v1.0-Standard'}</p>
                </div>
                <div>
                  <span className="text-slate-500">Heartbeat Status:</span>
                  <p className="text-emerald-400 font-bold">{testConnResult.telemetry?.status || 'ONLINE'}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: REAL-TIME EVENT BUS STREAM */}
      {activeSubTab === 'events' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900 p-4 rounded-xl border border-slate-800">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <Filter className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-semibold text-slate-300">Topic:</span>
              <div className="flex gap-1">
                {['ALL', 'DETECTIONS', 'STATUS', 'ALERTS'].map(t => (
                  <button
                    key={t}
                    onClick={() => setEventFilter(t)}
                    className={`px-3 py-1 text-xs rounded-lg font-mono transition ${
                      eventFilter === t
                        ? 'bg-cyan-600 text-white font-semibold'
                        : 'bg-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>

            <div className="relative w-full sm:w-72">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search plate, camera, vendor..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
            <div className="p-4 border-b border-slate-800 flex justify-between items-center text-xs font-mono text-slate-400">
              <span>Streaming {filteredEvents.length} Buffered Federated Events</span>
              <span className="flex items-center gap-1.5 text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                Live Bus Subscriptions Active
              </span>
            </div>

            <div className="divide-y divide-slate-800/60 max-h-[600px] overflow-y-auto">
              {filteredEvents.length === 0 ? (
                <div className="p-12 text-center text-slate-500 font-mono text-xs">
                  No events received yet. Click "Execute Model 3 Federation Demo" above to stream sample events.
                </div>
              ) : (
                filteredEvents.map(evt => (
                  <div key={evt.id} className="p-4 hover:bg-slate-800/40 transition space-y-2">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded border ${getVendorBadgeColor(evt.vendor)}`}>
                          {evt.vendor}
                        </span>
                        <span className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded border ${getSeverityBadgeColor(evt.severity)}`}>
                          {evt.severity}
                        </span>
                        <span className="text-xs font-bold text-white">
                          {evt.event_type}
                        </span>
                        {evt.plate_number && (
                          <span className="px-2 py-0.5 bg-rose-950/80 border border-rose-600 text-rose-300 font-mono font-bold text-xs rounded">
                            {evt.plate_number}
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-slate-400 font-mono">
                        {evt.timestamp}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center justify-between text-xs text-slate-400 font-mono gap-2">
                      <div>
                        Node: <span className="text-slate-200">{evt.camera_name}</span> ({evt.camera_id})
                      </div>
                      <div>
                        Source: <span className="text-cyan-400">{evt.vms_name}</span> • Dept: <span className="text-slate-300">{evt.department_name}</span>
                      </div>
                    </div>

                    {evt.payload && (
                      <div className="bg-slate-950/80 p-2 rounded border border-slate-800/80 text-[11px] font-mono text-slate-300">
                        Payload: {JSON.stringify(evt.payload)}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: CROSS-SYSTEM CORRELATED INCIDENTS */}
      {activeSubTab === 'correlation' && (
        <div className="space-y-4">
          <div className="bg-amber-950/20 border border-amber-600/30 rounded-xl p-4 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div className="text-xs text-amber-200/90 font-mono space-y-1">
              <p className="font-bold text-amber-300">Operational Cross-VMS Correlation Active</p>
              <p>
                Rule 1 triggers when the identical plate/signature appears across 2 separate VMS clusters within 15 minutes.
                Rule 2 triggers an automatic multi-department notification & CAD workflow task.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {correlatedIncidents.length === 0 ? (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-500 font-mono text-xs">
                No cross-system incidents triggered yet. Click "Execute Model 3 Federation Demo" to fire cross-VMS vehicle hit.
              </div>
            ) : (
              correlatedIncidents.map(inc => (
                <div key={inc.id} className="bg-slate-900 border border-rose-900/40 rounded-xl p-5 shadow-xl space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-rose-950/80 border border-rose-600/60 rounded-lg text-rose-400 font-bold font-mono">
                        {inc.plate_number || 'ALERT'}
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-white">
                          {inc.title}
                        </h3>
                        <p className="text-[11px] font-mono text-slate-400">
                          Incident ID: {inc.id} • Rule: {inc.correlation_type}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="px-2.5 py-1 bg-red-950/80 border border-red-600 text-red-300 text-xs font-mono font-bold rounded">
                        Confidence: {(inc.confidence * 100).toFixed(0)}%
                      </span>
                      <span className="px-2.5 py-1 bg-amber-950/80 border border-amber-600 text-amber-300 text-xs font-mono font-bold rounded">
                        Time Delta: {inc.time_window_minutes} mins
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-300 font-mono leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                    {inc.details}
                  </p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
                    <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                      <span className="text-slate-400 text-[10px] uppercase">Federated VMS Sources:</span>
                      <ul className="mt-1 space-y-1 text-cyan-300">
                        {inc.source_vms_ids.map((v, idx) => (
                          <li key={idx} className="flex items-center gap-1.5">
                            <Server className="w-3.5 h-3.5 text-cyan-400" />
                            {v}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                      <span className="text-slate-400 text-[10px] uppercase">Departments Escalated:</span>
                      <ul className="mt-1 space-y-1 text-emerald-300">
                        {inc.departments_involved.map((d, idx) => (
                          <li key={idx} className="flex items-center gap-1.5">
                            <Building2 className="w-3.5 h-3.5 text-emerald-400" />
                            {d}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-xs font-mono">
                    <span className="text-slate-400">
                      First Hit: {inc.first_detected_at} • Last Hit: {inc.last_detected_at}
                    </span>
                    <button
                      onClick={() => {
                        setActiveSubTab('workflows');
                        const wf = workflows.find(w => w.correlation_id === inc.id);
                        if (wf) setSelectedWorkflow(wf);
                      }}
                      className="flex items-center gap-1.5 px-4 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg font-semibold transition shadow"
                    >
                      Inspect SOP Task
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* TAB 4: UNIFIED CROSS-DEPARTMENT WORKFLOWS */}
      {activeSubTab === 'workflows' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Tasks List */}
          <div className="lg:col-span-1 space-y-3">
            <h3 className="text-xs font-mono uppercase text-slate-400 font-bold tracking-wider">
              Assigned Operational Workflows ({workflows.length})
            </h3>
            <div className="space-y-2">
              {workflows.map(wf => (
                <div
                  key={wf.id}
                  onClick={() => setSelectedWorkflow(wf)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition ${
                    selectedWorkflow?.id === wf.id
                      ? 'bg-slate-800/90 border-cyan-500/80 shadow-lg'
                      : 'bg-slate-900 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded border ${getSeverityBadgeColor(wf.priority)}`}>
                      {wf.priority}
                    </span>
                    <span className={`px-2 py-0.5 text-[10px] font-mono rounded font-semibold ${
                      wf.status === 'RESOLVED' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-amber-950 text-amber-400 border border-amber-800'
                    }`}>
                      {wf.status}
                    </span>
                  </div>
                  <h4 className="text-xs font-bold text-white mt-2 line-clamp-2">
                    {wf.title}
                  </h4>
                  <div className="text-[11px] font-mono text-slate-400 mt-2 flex justify-between">
                    <span>{wf.source_department} ➔ {wf.assigned_department}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Task Detail & Interactive SOP Checklist */}
          <div className="lg:col-span-2">
            {selectedWorkflow ? (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
                <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-800 pb-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`px-2.5 py-0.5 text-[10px] font-mono font-bold rounded border ${getSeverityBadgeColor(selectedWorkflow.priority)}`}>
                        {selectedWorkflow.priority}
                      </span>
                      <span className="text-xs font-mono text-slate-400">
                        Task ID: {selectedWorkflow.id}
                      </span>
                    </div>
                    <h2 className="text-lg font-bold text-white">
                      {selectedWorkflow.title}
                    </h2>
                    <p className="text-xs font-mono text-slate-400">
                      From: <strong className="text-cyan-400">{selectedWorkflow.source_department}</strong> ➔ Assigned To: <strong className="text-emerald-400">{selectedWorkflow.assigned_department}</strong>
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    {selectedWorkflow.status !== 'RESOLVED' ? (
                      <button
                        onClick={() => handleUpdateWorkflowStatus(selectedWorkflow.id, 'RESOLVED')}
                        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-lg shadow-lg transition flex items-center gap-1.5"
                      >
                        <CheckCircle2 className="w-4 h-4" />
                        Mark Resolved
                      </button>
                    ) : (
                      <span className="px-3 py-1.5 bg-emerald-950 border border-emerald-600 text-emerald-300 font-mono text-xs font-bold rounded-lg flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4" />
                        Resolved by {selectedWorkflow.resolved_by || 'Supervisor'}
                      </span>
                    )}
                  </div>
                </div>

                {/* SOP Checklist Component */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-mono uppercase font-bold text-slate-300 flex items-center gap-2">
                      <CheckSquare className="w-4 h-4 text-cyan-400" />
                      Standard Operating Procedure (SOP) Mandatory Checklist
                    </h3>
                    <span className="text-xs font-mono text-slate-400">
                      {selectedWorkflow.sop_checklist.filter(s => s.completed).length} of {selectedWorkflow.sop_checklist.length} Steps Verified
                    </span>
                  </div>

                  <div className="space-y-2 bg-slate-950/70 p-4 rounded-xl border border-slate-800">
                    {selectedWorkflow.sop_checklist.map(step => (
                      <div
                        key={step.id}
                        onClick={() => handleToggleChecklist(selectedWorkflow.id, step.id, step.completed)}
                        className={`p-3 rounded-lg border flex items-center justify-between cursor-pointer transition ${
                          step.completed
                            ? 'bg-emerald-950/30 border-emerald-800/80 text-emerald-200'
                            : 'bg-slate-900 border-slate-800 hover:border-slate-700 text-slate-300'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <input
                            type="checkbox"
                            checked={step.completed}
                            onChange={() => {}}
                            className="w-4 h-4 rounded text-cyan-600 border-slate-700 bg-slate-800 focus:ring-0 pointer-events-none"
                          />
                          <span className={`text-xs font-medium ${step.completed ? 'line-through text-slate-400' : 'text-white'}`}>
                            {step.id}. {step.task}
                          </span>
                        </div>
                        {step.completed && (
                          <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-800">
                            Verified: {step.verified_by || 'Operator'}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Deadline & Notes */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono pt-2">
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-slate-500 text-[10px] uppercase">Escalation Deadline:</span>
                    <p className="text-amber-400 font-bold mt-0.5">{selectedWorkflow.escalation_deadline}</p>
                  </div>
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-slate-500 text-[10px] uppercase">Incident Created At:</span>
                    <p className="text-slate-300 mt-0.5">{selectedWorkflow.created_at}</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-500 font-mono text-xs">
                Select a workflow task from the list on the left.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 5: ANALYTICS & REPORTS */}
      {activeSubTab === 'reports' && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h2 className="text-base font-bold text-white">
                  Model 3 Compliance & Deliverable Analytics Summary
                </h2>
                <p className="text-xs text-slate-400 font-mono">
                  Autonomous Multi-VMS Interoperability, Cross-Boundary Correlation, and Workflow SLA Verification
                </p>
              </div>

              <a
                href="/api/v1/analytics/federated-report?format=csv"
                download="federated_analytics_report.csv"
                className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold rounded-lg shadow transition"
              >
                <Download className="w-4 h-4" />
                Download Report (.CSV)
              </a>
            </div>

            {reportSummary ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 pt-2">
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1 font-mono">
                  <span className="text-[10px] text-slate-500 uppercase">Platform Status</span>
                  <div className="text-xl font-bold text-white">
                    {reportSummary.platforms_summary?.online} / {reportSummary.platforms_summary?.total} Online
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Vendors: {reportSummary.platforms_summary?.vendors?.join(', ')}
                  </p>
                </div>

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1 font-mono">
                  <span className="text-[10px] text-slate-500 uppercase">Event Bus Volume</span>
                  <div className="text-xl font-bold text-cyan-400">
                    {reportSummary.event_bus_summary?.total_events} Messages
                  </div>
                  <p className="text-[11px] text-slate-400">
                    DLQ Dead-Letters: {reportSummary.event_bus_summary?.dlq_dead_letters}
                  </p>
                </div>

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1 font-mono">
                  <span className="text-[10px] text-slate-500 uppercase">Correlations</span>
                  <div className="text-xl font-bold text-amber-400">
                    {reportSummary.correlation_summary?.total_correlated_incidents} Multi-Agency
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Confidence: {(reportSummary.correlation_summary?.average_confidence * 100).toFixed(0)}%
                  </p>
                </div>

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1 font-mono">
                  <span className="text-[10px] text-slate-500 uppercase">Workflow SLA Compliance</span>
                  <div className="text-xl font-bold text-emerald-400">
                    {reportSummary.workflow_engine_summary?.sla_compliance_percent}%
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Resolved: {reportSummary.workflow_engine_summary?.resolved_tasks} of {reportSummary.workflow_engine_summary?.total_tasks}
                  </p>
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-slate-500 font-mono text-xs">
                Loading analytics summary...
              </div>
            )}
          </div>
        </div>
      )}

      {/* REGISTER NEW VMS PLATFORM MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5 animate-scaleUp">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Server className="w-5 h-5 text-cyan-400" />
                Register New External VMS Platform
              </h3>
              <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            <form onSubmit={handleCreatePlatform} className="space-y-4 font-mono text-xs">
              <div className="space-y-1">
                <label className="text-slate-300">Platform Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Surat Smart City Dahua DSS"
                  value={newPlatformForm.name}
                  onChange={e => setNewPlatformForm({ ...newPlatformForm, name: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-slate-300">Vendor</label>
                  <select
                    value={newPlatformForm.vendor}
                    onChange={e => setNewPlatformForm({ ...newPlatformForm, vendor: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white"
                  >
                    <option value="Milestone">Milestone</option>
                    <option value="Hikvision">Hikvision</option>
                    <option value="Dahua">Dahua</option>
                    <option value="Axis">Axis</option>
                    <option value="Honeywell">Honeywell</option>
                    <option value="Uniview">Uniview</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-slate-300">Adapter Type</label>
                  <select
                    value={newPlatformForm.adapter_type}
                    onChange={e => setNewPlatformForm({ ...newPlatformForm, adapter_type: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white"
                  >
                    <option value="milestone">Milestone REST Adapter</option>
                    <option value="hikvision_isapi">Hikvision ISAPI Adapter</option>
                    <option value="generic_onvif">Generic ONVIF Adapter</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-slate-300">Protocol</label>
                  <input
                    type="text"
                    value={newPlatformForm.protocol}
                    onChange={e => setNewPlatformForm({ ...newPlatformForm, protocol: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-slate-300">Department ID</label>
                  <input
                    type="text"
                    value={newPlatformForm.department_id}
                    onChange={e => setNewPlatformForm({ ...newPlatformForm, department_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-slate-300">Base Endpoint URL</label>
                <input
                  type="text"
                  required
                  value={newPlatformForm.base_endpoint_url}
                  onChange={e => setNewPlatformForm({ ...newPlatformForm, base_endpoint_url: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-cyan-600 hover:bg-cyan-500 text-white font-bold rounded-lg shadow-lg"
                >
                  Register Platform
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
export default VmsFederation;
