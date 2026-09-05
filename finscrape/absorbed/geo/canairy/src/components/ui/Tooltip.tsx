import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { cn } from '../../utils/cn';

interface TooltipProps {
  content: string;
  side?: 'top' | 'right' | 'bottom' | 'left';
  children: React.ReactElement;
  className?: string;
  wrapperClassName?: string;
}

export const Tooltip: React.FC<TooltipProps> = ({
  content,
  side = 'right',
  children,
  className,
  wrapperClassName,
}) => {
  const [visible, setVisible] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const triggerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (visible && triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      const tooltipRect = tooltipRef.current?.getBoundingClientRect();
      const tooltipWidth = tooltipRect?.width || 100;
      const tooltipHeight = tooltipRect?.height || 32;

      let top = 0;
      let left = 0;

      switch (side) {
        case 'right':
          top = rect.top + rect.height / 2 - tooltipHeight / 2;
          left = rect.right + 8;
          break;
        case 'left':
          top = rect.top + rect.height / 2 - tooltipHeight / 2;
          left = rect.left - tooltipWidth - 8;
          break;
        case 'top':
          top = rect.top - tooltipHeight - 8;
          left = rect.left + rect.width / 2 - tooltipWidth / 2;
          break;
        case 'bottom':
          top = rect.bottom + 8;
          left = rect.left + rect.width / 2 - tooltipWidth / 2;
          break;
      }

      setPosition({ top, left });
    }
  }, [visible, side]);

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={() => setVisible(true)}
        onMouseLeave={() => setVisible(false)}
        className={cn('inline-flex', wrapperClassName)}
      >
        {children}
      </div>
      {visible &&
        createPortal(
          <div
            ref={tooltipRef}
            className={cn(
              'fixed z-[100] px-2.5 py-1.5 rounded-md',
              'bg-olive-card border border-olive',
              'text-xs font-medium text-olive-primary',
              'shadow-lg shadow-black/20',
              'animate-in fade-in-0 zoom-in-95 duration-150',
              'pointer-events-none whitespace-nowrap',
              className
            )}
            style={{ top: position.top, left: position.left }}
          >
            {content}
          </div>,
          document.body
        )}
    </>
  );
};

export default Tooltip;
