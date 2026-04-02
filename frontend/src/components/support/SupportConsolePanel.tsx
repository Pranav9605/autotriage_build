import { useState, useEffect, useCallback } from 'react';
import { Incident, useIncidents } from '@/context/IncidentContext';
import { api } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { SourceTypeBadge } from '@/components/ui/SourceTypeBadge';
import { SourceBadge } from '@/components/ui/SourceBadge';
import { PriorityBadge } from '@/components/ui/PriorityBadge';
import { ConfidenceIndicator } from '@/components/ui/ConfidenceIndicator';
import {
  Check,
  Pencil,
  UserPlus,
  ExternalLink,
  Sparkles,
  Maximize2,
  Minimize2,
  Save,
  Clock,
  User,
  FileText,
  Plus
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';

const ISSUE_TYPES = [
  'FI - Finance',
  'MM - Materials',
  'SD - Sales',
  'BASIS - System',
  'ABAP - Development',
  'PI_PO - Integration',
  'PP - Production',
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

export function SupportConsolePanel() {
  const { state, updateIncident, addNote, setFullScreen } = useIncidents();
  const { toast } = useToast();
  const [isEditing, setIsEditing] = useState(false);
  const [editedFields, setEditedFields] = useState<Partial<Incident>>({});
  const [newNote, setNewNote] = useState('');

  const incident = state.incidents.find(inc => inc.id === state.selectedIncidentId) || null;
  const isFullScreen = state.isFullScreen;

  // Reset edit state when incident changes
  useEffect(() => {
    setIsEditing(false);
    setEditedFields({});
    setNewNote('');
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

  const handleAddNote = useCallback(() => {
    if (incident && newNote.trim()) {
      addNote(incident.id, newNote.trim());
      setNewNote('');
      toast({
        title: "Note added",
        description: "Your note has been saved."
      });
    }
  }, [incident, newNote, addNote, toast]);

  const handleAccept = useCallback(async () => {
    if (incident) {
      const team = editedFields.suggestedTeam || incident.suggestedTeam;
      updateIncident(incident.id, {
        status: 'In Progress',
        assignedTeam: team
      });
      if (incident.decisionId) {
        try {
          await api.submitFeedback(incident.decisionId, {
            action: 'accepted',
            consultant_id: 'consultant',
          });
        } catch (err) {
          console.warn('Feedback POST failed', err);
        }
      }
      toast({
        title: "Decision accepted",
        description: `Ticket assigned to ${team}.`
      });
    }
  }, [incident, editedFields, updateIncident, toast]);

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
      <div className="flex-1 bg-card flex items-center justify-center">
        <div className="text-center p-6">
          <div className="w-14 h-14 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
            <Sparkles className="w-6 h-6 text-muted-foreground" />
          </div>
          <p className="text-muted-foreground text-sm">Select an incident to view details</p>
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
    <div className={cn(
      "flex-1 bg-card flex flex-col",
      isFullScreen && "fixed inset-0 z-50"
    )}>
      {/* Header */}
      <div className="border-b border-border px-5 py-4 shrink-0">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-sm font-semibold text-foreground">{incident.id}</span>
            <SourceBadge source={incident.source as any} />
            <PriorityBadge priority={incident.priority} />
            {incident.aiSource && <SourceTypeBadge source={incident.aiSource} />}
          </div>
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-8 w-8"
            onClick={() => setFullScreen(!isFullScreen)}
          >
            {isFullScreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </Button>
        </div>
        
        <h2 className="text-base font-semibold text-foreground leading-snug mb-3">
          {incident.shortText}
        </h2>

        {/* Status Bar */}
        <div className="flex items-center gap-4 text-xs text-muted-foreground mb-4">
          <div className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" />
            <span>Created {incident.age} ago</span>
          </div>
          <div className="flex items-center gap-1.5">
            <User className="w-3.5 h-3.5" />
            <span>{incident.assignee || 'Unassigned'}</span>
          </div>
          <span className={cn(
            "px-2 py-0.5 rounded text-xs font-medium",
            incident.status === 'New' && "bg-primary/10 text-primary",
            incident.status === 'In Progress' && "bg-warning/10 text-warning",
            incident.status === 'Pending' && "bg-muted text-muted-foreground",
            incident.status === 'Resolved' && "bg-accent text-accent-foreground"
          )}>
            {incident.status}
          </span>
        </div>

        {/* Quick Actions */}
        <div className="flex flex-wrap items-center gap-2">
          <Button size="sm" className="gap-1.5" onClick={handleAccept}>
            <Check className="w-4 h-4" />
            Accept
          </Button>
          <Button size="sm" variant="outline" className="gap-1.5">
            <UserPlus className="w-4 h-4" />
            Assign
          </Button>
          <Button size="sm" variant="outline" onClick={handleResolve}>
            Resolve
          </Button>
          <Button size="sm" variant="secondary" className="gap-1.5" onClick={handlePushToJira}>
            <ExternalLink className="w-4 h-4" />
            Jira
          </Button>
          <Button size="sm" variant="secondary" className="gap-1.5" onClick={handlePushToSAP}>
            <ExternalLink className="w-4 h-4" />
            SAP
          </Button>
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-5 space-y-5">
          {/* Description */}
          <section>
            <h3 className="text-sm font-semibold mb-2 text-foreground">Description</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">{incident.longText}</p>
            {incident.errorCode && (
              <div className="mt-3 inline-flex items-center gap-1.5 px-2.5 py-1 bg-destructive/10 text-destructive rounded text-xs font-mono">
                Error: {incident.errorCode}
              </div>
            )}
          </section>

          {/* SAP Context */}
          {(incident.sapModule || incident.tcode || incident.errorCode || incident.environment) && (
            <section>
              <h3 className="text-sm font-semibold mb-2 text-foreground">SAP Context</h3>
              <div className="grid grid-cols-2 gap-2">
                {incident.sapModule && (
                  <div className="bg-muted/50 rounded-lg p-2.5">
                    <p className="text-xs text-muted-foreground mb-0.5">Module</p>
                    <p className="text-sm font-mono font-medium">{incident.sapModule}</p>
                  </div>
                )}
                {incident.tcode && (
                  <div className="bg-muted/50 rounded-lg p-2.5">
                    <p className="text-xs text-muted-foreground mb-0.5">T-Code</p>
                    <p className="text-sm font-mono font-medium">{incident.tcode}</p>
                  </div>
                )}
                {incident.errorCode && (
                  <div className="bg-muted/50 rounded-lg p-2.5">
                    <p className="text-xs text-muted-foreground mb-0.5">Error Code</p>
                    <p className="text-sm font-mono font-medium text-destructive">{incident.errorCode}</p>
                  </div>
                )}
                {incident.environment && (
                  <div className="bg-muted/50 rounded-lg p-2.5">
                    <p className="text-xs text-muted-foreground mb-0.5">Environment</p>
                    <p className={`text-sm font-medium ${
                      incident.environment === 'PRD' ? 'text-red-600' :
                      incident.environment === 'QAS' ? 'text-amber-600' : 'text-muted-foreground'
                    }`}>{incident.environment}</p>
                  </div>
                )}
              </div>
            </section>
          )}


          <section className="border border-border rounded-lg p-4 bg-muted/30">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-primary" />
                <h3 className="text-sm font-semibold text-foreground">AI Analysis</h3>
                <ConfidenceIndicator confidence={incident.confidence} />
              </div>
              {isEditing ? (
                <div className="flex gap-2">
                  <Button size="sm" onClick={handleSaveEdit} className="gap-1.5 h-7">
                    <Save className="w-3.5 h-3.5" />
                    Save
                  </Button>
                  <Button size="sm" variant="ghost" onClick={handleCancelEdit} className="h-7">
                    Cancel
                  </Button>
                </div>
              ) : (
                <Button size="sm" variant="ghost" onClick={handleStartEdit} className="gap-1.5 h-7">
                  <Pencil className="w-3.5 h-3.5" />
                  Edit
                </Button>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              {/* Issue Type */}
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Issue Type</label>
                {isEditing ? (
                  <Select
                    value={displayValues.issueType}
                    onValueChange={(value) => setEditedFields(prev => ({ ...prev, issueType: value }))}
                  >
                    <SelectTrigger className="h-8">
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
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Severity</label>
                {isEditing ? (
                  <Select
                    value={displayValues.severity}
                    onValueChange={(value) => setEditedFields(prev => ({ ...prev, severity: value as typeof SEVERITIES[number] }))}
                  >
                    <SelectTrigger className="h-8">
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
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Root Cause</label>
                {isEditing ? (
                  <Input
                    value={displayValues.rootCause}
                    onChange={(e) => setEditedFields(prev => ({ ...prev, rootCause: e.target.value }))}
                    className="h-8"
                  />
                ) : (
                  <p className="text-sm text-foreground">{displayValues.rootCause}</p>
                )}
              </div>

              {/* Assign To */}
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Assign To</label>
                {isEditing ? (
                  <Select
                    value={displayValues.suggestedTeam}
                    onValueChange={(value) => setEditedFields(prev => ({ ...prev, suggestedTeam: value }))}
                  >
                    <SelectTrigger className="h-8">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {TEAMS.map(team => (
                        <SelectItem key={team} value={team}>{team}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <p className="text-sm font-medium text-foreground">{displayValues.suggestedTeam}</p>
                )}
              </div>
            </div>

            {/* Summary */}
            <div className="space-y-1 mb-4">
              <label className="text-xs font-medium text-muted-foreground">Summary</label>
              {isEditing ? (
                <Textarea
                  value={displayValues.aiSummary}
                  onChange={(e) => setEditedFields(prev => ({ ...prev, aiSummary: e.target.value }))}
                  className="min-h-[60px]"
                />
              ) : (
                <p className="text-sm text-foreground leading-relaxed">{displayValues.aiSummary}</p>
              )}
            </div>

            {/* Solution */}
            <div className="space-y-1 mb-4">
              <label className="text-xs font-medium text-muted-foreground">Recommended Solution</label>
              {isEditing ? (
                <Textarea
                  value={displayValues.aiSolution}
                  onChange={(e) => setEditedFields(prev => ({ ...prev, aiSolution: e.target.value }))}
                  className="min-h-[80px]"
                />
              ) : (
                <p className="text-sm text-foreground leading-relaxed">{displayValues.aiSolution}</p>
              )}
            </div>

            {/* Key Points */}
            <div className="space-y-1">
              <label className="text-xs font-medium text-muted-foreground">Key Points</label>
              <ul className="space-y-1">
                {incident.aiBullets.map((bullet, idx) => (
                  <li key={idx} className="text-sm text-foreground flex items-start gap-2">
                    <span className="text-primary mt-0.5">•</span>
                    {bullet}
                  </li>
                ))}
              </ul>
            </div>
          </section>

          {/* Notes Section */}
          <section>
            <h3 className="text-sm font-semibold mb-3 text-foreground">Notes</h3>
            {incident.notes.length > 0 && (
              <div className="space-y-2 mb-3">
                {incident.notes.map((note, idx) => (
                  <div key={idx} className="flex items-start gap-2 p-2 bg-muted/50 rounded text-sm">
                    <FileText className="w-3.5 h-3.5 mt-0.5 text-muted-foreground shrink-0" />
                    <span className="text-foreground">{note}</span>
                  </div>
                ))}
              </div>
            )}
            <div className="flex gap-2">
              <Input
                value={newNote}
                onChange={(e) => setNewNote(e.target.value)}
                placeholder="Add a note..."
                className="flex-1"
                onKeyDown={(e) => e.key === 'Enter' && handleAddNote()}
              />
              <Button size="sm" variant="outline" onClick={handleAddNote} disabled={!newNote.trim()}>
                <Plus className="w-4 h-4" />
              </Button>
            </div>
          </section>
        </div>
      </ScrollArea>
    </div>
  );
}
