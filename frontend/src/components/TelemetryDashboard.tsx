import React from 'react';
import { motion } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { ShieldAlert, ShieldCheck } from 'lucide-react';

const mockData = [
  { name: 'Align 1', rmse: 0.35, anomaly: false },
  { name: 'Align 2', rmse: 0.28, anomaly: false },
  { name: 'Align 3', rmse: 2.50, anomaly: true },
];

export const TelemetryDashboard: React.FC = () => {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="p-6 bg-[#1e293b]/80 backdrop-blur-md rounded-2xl border border-slate-700 shadow-2xl text-white"
    >
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-sky-400">ML Anomaly Detection</h2>
        <div className="flex items-center gap-2 text-sm text-green-400 bg-green-400/10 px-3 py-1 rounded-full">
          <ShieldCheck size={16} /> Zero-Trust Active
        </div>
      </div>
      
      <div className="h-64 w-full mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={mockData}>
            <XAxis dataKey="name" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none' }} />
            <Line type="monotone" dataKey="rmse" stroke="#38bdf8" strokeWidth={3} dot={{ r: 6 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="space-y-3">
        {mockData.map((item, idx) => (
          <motion.div 
            key={idx}
            whileHover={{ scale: 1.02 }}
            className={`p-4 rounded-lg flex items-center justify-between ${
              item.anomaly ? 'bg-red-500/20 border-red-500/50' : 'bg-slate-800/50 border-slate-700'
            } border`}
          >
            <span className="font-medium">{item.name} (RMSE: {item.rmse})</span>
            {item.anomaly ? <ShieldAlert className="text-red-400" /> : <ShieldCheck className="text-green-400" />}
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};
