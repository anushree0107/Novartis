"use client";

import { useState, useEffect } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import {
  AlertTriangle,
  AlertCircle,
  AlertOctagon,
  Info,
  Bell,
  Sparkles,
  TrendingUp,
  Shield,
  Database,
  Settings,
  ChevronRight,
  Clock,
  User,
  Building,
  Cpu,
} from "lucide-react";
import { fetchAlerts, Alert } from "../services/api";

interface AlertsProps {
  onAiClick: (title: string, content: string) => void;
}

// Mock data for fallback
const MOCK_ALERTS: Alert[] = [
  {
    id: "1",
    title: "Critical Data Discrepancy",
    description:
      "Multiple conflicting vital signs entries detected for Subject 1034",
    severity: "critical",
    category: "data_quality",
    entity_type: "patient",
    entity_id: "Subject 1034",
    recommended_action: "Review and correct vital signs entries",
    llm_analysis: "",
  },
  {
    id: "2",
    title: "Query Overdue",
    description: "Query #2847 has exceeded response deadline by 5 days",
    severity: "high",
    category: "data_quality",
    entity_type: "site",
    entity_id: "Site 0042",
    recommended_action: "Follow up with site coordinator",
    llm_analysis: "",
  },
  {
    id: "3",
    title: "Missing Lab Results",
    description: "Expected lab results not received within protocol timeframe",
    severity: "medium",
    category: "protocol",
    entity_type: "patient",
    entity_id: "Subject 1089",
    recommended_action: "Contact lab for missing results",
    llm_analysis: "",
  },
  {
    id: "4",
    title: "Protocol Deviation",
    description: "Visit window violation detected for scheduled assessment",
    severity: "high",
    category: "protocol",
    entity_type: "patient",
    entity_id: "Subject 1156",
    recommended_action: "Document deviation and assess impact",
    llm_analysis: "",
  },
  {
    id: "5",
    title: "Data Entry Incomplete",
    description: "Required fields missing in adverse event form",
    severity: "medium",
    category: "data_quality",
    entity_type: "site",
    entity_id: "Site 0089",
    recommended_action: "Complete missing fields",
    llm_analysis: "",
  },
  {
    id: "6",
    title: "System Performance",
    description: "Slow query response times detected in production environment",
    severity: "low",
    category: "system",
    entity_type: "system",
    entity_id: "System",
    recommended_action: "Monitor system performance",
    llm_analysis: "",
  },
];

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-[#0a0f18]/95 backdrop-blur-xl border border-white/10 rounded-xl px-4 py-3 shadow-2xl">
        <p className="text-white font-semibold text-sm">{data.name}</p>
        <p className="text-gray-400 text-xs mt-1">
          {data.value} alerts ({((data.value / data.total) * 100).toFixed(0)}%)
        </p>
      </div>
    );
  }
  return null;
};

