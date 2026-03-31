import { cn } from '@/lib/utils';
import { MessageCircle, Ticket, Mail, Phone, MessageSquare } from 'lucide-react';

// Extended Source type that includes Chat
type Source = 'WhatsApp' | 'Jira' | 'Email' | 'Phone' | 'Chat';

interface SourceBadgeProps {
  source: Source;
  showLabel?: boolean;
  className?: string;
}

const sourceConfig: Record<Source, { icon: typeof MessageCircle; class: string }> = {
  WhatsApp: { icon: MessageCircle, class: 'source-whatsapp' },
  Jira: { icon: Ticket, class: 'source-jira' },
  Email: { icon: Mail, class: 'source-email' },
  Phone: { icon: Phone, class: 'source-phone' },
  Chat: { icon: MessageSquare, class: 'source-chat' },
};

export function SourceBadge({ source, showLabel = true, className }: SourceBadgeProps) {
  const config = sourceConfig[source];
  if (!config) return null;
  const Icon = config.icon;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium",
        config.class,
        className
      )}
    >
      <Icon className="w-3 h-3" />
      {showLabel && <span>{source}</span>}
    </span>
  );
}
