import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polygon, Circle, useMapEvents, useMap } from 'react-leaflet';
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
  Layers, 
  Eye, 
  MapPin, 
  Compass, 
  Maximize2, 
  Activity, 
  ShieldAlert,
  Play,
  X
} from 'lucide-react';
import { Department } from '../types';

// Fix Leaflet default marker icon paths in React
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom Status Icon Generators
const createCameraIcon = (status: string, cameraType: string) => {
  const color = status === 'Active' ? '#10b981' : status === 'Maintenance Due' ? '#f59e0b' : '#ef4444';
  const html = `
    <div style="background-color: ${color}; width: 14px; height: 14px; border-radius: 50%; border: 2px solid #0f172a; box-shadow: 0 0 10px ${color};"></div>
  `;
  return L.divIcon({
    html: html,
    className: 'custom-cam-marker',
    iconSize: [14, 14],
    iconAnchor: [7, 7]
  });
};

interface GisMapProps {
  departments: Department[];
}

export const GisMap: React.FC<GisMapProps> = ({ departments }) => {
  const [gisCameras, setGisCameras] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Layer Toggles
  const [showFovCones, setShowFovCones] = useState(true);
  const [selectedDeptFilter, setSelectedDeptFilter] = useState('');
  const [selectedStatusFilter, setSelectedStatusFilter] = useState('');

  // Proximity Search Tool
  const [searchLat, setSearchLat] = useState<number | null>(null);
  const [searchLng, setSearchLng] = useState<number | null>(null);
  const [searchRadius, setSearchRadius] = useState<number>(500); // meters
  const [proximityMatches, setProximityMatches] = useState<any[]>([]);
  const [isSearchingProximity, setIsSearchingProximity] = useState(false);

  // Selected Camera Live Feed Preview Drawer
  const [selectedCam, setSelectedCam] = useState<any | null>(null);

  const fetchGisCameras = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedDeptFilter) params.append('dept_id', selectedDeptFilter);
      if (selectedStatusFilter) params.append('status', selectedStatusFilter);

      const res = await fetch(`/api/gis/cameras?${params.toString()}`);
      const data = await res.json();
      setGisCameras(data || []);
    } catch (e) {
      console.error('Failed to fetch GIS cameras', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGisCameras();
  }, [selectedDeptFilter, selectedStatusFilter]);

  // Spatial Radius Proximity Search Handler
  const executeRadiusSearch = async (lat: number, lng: number, radius: number) => {
    setSearchLat(lat);
    setSearchLng(lng);
    setIsSearchingProximity(true);
    try {
      const res = await fetch(`/api/gis/radius-search?lat=${lat}&lng=${lng}&radius_meters=${radius}`);
      const data = await res.json();
      setProximityMatches(data.matches || []);
    } catch (e) {
      console.error('Radius search failed', e);
    } finally {
      setIsSearchingProximity(false);
    }
  };

  // Map Click Listener Component
  function MapClickListener() {
    useMapEvents({
      click(e) {
        executeRadiusSearch(e.latlng.lat, e.latlng.lng, searchRadius);
      },
    });
    return null;
  }

  return (
    <div className="space-y-4">
      {/* Map Control Header */}
      <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center">
            <Compass className="w-5 h-5 text-cyan-400 mr-2" />
            Advanced GIS Command Map & PostGIS FOV Visualizer
          </h2>
          <p className="text-xs text-slate-400">
            Real-time PostGIS spatial indexing, azimuth coverage cones, and 500m proximity search tool
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-xs">
          {/* FOV Cone Toggle */}
          <button 
            onClick={() => setShowFovCones(!showFovCones)}
            className={`px-3 py-1.5 rounded-lg border font-medium flex items-center space-x-1.5 transition ${
              showFovCones
                ? 'bg-cyan-950 text-cyan-400 border-cyan-800'
                : 'bg-slate-800 text-slate-400 border-slate-700'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>FOV Cones {showFovCones ? 'ON' : 'OFF'}</span>
          </button>

          {/* Department Layer Toggle */}
          <select 
            value={selectedDeptFilter}
            onChange={(e) => setSelectedDeptFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500"
          >
            <option value="">All 26 Sovereign Departments</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>

          {/* Radius Selector */}
          <div className="flex items-center space-x-1 bg-slate-950 px-2 py-1 rounded-lg border border-slate-800 text-slate-300">
            <span className="text-slate-400">Proximity Radius:</span>
            <select 
              value={searchRadius}
              onChange={(e) => {
                const r = Number(e.target.value);
                setSearchRadius(r);
                if (searchLat && searchLng) executeRadiusSearch(searchLat, searchLng, r);
              }}
              className="bg-transparent text-cyan-400 font-mono focus:outline-none"
            >
              <option value={200}>200m</option>
              <option value={500}>500m</option>
              <option value={1000}>1000m (1km)</option>
              <option value={2000}>2000m (2km)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Proximity Result Banner if active */}
      {searchLat && searchLng && (
        <div className="bg-cyan-950/60 border border-cyan-800/80 p-3 rounded-xl flex items-center justify-between text-xs text-cyan-200">
          <div className="flex items-center space-x-2">
            <MapPin className="w-4 h-4 text-cyan-400 animate-bounce" />
            <span>
              Proximity Scan around Target Point (<strong>{searchLat.toFixed(4)}, {searchLng.toFixed(4)}</strong>): 
              <strong className="text-white ml-1.5">{proximityMatches.length} cameras found within {searchRadius}m</strong>
            </span>
          </div>
          <button 
            onClick={() => {
              setSearchLat(null);
              setSearchLng(null);
              setProximityMatches([]);
            }}
            className="text-cyan-400 hover:text-white text-xs underline"
          >
            Clear Scan Overlay
          </button>
        </div>
      )}

      {/* Main Map Container */}
      <div className="relative z-0 isolate bg-slate-950 border border-slate-800 rounded-xl overflow-hidden shadow-2xl h-[650px]">
        <MapContainer 
          center={[22.8000, 71.8000]} // Gujarat Geographic Center
          zoom={9} 
          scrollWheelZoom={true}
          style={{ width: '100%', height: '100%' }}
        >
          <MapResizeController />
          <MapClickListener />

          {/* Zero-Watermark Professional Command Center Dark Map Tiles */}
          <TileLayer
            attribution='&copy; <a href="https://www.esri.com/">Esri</a>, DeLorme, NAVTEQ, USGS, TomTom'
            url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
          />

          {/* Proximity Circle Overlay if active */}
          {searchLat && searchLng && (
            <Circle 
              center={[searchLat, searchLng]} 
              radius={searchRadius}
              pathOptions={{ color: '#06b6d4', fillColor: '#06b6d4', fillOpacity: 0.15, weight: 2, dashArray: '4, 4' }}
            />
          )}

          {/* FOV Cones Polygons Layer */}
          {showFovCones && gisCameras.map((cam) => {
            if (!cam.fov_cone_coords || cam.fov_cone_coords.length === 0) return null;
            const color = cam.is_online ? '#06b6d4' : '#ef4444';
            return (
              <Polygon 
                key={`fov-${cam.id}`}
                positions={cam.fov_cone_coords}
                pathOptions={{
                  color: color,
                  fillColor: color,
                  fillOpacity: 0.18,
                  weight: 1
                }}
              />
            );
          })}

          {/* Camera Markers Layer */}
          {gisCameras.map((cam) => (
            <Marker 
              key={cam.id} 
              position={[cam.latitude, cam.longitude]}
              icon={createCameraIcon(cam.status, cam.camera_type)}
            >
              <Popup>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between items-center font-mono text-[10px] text-cyan-400">
                    <span>{cam.asset_code}</span>
                    <span className={`px-1.5 py-0.5 rounded font-bold ${cam.is_online ? 'bg-emerald-950 text-emerald-400' : 'bg-red-950 text-red-400'}`}>
                      {cam.status}
                    </span>
                  </div>
                  <h4 className="font-bold text-white text-xs leading-tight">{cam.name}</h4>
                  <div className="text-slate-300 text-[11px]">
                    <div><strong>Dept:</strong> {cam.dept_name}</div>
                    <div><strong>Type:</strong> {cam.camera_type}</div>
                    <div><strong>Azimuth / Radius:</strong> {cam.fov_azimuth}° / {cam.coverage_radius}m</div>
                  </div>

                  <button 
                    onClick={() => setSelectedCam(cam)}
                    className="w-full mt-2 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold rounded text-[11px] flex items-center justify-center space-x-1"
                  >
                    <Play className="w-3 h-3 fill-current" />
                    <span>On-Demand Stream Preview</span>
                  </button>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>

      {/* On-Demand Video Feed Drawer Preview */}
      {selectedCam && (
        <div className="fixed bottom-6 right-6 z-[99999] bg-slate-900 border border-slate-700 rounded-xl p-4 shadow-2xl shadow-cyan-500/10 max-w-md w-full space-y-3">
          <div className="flex justify-between items-center border-b border-slate-800 pb-2">
            <div>
              <span className="text-[10px] font-mono text-cyan-400">{selectedCam.asset_code}</span>
              <h4 className="text-xs font-bold text-white leading-none mt-0.5">{selectedCam.name}</h4>
            </div>
            <button onClick={() => setSelectedCam(null)} className="text-slate-400 hover:text-white">
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Simulated HLS Video Player */}
          <div className="relative aspect-video bg-black rounded-lg overflow-hidden border border-slate-800 flex items-center justify-center">
            {selectedCam?.stream_url ? (
              <video 
                src={selectedCam.stream_url} 
                autoPlay 
                loop 
                muted 
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-slate-500 font-mono text-xs">
                NO STREAM CONFIGURED
              </div>
            )}
            <div className="absolute top-2 left-2 bg-red-600/80 text-white font-mono text-[9px] px-2 py-0.5 rounded flex items-center space-x-1">
              <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping" />
              <span>LIVE BROKERED FEED</span>
            </div>
            <div className="absolute bottom-2 right-2 bg-black/70 text-slate-300 font-mono text-[9px] px-2 py-0.5 rounded">
              WebRTC / HLS • 1080p 30FPS
            </div>
          </div>

          <div className="flex justify-between items-center text-[11px] text-slate-400">
            <span>Owner: <strong>{selectedCam.dept_name}</strong></span>
            <span className="text-emerald-400 font-semibold">PostGIS Lat/Long Verified</span>
          </div>
        </div>
      )}
    </div>
  );
};
