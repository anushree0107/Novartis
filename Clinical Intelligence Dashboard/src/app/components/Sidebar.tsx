"use client";
import { cn } from "../../lib/utils";

import {
  LayoutDashboard,
  Activity,
  BarChart3,
  LineChart,
  Box,
  Layers,
  MessageSquare,
  AlertTriangle,
  Zap,
  FileText,
  Search,
  Bot,
  ChevronRight,
  Sparkles,
} from "lucide-react";

const navigationGroups = [
  {
    label: "Overview",
    items: [
      { id: "executive", name: "Executive Dashboard", icon: LayoutDashboard },
      { id: "site-health", name: "Site Health", icon: Activity },
      { id: "dqi", name: "DQI Scores", icon: BarChart3 },
      { id: "analytics", name: "Analytics", icon: LineChart },
    ],
  },
  {
    label: "Intelligence",
    items: [
      { id: "simulator", name: "Digital Twin", icon: Box },
      { id: "clustering", name: "3D Clusters", icon: Layers },
      { id: "debate", name: "Debate Council", icon: MessageSquare },
    ],
  },
  {
    label: "Operations",
    items: [
      { id: "alerts", name: "Alerts", icon: AlertTriangle, badge: 3 },
      { id: "actions", name: "Actions", icon: Zap },
      { id: "reports", name: "Reports", icon: FileText },
    ],
  },
  {
    label: "Tools",
    items: [
      { id: "query", name: "Query", icon: Search },
      { id: "chat", name: "AI Chat", icon: Bot, isNew: true },
    ],
  },
];

interface SidebarProps {
  activeSection: string;
  onSectionChange: (section: string) => void;
}

export function Sidebar({ activeSection, onSectionChange }: SidebarProps) {
  return (
    <aside className="flex h-screen w-64 flex-col bg-gradient-to-b from-[#0a0f1a] to-[#0d1420] shrink-0 border-r border-white/5">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-6">
        <div className="relative">
          <img
            src="/trialpulse-logo.png"
            alt="TrialPulse Logo"
            className="h-16 w-16 object-cover"
          />
          <div className="absolute bottom-0 right-0 h-3.5 w-3.5 rounded-full border-2 border-[#0a0f1a] bg-emerald-400" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-white tracking-tight">
            TrialPulse
          </h1>
          <p className="text-[11px] text-slate-400 font-medium">
            Clinical Intelligence Platform
          </p>
        </div>
      </div>

      {/* Divider */}
      <div className="mx-4 h-px bg-gradient-to-r from-transparent via-slate-700/50 to-transparent" />

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {navigationGroups.map((group) => (
          <div key={group.label}>
            <h2 className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
              {group.label}
            </h2>
            <div className="space-y-1">
              {group.items.map((item) => {
                const isActive = activeSection === item.id;
                const Icon = item.icon;

                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => onSectionChange(item.id)}
                    className={cn(
                      "group relative flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200 text-left",
                      isActive
                        ? "bg-gradient-to-r from-cyan-500/15 to-blue-500/10 text-cyan-400 shadow-sm"
                        : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
                    )}
                  >
                    {/* Active indicator bar */}
                    {isActive && (
                      <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-gradient-to-b from-cyan-400 to-blue-500 rounded-r-full" />
                    )}

                    <div
                      className={cn(
                        "flex h-8 w-8 items-center justify-center rounded-lg transition-all duration-200",
                        isActive
                          ? "bg-cyan-500/20 text-cyan-400"
                          : "bg-slate-800/50 text-slate-400 group-hover:bg-slate-700/50 group-hover:text-slate-300"
                      )}
                    >
                      <Icon className="h-4 w-4" />
                    </div>

                    <span className="flex-1">{item.name}</span>

                    {/* Badge for alerts */}
                    {"badge" in item && item.badge && (
                      <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500/20 px-1.5 text-[10px] font-semibold text-red-400">
                        {item.badge}
                      </span>
                    )}

                    {/* New badge */}
                    {"isNew" in item && item.isNew && (
                      <span className="flex items-center gap-1 rounded-full bg-gradient-to-r from-violet-500/20 to-fuchsia-500/20 px-2 py-0.5 text-[10px] font-semibold text-violet-400">
                        <Sparkles className="h-2.5 w-2.5" />
                        New
                      </span>
                    )}

                    {/* Hover arrow */}
                    <ChevronRight
                      className={cn(
                        "h-4 w-4 transition-all duration-200",
                        isActive
                          ? "opacity-100 text-cyan-400"
                          : "opacity-0 -translate-x-2 group-hover:opacity-50 group-hover:translate-x-0"
                      )}
                    />
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Status Footer */}
      <div className="mx-4 h-px bg-gradient-to-r from-transparent via-slate-700/50 to-transparent" />
      <div className="p-4">
        <div className="flex items-center justify-between rounded-lg bg-slate-800/30 px-3 py-2.5">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500" />
            </span>
            <span className="text-xs font-medium text-slate-300">
              API Connected
            </span>
          </div>
          <span className="text-[10px] text-slate-500">v2.4.1</span>
        </div>
      </div>
    </aside>
  );
}