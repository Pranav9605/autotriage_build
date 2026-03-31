import { cn } from '@/lib/utils';
import { RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface IntegrationStatusProps {
  name: string;
  status: 'healthy' | 'warning' | 'error';
  lastSync: string;
  onReconnect?: () => void;
}

export function IntegrationStatus({ name, status, lastSync, onReconnect }: IntegrationStatusProps) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-border last:border-0">
      <div className="flex items-center gap-3">
        <div className={cn(
          "status-dot",
          status === 'healthy' && "status-dot-success",
          status === 'warning' && "status-dot-warning",
          status === 'error' && "status-dot-error"
        )} />
        <div>
          <p className="text-sm font-medium">{name}</p>
          <p className="text-xs text-muted-foreground">Last sync: {lastSync}</p>
        </div>
      </div>
      {status !== 'healthy' && (
        <Button variant="ghost" size="sm" onClick={onReconnect}>
          <RefreshCw className="w-4 h-4 mr-1" />
          Reconnect
        </Button>
      )}
    </div>
  );
}
