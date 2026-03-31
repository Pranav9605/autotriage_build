import { useState } from 'react';
import { cn } from '@/lib/utils';
import { 
  LayoutDashboard, 
  Inbox, 
  Settings, 
  ChevronLeft, 
  ChevronRight,
  Brain,
  BookOpen,
  MessageSquareText
} from 'lucide-react';
import { Button } from '@/components/ui/button';

type View = 'manager' | 'support' | 'chat' | 'admin' | 'knowledge-base';

interface AppLayoutProps {
  children: React.ReactNode;
  currentView: View;
  onViewChange: (view: View) => void;
}

export function AppLayout({ children, currentView, onViewChange }: AppLayoutProps) {
  const [collapsed, setCollapsed] = useState(false);

  const navItems = [
    { id: 'chat' as View, label: 'Chat Assistant', icon: MessageSquareText },
    { id: 'support' as View, label: 'Support View', icon: Inbox },
    { id: 'manager' as View, label: 'Executive Overview', icon: LayoutDashboard },
    { id: 'knowledge-base' as View, label: 'Knowledge Base', icon: BookOpen },
    { id: 'admin' as View, label: 'Admin / Integrations', icon: Settings },
  ];

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside 
        className={cn(
          "bg-sidebar text-sidebar-foreground flex flex-col transition-all duration-300 shrink-0",
          collapsed ? "w-16" : "w-64"
        )}
      >
        {/* Logo */}
        <div className="h-16 flex items-center px-4 border-b border-sidebar-border">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-sidebar-primary to-sidebar-primary/70 flex items-center justify-center shadow-lg shadow-sidebar-primary/30">
              <Brain className="w-5 h-5 text-sidebar-primary-foreground" />
            </div>
            {!collapsed && (
              <div className="flex flex-col">
                <span className="font-bold text-base tracking-tight leading-none">AutoTriage</span>
                <span className="text-[10px] text-sidebar-foreground/60 font-medium tracking-wide">INCIDENT COMMAND</span>
              </div>
            )}
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                currentView === item.id
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
              )}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </button>
          ))}
        </nav>

        {/* Collapse Toggle */}
        <div className="p-3 border-t border-sidebar-border">
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-center text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent/50"
            onClick={() => setCollapsed(!collapsed)}
          >
            {collapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <>
                <ChevronLeft className="w-4 h-4 mr-2" />
                <span>Collapse</span>
              </>
            )}
          </Button>
        </div>

        {/* Data Residency Footer */}
        {!collapsed && (
          <div className="px-4 py-3 text-xs text-sidebar-foreground/50 border-t border-sidebar-border">
            All processing & storage in India
          </div>
        )}
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
