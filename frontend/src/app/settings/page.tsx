"use client";

import { Settings, Cpu, Database, Key, Globe } from "lucide-react";

export default function SettingsPage() {
  const items = [
    {
      icon: <Cpu className="w-5 h-5 text-amd-red" />,
      label: "LLM Model",
      value: "DeepSeek-R1-Distill-Qwen-32B",
      sub: "AMD MI300X · vLLM",
    },
    {
      icon: <Globe className="w-5 h-5 text-amd-red" />,
      label: "vLLM Endpoint",
      value: "165.245.138.52:8000",
      sub: "DigitalOcean · Oregon",
    },
    {
      icon: <Database className="w-5 h-5 text-accent-success" />,
      label: "Database",
      value: "Supabase PostgreSQL",
      sub: process.env.NEXT_PUBLIC_SUPABASE_URL?.replace("https://", "") ?? "connected",
    },
    {
      icon: <Key className="w-5 h-5 text-amd-gray-400" />,
      label: "API Authentication",
      value: "X-API-Key",
      sub: "Header-based · SHA-256",
    },
  ];

  return (
    <div className="p-10 space-y-8">
      <div className="flex items-center gap-4">
        <Settings className="w-6 h-6 text-amd-red" />
        <div>
          <h2 className="text-2xl font-black tracking-tighter uppercase text-white">
            System <span className="text-amd-red">Configuration</span>
          </h2>
          <p className="text-xs font-mono text-amd-gray-500 uppercase tracking-widest mt-1">
            System_Config — ATLAS v1.0 · AMD Edition
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {items.map((item) => (
          <div
            key={item.label}
            className="bg-amd-gray-900 border border-amd-gray-800 rounded-lg p-6 flex items-start gap-4"
          >
            <div className="w-10 h-10 bg-amd-gray-800 rounded flex items-center justify-center shrink-0">
              {item.icon}
            </div>
            <div>
              <p className="text-[10px] font-mono text-amd-gray-500 uppercase tracking-widest">{item.label}</p>
              <p className="text-sm font-bold text-white mt-1">{item.value}</p>
              <p className="text-[10px] font-mono text-amd-gray-600 mt-0.5">{item.sub}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-amd-gray-900 border border-amd-gray-800 rounded-lg p-6">
        <p className="text-xs font-mono text-amd-gray-500 uppercase tracking-widest mb-4">Pipeline_Version</p>
        <div className="grid grid-cols-4 gap-4">
          {["Vision Agent", "Reasoning Agent", "Validator Agent", "Explainer Agent"].map((agent) => (
            <div key={agent} className="text-center space-y-2">
              <div className="w-2 h-2 bg-accent-success rounded-full mx-auto animate-pulse" />
              <p className="text-[10px] font-mono text-white uppercase">{agent.replace(" ", "_")}</p>
              <p className="text-[9px] font-mono text-amd-gray-600">v1.0.0 · ACTIVE</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