export function Alerts({ onAiClick }: AlertsProps) {
  const [alerts, setAlerts] = useState<Alert[]>(MOCK_ALERTS);
  const [loading, setLoading] = useState(true);
  const [hoveredSeverity, setHoveredSeverity] = useState<string | null>(null);

  useEffect(() => {
    const loadAlerts = async () => {
      try {
        const data = await fetchAlerts(50);
        setAlerts(data);
      } catch (err: any) {
        // Keep mock data on error
      } finally {
        setLoading(false);
      }
    };
    loadAlerts();
  }, []);

  const severityCounts = {
    total: alerts.length,
    critical: alerts.filter((a) => a.severity === "critical").length,
    high: alerts.filter((a) => a.severity === "high").length,
    medium: alerts.filter((a) => a.severity === "medium").length,
    low: alerts.filter((a) => a.severity === "low").length,
  };

  const severityData = [
    {
      name: "Critical",
      value: severityCounts.critical,
      color: "#ef4444",
      total: severityCounts.total,
    },
    {
      name: "High",
      value: severityCounts.high,
      color: "#f97316",
      total: severityCounts.total,
    },
    {
      name: "Medium",
      value: severityCounts.medium,
      color: "#eab308",
      total: severityCounts.total,
    },
    {
      name: "Low",
      value: severityCounts.low,
      color: "#22c55e",
      total: severityCounts.total,
    },
  ];

  const categoryCounts = alerts.reduce(
    (acc, a) => {
      const cat = a.category || "other";
      acc[cat] = (acc[cat] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  const categoryData = [
    {
      name: "Data Quality",
      value: categoryCounts["data_quality"] || 0,
      color: "#3b82f6",
      total: severityCounts.total,
    },
    {
      name: "Protocol",
      value: categoryCounts["protocol"] || 0,
      color: "#8b5cf6",
      total: severityCounts.total,
    },
    {
      name: "System",
      value: categoryCounts["system"] || 0,
      color: "#06b6d4",
      total: severityCounts.total,
    },
  ];

  const getSeverityConfig = (severity: string) => {
    const configs: Record<
      string,
      {
        color: string;
        bgColor: string;
        borderColor: string;
        icon: any;
        glow: string;
      }
    > = {
      critical: {
        color: "#ef4444",
        bgColor: "rgba(239, 68, 68, 0.1)",
        borderColor: "rgba(239, 68, 68, 0.3)",
        icon: AlertOctagon,
        glow: "0 0 20px rgba(239, 68, 68, 0.3)",
      },
      high: {
        color: "#f97316",
        bgColor: "rgba(249, 115, 22, 0.1)",
        borderColor: "rgba(249, 115, 22, 0.3)",
        icon: AlertTriangle,
        glow: "0 0 20px rgba(249, 115, 22, 0.3)",
      },
      medium: {
        color: "#eab308",
        bgColor: "rgba(234, 179, 8, 0.1)",
        borderColor: "rgba(234, 179, 8, 0.3)",
        icon: AlertCircle,
        glow: "0 0 20px rgba(234, 179, 8, 0.3)",
      },
      low: {
        color: "#22c55e",
        bgColor: "rgba(34, 197, 94, 0.1)",
        borderColor: "rgba(34, 197, 94, 0.3)",
        icon: Info,
        glow: "0 0 20px rgba(34, 197, 94, 0.3)",
      },
    };
    return configs[severity] || configs.low;
  };

  const getEntityIcon = (type: string) => {
    switch (type) {
      case "patient":
        return User;
      case "site":
        return Building;
      case "system":
        return Cpu;
      default:
        return Settings;
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "data_quality":
        return Database;
      case "protocol":
        return Shield;
      case "system":
        return Settings;
      default:
        return AlertCircle;
    }
  };

  return (
    <div className="space-y-8 p-1">
      {/* Header */}
      <div className="relative">
        <div className="absolute -inset-4 bg-gradient-to-r from-orange-500/10 via-red-500/10 to-amber-500/10 rounded-3xl blur-2xl" />
        <div className="relative flex items-start gap-5">
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-br from-orange-500 to-red-500 rounded-2xl blur-lg opacity-50" />
            <div className="relative w-14 h-14 bg-gradient-to-br from-orange-500 to-red-500 rounded-2xl flex items-center justify-center shadow-lg">
              <Bell className="w-7 h-7 text-white" />
            </div>
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-orange-400 via-red-400 to-amber-400 bg-clip-text text-transparent">
              Alerts & Notifications
            </h1>
            <p className="text-gray-400 mt-1 text-base">
              Monitor critical issues and system notifications in real-time
            </p>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-5 gap-4">
        {/* Total */}
        <div className="group relative">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          <div className="relative bg-[#0d1520]/80 backdrop-blur-xl rounded-2xl border border-white/10 p-5 text-center hover:border-blue-500/30 transition-all duration-300">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-xl flex items-center justify-center mx-auto mb-3">
              <TrendingUp className="w-5 h-5 text-blue-400" />
            </div>
            <div className="text-3xl font-bold text-white mb-1">
              {severityCounts.total}
            </div>
            <div className="text-xs text-gray-400 font-medium uppercase tracking-wider">
              Total Alerts
            </div>
          </div>
        </div>

        {/* Critical */}
        <div
          className="group relative cursor-pointer"
          onMouseEnter={() => setHoveredSeverity("critical")}
          onMouseLeave={() => setHoveredSeverity(null)}
        >
          <div
            className="absolute inset-0 bg-red-500/20 rounded-2xl blur-xl transition-opacity duration-300"
            style={{ opacity: hoveredSeverity === "critical" ? 1 : 0 }}
          />
          <div
            className="relative bg-[#0d1520]/80 backdrop-blur-xl rounded-2xl border border-white/10 p-5 text-center transition-all duration-300"
            style={{
              borderColor:
                hoveredSeverity === "critical"
                  ? "rgba(239, 68, 68, 0.5)"
                  : "rgba(255,255,255,0.1)",
              boxShadow:
                hoveredSeverity === "critical"
                  ? "0 0 30px rgba(239, 68, 68, 0.2)"
                  : "none",
            }}
          >
            <div className="w-10 h-10 bg-red-500/10 rounded-xl flex items-center justify-center mx-auto mb-3 border border-red-500/20">
              <AlertOctagon className="w-5 h-5 text-red-400" />
            </div>
            <div className="text-3xl font-bold text-red-400 mb-1">
              {severityCounts.critical}
            </div>
            <div className="text-xs text-gray-400 font-medium uppercase tracking-wider">
              Critical
            </div>
          </div>
        </div>

        {/* High */}
        <div
          className="group relative cursor-pointer"
          onMouseEnter={() => setHoveredSeverity("high")}
          onMouseLeave={() => setHoveredSeverity(null)}
        >
          <div
            className="absolute inset-0 bg-orange-500/20 rounded-2xl blur-xl transition-opacity duration-300"
            style={{ opacity: hoveredSeverity === "high" ? 1 : 0 }}
          />
          <div
            className="relative bg-[#0d1520]/80 backdrop-blur-xl rounded-2xl border border-white/10 p-5 text-center transition-all duration-300"
            style={{
              borderColor:
                hoveredSeverity === "high"
                  ? "rgba(249, 115, 22, 0.5)"
                  : "rgba(255,255,255,0.1)",
              boxShadow:
                hoveredSeverity === "high"
                  ? "0 0 30px rgba(249, 115, 22, 0.2)"
                  : "none",
            }}
          >
            <div className="w-10 h-10 bg-orange-500/10 rounded-xl flex items-center justify-center mx-auto mb-3 border border-orange-500/20">
              <AlertTriangle className="w-5 h-5 text-orange-400" />
            </div>
            <div className="text-3xl font-bold text-orange-400 mb-1">
              {severityCounts.high}
            </div>
            <div className="text-xs text-gray-400 font-medium uppercase tracking-wider">
              High
            </div>
          </div>
        </div>

        {/* Medium */}
        <div
          className="group relative cursor-pointer"
          onMouseEnter={() => setHoveredSeverity("medium")}
          onMouseLeave={() => setHoveredSeverity(null)}
        >
          <div
            className="absolute inset-0 bg-yellow-500/20 rounded-2xl blur-xl transition-opacity duration-300"
            style={{ opacity: hoveredSeverity === "medium" ? 1 : 0 }}
          />
          <div
            className="relative bg-[#0d1520]/80 backdrop-blur-xl rounded-2xl border border-white/10 p-5 text-center transition-all duration-300"
            style={{
              borderColor:
                hoveredSeverity === "medium"
                  ? "rgba(234, 179, 8, 0.5)"
                  : "rgba(255,255,255,0.1)",
              boxShadow:
                hoveredSeverity === "medium"
                  ? "0 0 30px rgba(234, 179, 8, 0.2)"
                  : "none",
            }}
          >
            <div className="w-10 h-10 bg-yellow-500/10 rounded-xl flex items-center justify-center mx-auto mb-3 border border-yellow-500/20">
              <AlertCircle className="w-5 h-5 text-yellow-400" />
            </div>
            <div className="text-3xl font-bold text-yellow-400 mb-1">
              {severityCounts.medium}
            </div>
            <div className="text-xs text-gray-400 font-medium uppercase tracking-wider">
              Medium
            </div>
          </div>
        </div>

        {/* Low */}
        <div
          className="group relative cursor-pointer"
          onMouseEnter={() => setHoveredSeverity("low")}
          onMouseLeave={() => setHoveredSeverity(null)}
        >
          <div
            className="absolute inset-0 bg-green-500/20 rounded-2xl blur-xl transition-opacity duration-300"
            style={{ opacity: hoveredSeverity === "low" ? 1 : 0 }}
          />
          <div
            className="relative bg-[#0d1520]/80 backdrop-blur-xl rounded-2xl border border-white/10 p-5 text-center transition-all duration-300"
            style={{
              borderColor:
                hoveredSeverity === "low"
                  ? "rgba(34, 197, 94, 0.5)"
                  : "rgba(255,255,255,0.1)",
              boxShadow:
                hoveredSeverity === "low"
                  ? "0 0 30px rgba(34, 197, 94, 0.2)"
                  : "none",
            }}
          >
            <div className="w-10 h-10 bg-green-500/10 rounded-xl flex items-center justify-center mx-auto mb-3 border border-green-500/20">
              <Info className="w-5 h-5 text-green-400" />
            </div>
            <div className="text-3xl font-bold text-green-400 mb-1">
              {severityCounts.low}
            </div>
            <div className="text-xs text-gray-400 font-medium uppercase tracking-wider">
              Low
            </div>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-2 gap-6">
        {/* Severity Distribution */}
        <div className="group relative">
          <div className="absolute inset-0 bg-gradient-to-br from-red-500/5 to-orange-500/5 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <div className="relative bg-[#0d1520]/80 backdrop-blur-xl rounded-2xl border border-white/10 p-6 hover:border-white/20 transition-all duration-300">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-gradient-to-r from-red-500 to-orange-500" />
                  Severity Distribution
                </h3>
                <p className="text-xs text-gray-500 mt-1">
                  Click segments for AI insights
                </p>
              </div>
              <div className="flex items-center gap-1 px-3 py-1.5 bg-white/5 rounded-lg">
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                <span className="text-xs text-gray-400">Interactive</span>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={severityData}
                  cx="50%"
                  cy="50%"
                  outerRadius={110}
                  innerRadius={0}
                  dataKey="value"
                  stroke="rgba(0,0,0,0.3)"
                  strokeWidth={2}
                  onClick={(data) => {
                    if (data && data.name) {
                      onAiClick(
                        `${data.name} Alerts Analysis`,
                        `**${data.name} Priority Alerts: ${data.value} total**\n\n` +
                        `**Percentage:** ${((data.value / severityCounts.total) * 100).toFixed(1)}% of all alerts\n\n` +
                        `**AI Analysis:**\n` +
                        `${data.name === "Critical"
                          ? "Critical alerts require immediate attention. These are high-impact issues that could affect data integrity or patient safety. Action within 24 hours is strongly recommended."
                          : data.name === "High"
                            ? "High priority alerts indicate significant issues that should be addressed within 48-72 hours. These may escalate to critical if not resolved promptly."
                            : data.name === "Medium"
                              ? "Medium priority alerts represent moderate issues. While not immediately urgent, they should be addressed within the week to prevent accumulation."
                              : "Low priority alerts are informational or minor issues. Address these during regular maintenance cycles to maintain optimal system health."
                        }`
                      );
                    }
                  }}
                  style={{ cursor: "pointer" }}
                >
                  {severityData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.color}
                      style={{
                        filter: "drop-shadow(0 0 8px " + entry.color + "40)",
                      }}
                    />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            {/* Legend */}
            <div className="flex justify-center gap-6 mt-4">
              {severityData.map((item) => (
                <div key={item.name} className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-xs text-gray-400">
                    {item.name} ({item.value})
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Category Distribution */}
        <div className="group relative">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <div className="relative bg-[#0d1520]/80 backdrop-blur-xl rounded-2xl border border-white/10 p-6 hover:border-white/20 transition-all duration-300">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-gradient-to-r from-blue-500 to-purple-500" />
                  Category Distribution
                </h3>
                <p className="text-xs text-gray-500 mt-1">
                  Alerts by classification type
                </p>
              </div>
              <div className="flex items-center gap-1 px-3 py-1.5 bg-white/5 rounded-lg">
                <Sparkles className="w-3.5 h-3.5 text-blue-400" />
                <span className="text-xs text-gray-400">Interactive</span>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={110}
                  dataKey="value"
                  stroke="rgba(0,0,0,0.3)"
                  strokeWidth={2}
                  onClick={(data) => {
                    if (data && data.name) {
                      onAiClick(
                        `${data.name} Category Analysis`,
                        `**${data.name} Alerts: ${data.value} total**\n\n` +
                        `**AI Analysis:**\n` +
                        `${data.name === "Data Quality"
                          ? "Data quality issues are the most common category. This typically includes missing values, inconsistencies, and validation failures. Focus on training and automated checks to reduce these."
                          : data.name === "Protocol"
                            ? "Protocol-related alerts indicate deviations from study procedures. These may include visit window violations, missed assessments, or documentation gaps."
                            : "System alerts relate to technical performance and infrastructure. Monitor these for potential impact on data collection workflows."
                        }`
                      );
                    }
                  }}
                  style={{ cursor: "pointer" }}
                >
                  {categoryData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.color}
                      style={{
                        filter: "drop-shadow(0 0 8px " + entry.color + "40)",
                      }}
                    />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            {/* Legend */}
            <div className="flex justify-center gap-6 mt-4">
              {categoryData.map((item) => (
                <div key={item.name} className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-xs text-gray-400">
                    {item.name} ({item.value})
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Section Header for Alert Cards */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-1 h-6 bg-gradient-to-b from-orange-500 to-red-500 rounded-full" />
          <h2 className="text-xl font-semibold text-white">Active Alerts</h2>
          <span className="px-2.5 py-1 bg-white/5 rounded-lg text-xs text-gray-400 font-medium">
            {alerts.length} items
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <Clock className="w-3.5 h-3.5" />
          <span>Updated just now</span>
        </div>
      </div>

      {/* Alert Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {alerts.map((alert) => {
          const config = getSeverityConfig(alert.severity);
          const SeverityIcon = config.icon;
          const EntityIcon = getEntityIcon(alert.entity_type);
          const CategoryIcon = getCategoryIcon(alert.category);

          return (
            <div key={alert.id} className="group relative">
              <div
                className="absolute inset-0 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                style={{ backgroundColor: config.bgColor }}
              />
              <div
                className="relative bg-[#0d1520]/80 backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden transition-all duration-300 hover:scale-[1.02]"
                style={{
                  borderLeftWidth: "4px",
                  borderLeftColor: config.color,
                }}
              >
                {/* Card Header */}
                <div className="p-5 pb-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3 flex-1">
                      <div
                        className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                        style={{
                          backgroundColor: config.bgColor,
                          border: `1px solid ${config.borderColor}`,
                        }}
                      >
                        <SeverityIcon
                          className="w-5 h-5"
                          style={{ color: config.color }}
                        />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-white font-semibold text-base leading-tight">
                          {alert.title}
                        </h4>
                        <p className="text-gray-400 text-sm mt-1.5 leading-relaxed line-clamp-2">
                          {alert.description}
                        </p>
                      </div>
                    </div>
                    <span
                      className="px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wide shrink-0"
                      style={{
                        backgroundColor: config.bgColor,
                        color: config.color,
                        border: `1px solid ${config.borderColor}`,
                      }}
                    >
                      {alert.severity}
                    </span>
                  </div>
                </div>

                {/* Card Meta */}
                <div className="px-5 py-3 bg-white/[0.02] border-t border-white/5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-1.5 text-gray-500">
                        <EntityIcon className="w-3.5 h-3.5" />
                        <span className="text-xs font-medium">
                          {alert.entity_id}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5 text-gray-500">
                        <CategoryIcon className="w-3.5 h-3.5" />
                        <span className="text-xs">
                          {alert.category?.replace("_", " ")}
                        </span>
                      </div>
                    </div>
                    <span className="px-2 py-1 bg-white/5 rounded text-xs text-gray-500 capitalize">
                      {alert.entity_type}
                    </span>
                  </div>
                </div>

                {/* Card Action */}
                <div className="px-5 py-4 border-t border-white/5">
                  <button
                    onClick={() =>
                      onAiClick(
                        `Alert Analysis: ${alert.title}`,
                        `Detailed analysis of ${alert.title}:\n\n**Alert Summary:**\n${alert.description}\n\n**Severity:** ${alert.severity.toUpperCase()}\n**Entity:** ${alert.entity_id}\n**Category:** ${alert.category}\n\n**Root Cause Analysis:**\nThis alert was triggered due to automated quality checks detecting an anomaly in the data submission pattern.\n\n**Recommended Actions:**\n${alert.recommended_action || "1. Review the source documentation\n2. Contact the site coordinator\n3. Update or correct the data entry within 24 hours"}`
                      )
                    }
                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-violet-500/10 to-purple-500/10 hover:from-violet-500/20 hover:to-purple-500/20 border border-violet-500/20 hover:border-violet-500/40 rounded-xl text-violet-300 text-sm font-medium transition-all duration-200 group/btn"
                  >
                    <Sparkles className="w-4 h-4 group-hover/btn:animate-pulse" />
                    <span>AI Analysis</span>
                    <ChevronRight className="w-4 h-4 opacity-0 -ml-2 group-hover/btn:opacity-100 group-hover/btn:ml-0 transition-all duration-200" />
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}