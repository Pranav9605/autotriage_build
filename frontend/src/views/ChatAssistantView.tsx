import { useState, useCallback } from 'react';
import { useIncidents, ChatMessage, ticketToIncident } from '@/context/IncidentContext';
import { ChatInput, SapContext } from '@/components/chat/ChatInput';
import { ChatMessageList } from '@/components/chat/ChatMessageList';
import { IncidentAnalysisPanel } from '@/components/chat/IncidentAnalysisPanel';
import { Button } from '@/components/ui/button';
import { Maximize2, Minimize2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { api } from '@/services/api';

export function ChatAssistantView() {
  const { state, createIncidentFromChat, addChatMessage, selectIncident, setFullScreen, getSelectedIncident } = useIncidents();
  const [localMessages, setLocalMessages] = useState<ChatMessage[]>([]);
  const [currentIncidentId, setCurrentIncidentId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const selectedIncident = getSelectedIncident();
  const isFullScreen = state.isFullScreen;

  const handleSendMessage = useCallback(async (
    content: string,
    mediaType?: 'image' | 'audio' | 'text',
    mediaUrl?: string,
    sapContext?: SapContext
  ) => {
    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date(),
      mediaType,
      mediaUrl
    };

    setLocalMessages(prev => [...prev, userMessage]);
    setIsProcessing(true);

    try {
      // Call the real triage API
      const ticketResp = await api.createTicket({
        source: 'chat',
        raw_text: content,
        reporter: undefined,
      });

      const incident = ticketToIncident(ticketResp);
      // Attach media context from the chat input
      if (mediaUrl) {
        incident.hasMedia = true;
        incident.mediaType = mediaType === 'text' ? undefined : mediaType;
        incident.mediaUrl = mediaUrl;
      }
      if (sapContext?.tcode)       incident.tcode = sapContext.tcode;
      if (sapContext?.errorCode)   incident.errorCode = sapContext.errorCode;
      if (sapContext?.environment) incident.environment = sapContext.environment as 'PRD' | 'QAS' | 'DEV';
      incident.chatHistory = [userMessage];

      const triage = ticketResp.triage;
      const aiText = triage
        ? `Triaged as **${triage.module} / ${triage.priority}** (${Math.round(triage.confidence * 100)}% confidence).\n\n` +
          `**Root cause:** ${triage.root_cause_hypothesis}\n\n` +
          `**Solution:** ${triage.recommended_solution}\n\n` +
          `**Assigned to:** ${triage.assign_to}` +
          (triage.manual_review_required ? `\n\n⚠️ Manual review required: ${triage.review_reason}` : '')
        : 'Ticket created — triage is pending.';

      const aiResponse: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: aiText,
        timestamp: new Date(),
      };

      setLocalMessages(prev => [...prev, aiResponse]);
      incident.chatHistory = [userMessage, aiResponse];

      // Add to context and select
      createIncidentFromChat(incident);
      setCurrentIncidentId(incident.id);
      selectIncident(incident.id);

    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Unknown error';
      const errorResponse: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: `Failed to triage ticket: ${errMsg}. Please check that the backend is running.`,
        timestamp: new Date(),
      };
      setLocalMessages(prev => [...prev, errorResponse]);

      // Fall back to local incident creation so the UI stays functional
      if (!currentIncidentId) {
        createIncidentFromChat({
          shortText: content.slice(0, 100),
          longText: content,
          hasMedia: !!mediaUrl,
          mediaType: mediaType === 'text' ? undefined : mediaType,
          mediaUrl,
          issueType: 'Technical Issue',
          severity: 'P3',
          rootCause: 'Pending analysis',
          suggestedTeam: 'General SAP Support',
          aiSummary: content.slice(0, 150),
          aiBullets: ['Backend unavailable — manual triage required'],
          aiRationale: 'Offline mode',
          aiSolution: 'Please assign manually.',
          confidence: 0,
          aiSource: 'llm',
          chatHistory: [userMessage, errorResponse],
          ...(sapContext?.tcode && { tcode: sapContext.tcode }),
          ...(sapContext?.environment && { environment: sapContext.environment as 'PRD' | 'QAS' | 'DEV' }),
          ...(sapContext?.errorCode && { errorCode: sapContext.errorCode }),
        });
      } else {
        addChatMessage(currentIncidentId, userMessage);
        addChatMessage(currentIncidentId, errorResponse);
      }
    } finally {
      setIsProcessing(false);
    }
  }, [currentIncidentId, createIncidentFromChat, addChatMessage, selectIncident]);

  const handleNewChat = useCallback(() => {
    setLocalMessages([]);
    setCurrentIncidentId(null);
    selectIncident(null);
  }, [selectIncident]);

  return (
    <div className={cn(
      "flex h-full",
      isFullScreen && "fixed inset-0 z-50 bg-background"
    )}>
      {/* Chat Area */}
      <div className={cn(
        "flex flex-col border-r border-border",
        isFullScreen ? "w-1/2" : "flex-1"
      )}>
        {/* Header */}
        <div className="h-14 border-b border-border px-4 flex items-center justify-between bg-card shrink-0">
          <div className="flex items-center gap-3">
            <h2 className="font-semibold text-foreground">Chat Assistant</h2>
            {currentIncidentId && (
              <span className="text-xs font-mono text-muted-foreground bg-muted px-2 py-0.5 rounded">
                {currentIncidentId}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleNewChat}>
              New Incident
            </Button>
            <Button 
              variant="ghost" 
              size="icon" 
              className="h-8 w-8"
              onClick={() => setFullScreen(!isFullScreen)}
            >
              {isFullScreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </Button>
          </div>
        </div>

        {/* Messages */}
        <ChatMessageList messages={localMessages} isProcessing={isProcessing} />

        {/* Input */}
        <ChatInput onSend={handleSendMessage} disabled={isProcessing} />
      </div>

      {/* Analysis Panel */}
      <div className={cn(
        "bg-card",
        isFullScreen ? "w-1/2" : "w-[480px]"
      )}>
        <IncidentAnalysisPanel 
          incident={selectedIncident}
          onClose={isFullScreen ? undefined : () => selectIncident(null)}
        />
      </div>
    </div>
  );
}

