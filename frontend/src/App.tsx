import React, { useState } from 'react';
import { TelemetryDashboard } from './components/TelemetryDashboard';
import { motion, AnimatePresence } from 'framer-motion';
import { Moon, Send, Search, Sparkles, Map, Database } from 'lucide-react';

function App() {
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState([
    { role: 'ai', text: 'Hello! I am your Lunar AI Copilot. I can analyze crater topologies, explain telemetry anomalies, or generate photogrammetry reports. What would you like to do?' }
  ]);
  const [isTyping, setIsTyping] = useState(false);

  const [searchInput, setSearchInput] = useState('');
  const [searchResults, setSearchResults] = useState<{title: string, match: number}[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleChatSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    
    setChatHistory(prev => [...prev, { role: 'user', text: chatInput }]);
    setChatInput('');
    setIsTyping(true);

    setTimeout(() => {
      setChatHistory(prev => [...prev, { 
        role: 'ai', 
        text: 'I am analyzing the latest MERN telemetry data. The pipeline is running smoothly, though I detected a minor RMSE spike during the last alignment phase due to shadowing in the Tycho crater region.' 
      }]);
      setIsTyping(false);
    }, 1500);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchInput.trim()) return;
    
    setIsSearching(true);
    setTimeout(() => {
      setSearchResults([
        { title: 'Apollo 11 Landing Site (Mare Tranquillitatis)', match: 98 },
        { title: 'Tycho Crater Shadow Topography', match: 85 },
        { title: 'Copernicus Crater Edge Alignment', match: 72 },
      ]);
      setIsSearching(false);
    }, 800);
  };

  return (
    <div className="min-h-screen bg-lunar-dark text-white p-4 md:p-8 font-sans selection:bg-sky-500/30">
      <motion.header 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-4 mb-8 border-b border-slate-700/50 pb-6"
      >
        <div className="bg-lunar-accent/20 p-3 rounded-xl border border-lunar-accent/30 shadow-[0_0_15px_rgba(56,189,248,0.2)]">
          <Moon className="text-lunar-accent" size={32} />
        </div>
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">Samanvaya V2</h1>
          <p className="text-slate-400 text-sm md:text-base">Hyperscale Lunar Image Correspondence Framework</p>
        </div>
      </motion.header>

      <main className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* Top Full Width: Dashboard */}
        <div className="col-span-1 md:col-span-2">
          <div className="mb-2">
            <h2 className="text-xl font-semibold flex items-center gap-2"><Database size={20} className="text-sky-400"/> System Telemetry</h2>
            <p className="text-slate-400 text-sm">Real-time pipeline monitoring and zero-trust anomaly detection.</p>
          </div>
          <TelemetryDashboard />
        </div>
        
        {/* Left Column: AI Copilot */}
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="p-6 bg-lunar-card backdrop-blur-xl rounded-2xl border border-slate-700/50 shadow-xl flex flex-col h-[450px]"
        >
          <div className="mb-4 flex items-center gap-2 border-b border-slate-700/50 pb-3">
            <Sparkles className="text-purple-400" size={24}/>
            <div>
              <h2 className="text-lg font-bold text-white">Lunar AI Copilot</h2>
              <p className="text-xs text-slate-400">Ask questions about your data in natural language</p>
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto pr-2 space-y-4 mb-4 custom-scrollbar">
            <AnimatePresence>
              {chatHistory.map((msg, i) => (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  key={i} 
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-[85%] p-3 rounded-2xl text-sm ${
                    msg.role === 'user' 
                      ? 'bg-sky-500/20 text-sky-100 border border-sky-500/30 rounded-br-none' 
                      : 'bg-slate-800 text-slate-200 border border-slate-700 rounded-bl-none'
                  }`}>
                    {msg.text}
                  </div>
                </motion.div>
              ))}
              {isTyping && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
                  <div className="bg-slate-800 border border-slate-700 text-slate-400 p-3 rounded-2xl rounded-bl-none text-sm flex gap-1">
                    <span className="animate-bounce">●</span><span className="animate-bounce delay-100">●</span><span className="animate-bounce delay-200">●</span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <form onSubmit={handleChatSubmit} className="relative mt-auto">
            <input 
              type="text" 
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="E.g. Analyze the latest RMSE spike..." 
              className="w-full bg-slate-900/50 border border-slate-600 rounded-xl py-3 pl-4 pr-12 text-white focus:outline-none focus:ring-2 focus:ring-sky-500/50 transition-all placeholder:text-slate-500"
            />
            <button type="submit" disabled={!chatInput.trim() || isTyping} className="absolute right-2 top-2 p-2 bg-sky-500 hover:bg-sky-400 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg transition-colors">
              <Send size={16} />
            </button>
          </form>
        </motion.div>

        {/* Right Column: Semantic Search */}
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="p-6 bg-lunar-card backdrop-blur-xl rounded-2xl border border-slate-700/50 shadow-xl flex flex-col h-[450px]"
        >
          <div className="mb-4 flex items-center gap-2 border-b border-slate-700/50 pb-3">
            <Map className="text-emerald-400" size={24}/>
            <div>
              <h2 className="text-lg font-bold text-white">Vector Search Engine</h2>
              <p className="text-xs text-slate-400">Search 10B+ geospatial records via embeddings</p>
            </div>
          </div>
          
          <form onSubmit={handleSearchSubmit} className="relative mb-6">
            <input 
              type="text" 
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search concepts (e.g. 'shadowed craters')" 
              className="w-full bg-slate-900/50 border border-slate-600 rounded-xl py-3 pl-11 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all placeholder:text-slate-500"
            />
            <Search className="absolute left-4 top-3.5 text-slate-400" size={18} />
          </form>

          <div className="flex-1 border border-slate-700/50 rounded-xl bg-slate-900/30 p-4 overflow-y-auto">
            {isSearching ? (
              <div className="h-full flex flex-col items-center justify-center space-y-4 text-emerald-400/70">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-400"></div>
                <p className="text-sm animate-pulse">Querying vector database...</p>
              </div>
            ) : searchResults.length > 0 ? (
              <div className="space-y-3">
                {searchResults.map((res, i) => (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.1 }}
                    key={i} 
                    className="p-3 bg-slate-800/60 hover:bg-slate-700/60 border border-slate-700 rounded-lg cursor-pointer transition-colors flex justify-between items-center group"
                  >
                    <span className="text-sm font-medium text-slate-200 group-hover:text-emerald-300 transition-colors">{res.title}</span>
                    <span className="text-xs bg-emerald-500/20 text-emerald-300 px-2 py-1 rounded-md border border-emerald-500/20">{res.match}% match</span>
                  </motion.div>
                ))}
              </div>
            ) : (
               <div className="h-full flex items-center justify-center">
                  <p className="text-sm text-slate-500 text-center px-8">Enter a semantic query to search the vectorized photogrammetry database.</p>
               </div>
            )}
          </div>
        </motion.div>

      </main>
      
      {/* Global styles for custom scrollbar */}
      <style>{`
        .custom-scrollbar::-webkit-scrollbar { width: 6px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #475569; }
      `}</style>
    </div>
  );
}

export default App;
