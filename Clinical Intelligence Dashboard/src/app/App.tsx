import { useState } from 'react';
import { LandingPage } from './components/LandingPage';
import { Sidebar } from './components/Sidebar';
import { ExecutiveDashboard } from './components/ExecutiveDashboard';
import { SiteHealthDashboard } from './components/SiteHealthDashboard';
import { DQIScores } from './components/DQIScores';
import { Analytics } from './components/Analytics';
import { Alerts } from './components/Alerts';
import { Actions } from './components/Actions';
import { Reports } from './components/Reports';
import { Query } from './components/Query';
import { Chat } from './components/Chat';
import { AIModal } from './components/AIModal';

export default function App() {
  const [showDashboard, setShowDashboard] = useState(false);
  const [activeSection, setActiveSection] = useState('executive');
  const [aiModalOpen, setAiModalOpen] = useState(false);
  const [aiModalContent, setAiModalContent] = useState({ title: '', content: '' });

  const openAiModal = (title: string, content: string) => {
    setAiModalContent({ title, content });
    setAiModalOpen(true);
  };

  const renderSection = () => {
    switch (activeSection) {
      case 'executive':
        return <ExecutiveDashboard />;
      case 'site-health':
        return <SiteHealthDashboard onAiClick={openAiModal} />;
      case 'dqi':
        return <DQIScores onAiClick={openAiModal} />;
      case 'analytics':
        return <Analytics onAiClick={openAiModal} />;
      case 'alerts':
        return <Alerts onAiClick={openAiModal} />;
      case 'actions':
        return <Actions />;
      case 'reports':
        return <Reports />;
      case 'query':
        return <Query />;
      case 'chat':
        return <Chat />;
      default:
        return <ExecutiveDashboard />;
    }
  };

  // Show landing page if not in dashboard mode
  if (!showDashboard) {
    return <LandingPage onEnterDashboard={() => setShowDashboard(true)} />;
  }

  // Show dashboard
  return (
    <div className="min-h-screen bg-[#e8eaf0] font-['Inter',sans-serif] relative overflow-hidden">
      {/* Background gradient overlay */}
      <div className="fixed inset-0 bg-gradient-radial from-[#d0d5e0] via-[#e8eaf0] to-[#e8eaf0] pointer-events-none" />

      {/* Main container */}
      <div className="relative flex h-screen">
        <Sidebar activeSection={activeSection} onSectionChange={setActiveSection} />

        <main className="flex-1 overflow-y-auto p-8">
          {renderSection()}
        </main>
      </div>

      <AIModal
        isOpen={aiModalOpen}
        onClose={() => setAiModalOpen(false)}
        title={aiModalContent.title}
        content={aiModalContent.content}
      />
    </div>
  );
}