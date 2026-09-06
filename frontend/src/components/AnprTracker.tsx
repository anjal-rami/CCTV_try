import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';

function MapResizeController() {
  const map = useMap();
  useEffect(() => {
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 150);
    return () => clearTimeout(timer);
  }, [map]);
  return null;
}
import { 
  Scan, 
  Search, 
  ShieldAlert, 
  MapPin, 
  Clock, 
  Plus, 
  CheckCircle2, 
  Play, 
  Navigation,
  Car,
  AlertTriangle,
  Layers,
  ChevronRight
} from 'lucide-react';
import { WatchlistItem, RouteSearchResult, RouteWaypoint, User } from '../types';

// Custom Route Marker Generator
const createRouteMarkerIcon = (step: number, isWatchlist: boolean) => {
  const bgColor = isWatchlist ? '#ef4444' : '#06b6d4';
  const html = `
    <div style="background-color: ${bgColor}; color: #0f172a; font-weight: 800; font-size: 11px; width: 22px; height: 22px; border-radius: 50%; border: 2px solid #ffffff; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 10px ${bgColor};">
      ${step}
    </div>
  `;
  return L.divIcon({
    html: html,
    className: 'custom-route-marker',
    iconSize: [22, 22],
    iconAnchor: [11, 11]
  });
};

interface AnprTrackerProps {
  currentUser?: User | null;
}

