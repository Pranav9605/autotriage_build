import { cn } from '@/lib/utils';
import { PriorityBadge } from '@/components/ui/PriorityBadge';
import { SourceBadge } from '@/components/ui/SourceBadge';
import { ConfidenceIndicator } from '@/components/ui/ConfidenceIndicator';
import { Image, Video, FileText, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import type { Incident } from '@/data/mockData';

interface IncidentListProps {
  incidents: Incident[];
  selectedId: string | null;
  onSelect: (incident: Incident) => void;
  selectedIds: string[];
  onToggleSelect: (id: string) => void;
}

export function IncidentList({ 
  incidents, 
  selectedId, 
  onSelect,
  selectedIds,
  onToggleSelect
}: IncidentListProps) {
  const getMediaIcon = (type?: string) => {
    switch (type) {
      case 'image': return <Image className="w-3.5 h-3.5 text-muted-foreground" />;
      case 'video': return <Video className="w-3.5 h-3.5 text-muted-foreground" />;
      case 'document': return <FileText className="w-3.5 h-3.5 text-muted-foreground" />;
      default: return null;
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-background">
      {/* List Header */}
      <div className="sticky top-0 bg-background/95 backdrop-blur-sm border-b border-border px-4 py-3 flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <Checkbox 
            checked={selectedIds.length === incidents.length && incidents.length > 0}
            onCheckedChange={(checked) => {
              if (checked) {
                // Select all
              }
            }}
          />
          <span className="text-sm font-medium">{incidents.length} incidents</span>
          {selectedIds.length > 0 && (
            <span className="text-xs text-muted-foreground">
              ({selectedIds.length} selected)
            </span>
          )}
        </div>
        {selectedIds.length > 0 && (
          <Button size="sm" variant="default">
            Bulk Accept ({selectedIds.length})
          </Button>
        )}
      </div>

      {/* Incident Rows */}
      <div className="divide-y divide-border">
        {incidents.map((incident) => (
          <div
            key={incident.id}
            onClick={() => onSelect(incident)}
            className={cn(
              "px-4 py-3.5 cursor-pointer transition-all hover:bg-muted/50 group border-l-2 border-transparent",
              selectedId === incident.id && "bg-primary/5 border-l-primary"
            )}
          >
            <div className="flex items-start gap-3">
              <Checkbox
                checked={selectedIds.includes(incident.id)}
                onCheckedChange={() => onToggleSelect(incident.id)}
                onClick={(e) => e.stopPropagation()}
                className="mt-1"
              />
              
              <div className="flex-1 min-w-0">
                {/* Row 1: ID, Age, Source, Priority */}
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-mono text-muted-foreground">{incident.id}</span>
                  <span className="text-xs text-muted-foreground">•</span>
                  <span className="text-xs text-muted-foreground">{incident.age}</span>
                  <SourceBadge source={incident.source} />
                  <PriorityBadge priority={incident.priority} size="sm" />
                  {incident.hasMedia && getMediaIcon(incident.mediaType)}
                </div>

                {/* Row 2: Summary */}
                <p className="text-sm font-medium text-foreground truncate mb-1.5">
                  {incident.shortText}
                </p>

                {/* Row 3: AI Suggestion & Confidence */}
                <div className="flex items-center gap-3">
                  <span className="text-xs text-muted-foreground">
                    → {incident.suggestedTeam}
                  </span>
                  <ConfidenceIndicator confidence={incident.confidence} />
                  {incident.confidence < 75 && (
                    <span className="inline-flex items-center gap-1 text-xs text-warning">
                      <AlertTriangle className="w-3 h-3" />
                      Manual triage recommended
                    </span>
                  )}
                </div>
              </div>

              {/* Quick Actions */}
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <Button size="sm" variant="ghost" className="h-7 px-2 text-xs">
                  Claim
                </Button>
                <Button size="sm" variant="ghost" className="h-7 px-2 text-xs">
                  Accept
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {incidents.length === 0 && (
        <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
          <p className="text-sm">No high-risk incidents. All SLAs within target.</p>
        </div>
      )}
    </div>
  );
}
