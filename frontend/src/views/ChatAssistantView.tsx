import { useState, useRef, useCallback } from 'react';
import { useIncidents, ChatMessage, Incident } from '@/context/IncidentContext';
import { ChatInput, SapContext } from '@/components/chat/ChatInput';
import { ChatMessageList } from '@/components/chat/ChatMessageList';
import { IncidentAnalysisPanel } from '@/components/chat/IncidentAnalysisPanel';
import { Button } from '@/components/ui/button';
import { Maximize2, Minimize2 } from 'lucide-react';
import { cn } from '@/lib/utils';

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

    // Add to local state first for immediate feedback
    setLocalMessages(prev => [...prev, userMessage]);
    setIsProcessing(true);

    // Simulate AI processing
    setTimeout(() => {
      const aiResponse: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: generateAIResponse(content, mediaType),
        timestamp: new Date()
      };
      
      setLocalMessages(prev => [...prev, aiResponse]);
      
      // If this is the first message, create an incident
      if (!currentIncidentId) {
        const incident = createIncidentFromChat({
          shortText: content.slice(0, 100),
          longText: content,
          hasMedia: !!mediaUrl,
          mediaType: mediaType === 'text' ? undefined : mediaType,
          mediaUrl,
          issueType: detectIssueType(content),
          severity: detectSeverity(content),
          rootCause: 'Pending analysis',
          suggestedTeam: detectTeam(content),
          aiSummary: `Issue reported: ${content.slice(0, 150)}...`,
          aiBullets: generateBullets(content),
          aiRationale: 'Initial analysis based on user input',
          aiSolution: generateSolution(content),
          confidence: 75,
          aiSource: 'llm',
          chatHistory: [userMessage, aiResponse],
          ...(sapContext?.tcode && { tcode: sapContext.tcode }),
          ...(sapContext?.environment && { environment: sapContext.environment as 'PRD' | 'QAS' | 'DEV' }),
          ...(sapContext?.errorCode && { errorCode: sapContext.errorCode })
        });
        setCurrentIncidentId(incident.id);
        selectIncident(incident.id);
      } else {
        // Add messages to existing incident
        addChatMessage(currentIncidentId, userMessage);
        addChatMessage(currentIncidentId, aiResponse);
      }
      
      setIsProcessing(false);
    }, 1500);
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

// Helper functions for AI simulation
function generateAIResponse(content: string, mediaType?: string): string {
  if (mediaType === 'audio') {
    return "I've transcribed and analyzed your audio message. Based on the description, this appears to be a technical issue that requires immediate attention. I've created an incident record and populated the analysis panel with my findings. Please review the suggested Issue Type, Severity, and recommended team assignment on the right.";
  }
  if (mediaType === 'image') {
    return "I've analyzed the uploaded image. Based on the error message visible, this appears to be a system configuration issue. I've documented my findings in the analysis panel. You can edit any of the fields before assigning to a team or pushing to external systems.";
  }
  return `I've analyzed your report. This appears to be a ${detectIssueType(content).toLowerCase()} that should be routed to the ${detectTeam(content)} team. My confidence level is 75% based on the information provided. You can review and modify my analysis in the panel on the right before taking any action.`;
}

function detectIssueType(content: string): string {
  const lower = content.toLowerCase();
  if (lower.includes('network') || lower.includes('connection')) return 'Network';
  if (lower.includes('performance') || lower.includes('slow')) return 'Performance';
  if (lower.includes('error') || lower.includes('crash')) return 'Technical Issue';
  if (lower.includes('billing') || lower.includes('invoice')) return 'Billing Inquiry';
  if (lower.includes('access') || lower.includes('login')) return 'Account Access';
  return 'Technical Issue';
}

function detectSeverity(content: string): 'P1' | 'P2' | 'P3' | 'P4' {
  const lower = content.toLowerCase();
  if (lower.includes('critical') || lower.includes('down') || lower.includes('urgent')) return 'P1';
  if (lower.includes('important') || lower.includes('blocking')) return 'P2';
  if (lower.includes('minor') || lower.includes('low')) return 'P4';
  return 'P3';
}

function detectTeam(content: string): string {
  const lower = content.toLowerCase();
  if (lower.includes('sap') || lower.includes('fi') || lower.includes('mm')) return 'SAP Support';
  if (lower.includes('network')) return 'L2 Network';
  if (lower.includes('server') || lower.includes('infra')) return 'L2 Infrastructure';
  if (lower.includes('billing')) return 'Finance Team';
  return 'L1 Support';
}

function generateBullets(content: string): string[] {
  return [
    'Issue reported via chat interface',
    `Primary concern: ${content.slice(0, 50)}...`,
    'Requires team review and validation',
    'AI analysis pending human approval'
  ];
}

function generateSolution(content: string): string {
  return 'Pending detailed analysis. Please review the AI-generated suggestions and modify as needed before assigning to a resolution team.';
}
