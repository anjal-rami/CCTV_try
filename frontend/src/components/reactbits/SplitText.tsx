import React from 'react';
import { motion, Variants } from 'framer-motion';

export interface SplitTextProps {
  text?: string;
  className?: string;
  delay?: number;
  startDelay?: number;
  by?: "character" | "word";
}

export default function SplitText({
  text = "",
  className = "",
  delay = 25,
  startDelay = 0,
  by = "character",
}: SplitTextProps) {
  const items = by === "word" ? text.split(" ") : text.split("");

  const container: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: delay / 1000,
        delayChildren: startDelay,
      },
    },
  };

  const child: Variants = {
    visible: {
      opacity: 1,
      y: 0,
      filter: 'blur(0px)',
      transition: {
        type: 'spring',
        damping: 14,
        stiffness: 120,
      },
    },
    hidden: {
      opacity: 0,
      y: 16,
      filter: 'blur(8px)',
    },
  };

  return (
    <motion.span
      key={text}
      className={`inline-flex flex-wrap ${className}`}
      variants={container}
      initial="hidden"
      animate="visible"
    >
      {items.map((segment, index) => (
        <motion.span
          variants={child}
          key={index}
          className="inline-block"
        >
          {segment === " " ? "\u00A0" : segment}
          {by === "word" && index < items.length - 1 ? "\u00A0" : ""}
        </motion.span>
      ))}
    </motion.span>
  );
}

export { SplitText };
