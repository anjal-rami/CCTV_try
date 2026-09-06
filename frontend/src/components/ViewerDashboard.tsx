import React, { useState } from 'react';
import { 
  Eye, 
  ShieldCheck, 
  Lock, 
  Grid, 
  Volume2, 
  VolumeX, 
  AlertTriangle,
  Tv
} from 'lucide-react';
import { Camera } from '../types';

interface ViewerDashboardProps {
  cameras: Camera[];
}

export const ViewerDashboard: React.FC<ViewerDashboardProps> = ({ cameras }) => {
  const [gridLayout, setGridLayout] = useState<'2x2' | '3x3'>('2x2');
  const [isPrivacyMaskEnabled, setIsPrivacyMaskEnabled] = useState<boolean>(true);

  const displayCameras = cameras.slice(0, gridLayout === '2x2' ? 4 : 9);

  return (
    <div className="space-y-4">
      {/* Header Bar */}
      <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="bg-purple-950 text-purple-400 border border-purple-800 px-2.5 py-0.5 rounded font-mono text-[10px] font-bold uppercase">
              DEPARTMENT OPERATOR SESSION
            </span>
            <span className="bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700 font-mono text-[10px]">
              PRIVACY MASKING ENFORCED
            </span>
          </div>
          <h2 className="text-lg font-bold text-white flex items-center mt-1">
            <Eye className="w-5 h-5 text-purple-400 mr-2" />
            Operational Department Monitoring Camera Feed
          </h2>
          <p className="text-xs text-slate-400">
            Real-time feed monitoring. License plates and human faces are automatically blurred for privacy protection.
          </p>
        </div>

        <div className="flex items-center space-x-3 text-xs">
          {/* Privacy Blur Toggle */}
          <button 
            onClick={() => setIsPrivacyMaskEnabled(!isPrivacyMaskEnabled)}
            className={`px-3 py-1.5 rounded-lg border font-semibold flex items-center space-x-1.5 transition ${
              isPrivacyMaskEnabled 
                ? 'bg-purple-950 text-purple-300 border-purple-800' 
                : 'bg-red-950 text-red-300 border-red-800'
            }`}
          >
            <Lock className="w-3.5 h-3.5" />
            <span>Privacy Blur Filter: {isPrivacyMaskEnabled ? 'ENABLED' : 'DISABLED (DEMO)'}</span>
          </button>

          {/* Grid Selector */}
          <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-lg border border-slate-800 font-mono">
            <button 
              onClick={() => setGridLayout('2x2')}
              className={`px-2.5 py-1 rounded text-[11px] ${gridLayout === '2x2' ? 'bg-purple-600 text-white font-bold' : 'text-slate-400'}`}
            >
              2x2
            </button>
            <button 
              onClick={() => setGridLayout('3x3')}
              className={`px-2.5 py-1 rounded text-[11px] ${gridLayout === '3x3' ? 'bg-purple-600 text-white font-bold' : 'text-slate-400'}`}
            >
              3x3
            </button>
          </div>
        </div>
      </div>

      {/* Strict Restrictions Notice Banner */}
      <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl text-xs text-slate-400 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-purple-400" />
          <span>
            <strong>Authority Restrictions:</strong> ANPR plate lookups, suspect tracking, watchlists, maintenance tickets, and registry editing are hidden from your role.
          </span>
        </div>
        <span className="font-mono text-[10px] text-purple-400 bg-purple-950 px-2 py-0.5 rounded border border-purple-800">ROLE: OPERATOR</span>
      </div>

      {/* Video Wall Grid Display */}
      <div className={`grid gap-3 bg-slate-950 border border-slate-800 p-3 rounded-xl h-[620px] overflow-hidden ${gridLayout === '2x2' ? 'grid-cols-2 grid-rows-2' : 'grid-cols-3 grid-rows-3'}`}>
        {displayCameras.map((cam) => (
          <div key={cam.id} className="relative bg-black rounded-xl border border-slate-800 overflow-hidden flex flex-col justify-between group">
            {/* Video Stream */}
            {cam?.stream_url ? (
              <video 
                src={cam.stream_url} 
                autoPlay 
                loop 
                muted 
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-slate-900/80 text-slate-500 font-mono text-xs">
                NO FEED AVAILABLE
              </div>
            )}

            {/* Privacy Redaction Blur Overlays (Faces & Plates) */}
            {isPrivacyMaskEnabled && (
              <>
                {/* Face Privacy Blur */}
                <div className="absolute top-1/4 right-1/3 w-20 h-20 rounded-full backdrop-blur-xl bg-slate-900/40 border border-white/20 flex items-center justify-center pointer-events-none">
                  <span className="text-[8px] font-mono text-purple-300 font-bold bg-purple-950/80 px-1 rounded">PRIVACY</span>
                </div>
                {/* License Plate Privacy Blur */}
                <div className="absolute bottom-1/3 left-1/4 w-32 h-10 rounded backdrop-blur-xl bg-slate-900/50 border border-white/20 flex items-center justify-center pointer-events-none">
                  <span className="text-[8px] font-mono text-purple-300 font-bold bg-purple-950/80 px-1 rounded">PLATE BLURRED</span>
                </div>
              </>
            )}

            {/* Header Overlay */}
            <div className="absolute top-2 left-2 right-2 flex justify-between items-center text-[10px] text-white">
              <span className="bg-slate-950/80 backdrop-blur px-2 py-0.5 rounded font-mono font-bold text-purple-300 border border-slate-800">
                {cam.asset_code} — {cam.name}
              </span>
              <span className="bg-emerald-950/80 text-emerald-400 font-mono text-[9px] px-2 py-0.5 rounded border border-emerald-800">
                ONLINE
              </span>
            </div>

            {/* Footer Overlay */}
            <div className="absolute bottom-2 left-2 text-[9px] font-mono text-slate-400 bg-slate-950/80 px-2 py-0.5 rounded">
              {cam.dept_name} • {cam.resolution}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
