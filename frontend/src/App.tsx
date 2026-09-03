import React from 'react';
import { TelemetryDashboard } from './components/TelemetryDashboard';
import { motion } from 'framer-motion';
import { Moon } from 'lucide-react';

function App() {
  return (
    <div className="min-h-screen bg-lunar-dark text-white p-8">
      <motion.header 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex items-center gap-3 mb-12 border-b border-slate-700 pb-6"
      >
        <Moon className="text-lunar-accent" size={32} />
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Samanvaya V2</h1>
          <p className="text-slate-400">Lunar Image Correspondence Framework</p>
        </div>
      </motion.header>

      <main className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="col-span-1 md:col-span-2">
          <TelemetryDashboard />
        </div>
        
        {/* Placeholder for Generative AI Chatbot */}
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="p-6 bg-lunar-card backdrop-blur-md rounded-2xl border border-slate-700 h-96 flex flex-col"
        >
          <h2 className="text-xl font-bold mb-4 text-lunar-accent">Lunar AI Copilot</h2>
          <div className="flex-1 border border-slate-700 rounded-lg bg-slate-900/50 p-4 mb-4">
            <p className="text-sm text-slate-400 italic">"How can I assist with your photogrammetry pipeline today?"</p>
          </div>
          <input 
            type="text" 
            placeholder="Ask about recent alignments..." 
            className="w-full bg-slate-800 border border-slate-600 rounded-lg p-3 text-white focus:outline-none focus:border-lunar-accent"
          />
        </motion.div>

        {/* Placeholder for Semantic Search */}
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          className="p-6 bg-lunar-card backdrop-blur-md rounded-2xl border border-slate-700 h-96 flex flex-col"
        >
          <h2 className="text-xl font-bold mb-4 text-lunar-accent">Vector Search</h2>
          <input 
            type="text" 
            placeholder="Search geospatial metadata (e.g. 'craters near Apollo 11')" 
            className="w-full bg-slate-800 border border-slate-600 rounded-lg p-3 text-white mb-4 focus:outline-none focus:border-lunar-accent"
          />
          <div className="flex-1 border border-slate-700 rounded-lg bg-slate-900/50 p-4 flex items-center justify-center">
            <p className="text-sm text-slate-500">Awaiting query...</p>
          </div>
        </motion.div>

      </main>
    </div>
  );
}

export default App;
