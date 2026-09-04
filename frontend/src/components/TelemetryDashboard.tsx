import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Area, AreaChart } from 'recharts';
import { ShieldAlert, ShieldCheck, Activity, RefreshCw, Cpu, HardDrive, Zap, Server } from 'lucide-react';

export const TelemetryDashboard: React.FC = () => {
  const [data, setData] = useState([
    { name: 'Align 1', rmse: 0.35, anomaly: false, conf: 98, latency: 182 },
    { name: 'Align 2', rmse: 0.28, anomaly: false, conf: 99, latency: 174 },
    { name: 'Align 3', rmse: 2.50, anomaly: true, conf: 45, latency: 412 },
    { name: 'Align 4', rmse: 0.41, anomaly: false, conf: 95, latency: 189 },
    { name: 'Align 5', rmse: 0.32, anomaly: false, conf: 97, latency: 180 },
    { name: 'Align 6', rmse: 0.34, anomaly: false, conf: 98, latency: 178 },
  ]);

  const [isRefreshing, setIsRefreshing] = useState(false);

  const simulateNewTelemetry = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setData((prev) => {
        const newData = [...prev.slice(1)];
        const isAnomaly = Math.random() > 0.85;
        const currentIdx = parseInt(prev[prev.length - 1].name.split(' ')[1], 10) + 1;
        newData.push({
          name: `Align ${currentIdx}`,
          rmse: isAnomaly ? +(Math.random() * 2.5 + 1.2).toFixed(2) : +(Math.random() * 0.2 + 0.22).toFixed(2),
          anomaly: isAnomaly,
          conf: isAnomaly ? Math.floor(Math.random() * 30 + 40) : Math.floor(Math.random() * 8 + 92),
          latency: isAnomaly ? Math.floor(Math.random() * 200 + 350) : Math.floor(Math.random() * 40 + 160),
        });
        return newData;
      });
      setIsRefreshing(false);
    }, 500);
  };

  useEffect(() => {
    const interval = setInterval(simulateNewTelemetry, 4500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      {/* 1. RESOURCE GAUGES BAR */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="pro-card p-3.5 space-y-1">
          <div className="flex items-center justify-between text-[10px] font-mono text-zinc-400 uppercase">
            <span className="flex items-center gap-1.5">
              <Cpu size={12} className="text-cyan-400" /> Pipeline CPU
            </span>
            <span className="text-cyan-300 font-bold">18.4%</span>
          </div>
          <div className="text-lg font-black font-mono text-white">4 Cores Active</div>
          <div className="w-full bg-zinc-950 rounded-full h-1.5 overflow-hidden border border-white/[0.06]">
            <div className="bg-cyan-400 h-full rounded-full" style={{ width: '18.4%' }} />
          </div>
        </div>

        <div className="pro-card p-3.5 space-y-1">
          <div className="flex items-center justify-between text-[10px] font-mono text-zinc-400 uppercase">
            <span className="flex items-center gap-1.5">
              <HardDrive size={12} className="text-emerald-400" /> Heap Ceiling
            </span>
            <span className="text-emerald-300 font-bold">45.0%</span>
          </div>
          <div className="text-lg font-black font-mono text-white">1,842 / 4,096 MiB</div>
          <div className="w-full bg-zinc-950 rounded-full h-1.5 overflow-hidden border border-white/[0.06]">
            <div className="bg-emerald-400 h-full rounded-full" style={{ width: '45%' }} />
          </div>
        </div>

        <div className="pro-card p-3.5 space-y-1">
          <div className="flex items-center justify-between text-[10px] font-mono text-zinc-400 uppercase">
            <span className="flex items-center gap-1.5">
              <Zap size={12} className="text-purple-400" /> Kornia CUDA
            </span>
            <span className="text-purple-300 font-bold">ACTIVE</span>
          </div>
          <div className="text-lg font-black font-mono text-white">178 ms Latency</div>
          <div className="w-full bg-zinc-950 rounded-full h-1.5 overflow-hidden border border-white/[0.06]">
            <div className="bg-purple-400 h-full rounded-full" style={{ width: '85%' }} />
          </div>
        </div>

        <div className="pro-card p-3.5 space-y-1">
          <div className="flex items-center justify-between text-[10px] font-mono text-zinc-400 uppercase">
            <span className="flex items-center gap-1.5">
              <Server size={12} className="text-amber-400" /> IsolationForest
            </span>
            <span className="text-emerald-400 font-bold">NOMINAL</span>
          </div>
          <div className="text-lg font-black font-mono text-white">99.2% Healthy</div>
          <div className="w-full bg-zinc-950 rounded-full h-1.5 overflow-hidden border border-white/[0.06]">
            <div className="bg-emerald-400 h-full rounded-full" style={{ width: '99.2%' }} />
          </div>
        </div>
      </div>

      {/* 2. REAL-TIME RMSE & LATENCY TELEMETRY CHART */}
      <div className="pro-card p-5 md:p-6 space-y-4">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-white/[0.08] pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-cyan-500/10 rounded-xl border border-cyan-500/30 text-cyan-400">
              <Activity size={20} />
            </div>
            <div>
              <h3 className="text-sm md:text-base font-bold text-white font-mono uppercase tracking-wider">
                Real-Time RMSE &amp; Outlier Drift Spectrum
              </h3>
              <p className="text-[11px] text-zinc-400 font-sans">
                Continuous unsupervised anomaly scoring from Python ML service (:8001) via Scikit-Learn IsolationForest.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={simulateNewTelemetry}
              className="pro-btn-secondary px-3 py-1.5 rounded-xl text-xs flex items-center gap-1.5 cursor-pointer"
            >
              <RefreshCw size={13} className={isRefreshing ? 'animate-spin' : ''} />
              <span>Poll Microservice</span>
            </button>
            <div className="flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-950/60 border border-emerald-500/30 px-3 py-1.5 rounded-xl font-mono">
              <ShieldCheck size={14} /> Zero-Trust Verified
            </div>
          </div>
        </div>

        {/* RECHARTS AREA CHART */}
        <div className="h-64 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorRmse" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00f0ff" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#00f0ff" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
              <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 11, fontFamily: 'JetBrains Mono' }} tickLine={false} axisLine={false} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11, fontFamily: 'JetBrains Mono' }} tickLine={false} axisLine={false} domain={[0, 3.0]} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(3, 7, 18, 0.95)',
                  border: '1px solid rgba(0, 240, 255, 0.3)',
                  borderRadius: '12px',
                  boxShadow: '0 8px 30px rgba(0,0,0,0.8)',
                  fontFamily: 'JetBrains Mono',
                  fontSize: '11px',
                  color: '#fff',
                }}
                itemStyle={{ color: '#00f0ff' }}
              />
              <Area
                type="monotone"
                dataKey="rmse"
                stroke="#00f0ff"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#colorRmse)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* LIVE NODES CARD GRID */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3 pt-2">
          {data.map((item) => (
            <motion.div
              key={item.name}
              initial={{ opacity: 0, scale: 0.94 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.2 }}
              className={`p-3 rounded-xl border transition-all ${
                item.anomaly
                  ? 'bg-rose-950/40 border-rose-500/60 shadow-[0_0_15px_rgba(244,63,94,0.2)]'
                  : 'bg-zinc-950/60 border-white/[0.06] hover:border-white/[0.15]'
              }`}
            >
              <div className="flex justify-between items-start mb-1 text-[10px] font-mono text-zinc-400">
                <span>{item.name}</span>
                {item.anomaly ? (
                  <ShieldAlert size={14} className="text-rose-400" />
                ) : (
                  <ShieldCheck size={14} className="text-emerald-400" />
                )}
              </div>

              <div className="text-base font-black font-mono flex items-baseline gap-1">
                <span className={item.anomaly ? 'text-rose-400' : 'text-cyan-300'}>{item.rmse}</span>
                <span className="text-[9px] font-normal text-zinc-500">px</span>
              </div>

              <div className="text-[10px] font-mono text-zinc-500 flex items-center justify-between pt-1">
                <span>{item.latency}ms</span>
                <span className={item.conf < 80 ? 'text-rose-400' : 'text-emerald-400'}>{item.conf}%</span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};