export const AnprTracker: React.FC<AnprTrackerProps> = ({ currentUser }) => {
  // Check strict law enforcement authority for Watchlist CRUD
  const hasWatchlistWriteAccess = (): boolean => {
    if (!currentUser) return true; // Default fallback for dev if unauthenticated
    const role = currentUser.role;
    if (role === 'SUPER_ADMIN' || role === 'AI_ANALYST') return true;
    if (role === 'DEPARTMENT_ADMIN') {
      const dept = (currentUser.departmentName || '').toLowerCase();
      return dept.includes('police') || dept.includes('home') || dept.includes('rto') || dept.includes('transport');
    }
    return false;
  };

  const isWriteAuthorized = hasWatchlistWriteAccess();

  // ANPR Route Reconstruction State
  const [searchPlate, setSearchPlate] = useState('GJ-01-AB-1234');
  const [routeResult, setRouteResult] = useState<RouteSearchResult | null>(null);
  const [loadingRoute, setLoadingRoute] = useState(false);
  const [selectedWaypoint, setSelectedWaypoint] = useState<RouteWaypoint | null>(null);

  // Watchlist State
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [showAddWatchlist, setShowAddWatchlist] = useState(false);
  const [newPlate, setNewPlate] = useState('');
  const [newCategory, setNewCategory] = useState('Stolen Vehicle');
  const [newDesc, setNewDesc] = useState('');
  const [newSeverity, setNewSeverity] = useState('Critical');

  // Restricted Zone Setup Canvas Demo State
  const [drawingCam, setDrawingCam] = useState<string>('CAM-0042');
  const [intrusionAlerts, setIntrusionAlerts] = useState<string[]>([]);

  const fetchWatchlist = async () => {
    try {
      const res = await fetch('/api/anpr/watchlist');
      const data = await res.json();
      setWatchlist(data || []);
    } catch (e) {
      console.error('Failed to fetch watchlist', e);
    }
  };

  const handleRouteSearch = async (plateToSearch?: string) => {
    const target = (plateToSearch || searchPlate).trim();
    if (!target) return;
    setLoadingRoute(true);
    try {
      const res = await fetch(`/api/anpr/search?plate_number=${encodeURIComponent(target)}`);
      const data = await res.json();
      setRouteResult(data);
      if (data.waypoints && data.waypoints.length > 0) {
        setSelectedWaypoint(data.waypoints[0]);
      }
    } catch (e) {
      console.error('ANPR route search failed', e);
    } finally {
      setLoadingRoute(false);
    }
  };

  useEffect(() => {
    fetchWatchlist();
    handleRouteSearch('GJ-01-AB-1234'); // Initial search on load
  }, []);

  const handleAddWatchlist = async () => {
    if (!newPlate.trim()) return;
    try {
      const res = await fetch('/api/anpr/watchlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plate_number: newPlate,
          category: newCategory,
          description: newDesc || 'Flagged via Control Center',
          severity: newSeverity,
          flagged_by: 'Control Room Officer'
        })
      });
      const data = await res.json();
      if (data.success) {
        setShowAddWatchlist(false);
        setNewPlate('');
        setNewDesc('');
        fetchWatchlist();
      }
    } catch (e) {
      console.error('Failed to add watchlist item', e);
    }
  };

  // Convert waypoints to Leaflet LatLng tuples
  const polylineCoords: [number, number][] = routeResult?.waypoints.map((w) => [w.latitude, w.longitude]) || [];

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="bg-slate-900/90 border border-slate-800 p-5 rounded-xl shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center">
            <Scan className="w-6 h-6 text-cyan-400 mr-2.5" />
            AI ANPR Engine & Cross-Camera Vehicle Route Reconstruction
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Deep Sort & PaddleOCR multi-node tracking across 80,000+ camera streams with GIS journey tracing
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {isWriteAuthorized ? (
            <button 
              onClick={() => setShowAddWatchlist(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 hover:from-red-500 hover:to-amber-500 text-white text-xs font-semibold rounded-lg shadow-lg shadow-red-500/20 transition"
            >
              <Plus className="w-4 h-4" />
              <span>Add Vehicle to Flagged Watchlist</span>
            </button>
          ) : (
            <span className="text-[11px] font-mono text-amber-400 bg-amber-950/80 border border-amber-800 px-3 py-1.5 rounded-lg flex items-center">
              <ShieldAlert className="w-3.5 h-3.5 mr-1.5 text-amber-400" />
              Watchlist CRUD Locked (Police / AI Analyst Only)
            </span>
          )}
        </div>
      </div>

      {/* Main ANPR Route Reconstruction Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Panel: Search & Waypoints List */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
          <h3 className="text-base font-bold text-white flex items-center">
            <Navigation className="w-5 h-5 text-cyan-400 mr-2" />
            Vehicle License Plate Route Tracker
          </h3>

          {/* Search Box */}
          <div className="flex space-x-2">
            <input 
              type="text"
              value={searchPlate}
              onChange={(e) => setSearchPlate(e.target.value.toUpperCase())}
              placeholder="e.g. MH-12-AB-1234"
              className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white font-mono uppercase focus:outline-none focus:border-cyan-500"
            />
            <button 
              onClick={() => handleRouteSearch()}
              disabled={loadingRoute}
              className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold rounded-lg shadow transition disabled:opacity-50"
            >
              {loadingRoute ? 'Tracing...' : 'Trace Journey'}
            </button>
          </div>

          {/* Sample Target Plate Quick Chips */}
          <div className="flex flex-wrap gap-1.5 text-[11px]">
            <span className="text-slate-400 self-center mr-1">Quick Sample:</span>
            {['GJ-01-AB-1234', 'GJ-05-XY-9876', 'GJ-06-DE-5555'].map((plate) => (
              <button 
                key={plate}
                onClick={() => {
                  setSearchPlate(plate);
                  handleRouteSearch(plate);
                }}
                className={`px-2 py-0.5 rounded font-mono border transition ${
                  searchPlate === plate
                    ? 'bg-cyan-950 text-cyan-400 border-cyan-800'
                    : 'bg-slate-950 text-slate-300 border-slate-800 hover:bg-slate-800'
                }`}
              >
                {plate}
              </button>
            ))}
          </div>

          {/* Summary Box */}
          {routeResult && (
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-3.5 space-y-2 text-xs">
              <div className="flex justify-between items-center text-slate-300">
                <span>Total Camera Detections:</span>
                <strong className="text-cyan-400 font-mono">{routeResult.total_detections} nodes</strong>
              </div>
              <div className="flex justify-between items-center text-slate-300">
                <span>Total Distance Traversed:</span>
                <strong className="text-emerald-400 font-mono">{routeResult.total_distance_km} km</strong>
              </div>
              <div className="flex justify-between items-center text-slate-300">
                <span>First Detections Seen:</span>
                <span className="font-mono text-slate-400">{routeResult.first_seen || 'N/A'}</span>
              </div>
            </div>
          )}

          {/* Chronological Waypoints List */}
          <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
            <h4 className="text-xs font-semibold uppercase text-slate-400 tracking-wider">Chronological Node Traversals</h4>
            {routeResult && routeResult.waypoints.map((w) => (
              <div 
                key={w.detection_id}
                onClick={() => setSelectedWaypoint(w)}
                className={`p-3 rounded-lg border text-xs cursor-pointer transition ${
                  selectedWaypoint?.detection_id === w.detection_id
                    ? 'bg-cyan-950/60 border-cyan-500/80 shadow-lg'
                    : 'bg-slate-950/70 border-slate-800 hover:bg-slate-800/60'
                }`}
              >
                <div className="flex justify-between items-center mb-1">
                  <div className="flex items-center space-x-2">
                    <span className="w-5 h-5 rounded-full bg-cyan-500 text-slate-950 font-bold flex items-center justify-center text-[10px]">
                      {w.step}
                    </span>
                    <span className="font-bold text-white">{w.camera_name}</span>
                  </div>
                  {w.is_watchlist_hit && (
                    <span className="bg-red-950 text-red-400 border border-red-800 px-1.5 py-0.5 rounded text-[9px] font-bold">
                      WATCHLIST HIT
                    </span>
                  )}
                </div>

                <div className="text-slate-400 text-[11px] space-y-0.5 pl-7">
                  <div>Department: <strong className="text-slate-300">{w.dept_name}</strong></div>
                  <div>Timestamp: <span className="font-mono text-cyan-300">{w.timestamp}</span></div>
                  {w.distance_from_prev_km > 0 && (
                    <div>Traversed from prev: <span className="font-mono text-emerald-400">+{w.distance_from_prev_km} km</span></div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Panel: GIS Map Traversal & Snapshot Frame */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden shadow-2xl h-[420px] relative z-0 isolate">
            <MapContainer
              center={polylineCoords.length > 0 ? polylineCoords[0] : [22.8000, 71.8000]}
              zoom={9}
              style={{ width: '100%', height: '100%' }}
            >
              <MapResizeController />
              <TileLayer
                attribution='&copy; <a href="https://www.esri.com/">Esri</a>, DeLorme, NAVTEQ, USGS, TomTom'
                url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
              />

              {/* Animated Journey Path Polyline */}
              {polylineCoords.length > 1 && (
                <Polyline 
                  positions={polylineCoords} 
                  pathOptions={{ color: '#06b6d4', weight: 4, opacity: 0.8, dashArray: '6, 6' }} 
                />
              )}

              {/* Waypoint Markers */}
              {routeResult?.waypoints.map((w) => (
                <Marker 
                  key={w.detection_id}
                  position={[w.latitude, w.longitude]}
                  icon={createRouteMarkerIcon(w.step, w.is_watchlist_hit)}
                >
                  <Popup>
                    <div className="space-y-1 text-xs">
                      <div className="font-bold text-white">Step #{w.step}: {w.camera_name}</div>
                      <div>Plate: <strong className="text-cyan-400 font-mono">{w.plate_number}</strong></div>
                      <div>Time: {w.timestamp}</div>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>

          {/* Selected Waypoint Evidence Frame Inspection */}
          {selectedWaypoint && (
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-lg flex flex-col md:flex-row items-center gap-4">
              <div className="w-full md:w-64 h-36 bg-black rounded-lg border border-slate-800 overflow-hidden relative flex-shrink-0">
                <img 
                  src={selectedWaypoint.snapshot_url} 
                  alt="ANPR Visual Evidence Frame"
                  className="w-full h-full object-cover" 
                />
                <div className="absolute top-2 left-2 bg-slate-950/80 px-2 py-0.5 rounded text-[10px] font-mono text-cyan-400 border border-slate-800">
                  EVIDENCE SNAPSHOT
                </div>
              </div>

              <div className="flex-1 space-y-2 text-xs">
                <div className="flex justify-between items-center">
                  <h4 className="font-bold text-white text-sm">ANPR Visual Frame Telemetry</h4>
                  <span className="font-mono text-cyan-400 font-bold bg-cyan-950 px-2 py-0.5 rounded border border-cyan-800">
                    Confidence: {(selectedWaypoint.confidence * 100).toFixed(1)}%
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-slate-300">
                  <div>Plate Characters: <strong className="text-white font-mono">{selectedWaypoint.plate_number}</strong></div>
                  <div>Vehicle Type & Color: <strong className="text-white">{selectedWaypoint.vehicle_color} {selectedWaypoint.vehicle_type}</strong></div>
                  <div>Camera Node: <strong className="text-white">{selectedWaypoint.camera_name}</strong></div>
                  <div>Timestamp: <strong className="text-cyan-300 font-mono">{selectedWaypoint.timestamp}</strong></div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Active Watchlist Management Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-bold text-white flex items-center">
              <ShieldAlert className="w-5 h-5 text-red-400 mr-2" />
              Active High-Priority Flagged Vehicle Watchlist
            </h3>
            <p className="text-xs text-slate-400">Continuous AI stream matching for stolen, suspect, and blacklisted commercial vehicles</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase font-semibold text-[11px] border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Plate Number</th>
                <th className="py-3 px-4">Flagged Category</th>
                <th className="py-3 px-4">Description / Case Info</th>
                <th className="py-3 px-4">Flagged By</th>
                <th className="py-3 px-4">Created Date</th>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {watchlist.map((w) => (
                <tr key={w.id} className="hover:bg-slate-800/40 transition">
                  <td className="py-2.5 px-4 font-mono text-red-400 font-bold">{w.plate_number}</td>
                  <td className="py-2.5 px-4 font-semibold text-white">{w.category}</td>
                  <td className="py-2.5 px-4 text-slate-300">{w.description}</td>
                  <td className="py-2.5 px-4">{w.flagged_by}</td>
                  <td className="py-2.5 px-4 font-mono text-slate-400">{w.created_at}</td>
                  <td className="py-2.5 px-4">
                    <span className={`px-2 py-0.5 rounded font-mono text-[10px] ${w.severity === 'Critical' ? 'bg-red-950 text-red-400 border border-red-800' : 'bg-amber-950 text-amber-400 border border-amber-800'}`}>
                      {w.severity}
                    </span>
                  </td>
                  <td className="py-2.5 px-4 text-right">
                    <button 
                      onClick={() => {
                        setSearchPlate(w.plate_number);
                        handleRouteSearch(w.plate_number);
                      }}
                      className="text-cyan-400 hover:underline text-xs"
                    >
                      Trace Route
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Watchlist Modal */}
      {showAddWatchlist && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white flex items-center">
              <ShieldAlert className="w-5 h-5 text-red-400 mr-2" />
              Flag Vehicle on Active Watchlist
            </h3>

            <div>
              <label className="text-xs text-slate-300 block mb-1">License Plate Number *</label>
              <input 
                type="text"
                placeholder="e.g. MH-12-AB-9999"
                value={newPlate}
                onChange={(e) => setNewPlate(e.target.value.toUpperCase())}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white font-mono uppercase focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div>
              <label className="text-xs text-slate-300 block mb-1">Category</label>
              <select 
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white"
              >
                <option value="Stolen Vehicle">Stolen Vehicle</option>
                <option value="Wanted Suspect">Wanted Suspect</option>
                <option value="Blacklisted Truck">Blacklisted Truck</option>
                <option value="Missing Person">Missing Person</option>
              </select>
            </div>

            <div>
              <label className="text-xs text-slate-300 block mb-1">Case Description</label>
              <textarea 
                rows={2}
                placeholder="Provide incident or FIR details..."
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="flex justify-end space-x-3 pt-2">
              <button onClick={() => setShowAddWatchlist(false)} className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg text-xs">
                Cancel
              </button>
              <button 
                onClick={handleAddWatchlist}
                disabled={!newPlate.trim()}
                className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white font-semibold rounded-lg text-xs disabled:opacity-50"
              >
                Add to Watchlist
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
