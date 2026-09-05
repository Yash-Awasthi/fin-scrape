import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { cn } from '../../utils/cn';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  className?: string;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  size = 'md',
  className,
}) => {
  // Handle escape key and body scroll
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-7xl',
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-40"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none"
          >
            <div
              className={cn(
                'bg-[#141416]/95 backdrop-blur-xl border border-white/[0.06] rounded-2xl shadow-2xl',
                'w-full pointer-events-auto max-h-[90vh] overflow-hidden flex flex-col',
                sizeClasses[size],
                className
              )}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              {(title || description) && (
                <div className="flex items-start justify-between p-6 border-b border-white/[0.04]">
                  <div>
                    {title && (
                      <h2 className="text-xl font-semibold text-white">
                        {title}
                      </h2>
                    )}
                    {description && (
                      <p className="mt-1 text-sm text-white/30">
                        {description}
                      </p>
                    )}
                  </div>
                  <button
                    onClick={onClose}
                    className="p-2 text-white/30 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
                    aria-label="Close modal"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              )}

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-6">
                {children}
              </div>
              
              {/* Close button when no title */}
              {!title && !description && (
                <button
                  onClick={onClose}
                  className="absolute top-4 right-4 z-10 p-2 text-white/30 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
                  aria-label="Close modal"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

interface ModalFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  separator?: boolean;
}

export const ModalFooter: React.FC<ModalFooterProps> = ({
  children,
  separator = true,
  className,
  ...props
}) => (
  <div
    className={cn(
      'flex items-center justify-end gap-3 px-6 py-4',
      separator && 'border-t border-bmb-border mt-6 -mx-6',
      className
    )}
    {...props}
  >
    {children}
  </div>
);