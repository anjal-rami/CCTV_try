import React, { useState, useEffect } from 'react';
import { 
  Grid, 
  Maximize2, 
  RotateCw, 
  Tv, 
  Play, 
  Pause, 
  Bookmark, 
  ShieldCheck,
  Volume2,
  VolumeX,
  Layers
} from 'lucide-react';
import { Camera } from '../types';

interface VideoWallProps {
  cameras: Camera[];
}

const PRESET_WALLS = [
  { id: 'traffic', name: 'High-Density Traffic Junctions', deptCode: 'TRN' },
  { id: 'police', name: 'Police Control Room Patrol', deptCode: 'POL' },
  { id: 'godowns', name: 'Civil Supplies & Godowns', deptCode: 'FCS' },
  { id: 'rto', name: 'RTO Checkpoints & Weighbridges', deptCode: 'RTO' },
];

export const VideoWall: React.FC<VideoWallProps> = ({ cameras }) => {
  const [gridLayout, setGridLayout] = useState<'1x1' | '2x2' | '3x3' | '4x4' | '1+5'>('3x3');
  const [activePreset, setActivePreset] = useState<string>('traffic');
  const [isPatrolActive, setIsPatrolActive] = useState<boolean>(false);
  const [patrolIndex, setPatrolIndex] = useState<number>(0);
  const [isMuted, setIsMuted] = useState<boolean>(true);

  // Selected cameras for grid display
  const [gridCameras, setGridCameras] = useState<Camera[]>([]);

  useEffect(() => {
    // Select cameras based on preset
    let target = cameras;
    if (activePreset === 'traffic') {
      target = cameras.filter((c) => c.dept_id === 'DEPT-02' || c.camera_type.includes('ANPR'));
    } else if (activePreset === 'police') {
      target = cameras.filter((c) => c.dept_id === 'DEPT-01');
    } else if (activePreset === 'godowns') {
      target = cameras.filter((c) => c.dept_id === 'DEPT-04');
    } else if (activePreset === 'rto') {
      target = cameras.filter((c) => c.dept_id === 'DEPT-03');
    }

    if (target.length === 0) target = cameras;
    
    // Slice based on layout size
    const count = gridLayout === '1x1' ? 1 : gridLayout === '2x2' ? 4 : gridLayout === '3x3' ? 9 : gridLayout === '4x4' ? 16 : 6;
    setGridCameras(target.slice(0, count));
  }, [gridLayout, activePreset, cameras]);

  // Automated Patrol Mode Rotation Carousel
  useEffect(() => {
    if (!isPatrolActive) return;
    const timer = setInterval(() => {
      setPatrolIndex((prev) => (prev + 1) % Math.max(1, Math.floor(cameras.length / 4)));
      const count = gridLayout === '3x3' ? 9 : 4;
      const start = (patrolIndex * count) % Math.max(1, cameras.length - count);
      setGridCameras(cameras.slice(start, start + count));
    }, 6000);
    return () => clearInterval(timer);
  }, [isPatrolActive, patrolIndex, cameras, gridLayout]);

  const getGridClass = () => {
    switch (gridLayout) {
      case '1x1': return 'grid-cols-1 grid-rows-1';
      case '2x2': return 'grid-cols-2 grid-rows-2';
      case '3x3': return 'grid-cols-3 grid-rows-3';
      case '4x4': return 'grid-cols-4 grid-rows-4';
      case '1+5': return 'grid-cols-3 grid-rows-2';
      default: return 'grid-cols-3 grid-rows-3';
    }
  };

  return (
    <div className="space-y-4">
      {/* Control Toolbar */}
      <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center">
            <Tv className="w-5 h-5 text-cyan-400 mr-2" />
            Configurable Video Wall & Multi-Stream Grid
          </h2>
          <p className="text-xs text-slate-400">
            Vendor-agnostic VMS stream brokering, saved presets, and automated patrol rotation carousel
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-xs">
          {/* Saved Layout Presets */}
          <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
            <Bookmark className="w-3.5 h-3.5 text-cyan-400 ml-1.5" />
            <select 
              value={activePreset} 
              onChange={(e) => setActivePreset(e.target.value)}
              className="bg-transparent text-white font-medium focus:outline-none pr-2"
            >
              {PRESET_WALLS.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          {/* Grid Layout Switcher */}
          <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
            {(['1x1', '2x2', '3x3', '4x4', '1+5'] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => setGridLayout(mode)}
                className={`px-2.5 py-1 rounded font-mono text-[11px] transition ${
                  gridLayout === mode
                    ? 'bg-cyan-600 text-white font-bold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>

          {/* Patrol Mode Toggle */}
          <button 
            onClick={() => setIsPatrolActive(!isPatrolActive)}
            className={`px-3 py-1.5 rounded-lg border font-semibold flex items-center space-x-1.5 transition ${
              isPatrolActive 
                ? 'bg-amber-950 text-amber-300 border-amber-800' 
                : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700'
            }`}
          >
            <RotateCw className={`w-3.5 h-3.5 ${isPatrolActive ? 'animate-spin' : ''}`} />
            <span>Patrol Rotation {isPatrolActive ? 'ACTIVE' : 'OFF'}</span>
          </button>

          {/* Audio Mute Toggle */}
          <button 
            onClick={() => setIsMuted(!isMuted)}
            className="p-1.5 bg-slate-950 border border-slate-800 rounded-lg text-slate-400 hover:text-white"
          >
            {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4 text-emerald-400" />}
          </button>
        </div>
      </div>

      {/* Main Video Wall Grid Display */}
      <div className={`grid gap-2 bg-slate-950 border border-slate-800 p-2 rounded-xl h-[680px] overflow-hidden ${getGridClass()}`}>
        {gridCameras.map((cam, idx) => (
          <div 
            key={cam.id} 
            className="relative bg-black rounded-lg border border-slate-800 overflow-hidden group flex flex-col justify-between"
          >
            {/* Live Video Element */}
            {cam?.stream_url ? (
              <video 
                src={cam.stream_url}
                autoPlay
                loop
                muted={isMuted}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-slate-900/80 text-slate-500 font-mono text-[10px]">
                FEED UNAVAILABLE
              </div>
            )}

            {/* AI Bounding Box Overlay Simulation */}
            <div className="absolute top-1/3 left-1/4 w-28 h-20 border-2 border-cyan-400/80 rounded bg-cyan-400/10 pointer-events-none flex items-start p-1">
              <span className="bg-cyan-500 text-slate-950 text-[9px] font-mono font-bold px-1 rounded">
                VEHICLE 98.4%
              </span>
            </div>

            {/* Top Stream Header Overlay */}
            <div className="absolute top-2 left-2 right-2 flex justify-between items-start pointer-events-none">
              <div className="bg-slate-950/80 backdrop-blur border border-slate-800 px-2 py-1 rounded text-[10px] text-white">
                <span className="font-mono text-cyan-400 font-bold mr-1 border-r border-slate-700 pr-1.5">{cam.asset_code}</span>
                <span>{cam.name}</span>
              </div>

              <span className="bg-red-600/80 text-white font-mono text-[9px] px-1.5 py-0.5 rounded flex items-center space-x-1">
                <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping" />
                <span>LIVE</span>
              </span>
            </div>

            {/* Bottom Stream Footer Overlay */}
            <div className="absolute bottom-2 left-2 right-2 flex justify-between items-end opacity-90 transition pointer-events-none">
              <span className="bg-slate-950/80 border border-slate-800 text-slate-300 font-mono text-[9px] px-2 py-0.5 rounded">
                {cam.dept_name} • {cam.resolution}
              </span>
              <span className="bg-slate-950/80 border border-slate-800 text-cyan-400 font-mono text-[9px] px-2 py-0.5 rounded">
                {cam.protocol}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
