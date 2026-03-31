import { cn } from '@/lib/utils';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

interface ConfidenceIndicatorProps {
  confidence: number;
  showLabel?: boolean;
  className?: string;
}

export function ConfidenceIndicator({ confidence, showLabel = true, className }: ConfidenceIndicatorProps) {
  const getConfidenceLevel = () => {
    if (confidence >= 85) return 'high';
    if (confidence >= 70) return 'medium';
    return 'low';
  };

  const level = getConfidenceLevel();

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div className={cn("inline-flex items-center gap-1.5", className)}>
          <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full transition-all",
                level === 'high' && "bg-success",
                level === 'medium' && "bg-warning",
                level === 'low' && "bg-destructive"
              )}
              style={{ width: `${confidence}%` }}
            />
          </div>
          {showLabel && (
            <span className={cn(
              "text-xs font-medium",
              level === 'high' && "confidence-high",
              level === 'medium' && "confidence-medium",
              level === 'low' && "confidence-low"
            )}>
              {confidence}%
            </span>
          )}
        </div>
      </TooltipTrigger>
      <TooltipContent>
        <p className="text-xs">Confidence %: model's estimated probability the suggestion is correct.</p>
      </TooltipContent>
    </Tooltip>
  );
}
