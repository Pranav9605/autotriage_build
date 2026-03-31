import { useRef, useEffect } from 'react';
import { ChatMessage } from '@/context/IncidentContext';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import { User, Bot, Image, Mic, Loader2 } from 'lucide-react';

interface ChatMessageListProps {
  messages: ChatMessage[];
  isProcessing?: boolean;
}

export function ChatMessageList({ messages, isProcessing }: ChatMessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isProcessing]);

  if (messages.length === 0 && !isProcessing) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
            <Bot className="w-8 h-8 text-primary" />
          </div>
          <h3 className="text-lg font-semibold text-foreground mb-2">
            Incident Intake Assistant
          </h3>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Describe your issue using text, upload an image or screenshot, or record an audio message. 
            I'll analyze the problem and help route it to the right team.
          </p>
          <div className="flex flex-wrap gap-2 justify-center mt-4">
            <span className="text-xs bg-muted px-2 py-1 rounded">Text</span>
            <span className="text-xs bg-muted px-2 py-1 rounded">Images</span>
            <span className="text-xs bg-muted px-2 py-1 rounded">Audio</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1">
      <div className="p-4 space-y-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        
        {isProcessing && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4 text-primary" />
            </div>
            <div className="bg-muted rounded-lg px-4 py-3 max-w-[80%]">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Analyzing...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';

  return (
    <div className={cn(
      "flex items-start gap-3",
      isUser && "flex-row-reverse"
    )}>
      <div className={cn(
        "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
        isUser ? "bg-primary" : "bg-primary/10"
      )}>
        {isUser ? (
          <User className="w-4 h-4 text-primary-foreground" />
        ) : (
          <Bot className="w-4 h-4 text-primary" />
        )}
      </div>
      
      <div className={cn(
        "rounded-lg px-4 py-3 max-w-[80%]",
        isUser ? "bg-primary text-primary-foreground" : "bg-muted"
      )}>
        {/* Media indicator */}
        {message.mediaType && message.mediaType !== 'text' && (
          <div className={cn(
            "flex items-center gap-2 mb-2 text-xs",
            isUser ? "text-primary-foreground/70" : "text-muted-foreground"
          )}>
            {message.mediaType === 'image' && <Image className="w-3.5 h-3.5" />}
            {message.mediaType === 'audio' && <Mic className="w-3.5 h-3.5" />}
            <span>{message.mediaType === 'image' ? 'Image attached' : 'Audio attached'}</span>
          </div>
        )}

        {/* Image preview */}
        {message.mediaType === 'image' && message.mediaUrl && (
          <img 
            src={message.mediaUrl} 
            alt="Uploaded" 
            className="rounded max-w-full max-h-48 mb-2"
          />
        )}

        {/* Audio player */}
        {message.mediaType === 'audio' && message.mediaUrl && (
          <audio 
            controls 
            src={message.mediaUrl} 
            className="max-w-full mb-2"
          />
        )}

        <p className={cn(
          "text-sm leading-relaxed",
          isUser ? "text-primary-foreground" : "text-foreground"
        )}>
          {message.content}
        </p>
        
        <span className={cn(
          "text-[10px] mt-1 block",
          isUser ? "text-primary-foreground/60" : "text-muted-foreground"
        )}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  );
}
