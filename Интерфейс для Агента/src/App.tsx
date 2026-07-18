import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { DialogsView } from './components/views/DialogsView';
import { AgentsView } from './components/views/AgentsView';
import { KnowledgeBaseView } from './components/views/KnowledgeBaseView';
import { MonitoringView } from './components/views/MonitoringView';
import { TabType } from './types';

export default function App() {
  const [activeTab, setActiveTab] = useState<TabType>('dialogs');

  const renderContent = () => {
    switch (activeTab) {
      case 'dialogs':
        return <DialogsView />;
      case 'agents':
        return <AgentsView />;
      case 'knowledge':
        return <KnowledgeBaseView />;
      case 'monitoring':
        return <MonitoringView />;
      default:
        return (
          <div className="flex-1 flex items-center justify-center text-gray-400 flex-col gap-4">
            <span className="text-4xl">🚧</span>
            <p>Раздел в разработке. Кликай по разделам «Центр агента» слева.</p>
          </div>
        );
    }
  };

  return (
    <div className="flex h-screen bg-[#F8FAFC] text-gray-900 font-sans overflow-hidden">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <div className="p-8 pb-12 w-full max-w-[1400px] mx-auto">
          {renderContent()}
        </div>
      </main>
    </div>
  );
}

