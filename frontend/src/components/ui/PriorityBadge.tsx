import { forwardRef } from 'react';
import { cn } from '@/lib/utils';
import type { Priority } from '@/data/mockData';

interface PriorityBadgeProps {
  priority: Priority;
  size?: 'sm' | 'md';
  className?: string;
}

export const PriorityBadge = forwardRef<HTMLSpanElement, PriorityBadgeProps>(
  ({ priority, size = 'md', className }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center font-medium rounded",
          size === 'sm' ? 'px-1.5 py-0.5 text-xs' : 'px-2 py-1 text-xs',
          priority === 'P1' && 'priority-p1',
          priority === 'P2' && 'priority-p2',
          priority === 'P3' && 'priority-p3',
          priority === 'P4' && 'priority-p4',
          className
        )}
      >
        {priority}
      </span>
    );
  }
);

PriorityBadge.displayName = 'PriorityBadge';
