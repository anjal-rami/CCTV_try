import React from 'react';
import SplitText from './reactbits/SplitText';
import AnimatedCard from './AnimatedCard';

export const SurveillanceHero: React.FC = () => {
  return (
    <div className="mb-8 p-6 md:p-10 rounded-2xl bg-neutral-950/80 border border-neutral-800/80 shadow-2xl backdrop-blur-md">
      {/* Header Section: Cascading Line Animations */}
      <header className="mb-10">
        {/* Line 1: Badge */}
        <div className="inline-block mb-3">
          <span className="text-xs uppercase font-mono tracking-widest text-indigo-400 bg-indigo-500/10 px-3 py-1 rounded-full border border-indigo-500/20 inline-flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-pulse" />
            <SplitText 
              text="Surveillance Mesh Active" 
              by="character" 
              delay={20} 
              startDelay={0.1} 
            />
          </span>
        </div>

        {/* Line 2: Main Title */}
        <h1 className="text-3xl md:text-5xl font-bold tracking-tight text-white mb-3">
          <SplitText 
            text="Command Vision Portal" 
            by="character" 
            delay={35} 
            startDelay={0.3} 
          />
        </h1>

        {/* Line 3: Subtitle */}
        <p className="text-sm md:text-base text-neutral-400 max-w-2xl">
          <SplitText 
            text="Unified real-time CCTV stream inference, edge telemetry, and algorithmic incident detection across state nodes." 
            by="word" 
            delay={20} 
            startDelay={0.8} 
          />
        </p>
      </header>

      {/* Cards Section: Using Reusable AnimatedCard Components */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <AnimatedCard
          tag="CAM_GJ_01"
          tagColor="text-indigo-300"
          statusColor="bg-emerald-400"
          pulse={true}
          title="Chiman bhai Bridge"
          subtitle="Stream Active: 30 FPS • YOLOv8"
          footerText="Live Stream Pipeline"
          delayOffset={1.0}
        />

        <AnimatedCard
          tag="CAM_GJ_02"
          tagColor="text-indigo-300"
          statusColor="bg-emerald-400"
          pulse={false}
          title="Paldi Circle"
          subtitle="ANPR Inspection: Active"
          footerText="OCR Ingestion Active"
          delayOffset={1.0}
        />

        <AnimatedCard
          tag="ALERT_LOG"
          tagColor="text-rose-400 font-bold"
          statusColor="bg-rose-500"
          pulse={true}
          title="Rule Engine Hits"
          subtitle="1 Incident Pending Review"
          footerText="Wrong-Way Driving Flagged"
          footerColor="text-rose-400/80"
          spotlightColor="rgba(244, 63, 94, 0.2)"
          delayOffset={1.0}
        />
      </div>
    </div>
  );
};

export default SurveillanceHero;
