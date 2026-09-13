import React from 'react';
import AnimatedPage from '../components/AnimatedPage';
import SplitText from '../components/reactbits/SplitText';
import SpotlightCard from '../components/reactbits/SpotlightCard';

export default function AnalyticsPage() {
  return (
    <AnimatedPage pageKey="analytics">
      <header className="mb-10">
        <div className="inline-block mb-3">
          <span className="text-xs uppercase font-mono tracking-widest text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20 inline-flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <SplitText text="System Telemetry Engine" by="character" delay={20} startDelay={0.1} />
          </span>
        </div>
        <h1 className="text-3xl md:text-5xl font-bold tracking-tight text-white mb-3">
          <SplitText text="Platform Performance" by="character" delay={30} startDelay={0.25} />
        </h1>
        <p className="text-sm md:text-base text-neutral-400 max-w-2xl">
          <SplitText text="Benchmarking model latency, tracking frame drops, and verifying vector similarity scores." by="word" delay={20} startDelay={0.65} />
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <SpotlightCard>
          <div className="flex justify-between items-center mb-3">
            <span className="font-mono text-xs text-indigo-300">
              <SplitText text="METRIC_01" by="character" startDelay={0.8} />
            </span>
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
          </div>
          <h3 className="font-semibold text-lg text-white mb-1">
            <SplitText text="Inference Latency" by="word" startDelay={0.9} />
          </h3>
          <p className="text-sm text-neutral-400 mb-3">
            <SplitText text="Average: 18.2ms • GPU TensorRT" by="word" startDelay={1.0} />
          </p>
          <div className="h-20 bg-neutral-950/80 rounded-lg border border-neutral-800/80 flex items-center justify-center text-xs font-mono text-emerald-400">
            Optimal Performance
          </div>
        </SpotlightCard>

        <SpotlightCard>
          <div className="flex justify-between items-center mb-3">
            <span className="font-mono text-xs text-indigo-300">
              <SplitText text="METRIC_02" by="character" startDelay={0.8} />
            </span>
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
          </div>
          <h3 className="font-semibold text-lg text-white mb-1">
            <SplitText text="Throughput Rate" by="word" startDelay={0.9} />
          </h3>
          <p className="text-sm text-neutral-400 mb-3">
            <SplitText text="1,420 Vehicles Processed / hr" by="word" startDelay={1.0} />
          </p>
          <div className="h-20 bg-neutral-950/80 rounded-lg border border-neutral-800/80 flex items-center justify-center text-xs font-mono text-neutral-400">
            Network Peak Handled
          </div>
        </SpotlightCard>

        <SpotlightCard>
          <div className="flex justify-between items-center mb-3">
            <span className="font-mono text-xs text-indigo-300">
              <SplitText text="METRIC_03" by="character" startDelay={0.8} />
            </span>
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
          </div>
          <h3 className="font-semibold text-lg text-white mb-1">
            <SplitText text="ReID Similarity" by="word" startDelay={0.9} />
          </h3>
          <p className="text-sm text-neutral-400 mb-3">
            <SplitText text="OSNet Model: 0.89 Match Score" by="word" startDelay={1.0} />
          </p>
          <div className="h-20 bg-neutral-950/80 rounded-lg border border-neutral-800/80 flex items-center justify-center text-xs font-mono text-indigo-300">
            pgvector Search Ready
          </div>
        </SpotlightCard>
      </div>
    </AnimatedPage>
  );
}
