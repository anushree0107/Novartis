import { ChartBar, TrendingUp, Bell, Zap, FileText, MessageCircle, MessagesSquare, HeartPulse, LayoutDashboard } from 'lucide-react';

interface SidebarProps {
  activeSection: string;
  onSectionChange: (section: string) => void;
}

export function Sidebar({ activeSection, onSectionChange }: SidebarProps) {
  const navItems = [
    { id: 'executive', icon: '📊', label: 'Executive Dashboard', IconComponent: LayoutDashboard },
    { id: 'site-health', icon: '🏥', label: 'Site Health', IconComponent: HeartPulse },
    { id: 'dqi', icon: '�', label: 'DQI Scores', IconComponent: ChartBar },
    { id: 'analytics', icon: '📈', label: 'Analytics', IconComponent: TrendingUp },
    { id: 'alerts', icon: '🔔', label: 'Alerts', IconComponent: Bell },
    { id: 'actions', icon: '⚡', label: 'Actions', IconComponent: Zap },
    { id: 'reports', icon: '📝', label: 'Reports', IconComponent: FileText },
    { id: 'query', icon: '💬', label: 'Query', IconComponent: MessageCircle },
    { id: 'chat', icon: '🤖', label: 'AI Chat', IconComponent: MessagesSquare },
  ];

  return (
    <div className="w-[260px] h-screen bg-[#1e3a8a] backdrop-blur-xl border-r border-[#2563eb]/20 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-[#2563eb]/20">
        <div className="flex items-center gap-0">
          <img src="/trialpulse-logo.png" alt="TrialPulse" className="w-60 h-60 object-contain -m-16" />
          <div>
            <h1 className="text-lg font-bold bg-gradient-to-r from-[#3b82f6] to-[#a855f7] bg-clip-text text-transparent">
              TrialPulse
            </h1>
            <p className="text-[10px] text-blue-200">Clinical Intelligence Platform</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {navItems.map((item) => (
            <li key={item.id}>
              <button
                onClick={() => onSectionChange(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${activeSection === item.id
                  ? 'bg-gradient-to-r from-[#3b82f6] to-[#2563eb] text-white shadow-[0_0_20px_rgba(37,99,235,0.4)]'
                  : 'text-blue-100 hover:bg-white/10'
                  }`}
              >
                <span className="text-xl">{item.icon}</span>
                <span>{item.label}</span>
              </button>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-6 border-t border-[#2563eb]/20">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-xs text-blue-200">API Connected</span>
        </div>
      </div>
    </div>
  );
}