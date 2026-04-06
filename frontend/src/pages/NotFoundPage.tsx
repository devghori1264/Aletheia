/**
 * 404 Not Found Page
 */

import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Home, Search, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export default function NotFoundPage() {
  return (
    <div className="flex h-[70vh] items-center justify-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md text-center"
      >
        {/* 404 Text */}
        <div className="relative">
          <h1 className="text-9xl font-bold text-neutral-800">404</h1>
          <div className="absolute inset-0 flex items-center justify-center">
            <Search className="h-20 w-20 text-neutral-600" />
          </div>
        </div>

        {/* Message */}
        <h2 className="mt-6 text-2xl font-bold text-white">Page Not Found</h2>
        <p className="mt-2 text-neutral-400">
          The page you're looking for doesn't exist or has been moved.
        </p>

        {/* Actions */}
        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
          <Link to="/">
            <Button leftIcon={<Home className="h-4 w-4" />}>Go Home</Button>
          </Link>
          <Button
            variant="secondary"
            leftIcon={<ArrowLeft className="h-4 w-4" />}
            onClick={() => window.history.back()}
          >
            Go Back
          </Button>
        </div>
      </motion.div>
    </div>
  );
}
