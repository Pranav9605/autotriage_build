import { useState, useEffect, useCallback } from 'react';
import { Incident, useIncidents } from '@/context/IncidentContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { SourceTypeBadge } from '@/components/ui/SourceTypeBadge';
import { ConfidenceIndicator } from '@/components/ui/ConfidenceIndicator';
import { 
  Check, 
  Pencil, 
  X, 
  UserPlus, 
  ExternalLink,
  Sparkles,
  Maximize2,
  Minimize2,
  Save,
  FileText
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';

interface IncidentAnalysisPanelProps {
  incident: Incident | null;
  onClose?: () => void;
}

const ISSUE_TYPES = [
  'FI - Finance',
  'MM - Materials',
  'SD - Sales',
  'BASIS - System',
  'ABAP - Development',
  'PI_PO - Integration',
  'PP - Production',
  'Integration',
  'Performance'
];

const TEAMS = [
  'SAP Finance Team',
  'SAP MM Team',
  'SAP SD Team',
  'BASIS Team',
  'ABAP Dev Team',
  'Integration Team',
  'L1 Support',
  'L2 Infrastructure'
];

const SEVERITIES = ['P1', 'P2', 'P3', 'P4'] as const;

export function IncidentAnalysisPanel({ incident, onClose }: IncidentAnalysisPanelProps) {
  const { updateIncident, setFullScreen, state } = useIncidents();
  const { toast } = useToast();
  const [isEditing, setIsEditing] = useState(false);
  const [editedFields, setEditedFields] = useState<Partial<Incident>>({});

  // Reset edit state when incident changes
  useEffect(() => {
    setIsEditing(false);
    setEditedFields({});
  }, [incident?.id]);

  const handleStartEdit = useCallback(() => {
    if (incident) {
      setEditedFields({
        issueType: incident.issueType,
        severity: incident.severity,
        rootCause: incident.rootCause,
        suggestedTeam: incident.suggestedTeam,
        aiSummary: incident.aiSummary,
        aiSolution: incident.aiSolution
      });
      setIsEditing(true);
    }
  }, [incident]);

  const handleCancelEdit = useCallback(() => {
    setIsEditing(false);
    setEditedFields({});
  }, []);

  const handleSaveEdit = useCallback(() => {
    if (incident) {
      updateIncident(incident.id, editedFields);
      setIsEditing(false);
      setEditedFields({});
      toast({
        title: "Changes saved",
        description: "AI analysis has been updated."
      });
    }
  }, [incident, editedFields, updateIncident, toast]);

  const handleAccept = useCallback(() => {
    if (incident) {
      const team = editedFields.suggestedTeam || incident.suggestedTeam;
      updateIncident(incident.id, { 
        status: 'In Progress',
        assignedTeam: team
      });
      toast({
        title: "Decision accepted",
        description: `Ticket assigned to ${team}.`
      });
    }
  }, [incident, editedFields, updateIncident, toast]);

  const handleAssign = useCallback((team: string, assignee?: string) => {
    if (incident) {
      updateIncident(incident.id, { 
        assignedTeam: team,
        assignee: assignee || null,
        status: 'In Progress'
      });
      toast({
        title: "Incident assigned",
        description: `Assigned to ${team}${assignee ? ` (${assignee})` : ''}`
      });
    }
  }, [incident, updateIncident, toast]);

  const handleResolve = useCallback(() => {
    if (incident) {
      updateIncident(incident.id, { status: 'Resolved' });
      toast({
        title: "Incident resolved",
        description: `${incident.id} marked as resolved.`
      });
    }
  }, [incident, updateIncident, toast]);

  const handlePushToJira = useCallback(() => {
    const jiraKey = `SAP-${Math.floor(100 + Math.random() * 900)}`;
    toast({
      title: "Pushed to Jira",
      description: `Issue key: ${jiraKey} created.`
    });
  }, [toast]);

  const handlePushToSAP = useCallback(() => {
    toast({
      title: "Pushed to SAP SolMan",
      description: "Incident logged in SAP Solution Manager."
    });
  }, [toast]);

  if (!incident) {
    return (
      <div className="h-full flex flex-col">
        <div className="h-14 border-b border-border px-4 flex items-center bg-card">
          <h3 className="font-semibold text-foreground">Analysis Panel</h3>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center p-6">
            <div className="w-14 h-14 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
              <Sparkles className="w-6 h-6 text-muted-foreground" />
            </div>
            <p className="text-muted-foreground text-sm">
              Submit a message to create an incident and view AI analysis
            </p>
          </div>
        </div>
      </div>
    );
  }

  const displayValues = isEditing ? {
    issueType: editedFields.issueType ?? incident.issueType,
    severity: editedFields.severity ?? incident.severity,
    rootCause: editedFields.rootCause ?? incident.rootCause,
    suggestedTeam: editedFields.suggestedTeam ?? incident.suggestedTeam,
    aiSummary: editedFields.aiSummary ?? incident.aiSummary,
    aiSolution: editedFields.aiSolution ?? incident.aiSolution
  } : incident;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="h-14 border-b border-border px-4 flex items-center justify-between bg-card shrink-0">
        <div className="flex items-center gap-3">
          <h3 className="font-semibold text-foreground">AI Analysis</h3>
          <span className="font-mono text-xs text-muted-foreground">{incident.id}</span>
          {incident.aiSource && <SourceTypeBadge source={incident.aiSource} />}
        </div>
        <div className="flex items-center gap-2">
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-8 w-8"
            onClick={() => setFullScreen(!state.isFullScreen)}
          >
            {state.isFullScreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </Button>
          {onClose && (
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 space-y-5">
          {/* Confidence */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-foreground">AI Confidence</span>
            <ConfidenceIndicator confidence={incident.confidence} />
          </div>

          {/* Edit/Save Controls */}
          <div className="flex items-center gap-2">
            {isEditing ? (
              <>
                <Button size="sm" onClick={handleSaveEdit} className="gap-1.5">
                  <Save className="w-4 h-4" />
                  Save Changes
                </Button>
                <Button size="sm" variant="outline" onClick={handleCancelEdit}>
                  Cancel
                </Button>
              </>
            ) : (
              <Button size="sm" variant="outline" onClick={handleStartEdit} className="gap-1.5">
                <Pencil className="w-4 h-4" />
                Edit Analysis
              </Button>
            )}
          </div>

          {/* Issue Type */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Issue Type
            </label>
            {isEditing ? (
              <Select
                value={displayValues.issueType}
                onValueChange={(value) => setEditedFields(prev => ({ ...prev, issueType: value }))}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ISSUE_TYPES.map(type => (
                    <SelectItem key={type} value={type}>{type}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <p className="text-sm font-medium text-foreground">{displayValues.issueType}</p>
            )}
          </div>

          {/* Severity */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Severity
            </label>
            {isEditing ? (
              <Select
                value={displayValues.severity}
                onValueChange={(value) => setEditedFields(prev => ({ ...prev, severity: value as typeof SEVERITIES[number] }))}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SEVERITIES.map(sev => (
                    <SelectItem key={sev} value={sev}>{sev}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <p className="text-sm font-medium text-foreground">{displayValues.severity}</p>
            )}
          </div>

          {/* Root Cause */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Root Cause
            </label>
            {isEditing ? (
              <Input
                value={displayValues.rootCause}
                onChange={(e) => setEditedFields(prev => ({ ...prev, rootCause: e.target.value }))}
              />
            ) : (
              <p className="text-sm text-foreground">{displayValues.rootCause}</p>
            )}
          </div>

          {/* Assign To */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Assign To
            </label>
            {isEditing ? (
              <Select
                value={displayValues.suggestedTeam}
                onValueChange={(value) => setEditedFields(prev => ({ ...prev, suggestedTeam: value }))}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TEAMS.map(team => (
                    <SelectItem key={team} value={team}>{team}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-foreground">{displayValues.suggestedTeam}</p>
                {incident.assignedTeam && (
                  <span className="text-xs text-primary">Assigned</span>
                )}
              </div>
            )}
          </div>

          {/* AI Summary */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Summary
            </label>
            {isEditing ? (
              <Textarea
                value={displayValues.aiSummary}
                onChange={(e) => setEditedFields(prev => ({ ...prev, aiSummary: e.target.value }))}
                className="min-h-[80px]"
              />
            ) : (
              <p className="text-sm text-foreground leading-relaxed">{displayValues.aiSummary}</p>
            )}
          </div>

          {/* AI Solution */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Recommended Solution
            </label>
            {isEditing ? (
              <Textarea
                value={displayValues.aiSolution}
                onChange={(e) => setEditedFields(prev => ({ ...prev, aiSolution: e.target.value }))}
                className="min-h-[100px]"
              />
            ) : (
              <p className="text-sm text-foreground leading-relaxed">{displayValues.aiSolution}</p>
            )}
          </div>

          {/* Key Points */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Key Points
            </label>
            <ul className="space-y-1.5">
              {incident.aiBullets.map((bullet, idx) => (
                <li key={idx} className="text-sm text-foreground flex items-start gap-2">
                  <span className="text-primary mt-1">•</span>
                  {bullet}
                </li>
              ))}
            </ul>
          </div>

          {/* SAP Context */}
          {(incident.tcode || incident.environment || incident.errorCode) && (
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                SAP Context
              </label>
              <div className="grid grid-cols-2 gap-2">
                {incident.sapModule && (
                  <div className="bg-muted/50 rounded p-2">
                    <p className="text-xs text-muted-foreground">Module</p>
                    <p className="text-sm font-mono font-medium">{incident.sapModule}</p>
                  </div>
                )}
                {incident.tcode && (
                  <div className="bg-muted/50 rounded p-2">
                    <p className="text-xs text-muted-foreground">T-Code</p>
                    <p className="text-sm font-mono font-medium">{incident.tcode}</p>
                  </div>
                )}
                {incident.errorCode && (
                  <div className="bg-muted/50 rounded p-2">
                    <p className="text-xs text-muted-foreground">Error Code</p>
                    <p className="text-sm font-mono font-medium">{incident.errorCode}</p>
                  </div>
                )}
                {incident.environment && (
                  <div className="bg-muted/50 rounded p-2">
                    <p className="text-xs text-muted-foreground">Environment</p>
                    <p className={`text-sm font-medium ${
                      incident.environment === 'PRD' ? 'text-red-600' :
                      incident.environment === 'QAS' ? 'text-amber-600' : 'text-muted-foreground'
                    }`}>{incident.environment}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Similar Tickets */}
          {incident.similarTickets && incident.similarTickets.length > 0 && (
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Similar Tickets
              </label>
              <div className="flex flex-wrap gap-2">
                {incident.similarTickets.map((t) => (
                  <span
                    key={t.id}
                    className="inline-flex items-center gap-1 text-xs bg-primary/10 text-primary px-2 py-1 rounded-full font-mono"
                  >
                    {t.id} · {t.match}% match
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Notes */}
          {incident.notes.length > 0 && (
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Notes
              </label>
              <ul className="space-y-1.5">
                {incident.notes.map((note, idx) => (
                  <li key={idx} className="text-sm text-muted-foreground flex items-start gap-2">
                    <FileText className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                    {note}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Actions Footer */}
      <div className="border-t border-border p-4 space-y-3 bg-card shrink-0">
        {/* Primary Actions */}
        <div className="flex flex-wrap gap-2">
          <Button size="sm" className="gap-1.5" onClick={handleAccept}>
            <Check className="w-4 h-4" />
            Accept
          </Button>
          <Button size="sm" variant="outline" className="gap-1.5" onClick={() => handleAssign(displayValues.suggestedTeam)}>
            <UserPlus className="w-4 h-4" />
            Assign
          </Button>
          <Button size="sm" variant="outline" onClick={handleResolve}>
            Resolve
          </Button>
        </div>

        {/* External Integrations */}
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="secondary" className="gap-1.5" onClick={handlePushToJira}>
            <ExternalLink className="w-4 h-4" />
            Push to Jira
          </Button>
          <Button size="sm" variant="secondary" className="gap-1.5" onClick={handlePushToSAP}>
            <ExternalLink className="w-4 h-4" />
            Push to SAP
          </Button>
        </div>
      </div>
    </div>
  );
}
