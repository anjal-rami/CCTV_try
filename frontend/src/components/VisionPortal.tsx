import React, { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import Navbar from './Navbar';
import CamerasPage from '../pages/CamerasPage';
import AlertsPage from '../pages/AlertsPage';
import AnalyticsPage from '../pages/AnalyticsPage';

export default function VisionPortal() {
  const [activeTab, setActiveTab] = useState('cameras');

  const pageVariants = {
    initial: { opacity: 0, y: 12, filter: 'blur(4px)' },
    animate: { opacity: 1, y: 0, filter: 'blur(0px)' },
    exit: { opacity: 0, y: -12, filter: 'blur(4px)' },
  };

  return (
    <div className="py-6 max-w-7xl mx-auto px-4 md:px-8">
      {/* Animated Navigation Bar */}
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Animated Page Transitions */}
      <AnimatePresence mode="wait">
        <motion.main
          key={activeTab}
          variants={pageVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          transition={{ duration: 0.25, ease: 'easeInOut' }}
        >
          {activeTab === 'cameras' && <CamerasPage />}
          {activeTab === 'alerts' && <AlertsPage />}
          {activeTab === 'analytics' && <AnalyticsPage />}
        </motion.main>
      </AnimatePresence>
    </div>
  );
}

export { VisionPortal };
