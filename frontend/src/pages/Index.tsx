import { useState } from 'react';
import { AppLayout } from '@/components/layout/AppLayout';
import { ManagerView } from '@/views/ManagerView';
import { SupportView } from '@/views/SupportView';
import { ChatAssistantView } from '@/views/ChatAssistantView';
import { AdminView } from '@/views/AdminView';
import { KnowledgeBaseView } from '@/views/KnowledgeBaseView';
import { IncidentProvider } from '@/context/IncidentContext';

type View = 'manager' | 'support' | 'chat' | 'admin' | 'knowledge-base';

const Index = () => {
  const [currentView, setCurrentView] = useState<View>('chat');

  const renderView = () => {
    switch (currentView) {
      case 'manager':
        return <ManagerView />;
      case 'support':
        return <SupportView />;
      case 'chat':
        return <ChatAssistantView />;
      case 'knowledge-base':
        return <KnowledgeBaseView />;
      case 'admin':
        return <AdminView />;
      default:
        return <ChatAssistantView />;
    }
  };

  return (
    <IncidentProvider>
      <AppLayout currentView={currentView} onViewChange={setCurrentView}>
        {renderView()}
      </AppLayout>
    </IncidentProvider>
  );
};

export default Index;
