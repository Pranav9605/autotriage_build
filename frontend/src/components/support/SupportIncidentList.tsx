import { cn } from '@/lib/utils';
import { PriorityBadge } from '@/components/ui/PriorityBadge';
import { SourceBadge } from '@/components/ui/SourceBadge';
import { ConfidenceIndicator } from '@/components/ui/ConfidenceIndicator';
import { Image, Video, FileText, Mic, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Incident, useIncidents } from '@/context/IncidentContext';
import { useToast } from '@/hooks/use-toast';

interface SupportIncidentListProps {
  incidents: Incident[];
  selectedIds: string[];
  onToggleSelect: (id: string) => void;
  onSelectAll: () => void;
}

export function SupportIncidentList({ 
  incidents, 
  selectedIds,
  onToggleSelect,
  onSelectAll
}: SupportIncidentListProps) {
  const { selectIncident, updateIncident, state } = useIncidents();
  const { toast } = useToast();

  const getMediaIcon = (type?: string) => {
    switch (type) {
      case 'image': return <Image className="w-3.5 h-3.5 text-muted-foreground" />;
      case 'video': return <Video className="w-3.5 h-3.5 text-muted-foreground" />;
      case 'document': return <FileText className="w-3.5 h-3.5 text-muted-foreground" />;
      case 'audio': return <Mic className="w-3.5 h-3.5 text-muted-foreground" />;
      default: return null;
    }
  };

  const getSapModuleStyle = (module?: string) => {
    switch (module) {
      case 'FI':    return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300';
      case 'MM':    return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300';
      case 'SD':    return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300';
      case 'BASIS': return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300';
      case 'ABAP':  return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300';
      case 'PI_PO': return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300';
      case 'PP':    return 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300';
      default:      return 'bg-muted text-muted-foreground';
    }
  };

  const getEnvStyle = (env?: string) => {
    switch (env) {
      case 'PRD': return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300';
      case 'QAS': return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300';
      default:    return 'bg-muted text-muted-foreground';
    }
  };

  const handleClaim = (e: React.MouseEvent, incident: Incident) => {
    e.stopPropagation();
    updateIncident(incident.id, { 
      assignee: 'Current User',
      status: 'In Progress'
    });
    toast({
      title: "Incident claimed",
      description: `${incident.id} is now assigned to you`
    });
  };

  const handleAccept = (e: React.MouseEvent, incident: Incident) => {
    e.stopPropagation();
    updateIncident(incident.id, { 
      assignedTeam: incident.suggestedTeam,
      status: 'In Progress'
    });
    toast({
      title: "AI suggestion accepted",
      description: `Assigned to ${incident.suggestedTeam}`
    });
  };

  return (
    <div className="flex-1 overflow-y-auto bg-background border-r border-border">
      {/* List Header */}
      <div className="sticky top-0 bg-background/95 backdrop-blur-sm border-b border-border px-4 py-3 flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <Checkbox 
            checked={selectedIds.length === incidents.length && incidents.length > 0}
            onCheckedChange={onSelectAll}
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
            onClick={() => selectIncident(incident.id)}
            className={cn(
              "px-4 py-3.5 cursor-pointer transition-all hover:bg-muted/50 group border-l-2 border-transparent",
              state.selectedIncidentId === incident.id && "bg-primary/5 border-l-primary"
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
                {/* Row 1: ID, Age, Source, Priority, SAP Module, T-Code, Environment, Status */}
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <span className="text-xs font-mono text-muted-foreground">{incident.id}</span>
                  <span className="text-xs text-muted-foreground">•</span>
                  <span className="text-xs text-muted-foreground">{incident.age}</span>
                  <SourceBadge source={incident.source as any} />
                  <PriorityBadge priority={incident.priority} size="sm" />
                  {incident.sapModule && (
                    <span className={`text-xs font-medium px-1.5 py-0.5 rounded font-mono ${getSapModuleStyle(incident.sapModule)}`}>
                      {incident.sapModule}
                    </span>
                  )}
                  {incident.tcode && (
                    <span className="text-xs font-mono bg-muted text-muted-foreground px-1.5 py-0.5 rounded">
                      {incident.tcode}
                    </span>
                  )}
                  {incident.environment && (
                    <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${getEnvStyle(incident.environment)}`}>
                      {incident.environment}
                    </span>
                  )}
                  {incident.hasMedia && getMediaIcon(incident.mediaType)}
                  {incident.assignedTeam && (
                    <span className="text-xs bg-primary/10 text-primary px-1.5 py-0.5 rounded">
                      {incident.assignedTeam}
                    </span>
                  )}
                </div>

                {/* Row 2: Title + Issue Type */}
                <div className="flex items-center gap-2 mb-1.5">
                  <p className="text-sm font-medium text-foreground truncate">
                    {incident.shortText}
                  </p>
                  <span className="text-xs text-muted-foreground shrink-0">
                    [{incident.issueType}]
                  </span>
                </div>

                {/* Row 3: AI Suggestion & Confidence */}
                <div className="flex items-center gap-3">
                  <span className="text-xs text-muted-foreground">
                    Suggested: {incident.suggestedTeam}
                  </span>
                  <ConfidenceIndicator confidence={incident.confidence} />
                  {(incident.manual_review_required ?? incident.confidence < 70) && (
                    <span className="inline-flex items-center gap-1 text-xs text-warning">
                      <AlertTriangle className="w-3 h-3" />
                      Manual review
                    </span>
                  )}
                </div>
              </div>

              {/* Quick Actions */}
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                <Button 
                  size="sm" 
                  variant="ghost" 
                  className="h-7 px-2 text-xs"
                  onClick={(e) => handleClaim(e, incident)}
                >
                  Claim
                </Button>
                <Button 
                  size="sm" 
                  variant="ghost" 
                  className="h-7 px-2 text-xs"
                  onClick={(e) => handleAccept(e, incident)}
                >
                  Accept
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {incidents.length === 0 && (
        <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
          <p className="text-sm">No incidents match your filters.</p>
        </div>
      )}
    </div>
  );
}
