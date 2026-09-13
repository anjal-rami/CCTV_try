import React from 'react';
import AnimatedPage from '../components/AnimatedPage';
import SplitText from '../components/reactbits/SplitText';
import SpotlightCard from '../components/reactbits/SpotlightCard';

export default function AlertsPage() {
  return (
    <AnimatedPage pageKey="alerts">
      <header className="mb-10">
        <div className="inline-block mb-3">
          <span className="text-xs uppercase font-mono tracking-widest text-rose-400 bg-rose-500/10 px-3 py-1 rounded-full border border-rose-500/20 inline-flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-rose-400 animate-pulse" />
            <SplitText text="Incident Response Active" by="character" delay={20} startDelay={0.1} />
          </span>
        </div>
        <h1 className="text-3xl md:text-5xl font-bold tracking-tight text-white mb-3">
          <SplitText text="Rule Engine Alerts" by="character" delay={30} startDelay={0.25} />
        </h1>
        <p className="text-sm md:text-base text-neutral-400 max-w-2xl">
          <SplitText text="Automated safety violations flagged via trajectory vectors and watchlist hit logs." by="word" delay={20} startDelay={0.65} />
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <SpotlightCard spotlightColor="rgba(244, 63, 94, 0.2)">
          <div className="flex justify-between items-center mb-3">
            <span className="font-mono text-xs text-rose-400 font-bold">
              <SplitText text="ALERT_01" by="character" startDelay={0.8} />
            </span>
            <span className="h-2 w-2 rounded-full bg-rose-500 animate-pulse" />
          </div>
          <h3 className="font-semibold text-lg text-white mb-1">
            <SplitText text="Wrong-Way Driving" by="word" startDelay={0.9} />
          </h3>
          <p className="text-sm text-neutral-400 mb-3">
            <SplitText text="Chiman bhai Bridge • Conf: 94%" by="word" startDelay={1.0} />
          </p>
          <div className="h-20 bg-neutral-950/80 rounded-lg border border-neutral-800/80 flex items-center justify-center text-xs font-mono text-rose-400">
            Vector Direction Inverted
          </div>
        </SpotlightCard>

        <SpotlightCard spotlightColor="rgba(251, 191, 36, 0.2)">
          <div className="flex justify-between items-center mb-3">
            <span className="font-mono text-xs text-amber-400 font-bold">
              <SplitText text="HOTLIST_HIT" by="character" startDelay={0.8} />
            </span>
            <span className="h-2 w-2 rounded-full bg-amber-400" />
          </div>
          <h3 className="font-semibold text-lg text-white mb-1">
            <SplitText text="Stolen Vehicle Flag" by="word" startDelay={0.9} />
          </h3>
          <p className="text-sm text-neutral-400 mb-3">
            <SplitText text="Plate: GJ01XX1234 • Paldi Circle" by="word" startDelay={1.0} />
          </p>
          <div className="h-20 bg-neutral-950/80 rounded-lg border border-neutral-800/80 flex items-center justify-center text-xs font-mono text-amber-400">
            Database Match Found
          </div>
        </SpotlightCard>

        <SpotlightCard spotlightColor="rgba(99, 102, 241, 0.2)">
          <div className="flex justify-between items-center mb-3">
            <span className="font-mono text-xs text-indigo-400 font-bold">
              <SplitText text="CONGESTION" by="character" startDelay={0.8} />
            </span>
            <span className="h-2 w-2 rounded-full bg-indigo-400" />
          </div>
          <h3 className="font-semibold text-lg text-white mb-1">
            <SplitText text="Density Spike Surge" by="word" startDelay={0.9} />
          </h3>
          <p className="text-sm text-neutral-400 mb-3">
            <SplitText text="Density: 82% • Janpath Cross" by="word" startDelay={1.0} />
          </p>
          <div className="h-20 bg-neutral-950/80 rounded-lg border border-neutral-800/80 flex items-center justify-center text-xs font-mono text-indigo-300">
            Threshold Exceeded (&gt;80%)
          </div>
        </SpotlightCard>
      </div>
    </AnimatedPage>
  );
}
