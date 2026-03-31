import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface KpiCardProps {
  title: string;
  value: string | number;
  trend?: number;
  trendLabel?: string;
  status?: 'success' | 'warning' | 'error';
  className?: string;
}

export function KpiCard({ 
  title, 
  value, 
  trend, 
  trendLabel = 'vs last period',
  status,
  className 
}: KpiCardProps) {
  const getTrendIcon = () => {
    if (trend === undefined || trend === 0) {
      return <Minus className="w-3 h-3" />;
    }
    return trend > 0 
      ? <TrendingUp className="w-3 h-3" />
      : <TrendingDown className="w-3 h-3" />;
  };

  const getTrendColor = () => {
    if (trend === undefined || trend === 0) return 'text-muted-foreground';
    // For metrics where down is good (SLA breaches, MTTR, time to assignment)
    if (trendLabel?.includes('breaches') || trendLabel?.includes('time')) {
      return trend < 0 ? 'text-success' : 'text-destructive';
    }
    // For metrics where up is good (acceptance rate)
    return trend > 0 ? 'text-success' : 'text-destructive';
  };

  return (
    <div className={cn("kpi-card", className)}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-muted-foreground font-medium">{title}</p>
          <p className="text-2xl font-semibold mt-1">{value}</p>
        </div>
        {status && (
          <div className={cn(
            "status-dot mt-1",
            status === 'success' && "status-dot-success",
            status === 'warning' && "status-dot-warning",
            status === 'error' && "status-dot-error"
          )} />
        )}
      </div>
      {trend !== undefined && (
        <div className={cn("flex items-center gap-1 mt-2 text-xs", getTrendColor())}>
          {getTrendIcon()}
          <span>{Math.abs(trend)}%</span>
          <span className="text-muted-foreground">{trendLabel}</span>
        </div>
      )}
    </div>
  );
}
