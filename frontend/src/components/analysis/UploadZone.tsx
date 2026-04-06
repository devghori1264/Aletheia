/**
 * Upload Zone Component
 *
 * Drag-and-drop file upload with preview and validation.
 */

import { useState, useCallback } from 'react';
import { useDropzone, type FileRejection } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload,
  Film,
  Image,
  X,
  AlertCircle,
  CheckCircle2,
  FileVideo,
} from 'lucide-react';
import { cn, formatBytes, validateFile, isVideoFile, isImageFile } from '@/utils';
import { Button } from '@/components/ui/Button';

// =============================================================================
// Types
// =============================================================================

interface UploadZoneProps {
  onFilesSelected: (files: File[]) => void;
  accept?: string[] | Record<string, string[]>;
  maxSize?: number;
  maxFiles?: number;
  disabled?: boolean;
  className?: string;
}

interface PreviewFile {
  file: File;
  preview: string;
  isVideo: boolean;
}

// =============================================================================
// Constants
// =============================================================================

const DEFAULT_ACCEPT = ['video/mp4', 'video/webm', 'video/quicktime', 'image/jpeg', 'image/png'];
const DEFAULT_MAX_SIZE = 500 * 1024 * 1024; // 500MB
const DEFAULT_MAX_FILES = 10;

// =============================================================================
// Component
// =============================================================================

