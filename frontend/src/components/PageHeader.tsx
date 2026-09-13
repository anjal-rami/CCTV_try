import React from 'react';
import SplitText from './reactbits/SplitText';

export interface PageHeaderProps {
  badge?: string;
  title: string;
  subtitle?: string;
  className?: string;
}

export default function PageHeader({ badge, title, subtitle, className = "" }: PageHeaderProps) {
  return (
    <header className={`mb-10 ${className}`}>
      {badge && (
        <div className="inline-block mb-3">
          <span className="text-xs uppercase font-mono tracking-widest text-indigo-400 bg-indigo-500/10 px-3 py-1 rounded-full border border-indigo-500/20 inline-flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-pulse" />
            <SplitText text={badge} by="character" delay={20} startDelay={0.1} />
          </span>
        </div>
      )}

      <h1 className="text-3xl md:text-5xl font-bold tracking-tight text-white mb-3">
        <SplitText text={title} by="character" delay={30} startDelay={0.25} />
      </h1>

      {subtitle && (
        <p className="text-sm md:text-base text-neutral-400 max-w-2xl">
          <SplitText text={subtitle} by="word" delay={20} startDelay={0.65} />
        </p>
      )}
    </header>
  );
}

export { PageHeader };
