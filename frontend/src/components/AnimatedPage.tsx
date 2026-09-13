import React from 'react';
import { motion } from 'framer-motion';

export interface AnimatedPageProps {
  children: React.ReactNode;
  pageKey?: string | number;
  className?: string;
}

export default function AnimatedPage({
  children,
  pageKey,
  className = ""
}: AnimatedPageProps) {
  return (
    <motion.div
      key={pageKey} // FORCES COMPLETE REMOUNT
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.2 }}
      className={`mb-8 p-6 md:p-10 rounded-2xl bg-neutral-950/80 border border-neutral-800/80 shadow-2xl backdrop-blur-md ${className}`.trim()}
    >
      {children}
    </motion.div>
  );
}

export { AnimatedPage };
