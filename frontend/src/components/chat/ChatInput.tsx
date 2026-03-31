import { useState, useRef, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Send, Mic, MicOff, Image, Paperclip, Square, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface SapContext {
  tcode?: string;
  environment?: string;
  errorCode?: string;
}

interface ChatInputProps {
  onSend: (content: string, mediaType?: 'image' | 'audio' | 'text', mediaUrl?: string, sapContext?: SapContext) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [showSapContext, setShowSapContext] = useState(false);
  const [sapContext, setSapContext] = useState<SapContext>({ tcode: '', environment: '', errorCode: '' });
  const fileInputRef = useRef<HTMLInputElement>(null);
  const audioInputRef = useRef<HTMLInputElement>(null);
  const recordingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const handleSend = useCallback(() => {
    if (message.trim() && !disabled) {
      const ctx = (sapContext.tcode || sapContext.environment || sapContext.errorCode) ? sapContext : undefined;
      onSend(message.trim(), 'text', undefined, ctx);
      setMessage('');
    }
  }, [message, onSend, disabled, sapContext]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  const handleImageUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      onSend(`Uploaded image: ${file.name}`, 'image', url);
    }
  }, [onSend]);

  const handleAudioUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      onSend(`Uploaded audio: ${file.name}`, 'audio', url);
    }
  }, [onSend]);

  const toggleRecording = useCallback(() => {
    if (isRecording) {
      setIsRecording(false);
      if (recordingIntervalRef.current) {
        clearInterval(recordingIntervalRef.current);
      }
      onSend(`Voice recording (${recordingTime}s)`, 'audio');
      setRecordingTime(0);
    } else {
      setIsRecording(true);
      recordingIntervalRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    }
  }, [isRecording, recordingTime, onSend]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="border-t border-border bg-card p-4">
      {/* Recording indicator */}
      {isRecording && (
        <div className="flex items-center gap-2 mb-3 text-destructive">
          <div className="w-2 h-2 bg-destructive rounded-full animate-pulse" />
          <span className="text-sm font-medium">Recording... {formatTime(recordingTime)}</span>
        </div>
      )}

      <div className="flex items-end gap-2">
        {/* Media buttons */}
        <div className="flex items-center gap-1">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleImageUpload}
          />
          <input
            ref={audioInputRef}
            type="file"
            accept="audio/*,.wav,.mp3,.m4a"
            className="hidden"
            onChange={handleAudioUpload}
          />
          <Button
            variant="ghost"
            size="icon"
            className="h-9 w-9 text-muted-foreground hover:text-foreground"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled || isRecording}
          >
            <Image className="h-5 w-5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-9 w-9 text-muted-foreground hover:text-foreground"
            onClick={() => audioInputRef.current?.click()}
            disabled={disabled || isRecording}
          >
            <Paperclip className="h-5 w-5" />
          </Button>
          <Button
            variant={isRecording ? "destructive" : "ghost"}
            size="icon"
            className={cn(
              "h-9 w-9",
              isRecording ? "" : "text-muted-foreground hover:text-foreground"
            )}
            onClick={toggleRecording}
            disabled={disabled}
          >
            {isRecording ? <Square className="h-4 w-4" /> : <Mic className="h-5 w-5" />}
          </Button>
        </div>

        {/* Text input */}
        <Textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe the incident or ask a question..."
          className="flex-1 min-h-[44px] max-h-[200px] resize-none"
          disabled={disabled || isRecording}
        />

        {/* Send button */}
        <Button
          size="icon"
          className="h-11 w-11"
          onClick={handleSend}
          disabled={!message.trim() || disabled || isRecording}
        >
          <Send className="h-5 w-5" />
        </Button>
      </div>

      {/* SAP Context toggle */}
      <div className="mt-2">
        <button
          type="button"
          onClick={() => setShowSapContext(prev => !prev)}
          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          {showSapContext ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          {showSapContext ? 'Hide SAP Context' : '+ Add SAP Context'}
        </button>

        {showSapContext && (
          <div className="mt-2 grid grid-cols-3 gap-2">
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">T-Code</label>
              <Input
                placeholder="e.g. FB50, ME21N"
                className="h-8 text-xs font-mono"
                value={sapContext.tcode}
                onChange={e => setSapContext(prev => ({ ...prev, tcode: e.target.value }))}
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Environment</label>
              <Select
                value={sapContext.environment}
                onValueChange={val => setSapContext(prev => ({ ...prev, environment: val }))}
              >
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue placeholder="Select..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="PRD">PRD</SelectItem>
                  <SelectItem value="QAS">QAS</SelectItem>
                  <SelectItem value="DEV">DEV</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Error Code</label>
              <Input
                placeholder="e.g. F5 301"
                className="h-8 text-xs font-mono"
                value={sapContext.errorCode}
                onChange={e => setSapContext(prev => ({ ...prev, errorCode: e.target.value }))}
              />
            </div>
          </div>
        )}
      </div>

      <p className="text-xs text-muted-foreground mt-2">
        Supports text, images, and audio. Press Enter to send.
      </p>
    </div>
  );
}
