/**
 * Loading Screen Component
 *
 * Full-page loading indicator for suspense boundaries.
 */

import { motion } from 'framer-motion';
import { Shield } from 'lucide-react';

export function LoadingScreen() {
  return (
    <div className="flex h-[calc(100vh-4rem)] items-center justify-center lg:h-screen">
      <div className="flex flex-col items-center gap-6">
        {/* Animated Logo */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="relative"
        >
          {/* Glow ring */}
          <motion.div
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.5, 0.2, 0.5],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
            className="absolute inset-0 rounded-2xl bg-gradient-to-br from-primary-500 to-accent-500 blur-xl"
          />

          {/* Icon container */}
          <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary-500 to-accent-500">
            <Shield className="h-8 w-8 text-white" />
          </div>
        </motion.div>

        {/* Loading text */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-center"
        >
          <h2 className="font-display text-lg font-semibold text-white">Loading</h2>
          <p className="mt-1 text-sm text-neutral-500">Initializing Aletheia...</p>
        </motion.div>

        {/* Progress dots */}
        <div className="flex gap-1.5">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              animate={{
                scale: [1, 1.2, 1],
                opacity: [0.3, 1, 0.3],
              }}
              transition={{
                duration: 1,
                repeat: Infinity,
                delay: i * 0.2,
              }}
              className="h-2 w-2 rounded-full bg-primary-500"
            />
          ))}
        </div>
      </div>
    </div>
  );
}
