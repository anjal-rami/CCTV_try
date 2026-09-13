import React from 'react';
import SpotlightCard from './reactbits/SpotlightCard';
import SplitText from './reactbits/SplitText';

export interface AnimatedCardProps {
  tag: string;
  tagColor?: string;
  statusColor?: string;
  pulse?: boolean;
  title: string;
  subtitle: string;
  footerText?: string;
  footerColor?: string;
  spotlightColor?: string;
  delayOffset?: number;
}

export default function AnimatedCard({
  tag,
  tagColor = "text-indigo-300",
  statusColor = "bg-emerald-400",
  pulse = false,
  title,
  subtitle,
  footerText,
  footerColor = "text-neutral-500",
  spotlightColor,
  delayOffset = 0.8
}: AnimatedCardProps) {
  return (
    <SpotlightCard spotlightColor={spotlightColor}>
      <div className="flex justify-between items-center mb-3">
        <span className={`font-mono text-xs ${tagColor}`}>
          <SplitText text={tag} by="character" startDelay={delayOffset} />
        </span>
        <span className={`h-2 w-2 rounded-full ${statusColor} ${pulse ? 'animate-ping' : ''}`} />
      </div>

      <h3 className="font-semibold text-lg text-white mb-1">
        <SplitText text={title} by="word" startDelay={delayOffset + 0.1} />
      </h3>

      <p className="text-sm text-neutral-400 mb-3">
        <SplitText text={subtitle} by="word" startDelay={delayOffset + 0.2} />
      </p>

      {footerText && (
        <div className={`h-20 bg-neutral-950/80 rounded-lg border border-neutral-800/80 flex items-center justify-center text-xs font-mono ${footerColor}`}>
          {footerText}
        </div>
      )}
    </SpotlightCard>
  );
}

export { AnimatedCard };
