import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Filter, 
  Upload, 
  Plus, 
  Download, 
  Eye, 
  Settings2, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  FileSpreadsheet,
  Building2,
  HardDrive,
  Wifi,
  ShieldCheck,
  X,
  History
} from 'lucide-react';
import { Camera, Department, AuditLog } from '../types';

interface CameraRegistryProps {
  departments: Department[];
  onSelectCameraForMap?: (cam: Camera) => void;
}

export const CameraRegistry: React.FC<CameraRegistryProps> = ({ departments, onSelectCameraForMap }) => {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);

  // Filters
  const [search, setSearch] = useState('');
  const [selectedDept, setSelectedDept] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [selectedType, setSelectedType] = useState('');

  // Selected Camera Detail Drawer
  const [selectedCam, setSelectedCam] = useState<Camera | null>(null);
  const [camDetails, setCamDetails] = useState<any>(null);

  // State Transition Modal
  const [showLifecycleModal, setShowLifecycleModal] = useState(false);
  const [targetStatus, setTargetStatus] = useState('Active');
  const [justification, setJustification] = useState('');

  // Bulk CSV Onboarding Modal
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [csvText, setCsvText] = useState('');
  const [validationResult, setValidationResult] = useState<any>(null);
  const [validating, setValidating] = useState(false);
  const [committing, setCommitting] = useState(false);

  const fetchCameras = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (selectedDept) params.append('dept_id', selectedDept);
      if (selectedStatus) params.append('status', selectedStatus);
      if (selectedType) params.append('camera_type', selectedType);
      params.append('limit', '100');

      const res = await fetch(`/api/cameras?${params.toString()}`);
      const data = await res.json();
      setCameras(data.cameras || []);
      setTotal(data.total || 0);
    } catch (e) {
      console.error('Failed to fetch cameras', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCameras();
  }, [search, selectedDept, selectedStatus, selectedType]);

  const viewCameraDetails = async (cam: Camera) => {
    setSelectedCam(cam);
    try {
      const res = await fetch(`/api/cameras/${cam.id}`);
      const data = await res.json();
      setCamDetails(data);
    } catch (e) {
      console.error('Failed to fetch camera details', e);
    }
  };

  const handleStateTransition = async () => {
    if (!selectedCam || !justification) return;
    try {
      const res = await fetch(`/api/cameras/${selectedCam.id}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          new_status: targetStatus,
          justification: justification,
          user_name: 'Admin Control Officer'
        })
      });
      const data = await res.json();
      if (data.success) {
        setShowLifecycleModal(false);
        setJustification('');
        fetchCameras();
        viewCameraDetails(selectedCam);
      }
    } catch (e) {
      console.error('State transition failed', e);
    }
  };

  const handleBulkValidate = async () => {
    if (!csvText.trim()) return;
    setValidating(true);
    try {
      const res = await fetch('/api/cameras/bulk-validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ csv_text: csvText })
      });
      const data = await res.json();
      setValidationResult(data);
    } catch (e) {
      console.error('Bulk validation error', e);
    } finally {
      setValidating(false);
    }
  };

  const handleBulkCommit = async () => {
    if (!validationResult || !validationResult.valid_rows) return;
    setCommitting(true);
    try {
      const res = await fetch('/api/cameras/bulk-commit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ valid_rows: validationResult.valid_rows })
      });
      const data = await res.json();
      if (data.success) {
        alert(`Successfully onboarded ${data.committed_count} cameras into Registry!`);
        setShowBulkModal(false);
        setCsvText('');
        setValidationResult(null);
        fetchCameras();
      }
    } catch (e) {
      console.error('Commit failed', e);
    } finally {
      setCommitting(false);
    }
  };

  const downloadErrorCsv = () => {
    if (!validationResult || !validationResult.error_rows) return;
    let content = 'row_number,asset_code,name,errors\n';
    validationResult.error_rows.forEach((r: any) => {
      content += `"${r.row_number}","${r.asset_code}","${r.name}","${r.errors}"\n`;
    });
    const blob = new Blob([content], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'bulk_onboarding_errors.csv';
    a.click();
  };

  const sampleCsvTemplate = `asset_code,name,dept_id,camera_type,latitude,longitude,nvr_ip
GJ-GOV-CAM-2024-9001,SG Highway Toll Ahmedabad,DEPT-01,ANPR / LPR Dedicated,23.0225,72.5714,10.10.4.10
GJ-GOV-CAM-2024-9002,Gandhinagar Capital Gate,DEPT-04,IP Bullet,23.2156,72.6369,10.10.4.11
INVALID_ROW_DEMO,,DEPT-02,PTZ Speed Dome,INVALID_LAT,72.6369,10.10.4.11`;

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/90 border border-slate-800 p-5 rounded-xl shadow-lg">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center">
            <Building2 className="w-6 h-6 text-cyan-400 mr-2.5" />
            Scalable Multi-Department Camera Registry
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Managing 80,000+ camera assets across 26 Sovereign Government Departments with complete metadata profiles
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button 
            onClick={() => {
              setCsvText(sampleCsvTemplate);
              setValidationResult(null);
              setShowBulkModal(true);
            }}
            className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-semibold rounded-lg shadow-lg shadow-cyan-500/20 transition"
          >
            <Upload className="w-4 h-4" />
            <span>Bulk CSV Onboarding Engine</span>
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl shadow-lg grid grid-cols-1 md:grid-cols-4 gap-3">
        {/* Search */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input 
            type="text" 
            placeholder="Search Asset Code, Name, District..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        {/* Department Filter (26 Departments) */}
        <div>
          <select 
            value={selectedDept}
            onChange={(e) => setSelectedDept(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
          >
            <option value="">All 26 Government Departments</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>{d.name} ({d.code})</option>
            ))}
          </select>
        </div>

        {/* Camera Status */}
        <div>
          <select 
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Lifecycle Statuses</option>
            <option value="Active">Active</option>
            <option value="Maintenance Due">Maintenance Due</option>
            <option value="Fault/Repair">Fault/Repair</option>
            <option value="Decommissioned">Decommissioned</option>
          </select>
        </div>

        {/* Camera Type */}
        <div>
          <select 
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Hardware Types</option>
            <option value="IP Bullet">IP Bullet</option>
            <option value="IP Dome">IP Dome</option>
            <option value="PTZ Speed Dome">PTZ Speed Dome</option>
            <option value="Thermal InfraRed">Thermal InfraRed</option>
            <option value="ANPR / LPR Dedicated">ANPR / LPR Dedicated</option>
            <option value="360 Panoramic">360 Panoramic</option>
          </select>
        </div>
      </div>

      {/* Main Table View */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl shadow-lg overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex justify-between items-center text-xs text-slate-400">
          <span>Showing <strong className="text-white">{cameras.length}</strong> of <strong className="text-white">{total}</strong> registered camera nodes</span>
          <span className="font-mono text-cyan-400">PostGIS Index Active</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase font-semibold text-[11px] border-b border-slate-800">
              <tr>
                <th className="py-3.5 px-4">Asset Code</th>
                <th className="py-3.5 px-4">Camera Name</th>
                <th className="py-3.5 px-4">Department Owner</th>
                <th className="py-3.5 px-4">District / Ward</th>
                <th className="py-3.5 px-4">Hardware Type</th>
                <th className="py-3.5 px-4">Status & Health</th>
                <th className="py-3.5 px-4">Stream Protocol</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {cameras.map((cam) => (
                <tr key={cam.id} className="hover:bg-slate-800/50 transition">
                  <td className="py-3 px-4 font-mono text-cyan-400 font-semibold">{cam.asset_code}</td>
                  <td className="py-3 px-4 font-medium text-white">{cam.name}</td>
                  <td className="py-3 px-4">{cam.dept_name}</td>
                  <td className="py-3 px-4">{cam.district}</td>
                  <td className="py-3 px-4">
                    <span className="bg-slate-800 text-slate-300 px-2 py-0.5 rounded text-[11px] border border-slate-700">
                      {cam.camera_type}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <span className={`inline-block w-2 h-2 rounded-full ${cam.is_online ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'}`} />
                      <span className={`font-semibold ${cam.status === 'Active' ? 'text-emerald-400' : 'text-amber-400'}`}>
                        {cam.status}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-400">{cam.protocol} ({cam.resolution})</td>
                  <td className="py-3 px-4 text-right space-x-2">
                    <button 
                      onClick={() => viewCameraDetails(cam)}
                      className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-cyan-400 rounded text-[11px] transition"
                    >
                      Inspect Profile
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Camera Details & Lifecycle Drawer Modal */}
      {selectedCam && camDetails && (
        <div className="fixed inset-0 z-[99999] bg-black/70 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-2xl bg-slate-900 border-l border-slate-800 h-full overflow-y-auto p-6 space-y-6 shadow-2xl">
            <div className="flex justify-between items-start border-b border-slate-800 pb-4">
              <div>
                <span className="text-xs font-mono text-cyan-400">{selectedCam.asset_code}</span>
                <h3 className="text-lg font-bold text-white">{selectedCam.name}</h3>
                <p className="text-xs text-slate-400">{selectedCam.dept_name} • {selectedCam.station_division}</p>
              </div>
              <button onClick={() => setSelectedCam(null)} className="text-slate-400 hover:text-white p-1">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Quick Status Bar */}
            <div className="flex items-center justify-between bg-slate-950 p-4 rounded-xl border border-slate-800">
              <div>
                <span className="text-xs text-slate-400 uppercase font-semibold">Lifecycle State</span>
                <div className="text-sm font-bold text-white mt-0.5 flex items-center space-x-2">
                  <span className={`w-2.5 h-2.5 rounded-full ${selectedCam.is_online ? 'bg-emerald-400' : 'bg-red-400'}`} />
                  <span>{selectedCam.status}</span>
                </div>
              </div>

              <button 
                onClick={() => {
                  setTargetStatus(selectedCam.status);
                  setShowLifecycleModal(true);
                }}
                className="px-3 py-1.5 bg-cyan-950 text-cyan-400 border border-cyan-800 rounded-lg text-xs font-semibold hover:bg-cyan-900 transition"
              >
                Change Lifecycle State
              </button>
            </div>

            {/* Metadata Grid Tabs */}
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="bg-slate-950/60 p-3.5 rounded-lg border border-slate-800/80 space-y-2">
                <span className="text-cyan-400 font-semibold uppercase text-[10px] tracking-wider block">Geospatial Metadata</span>
                <div><strong className="text-slate-400">Coordinates:</strong> {selectedCam.latitude.toFixed(5)}, {selectedCam.longitude.toFixed(5)}</div>
                <div><strong className="text-slate-400">Altitude:</strong> {selectedCam.altitude}m</div>
                <div><strong className="text-slate-400">Azimuth / FOV Angle:</strong> {selectedCam.fov_azimuth}° / {selectedCam.fov_angle}°</div>
                <div><strong className="text-slate-400">Coverage Radius:</strong> {selectedCam.coverage_radius}m</div>
              </div>

              <div className="bg-slate-950/60 p-3.5 rounded-lg border border-slate-800/80 space-y-2">
                <span className="text-cyan-400 font-semibold uppercase text-[10px] tracking-wider block">Technical Specs</span>
                <div><strong className="text-slate-400">Camera Type:</strong> {selectedCam.camera_type}</div>
                <div><strong className="text-slate-400">Resolution & FPS:</strong> {selectedCam.resolution} @ {selectedCam.fps} FPS</div>
                <div><strong className="text-slate-400">NVR IP / Port:</strong> {selectedCam.nvr_ip}:{selectedCam.nvr_port}</div>
                <div><strong className="text-slate-400">Protocol:</strong> {selectedCam.protocol}</div>
              </div>

              <div className="bg-slate-950/60 p-3.5 rounded-lg border border-slate-800/80 space-y-2">
                <span className="text-cyan-400 font-semibold uppercase text-[10px] tracking-wider block">Storage & Network</span>
                <div><strong className="text-slate-400">Architecture:</strong> {selectedCam.storage_arch}</div>
                <div><strong className="text-slate-400">Storage Capacity:</strong> {selectedCam.storage_tb} TB</div>
                <div><strong className="text-slate-400">Retention Policy:</strong> {selectedCam.retention_days} Days</div>
                <div><strong className="text-slate-400">Link / Bandwidth:</strong> {selectedCam.link_type} ({selectedCam.bandwidth_mbps} Mbps)</div>
              </div>

              <div className="bg-slate-950/60 p-3.5 rounded-lg border border-slate-800/80 space-y-2">
                <span className="text-cyan-400 font-semibold uppercase text-[10px] tracking-wider block">Vendor & AMC Warranty</span>
                <div><strong className="text-slate-400">Vendor Name:</strong> {selectedCam.vendor_name}</div>
                <div><strong className="text-slate-400">Ownership:</strong> {selectedCam.ownership}</div>
                <div><strong className="text-slate-400">AMC Expiry:</strong> {selectedCam.amc_expiry}</div>
                <div><strong className="text-slate-400">Warranty Status:</strong> <span className={selectedCam.warranty_status === 'Active' ? 'text-emerald-400' : 'text-red-400'}>{selectedCam.warranty_status}</span></div>
              </div>
            </div>

            {/* Audit History Log */}
            <div>
              <h4 className="text-xs font-semibold uppercase text-slate-400 mb-2 flex items-center">
                <History className="w-4 h-4 mr-1 text-cyan-400" />
                Lifecycle Audit Trail History
              </h4>
              <div className="bg-slate-950 rounded-lg p-3 border border-slate-800 space-y-2 max-h-40 overflow-y-auto text-xs">
                {camDetails.audit_logs && camDetails.audit_logs.length > 0 ? (
                  camDetails.audit_logs.map((a: AuditLog) => (
                    <div key={a.id} className="border-b border-slate-800/60 pb-1.5 last:border-0 text-slate-300">
                      <div className="flex justify-between font-mono text-[10px] text-slate-400">
                        <span>{a.timestamp}</span>
                        <span>{a.user_name}</span>
                      </div>
                      <p className="mt-0.5"><strong className="text-cyan-400">{a.previous_state}</strong> → <strong className="text-emerald-400">{a.new_state}</strong>: {a.justification}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-slate-500 text-xs">No prior state transition logs.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Lifecycle Transition Modal */}
      {showLifecycleModal && selectedCam && (
        <div className="fixed inset-0 z-[99999] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white flex items-center">
              <Settings2 className="w-5 h-5 text-cyan-400 mr-2" />
              Camera Lifecycle Transition Engine
            </h3>
            <p className="text-xs text-slate-400">Target Asset: <strong className="text-white">{selectedCam.asset_code}</strong></p>

            <div>
              <label className="text-xs text-slate-300 block mb-1">Target Lifecycle Status</label>
              <select 
                value={targetStatus} 
                onChange={(e) => setTargetStatus(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
              >
                <option value="Planned">Planned</option>
                <option value="Procured">Procured</option>
                <option value="Installed">Installed</option>
                <option value="Active">Active</option>
                <option value="Maintenance Due">Maintenance Due</option>
                <option value="Fault/Repair">Fault/Repair</option>
                <option value="Replacement">Replacement</option>
                <option value="Decommissioned">Decommissioned</option>
              </select>
            </div>

            <div>
              <label className="text-xs text-slate-300 block mb-1">Audit Transition Justification *</label>
              <textarea 
                rows={3}
                placeholder="State reason for transition (e.g. Completed AMC repair, Routine upgrade)..."
                value={justification}
                onChange={(e) => setJustification(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="flex justify-end space-x-3 pt-2">
              <button onClick={() => setShowLifecycleModal(false)} className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg text-xs hover:bg-slate-700">
                Cancel
              </button>
              <button 
                onClick={handleStateTransition} 
                disabled={!justification.trim()}
                className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold rounded-lg text-xs disabled:opacity-50"
              >
                Commit State Change
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk CSV Onboarding Modal */}
      {showBulkModal && (
        <div className="fixed inset-0 z-[99999] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-3xl w-full p-6 space-y-4 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center">
                <FileSpreadsheet className="w-5 h-5 text-cyan-400 mr-2" />
                Bulk Camera CSV Onboarding & Pre-Commit Validator
              </h3>
              <button onClick={() => setShowBulkModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-400">
              Paste camera CSV dataset below to trigger dry-run simulation, row-level schema check, and error downloadable report.
            </p>

            <textarea 
              rows={6}
              value={csvText}
              onChange={(e) => setCsvText(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs font-mono text-cyan-300 focus:outline-none focus:border-cyan-500"
            />

            <div className="flex items-center space-x-3">
              <button 
                onClick={handleBulkValidate}
                disabled={validating}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-slate-700 font-semibold rounded-lg text-xs"
              >
                {validating ? 'Simulating Dry-Run...' : 'Run Dry-Run Pre-Commit Simulation'}
              </button>
            </div>

            {/* Validation Results Report */}
            {validationResult && (
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between bg-slate-950 p-3.5 rounded-lg border border-slate-800 text-xs">
                  <div>
                    <span className="text-slate-400">Simulation Status: </span>
                    <span className="text-white font-semibold">Processed {validationResult.total_rows_processed} rows</span>
                  </div>
                  <div className="flex space-x-4">
                    <span className="text-emerald-400 font-bold">{validationResult.valid_count} Valid Rows</span>
                    <span className="text-red-400 font-bold">{validationResult.error_count} Error Rows</span>
                  </div>
                </div>

                {/* Error Table */}
                {validationResult.error_count > 0 && (
                  <div className="bg-red-950/20 border border-red-900/60 rounded-lg p-3 text-xs space-y-2">
                    <div className="flex justify-between items-center text-red-300 font-semibold">
                      <span>Row-Level Syntax & Schema Validation Errors</span>
                      <button onClick={downloadErrorCsv} className="flex items-center space-x-1 text-red-400 hover:underline">
                        <Download className="w-3.5 h-3.5" />
                        <span>Download Error Rows CSV</span>
                      </button>
                    </div>

                    <div className="max-h-36 overflow-y-auto space-y-1.5 pr-1">
                      {validationResult.error_rows.map((err: any, idx: number) => (
                        <div key={idx} className="bg-slate-950/80 p-2 rounded border border-red-900/40 text-[11px]">
                          <span className="font-mono text-amber-400 font-bold">Row #{err.row_number}</span> [{err.asset_code}]: <span className="text-red-300">{err.errors}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Commit Action */}
                <div className="flex justify-between items-center pt-2">
                  <span className="text-xs text-slate-400">Partial Commit enabled: Valid rows will be committed while bad rows are ignored.</span>
                  <button 
                    onClick={handleBulkCommit}
                    disabled={committing || validationResult.valid_count === 0}
                    className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-lg text-xs shadow-lg shadow-emerald-600/20 disabled:opacity-50 transition"
                  >
                    {committing ? 'Committing...' : `Commit ${validationResult.valid_count} Valid Cameras to Registry`}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
