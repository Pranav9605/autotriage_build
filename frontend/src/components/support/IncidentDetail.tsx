import { PriorityBadge } from '@/components/ui/PriorityBadge';
import { SourceBadge } from '@/components/ui/SourceBadge';
import { ConfidenceIndicator } from '@/components/ui/ConfidenceIndicator';
import { SourceTypeBadge } from '@/components/ui/SourceTypeBadge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Check, 
  UserPlus, 
  ArrowUpRight, 
  MessageSquare, 
  Play, 
  FileText,
  Image,
  ExternalLink,
  Sparkles,
  Clock,
  User
} from 'lucide-react';
import { similarCases, kbArticles } from '@/data/mockData';
import type { Incident } from '@/data/mockData';

type AISourceType = 'ml' | 'kb' | 'cache' | 'llm';

interface IncidentDetailProps {
  incident: Incident | null;
}

export function IncidentDetail({ incident }: IncidentDetailProps) {
  if (!incident) {
    return (
      <div className="flex-1 min-w-[380px] max-w-[480px] bg-card border-l border-border flex items-center justify-center">
        <div className="text-center p-6">
          <div className="w-14 h-14 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
            <Sparkles className="w-6 h-6 text-muted-foreground" />
          </div>
          <p className="text-muted-foreground text-sm">Select an incident to view details</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 min-w-[380px] max-w-[480px] bg-card border-l border-border flex flex-col">
      {/* Header - Fixed */}
      <div className="p-5 border-b border-border bg-card shrink-0">
        <div className="mb-3">
          <div className="flex items-center flex-wrap gap-2 mb-2">
            <span className="font-mono text-sm font-semibold text-foreground">{incident.id}</span>
            <SourceBadge source={incident.source} />
            <PriorityBadge priority={incident.priority} />
          </div>
          <h2 className="text-base font-semibold text-foreground leading-snug">{incident.shortText}</h2>
        </div>

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
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <Button size="sm" className="gap-1.5">
            <Check className="w-4 h-4" />
            Accept
          </Button>
          <Button size="sm" variant="outline" className="gap-1.5">
            <UserPlus className="w-4 h-4" />
            Assign
          </Button>
          <Button size="sm" variant="outline" className="gap-1.5">
            <ArrowUpRight className="w-4 h-4" />
            Escalate
          </Button>
          <Button size="sm" variant="ghost" className="gap-1.5">
            <MessageSquare className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Scrollable Content */}
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

          {/* Media Viewer */}
          {incident.hasMedia && (
            <section>
              <h3 className="text-sm font-semibold mb-3 text-foreground">Attachments</h3>
              <div className="bg-muted/50 rounded-lg p-6 flex flex-col items-center justify-center border border-border">
                {incident.mediaType === 'video' ? (
                  <>
                    <Play className="w-10 h-10 text-muted-foreground mb-2" />
                    <p className="text-xs text-muted-foreground">Video attachment</p>
                    <Button size="sm" variant="ghost" className="mt-2 gap-1.5">
                      <FileText className="w-3.5 h-3.5" />
                      View Transcript
                    </Button>
                  </>
                ) : incident.mediaType === 'document' ? (
                  <>
                    <FileText className="w-10 h-10 text-muted-foreground mb-2" />
                    <p className="text-xs text-muted-foreground">Document attachment</p>
                  </>
                ) : (
                  <>
                    <Image className="w-10 h-10 text-muted-foreground mb-2" />
                    <p className="text-xs text-muted-foreground">Screenshot attached</p>
                  </>
                )}
              </div>
            </section>
          )}

          {/* AI Summary */}
          <section className="bg-primary/5 rounded-lg p-4 border border-primary/10">
            <div className="flex items-center flex-wrap gap-2 mb-3">
              <Sparkles className="w-4 h-4 text-primary" />
              <h3 className="text-sm font-semibold text-foreground">AI Summary</h3>
              <ConfidenceIndicator confidence={incident.confidence} />
              {incident.aiSource && (
                <SourceTypeBadge source={incident.aiSource as AISourceType} />
              )}
            </div>

            <p className="text-sm font-medium mb-3 text-foreground">{incident.aiSummary}</p>

            <ul className="space-y-1.5 mb-4">
              {incident.aiBullets.map((bullet, idx) => (
                <li key={idx} className="text-sm text-muted-foreground flex items-start gap-2">
                  <span className="text-primary mt-0.5">•</span>
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>

            <div className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
              <div>
                <span className="text-xs text-muted-foreground block">Suggested Category</span>
                <p className="font-medium text-foreground">{incident.suggestedCategory}</p>
              </div>
              <div>
                <span className="text-xs text-muted-foreground block">SAP Module</span>
                <p className="font-medium text-foreground">{incident.sapModule}</p>
              </div>
              <div>
                <span className="text-xs text-muted-foreground block">Suggested Team</span>
                <p className="font-medium text-foreground">{incident.suggestedTeam}</p>
              </div>
              <div>
                <span className="text-xs text-muted-foreground block">Suggested Priority</span>
                <div className="mt-0.5">
                  <PriorityBadge priority={incident.suggestedPriority} size="sm" />
                </div>
              </div>
            </div>

            <p className="text-xs text-muted-foreground mt-4 pt-3 border-t border-primary/10">
              {incident.aiRationale}
            </p>
          </section>

          {/* KB & Similar Cases */}
          <section>
            <h3 className="text-sm font-semibold mb-3 text-foreground">KB & Similar Cases</h3>
            
            <div className="space-y-2 mb-4">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Knowledge Base</p>
              {kbArticles.map((kb) => (
                <a 
                  key={kb.id}
                  href="#"
                  className="flex items-center justify-between p-2.5 rounded-md hover:bg-muted transition-colors border border-transparent hover:border-border"
                >
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-muted-foreground shrink-0" />
                    <span className="text-sm text-foreground">{kb.title}</span>
                  </div>
                  <ExternalLink className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                </a>
              ))}
            </div>

            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Similar Resolved Cases</p>
              {similarCases.map((sc) => (
                <div key={sc.id} className="p-2.5 rounded-md hover:bg-muted transition-colors border border-transparent hover:border-border">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-mono text-muted-foreground">{sc.id}</span>
                    <span className="text-xs text-muted-foreground">Resolved in {sc.resolvedIn}</span>
                  </div>
                  <p className="text-sm text-foreground">{sc.title}</p>
                  <p className="text-xs text-muted-foreground mt-1">→ {sc.resolution}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Apply to SAP/Jira */}
          <section>
            <h3 className="text-sm font-semibold mb-3 text-foreground">Apply to Systems</h3>
            
            <div className="bg-muted/50 rounded-lg p-4 mb-3 border border-border">
              <p className="text-xs font-medium text-muted-foreground mb-3 uppercase tracking-wide">Draft Preview</p>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between items-start gap-4">
                  <span className="text-muted-foreground shrink-0">Short Text:</span>
                  <span className="text-right text-foreground">{incident.shortText}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Component:</span>
                  <span className="font-mono text-foreground">{incident.sapModule}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Priority:</span>
                  <span className="text-foreground">{incident.suggestedPriority}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Team:</span>
                  <span className="text-foreground">{incident.suggestedTeam}</span>
                </div>
              </div>
            </div>

            <div className="flex gap-2">
              <Button size="sm" variant="outline" className="flex-1">
                Push to Jira
              </Button>
              <Button size="sm" variant="outline" className="flex-1">
                Create SAP Draft
              </Button>
            </div>

            <p className="text-xs text-muted-foreground text-center mt-3">
              Drafts can be reviewed before final submission
            </p>
          </section>
        </div>
      </ScrollArea>
    </div>
  );
}