export function UploadZone({
  onFilesSelected,
  accept = DEFAULT_ACCEPT,
  maxSize = DEFAULT_MAX_SIZE,
  maxFiles = DEFAULT_MAX_FILES,
  disabled = false,
  className,
}: UploadZoneProps) {
  const [files, setFiles] = useState<PreviewFile[]>([]);
  const [errors, setErrors] = useState<string[]>([]);

  // Handle file drop
  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: FileRejection[]) => {
      // Process errors
      const newErrors: string[] = [];
      rejectedFiles.forEach((rejection) => {
        rejection.errors.forEach((error) => {
          if (error.code === 'file-too-large') {
            newErrors.push(`${rejection.file.name}: File too large (max ${formatBytes(maxSize)})`);
          } else if (error.code === 'file-invalid-type') {
            newErrors.push(`${rejection.file.name}: Invalid file type`);
          } else {
            newErrors.push(`${rejection.file.name}: ${error.message}`);
          }
        });
      });
      setErrors(newErrors);

      // Process accepted files
      const newFiles: PreviewFile[] = acceptedFiles.map((file) => ({
        file,
        preview: URL.createObjectURL(file),
        isVideo: isVideoFile(file),
      }));

      setFiles((prev) => {
        const combined = [...prev, ...newFiles].slice(0, maxFiles);
        return combined;
      });
    },
    [maxSize, maxFiles]
  );

  // Dropzone configuration
  const acceptConfig = Array.isArray(accept)
    ? accept.reduce((acc, type) => ({ ...acc, [type]: [] }), {})
    : accept || {};
  
  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: acceptConfig,
    maxSize,
    maxFiles,
    disabled,
    multiple: maxFiles > 1,
  });

  // Remove file
  const removeFile = useCallback((index: number) => {
    setFiles((prev) => {
      const newFiles = [...prev];
      URL.revokeObjectURL(newFiles[index]?.preview ?? '');
      newFiles.splice(index, 1);
      return newFiles;
    });
  }, []);

  // Clear all files
  const clearFiles = useCallback(() => {
    files.forEach((f) => URL.revokeObjectURL(f.preview));
    setFiles([]);
    setErrors([]);
  }, [files]);

  // Start analysis
  const handleAnalyze = useCallback(() => {
    onFilesSelected(files.map((f) => f.file));
  }, [files, onFilesSelected]);

  return (
    <div className={cn('space-y-4', className)}>
      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={cn(
          'relative overflow-hidden rounded-2xl border-2 border-dashed transition-all duration-300',
          'cursor-pointer outline-none',
          isDragActive && !isDragReject && 'border-primary-500 bg-primary-500/5',
          isDragReject && 'border-danger-500 bg-danger-500/5',
          !isDragActive && !disabled && 'border-neutral-700 hover:border-neutral-600 hover:bg-neutral-800/30',
          disabled && 'cursor-not-allowed opacity-50 border-neutral-800',
          files.length === 0 && 'min-h-[300px]'
        )}
      >
        <input {...getInputProps()} />

        {/* Empty state */}
        {files.length === 0 && (
          <div className="flex h-full min-h-[300px] flex-col items-center justify-center p-8 text-center">
            {/* Icon */}
            <motion.div
              animate={{
                y: isDragActive ? -5 : 0,
                scale: isDragActive ? 1.1 : 1,
              }}
              className={cn(
                'flex h-16 w-16 items-center justify-center rounded-2xl transition-colors',
                isDragActive
                  ? 'bg-primary-500/20 text-primary-400'
                  : 'bg-neutral-800 text-neutral-400'
              )}
            >
              <Upload className="h-8 w-8" />
            </motion.div>

            {/* Text */}
            <div className="mt-6">
              <p className="text-lg font-medium text-white">
                {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
              </p>
              <p className="mt-2 text-sm text-neutral-400">
                or click to browse from your computer
              </p>
            </div>

            {/* Supported formats */}
            <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
              <div className="flex items-center gap-1.5 rounded-full bg-neutral-800/50 px-3 py-1.5 text-xs text-neutral-400">
                <Film className="h-3.5 w-3.5" />
                MP4, WebM, MOV
              </div>
              <div className="flex items-center gap-1.5 rounded-full bg-neutral-800/50 px-3 py-1.5 text-xs text-neutral-400">
                <Image className="h-3.5 w-3.5" />
                JPG, PNG
              </div>
            </div>

            {/* Size limit */}
            <p className="mt-4 text-xs text-neutral-500">
              Max file size: {formatBytes(maxSize)}
            </p>
          </div>
        )}

        {/* File previews */}
        {files.length > 0 && (
          <div className="p-4">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <AnimatePresence mode="popLayout">
                {files.map((file, index) => (
                  <motion.div
                    key={file.preview}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    layout
                    className="group relative overflow-hidden rounded-xl bg-neutral-800"
                  >
                    {/* Preview */}
                    <div className="aspect-video">
                      {file.isVideo ? (
                        <video
                          src={file.preview}
                          className="h-full w-full object-cover"
                          muted
                          playsInline
                        />
                      ) : (
                        <img
                          src={file.preview}
                          alt={file.file.name}
                          className="h-full w-full object-cover"
                        />
                      )}
                    </div>

                    {/* Overlay */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />

                    {/* File info */}
                    <div className="absolute bottom-0 left-0 right-0 p-3">
                      <div className="flex items-center gap-2">
                        {file.isVideo ? (
                          <FileVideo className="h-4 w-4 text-primary-400" />
                        ) : (
                          <Image className="h-4 w-4 text-accent-400" />
                        )}
                        <span className="truncate text-sm font-medium text-white">
                          {file.file.name}
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-neutral-400">
                        {formatBytes(file.file.size)}
                      </p>
                    </div>

                    {/* Remove button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        removeFile(index);
                      }}
                      className="absolute right-2 top-2 flex h-8 w-8 items-center justify-center rounded-full bg-black/50 text-white opacity-0 transition-opacity hover:bg-black/70 group-hover:opacity-100"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </motion.div>
                ))}
              </AnimatePresence>

              {/* Add more button */}
              {files.length < maxFiles && (
                <div className="flex aspect-video items-center justify-center rounded-xl border-2 border-dashed border-neutral-700 text-neutral-500 transition-colors hover:border-neutral-600 hover:text-neutral-400">
                  <div className="text-center">
                    <Upload className="mx-auto h-6 w-6" />
                    <p className="mt-2 text-sm">Add more</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Errors */}
      <AnimatePresence>
        {errors.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="rounded-xl bg-danger-500/10 p-4"
          >
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 flex-shrink-0 text-danger-400" />
              <div className="flex-1">
                <p className="font-medium text-danger-400">Upload errors</p>
                <ul className="mt-2 space-y-1 text-sm text-danger-300">
                  {errors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </div>
              <button
                onClick={() => setErrors([])}
                className="text-danger-400 hover:text-danger-300"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Actions */}
      {files.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between"
        >
          <div className="flex items-center gap-2 text-sm text-neutral-400">
            <CheckCircle2 className="h-4 w-4 text-success-400" />
            {files.length} file{files.length > 1 ? 's' : ''} selected
          </div>

          <div className="flex gap-3">
            <Button variant="ghost" onClick={clearFiles}>
              Clear all
            </Button>
            <Button variant="primary" onClick={handleAnalyze}>
              Analyze {files.length > 1 ? 'files' : 'file'}
            </Button>
          </div>
        </motion.div>
      )}
    </div>
  );
}
