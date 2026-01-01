import { ArrowRight, BarChart3, Activity, Bell, Zap, FileText, Database } from 'lucide-react';

interface LandingPageProps {
  onEnterDashboard: () => void;
}

export function LandingPage({ onEnterDashboard }: LandingPageProps) {
  const features = [
    {
      icon: <BarChart3 className="w-8 h-8" />,
      title: 'DQI Scores',
      description: 'Monitor data quality metrics with circular gauge charts and detailed breakdowns',
      color: '#3b82f6',
    },
    {
      icon: <Activity className="w-8 h-8" />,
      title: 'Analytics',
      description: 'Benchmark performance and view comprehensive site rankings',
      color: '#2563eb',
    },
    {
      icon: <Bell className="w-8 h-8" />,
      title: 'Alerts',
      description: 'Track critical issues with severity distributions and notifications',
      color: '#0460A9',
    },
    {
      icon: <Zap className="w-8 h-8" />,
      title: 'Agentic Actions',
      description: 'Execute complex operations using natural language commands',
      color: '#3b82f6',
    },
    {
      icon: <FileText className="w-8 h-8" />,
      title: 'Reports',
      description: 'Generate comprehensive markdown reports with previews',
      color: '#2563eb',
    },
    {
      icon: <Database className="w-8 h-8" />,
      title: 'Query Interface',
      description: 'Explore data with natural language queries',
      color: '#0460A9',
    },
  ];

  const stats = [
    { value: '99.9%', label: 'Uptime' },
    { value: '1.2s', label: 'Avg Response' },
    { value: '500+', label: 'Sites Monitored' },
    { value: '24/7', label: 'AI Support' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#e8eaf0] via-[#d0d5e0] to-[#e8eaf0] font-['Inter',sans-serif]">
      {/* Animated background particles */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-64 h-64 bg-blue-400/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute top-40 right-32 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-1000" />
        <div className="absolute bottom-20 left-1/3 w-80 h-80 bg-blue-300/10 rounded-full blur-3xl animate-pulse delay-2000" />
      </div>

      {/* Navigation */}
      <nav className="relative z-10 px-8 py-6 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="text-3xl drop-shadow-[0_0_12px_rgba(37,99,235,0.6)]">🔥</div>
          <div>
            <h1 className="text-2xl bg-gradient-to-r from-[#3b82f6] to-[#2563eb] bg-clip-text text-transparent">
              NOVARTIS
            </h1>
            <p className="text-xs text-gray-600">SAGE-Flow Clinical Intelligence</p>
          </div>
        </div>
        
        <button
          onClick={onEnterDashboard}
          className="px-6 py-2 bg-white/80 backdrop-blur-sm border border-blue-200 rounded-lg text-gray-800 hover:bg-white hover:shadow-lg transition-all duration-200"
        >
          Sign In
        </button>
      </nav>

      {/* Hero Section */}
      <div className="relative z-10 max-w-7xl mx-auto px-8 pt-20 pb-32">
        <div className="text-center mb-16">
          <div className="inline-block px-4 py-2 bg-white/60 backdrop-blur-sm border border-blue-200 rounded-full text-sm text-gray-700 mb-6">
            ✨ Next-Generation Clinical Intelligence Platform
          </div>
          
          <h1 className="text-6xl mb-6 bg-gradient-to-r from-[#3b82f6] via-[#2563eb] to-[#0460A9] bg-clip-text text-transparent">
            Transform Clinical Data
            <br />
            Into Actionable Insights
          </h1>
          
          <p className="text-xl text-gray-600 mb-10 max-w-3xl mx-auto">
            Monitor data quality, analyze performance, and execute intelligent actions
            with our AI-powered clinical intelligence dashboard
          </p>

          <div className="flex gap-4 justify-center">
            <button
              onClick={onEnterDashboard}
              className="px-8 py-4 bg-gradient-to-r from-[#3b82f6] to-[#2563eb] text-white rounded-lg hover:shadow-[0_0_30px_rgba(37,99,235,0.4)] transition-all duration-200 flex items-center gap-2 text-lg group"
            >
              Enter Dashboard
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
            
            <button className="px-8 py-4 bg-white/80 backdrop-blur-sm border border-blue-200 rounded-lg text-gray-800 hover:bg-white hover:shadow-lg transition-all duration-200 text-lg">
              Watch Demo
            </button>
          </div>
        </div>

        {/* Stats Bar */}
        <div className="grid grid-cols-4 gap-6 mb-20">
          {stats.map((stat, idx) => (
            <div
              key={idx}
              className="glass-card p-6 text-center hover:scale-105 transition-transform"
            >
              <div className="text-3xl bg-gradient-to-r from-[#3b82f6] to-[#2563eb] bg-clip-text text-transparent mb-2">
                {stat.value}
              </div>
              <div className="text-sm text-gray-600">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Features Grid */}
        <div className="mb-20">
          <h2 className="text-4xl text-center mb-4 bg-gradient-to-r from-[#3b82f6] to-[#2563eb] bg-clip-text text-transparent">
            Powerful Features
          </h2>
          <p className="text-center text-gray-600 mb-12 text-lg">
            Everything you need to manage clinical data quality and performance
          </p>

          <div className="grid grid-cols-3 gap-6">
            {features.map((feature, idx) => (
              <div
                key={idx}
                className="glass-card p-6 hover:scale-105 transition-all duration-300 group"
              >
                <div
                  className="w-16 h-16 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform"
                  style={{
                    background: `linear-gradient(135deg, ${feature.color}15, ${feature.color}30)`,
                    color: feature.color,
                  }}
                >
                  {feature.icon}
                </div>
                <h3 className="text-xl mb-2 text-gray-800">{feature.title}</h3>
                <p className="text-gray-600 text-sm">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Dashboard Preview */}
        <div className="glass-card p-8 mb-20">
          <h2 className="text-3xl text-center mb-4 bg-gradient-to-r from-[#3b82f6] to-[#2563eb] bg-clip-text text-transparent">
            AI-Powered Intelligence
          </h2>
          <p className="text-center text-gray-600 mb-8">
            Get instant insights and recommendations with our advanced AI analysis engine
          </p>
          
          <div className="bg-gradient-to-br from-[#1e3a8a] to-[#2563eb] rounded-xl p-8 text-white">
            <div className="grid grid-cols-2 gap-8">
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                  <span className="text-sm">AI Assistant Active</span>
                </div>
                <h3 className="text-2xl mb-3">🤖 Real-time Analysis</h3>
                <p className="text-blue-100 mb-4">
                  Our AI continuously monitors your data quality metrics and provides
                  actionable recommendations to improve site performance.
                </p>
                <ul className="space-y-2 text-sm text-blue-100">
                  <li className="flex items-start gap-2">
                    <span className="text-green-400 mt-1">✓</span>
                    <span>Automated anomaly detection</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-400 mt-1">✓</span>
                    <span>Predictive quality scoring</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-400 mt-1">✓</span>
                    <span>Natural language query processing</span>
                  </li>
                </ul>
              </div>
              
              <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6">
                <div className="text-sm text-blue-200 mb-3">Sample AI Insight</div>
                <div className="space-y-3">
                  <div className="bg-white/5 rounded p-3">
                    <div className="text-xs text-blue-200 mb-1">Query</div>
                    <div className="text-sm">"Which sites need immediate attention?"</div>
                  </div>
                  <div className="bg-white/5 rounded p-3">
                    <div className="text-xs text-blue-200 mb-1">AI Response</div>
                    <div className="text-sm">
                      3 sites showing declining DQI trends. Site 0042 requires
                      immediate query resolution. Estimated 2-day impact window.
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="text-center">
          <div className="glass-card p-12 bg-gradient-to-br from-white/90 to-white/70">
            <h2 className="text-4xl mb-4 bg-gradient-to-r from-[#3b82f6] to-[#2563eb] bg-clip-text text-transparent">
              Ready to Get Started?
            </h2>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Join hundreds of clinical sites using SAGE-Flow to maintain
              excellence in data quality and performance
            </p>
            <button
              onClick={onEnterDashboard}
              className="px-10 py-5 bg-gradient-to-r from-[#3b82f6] to-[#2563eb] text-white rounded-lg hover:shadow-[0_0_30px_rgba(37,99,235,0.5)] transition-all duration-200 text-xl group inline-flex items-center gap-3"
            >
              Launch Dashboard
              <ArrowRight className="w-6 h-6 group-hover:translate-x-2 transition-transform" />
            </button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="relative z-10 border-t border-blue-200 bg-white/50 backdrop-blur-sm py-8">
        <div className="max-w-7xl mx-auto px-8 flex justify-between items-center">
          <div className="text-sm text-gray-600">
            © 2026 Novartis. All rights reserved.
          </div>
          <div className="flex gap-6 text-sm text-gray-600">
            <a href="#" className="hover:text-gray-800 transition-colors">Privacy</a>
            <a href="#" className="hover:text-gray-800 transition-colors">Terms</a>
            <a href="#" className="hover:text-gray-800 transition-colors">Support</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
