"use client";

import { motion } from "motion/react";
import {
    Brain,
    BarChart3,
    Swords,
    Dna,
    ArrowRight,
    Sparkles,
    Activity,
    Database,
    Shield,
} from "lucide-react";

interface LandingPageProps {
    onEnterDashboard: () => void;
}

export function LandingPage({ onEnterDashboard }: LandingPageProps) {
    const stats = [
        { value: "424K+", label: "Graph Nodes", icon: Database },
        { value: "24", label: "Active Studies", icon: Activity },
        { value: "1,606", label: "Sites", icon: Shield },
    ];

    const features = [
        {
            icon: Brain,
            title: "AI-Powered",
            desc: "SAGE-Code Engine",
            gradient: "from-cyan-400 to-blue-500",
        },
        {
            icon: BarChart3,
            title: "DQI Scoring",
            desc: "Data Quality",
            gradient: "from-emerald-400 to-teal-500",
        },
        {
            icon: Swords,
            title: "Debate Council",
            desc: "Multi-Agent AI",
            gradient: "from-amber-400 to-orange-500",
        },
        {
            icon: Dna,
            title: "Digital Twin",
            desc: "Site Simulation",
            gradient: "from-pink-400 to-rose-500",
        },
    ];

    return (
        <div className="min-h-screen w-full relative overflow-hidden flex flex-col bg-[#030712]">
            {/* Animated background gradient orbs */}
            <div className="absolute inset-0 overflow-hidden">
                <motion.div
                    animate={{
                        scale: [1, 1.2, 1],
                        opacity: [0.3, 0.5, 0.3],
                    }}
                    transition={{
                        duration: 8,
                        repeat: Infinity,
                        ease: "easeInOut",
                    }}
                    className="absolute top-1/4 left-1/4 w-[600px] h-[600px] bg-cyan-500/20 rounded-full blur-[120px]"
                />
                <motion.div
                    animate={{
                        scale: [1.2, 1, 1.2],
                        opacity: [0.2, 0.4, 0.2],
                    }}
                    transition={{
                        duration: 10,
                        repeat: Infinity,
                        ease: "easeInOut",
                    }}
                    className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-blue-600/20 rounded-full blur-[100px]"
                />
                <motion.div
                    animate={{
                        scale: [1, 1.3, 1],
                        opacity: [0.15, 0.3, 0.15],
                    }}
                    transition={{
                        duration: 12,
                        repeat: Infinity,
                        ease: "easeInOut",
                    }}
                    className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-teal-500/15 rounded-full blur-[150px]"
                />
            </div>

            {/* Subtle grid pattern */}
            <div
                className="absolute inset-0 opacity-[0.02]"
                style={{
                    backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
                    backgroundSize: "60px 60px",
                }}
            />

            {/* Floating particles */}
            {[...Array(20)].map((_, i) => (
                <motion.div
                    key={i}
                    className="absolute w-1 h-1 bg-cyan-400/40 rounded-full"
                    style={{
                        left: `${Math.random() * 100}%`,
                        top: `${Math.random() * 100}%`,
                    }}
                    animate={{
                        y: [0, -30, 0],
                        opacity: [0.2, 0.8, 0.2],
                    }}
                    transition={{
                        duration: 3 + Math.random() * 2,
                        repeat: Infinity,
                        delay: Math.random() * 2,
                        ease: "easeInOut",
                    }}
                />
            ))}

            {/* Header */}
            <motion.header
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="relative z-10 flex items-center justify-between px-8 py-6"
            >
                <div className="flex items-center gap-3">
                    <img
                        src="/trialpulse-logo.png"
                        alt="TrialPulse Logo"
                        className="w-12 h-12 object-contain"
                    />
                    <span className="text-xl font-semibold text-white tracking-tight">
                        TrialPulse
                    </span>
                </div>
                <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={onEnterDashboard}
                    className="px-5 py-2.5 text-sm font-medium text-white bg-white/5 border border-white/10 rounded-full hover:bg-white/10 hover:border-white/20 transition-all duration-300"
                >
                    Sign In
                </motion.button>
            </motion.header>

            {/* Main Content */}
            <main className="flex-1 flex flex-col items-center justify-center relative z-10 px-4 sm:px-8 py-8">
                {/* Badge */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1, duration: 0.5 }}
                    className="mb-6"
                >
                    <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-sm font-medium">
                        <Sparkles className="w-4 h-4" />
                        Clinical Intelligence Platform
                    </span>
                </motion.div>

                {/* Title */}
                <motion.h1
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2, duration: 0.6 }}
                    className="text-5xl md:text-7xl lg:text-8xl font-bold text-center mb-6 tracking-tight"
                >
                    <span className="text-white">Trial</span>
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-400 to-teal-400">
                        Pulse
                    </span>
                </motion.h1>

                {/* Subtitle */}
                <motion.p
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3, duration: 0.6 }}
                    className="text-lg md:text-xl text-gray-400 text-center max-w-2xl mb-12 leading-relaxed"
                >
                    Accelerate clinical trials with AI-powered intelligence.
                    <br className="hidden md:block" />
                    <span className="text-gray-500">
                        Transform data into actionable insights.
                    </span>
                </motion.p>

                {/* Stats */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4, duration: 0.6 }}
                    className="flex flex-wrap justify-center gap-6 mb-12"
                >
                    {stats.map((stat, index) => (
                        <motion.div
                            key={index}
                            whileHover={{ scale: 1.05, y: -5 }}
                            className="group relative"
                        >
                            <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                            <div className="relative flex flex-col items-center px-8 py-6 rounded-2xl bg-white/[0.02] border border-white/[0.05] hover:border-cyan-500/30 transition-all duration-300 min-w-[140px]">
                                <stat.icon className="w-5 h-5 text-cyan-400/60 mb-2" />
                                <span className="text-3xl md:text-4xl font-bold text-white mb-1">
                                    {stat.value}
                                </span>
                                <span className="text-xs text-gray-500 uppercase tracking-wider">
                                    {stat.label}
                                </span>
                            </div>
                        </motion.div>
                    ))}
                </motion.div>

                {/* CTA Button */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5, duration: 0.5 }}
                    className="flex flex-col sm:flex-row items-center gap-4 mt-8"
                >
                    <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={onEnterDashboard}
                        className="group relative px-8 py-4 bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-semibold text-lg rounded-full overflow-hidden transition-all duration-300 shadow-[0_0_40px_rgba(6,182,212,0.3)]"
                    >
                        <span className="relative z-10 flex items-center gap-2">
                            Enter Dashboard
                            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                        </span>
                        <div className="absolute inset-0 bg-gradient-to-r from-cyan-400 to-blue-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                    </motion.button>
                    <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        className="px-8 py-4 text-gray-300 font-medium text-lg hover:text-white transition-colors duration-300"
                    >
                        Learn More
                    </motion.button>
                </motion.div>
            </main>

            {/* Feature Cards */}
            <motion.section
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6, duration: 0.6 }}
                className="relative z-10 w-full px-4 sm:px-8 py-8 mt-auto"
            >
                <div className="flex flex-col sm:flex-row justify-between gap-4 sm:gap-6 w-full">
                    {features.map((feature, index) => (
                        <motion.div
                            key={index}
                            whileHover={{ y: -8, scale: 1.02 }}
                            transition={{ type: "spring", stiffness: 300, damping: 20 }}
                            className="group relative cursor-pointer flex-1"
                        >
                            {/* Hover glow effect */}
                            <div
                                className={`absolute inset-0 bg-gradient-to-r ${feature.gradient} rounded-2xl blur-xl opacity-0 group-hover:opacity-20 transition-opacity duration-500`}
                            />

                            <div className="relative p-6 rounded-2xl bg-white/[0.02] border border-white/[0.05] hover:border-white/[0.15] backdrop-blur-sm transition-all duration-300 h-full">
                                {/* Icon container */}
                                <div
                                    className={`w-12 h-12 rounded-xl bg-gradient-to-r ${feature.gradient} flex items-center justify-center mb-4 shadow-lg`}
                                >
                                    <feature.icon className="w-6 h-6 text-white" />
                                </div>

                                <h3 className="text-lg font-semibold text-white mb-1">
                                    {feature.title}
                                </h3>
                                <p className="text-sm text-gray-500">{feature.desc}</p>

                                {/* Subtle arrow indicator */}
                                <div className="absolute bottom-6 right-6 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                                    <ArrowRight className="w-4 h-4 text-gray-500" />
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </motion.section>


        </div>
    );
}
