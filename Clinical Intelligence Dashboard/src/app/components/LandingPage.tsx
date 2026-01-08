import { ArrowRight, BarChart3, Activity, Bell, Zap, Shield, TrendingUp, Brain, Cpu } from 'lucide-react';

interface LandingPageProps {
  onEnterDashboard: () => void;
}

export function LandingPage({ onEnterDashboard }: LandingPageProps) {
  const stats = [
    { value: '50K+', label: 'Data Points Analyzed', icon: <BarChart3 className="w-5 h-5" /> },
    { value: '99.9%', label: 'Accuracy Rate', icon: <Shield className="w-5 h-5" /> },
    { value: '500+', label: 'Sites Monitored', icon: <TrendingUp className="w-5 h-5" /> },
    { value: '24/7', label: 'AI Support', icon: <Brain className="w-5 h-5" /> },
  ];

  const agents = [
    { icon: <BarChart3 className="w-6 h-6" />, title: 'DQI Agent', desc: 'Data Quality Index monitoring', gradient: 'from-blue-500 to-cyan-400' },
    { icon: <Activity className="w-6 h-6" />, title: 'Analytics Agent', desc: 'Performance benchmarking', gradient: 'from-violet-500 to-purple-400' },
    { icon: <Bell className="w-6 h-6" />, title: 'Alert Agent', desc: 'Smart notifications', gradient: 'from-orange-500 to-amber-400' },
    { icon: <Zap className="w-6 h-6" />, title: 'Action Agent', desc: 'Automated operations', gradient: 'from-emerald-500 to-teal-400' },
  ];

  return (
    <div className="h-screen w-screen overflow-hidden bg-gradient-to-b from-[#0f1419] via-[#0a0f14] to-[#0f1419] text-white font-['Inter',sans-serif] flex flex-col">
      {/* Gradient overlay at top */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-0 right-0 h-[400px] bg-gradient-to-b from-emerald-900/30 via-blue-900/20 to-transparent" />
        <div className="absolute top-20 left-1/4 w-[500px] h-[300px] bg-gradient-to-r from-emerald-500/10 to-blue-500/10 blur-[100px] rounded-full" />
        <div className="absolute top-10 right-1/4 w-[400px] h-[250px] bg-gradient-to-r from-blue-500/10 to-purple-500/10 blur-[80px] rounded-full" />
      </div>

      {/* Navigation */}
      <nav className="relative z-10 px-8 py-4 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
            <Cpu className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">TrialPulse</h1>
            <p className="text-[10px] text-gray-400">Clinical Intelligence Platform</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors">
            Sign In
          </button>
          <button
            onClick={onEnterDashboard}
            className="px-5 py-2 bg-gradient-to-r from-emerald-500 to-teal-500 text-white text-sm font-medium rounded-lg hover:shadow-lg hover:shadow-emerald-500/30 transition-all"
          >
            Get Started
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <div className="flex-1 relative z-10 flex flex-col items-center justify-center px-8">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-white/5 border border-white/10 rounded-full text-sm text-emerald-400 mb-6">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          Powered by Advanced AI Technology
        </div>

        {/* Main Heading */}
        <h1 className="text-5xl md:text-6xl font-bold text-center mb-4 leading-tight max-w-4xl">
          <span className="text-white">Precision Retrieval & AI for</span>
          <br />
          <span className="bg-gradient-to-r from-emerald-400 via-teal-400 to-cyan-400 bg-clip-text text-transparent">
            Clinical Intelligence
          </span>
        </h1>

        {/* Subtitle */}
        <p className="text-lg text-gray-400 text-center max-w-2xl mb-8 leading-relaxed">
          Transform your clinical trials with AI agents that provide real-time insights,
          predictions, and recommendations for smarter data decisions.
        </p>

        {/* CTA Buttons */}
        <div className="flex gap-4 mb-12">
          <button
            onClick={onEnterDashboard}
            className="group px-8 py-3 bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-medium rounded-lg hover:shadow-xl hover:shadow-emerald-500/30 transition-all flex items-center gap-2"
          >
            Start Your Journey
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>
          <button
            onClick={onEnterDashboard}
            className="px-8 py-3 bg-white/5 border border-white/20 text-white font-medium rounded-lg hover:bg-white/10 transition-all"
          >
            Sign In
          </button>
        </div>

        {/* Stats Row */}
        <div className="flex gap-8 mb-12">
          {stats.map((stat, idx) => (
            <div key={idx} className="flex flex-col items-center px-6">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500/20 to-teal-500/20 flex items-center justify-center text-emerald-400 mb-2">
                {stat.icon}
              </div>
              <div className="text-2xl font-bold text-white">{stat.value}</div>
              <div className="text-xs text-gray-500">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Agents Section */}
        <div className="w-full max-w-4xl">
          <h2 className="text-xl font-semibold text-center text-white mb-2">
            Meet Your AI Clinical Assistants
          </h2>
          <p className="text-sm text-gray-500 text-center mb-6">
            Four specialized AI agents working together to revolutionize your clinical experience
          </p>

          <div className="grid grid-cols-4 gap-4">
            {agents.map((agent, idx) => (
              <div
                key={idx}
                className="group p-4 bg-white/5 border border-white/10 rounded-xl hover:border-emerald-500/50 hover:bg-white/[0.07] transition-all cursor-pointer"
              >
                <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${agent.gradient} flex items-center justify-center mb-3 group-hover:scale-110 transition-transform`}>
                  {agent.icon}
                </div>
                <h3 className="font-medium text-white text-sm mb-1">{agent.title}</h3>
                <p className="text-xs text-gray-500">{agent.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom indicator */}
      <div className="relative z-10 flex justify-center pb-6">
        <div className="flex gap-2">
          {[0, 1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className={`w-2 h-2 rounded-full transition-colors ${i === 1 ? 'bg-white' : 'bg-white/30'}`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
