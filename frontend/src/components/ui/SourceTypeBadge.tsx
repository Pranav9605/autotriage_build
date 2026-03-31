import { forwardRef } from 'react';
import { cn } from '@/lib/utils';
import { Cpu, BookOpen, Database, Sparkles } from 'lucide-react';

type SourceType = 'ml' | 'kb' | 'cache' | 'llm';

interface SourceTypeBadgeProps {
  source: SourceType;
  className?: string;
}

const sourceConfig: Record<SourceType, { label: string; icon: React.ElementType; className: string }> = {
  ml: {
    label: 'ML',
    icon: Cpu,
    className: 'bg-blue-500/15 text-blue-600 border-blue-500/30'
  },
  kb: {
    label: 'KB',
    icon: BookOpen,
    className: 'bg-green-500/15 text-green-600 border-green-500/30'
  },
  cache: {
    label: 'CACHE',
    icon: Database,
    className: 'bg-yellow-500/15 text-yellow-600 border-yellow-500/30'
  },
  llm: {
    label: 'LLM',
    icon: Sparkles,
    className: 'bg-purple-500/15 text-purple-600 border-purple-500/30'
  }
};

export const SourceTypeBadge = forwardRef<HTMLSpanElement, SourceTypeBadgeProps>(
  ({ source, className }, ref) => {
    const config = sourceConfig[source];
    const Icon = config.icon;

    return (
      <span
        ref={ref}
        className={cn(
          "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border",
          config.className,
          className
        )}
      >
        <Icon className="w-3 h-3" />
        {config.label}
      </span>
    );
  }
);

SourceTypeBadge.displayName = 'SourceTypeBadge';
