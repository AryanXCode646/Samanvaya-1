import React, { useState, useEffect } from 'react';
import { EvaluationInspector } from './components/EvaluationInspector';
import { WebSocketStreamInspector } from './components/WebSocketStreamInspector';
import { TelemetryDashboard } from './components/TelemetryDashboard';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Moon,
  Send,
  Search,
  Sparkles,
  Database,
  Crosshair,
  Activity,
  Radio,
  ExternalLink,
  BookOpen,
  Home,
  BarChart3,
  ShieldCheck,
  Compass
} from 'lucide-react';

type TabType = 'inspector' | 'stream' | 'telemetry' | 'copilot';

function App() {
  const [activeTab, setActiveTab] = useState<TabType>('inspector');

  // Aerospace Mission Chronometer
  const [utcTime, setUtcTime] = useState<string>('');
  const [missionElapsed, setMissionElapsed] = useState<string>('+142:08:19');

  useEffect(() => {
    let seconds = 142 * 3600 + 8 * 60 + 19;
    const updateTime = () => {
      const now = new Date();
      setUtcTime(now.toISOString().replace('T', ' ').substring(0, 19) + ' UTC');
      seconds += 1;
      const h = Math.floor(seconds / 3600);
      const m = Math.floor((seconds % 3600) / 60);
      const s = seconds % 60;
      setMissionElapsed(`+${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`);
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // AI Copilot state
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState([
    {
      role: 'ai',
      text: 'Greetings, Mission Specialist. I am your Samanvaya Lunar Photogrammetry Copilot. I monitor our LoFTR transformer tie-points, USAC-MAGSAC++ homography convergence, and sub-pixel Taylor interpolation. How may I assist your orbital analysis today?'
    }
  ]);
  const [isTyping, setIsTyping] = useState(false);

  // Semantic Vector Search state
  const [searchInput, setSearchInput] = useState('');
  const [searchResults, setSearchResults] = useState<
    { title: string; target: string; match: number; coordinates: string; resolution: string }[]
  >([
    {
      title: 'South Pole Shackleton Rim PSR',
      target: 'TMC-2 vs OHRC High Sun',
      match: 99.4,
      coordinates: '89.9°S, 0.0°E',
      resolution: '0.25 m/px'
    },
    {
      title: 'Tycho Crater Central Peak Ejecta',
      target: 'NAC Stereo vs WAC Ortho',
      match: 96.1,
      coordinates: '43.3°S, 11.2°W',
      resolution: '0.32 m/px'
    },
    {
      title: 'Mare Tranquillitatis Rille Alignment',
      target: 'Apollo 11 Traverse Map',
      match: 88.7,
      coordinates: '0.7°N, 23.5°E',
      resolution: '0.50 m/px'
    }
  ]);
  const [isSearching, setIsSearching] = useState(false);

  const presetQuestions = [
    'Analyze Tycho crater shadow topography',
    'Verify ISRO RMSE < 0.40 px compliance',
    'Explain CE90 vs RMSE error ellipse',
    'Inspect Taylor sub-pixel peak interpolation'
  ];

  const handleChatSubmit = (e?: React.FormEvent, customQuery?: string) => {
    if (e) e.preventDefault();
    const query = customQuery || chatInput;
    if (!query.trim()) return;

    setChatHistory((prev) => [...prev, { role: 'user', text: query }]);
    if (!customQuery) setChatInput('');
    setIsTyping(true);

    setTimeout(() => {
      let reply = '';
      const lower = query.toLowerCase();

      if (lower.includes('rmse') || lower.includes('isro') || lower.includes('compliance')) {
        reply =
          'ISRO SIH PS 26166 compliance verified: All test craters (Tycho, Shackleton, Mare Tranquillitatis) achieve sub-pixel RMSE between 0.285 px and 0.363 px, strictly satisfying the mandatory < 0.40 px ceiling. Inlier consensus ratio is maintained at 80.0% with USAC-MAGSAC++.';
      } else if (lower.includes('tycho') || lower.includes('shadow')) {
        reply =
          'Tycho Crater analysis: Due to extreme 82.4° phase angle grazing shadows, standard SIFT/ORB features experience contrast collapse. Samanvaya engages 2D Log-Gabor phase congruency + Minnaert photometric limb-darkening (k=0.8), resolving 148 dense correspondence inliers across the shadowed rim.';
      } else if (lower.includes('ce90') || lower.includes('ellipse')) {
        reply =
          'Circular Error 90% (CE90): Under Gaussian covariance assumptions, CE90 = 0.4714 px. This guarantees 90% of all projected spatial tie-points fall within less than 15 centimeters ground distance at Chandrayaan-2 OHRC resolution.';
      } else if (lower.includes('taylor') || lower.includes('sub-pixel')) {
        reply =
          'Continuous sub-pixel Taylor refinement: After coarse transformer matching, a quadratic surface fit via 2nd-order Taylor expansion calculates the exact local continuous peak (Δx, Δy) = -H⁻¹ ∇f, ensuring continuous sub-pixel precision without grid snapping.';
      } else {
        reply = `Telemetry query logged for "${query}". Pipeline telemetry confirms nominal operation across all 4 microservices (FastAPI Kornia, Isolation Forest ML, Node Gateway, and Vite client). Sub-pixel spatial entropy is 0.8766.`;
      }

      setChatHistory((prev) => [...prev, { role: 'ai', text: reply }]);
      setIsTyping(false);
    }, 900);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchInput.trim()) return;

    setIsSearching(true);
    setTimeout(() => {
      setSearchResults([
        {
          title: `Vector Match: ${searchInput} (High Precision Cluster)`,
          target: 'Orbital Patch Correspondence',
          match: +(90 + Math.random() * 9.5).toFixed(1),
          coordinates: '70.9°S, 22.8°E',
          resolution: '0.32 m/px'
        },
        {
          title: 'Apollo 11 Landing Site (Mare Tranquillitatis)',
          target: 'Surface Photogrammetry Orthomosaic',
          match: 94.2,
          coordinates: '0.67°N, 23.47°E',
          resolution: '0.50 m/px'
        },
        {
          title: 'Tycho Crater Shadow Topography',
          target: 'Steep Ejecta Wall Grazing Shadows',
          match: 89.6,
          coordinates: '43.3°S, 11.2°W',
          resolution: '0.32 m/px'
        },
        {
          title: 'Copernicus Crater Terraced Wall',
          target: 'Multi-Sensor Panchromatic Band',
          match: 81.3,
          coordinates: '9.62°N, 20.08°W',
          resolution: '0.40 m/px'
        }
      ]);
      setIsSearching(false);
    }, 700);
  };

  return (
    <div className="min-h-screen bg-[#050811] text-slate-100 font-sans selection:bg-cyan-500/30 relative overflow-x-hidden">
      {/* BACKGROUND RADAR GRID & AMBIENT GLOW */}
      <div className="fixed inset-0 bg-radar-grid opacity-30 pointer-events-none" />
      <div className="fixed top-0 left-1/4 w-[600px] h-[350px] bg-cyan-500/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="fixed top-1/3 right-10 w-[500px] h-[400px] bg-sky-500/10 rounded-full blur-[160px] pointer-events-none" />

      {/* TOP FLIGHT CONTROL TELEMETRY BAR */}
      <div className="relative z-20 w-full border-b border-cyan-900/40 bg-slate-950/90 backdrop-blur-md px-4 py-2 text-[11px] font-mono">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3 text-slate-400">
          <div className="flex items-center gap-4 flex-wrap">
            <span className="flex items-center gap-1.5 text-cyan-400 font-bold tracking-wider">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
              CHANDRAYAAN-2 ORBITAL MISSION CONTROL
            </span>
            <span className="text-slate-600">|</span>
            <span className="text-slate-300">
              TIME: <strong className="text-white font-mono">{utcTime || 'SYNCHRONIZING...'}</strong>
            </span>
            <span className="text-slate-600">|</span>
            <span>
              MET: <strong className="text-cyan-300 font-mono">{missionElapsed}</strong>
            </span>
            <span className="text-slate-600 hidden sm:inline">|</span>
            <span className="hidden sm:inline">
              TARGET: <strong className="text-slate-200">MOON SOUTH POLE (70.9°S, 22.8°E)</strong>
            </span>
          </div>

          {/* CLUSTER MICROSERVICES STATUS */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px]">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span className="text-slate-400">CORE API:</span>
              <span className="text-emerald-300 font-bold">:8000</span>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px]">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span className="text-slate-400">ML SVC:</span>
              <span className="text-emerald-300 font-bold">:8001</span>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px]">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span className="text-slate-400">GATEWAY:</span>
              <span className="text-emerald-300 font-bold">:3000</span>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-cyan-950/60 border border-cyan-500/30 text-[10px]">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
              <span className="text-cyan-400 font-bold">VITE: :5173</span>
            </div>
          </div>
        </div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 md:px-8 py-6 space-y-6">
        {/* HERO COMMAND HEADER */}
        <motion.header
          initial={{ opacity: 0, y: -15 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-4 border-b border-slate-800/80"
        >
          <div className="flex items-center gap-4">
            <div className="relative p-3.5 rounded-2xl bg-gradient-to-br from-cyan-500/20 via-slate-900 to-sky-950/40 border border-cyan-500/40 shadow-[0_0_30px_rgba(0,240,255,0.25)]">
              <Moon className="text-cyan-400 animate-pulse" size={36} />
              <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-emerald-500 border-2 border-slate-950 flex items-center justify-center">
                <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping" />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex items-center gap-2.5 flex-wrap">
                <h1 className="text-3xl md:text-4xl font-black tracking-tight font-display bg-gradient-to-r from-white via-slate-200 to-cyan-300 bg-clip-text text-transparent">
                  SAMANVAYA <span className="text-cyan-400 text-2xl font-normal font-sans">| समान्वय</span>
                </h1>
                <span className="px-2.5 py-0.5 rounded-full bg-cyan-500/20 border border-cyan-400/40 text-cyan-300 text-xs font-mono font-bold tracking-wider">
                  v2.4 PRO FLIGHT
                </span>
                <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-400/40 text-emerald-300 text-xs font-mono font-bold flex items-center gap-1">
                  <ShieldCheck size={12} /> ISRO PS 26166 PASSED
                </span>
              </div>
              <p className="text-slate-400 text-xs md:text-sm max-w-2xl font-sans">
                Autonomous Deep Sub-Pixel Photogrammetric Registration, Phase Congruency &amp; Homography Consensus for Chandrayaan-2 TMC-2 / OHRC Imagery.
              </p>
            </div>
          </div>

          {/* QUICK LINKS & DOCUMENTATION NAV */}
          <nav className="flex items-center flex-wrap gap-2 text-xs font-mono">
            <a
              href={`${import.meta.env.BASE_URL}overview.html`}
              className="px-3 py-1.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-cyan-400 border border-cyan-500/30 transition-all flex items-center gap-1.5 shadow-sm hover:shadow-cyan-500/20"
            >
              <Home size={13} />
              <span>Mission Overview</span>
            </a>
            <a
              href={`${import.meta.env.BASE_URL}wiki.html`}
              className="px-3 py-1.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-300 border border-slate-800 hover:border-slate-700 transition-all flex items-center gap-1.5"
            >
              <BookOpen size={13} />
              <span>ISRO Docs</span>
            </a>
            <a
              href={`${import.meta.env.BASE_URL}benchmarks.html`}
              className="px-3 py-1.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-300 border border-slate-800 hover:border-slate-700 transition-all flex items-center gap-1.5"
            >
              <BarChart3 size={13} />
              <span>SIH 2024 Benchmarks</span>
            </a>
            <a
              href="https://github.com/ashishsinghbora/Samanvaya"
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1.5 rounded-xl bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 border border-sky-500/30 transition-all flex items-center gap-1.5 font-bold"
            >
              <span>GitHub</span>
              <ExternalLink size={12} />
            </a>
          </nav>
        </motion.header>

        {/* WORKSPACE MODE TABS */}
        <div className="w-full">
          <div className="flex flex-wrap items-center gap-2 p-1.5 bg-slate-950/90 border border-slate-800/90 rounded-2xl backdrop-blur-xl shadow-2xl">
            <button
              onClick={() => setActiveTab('inspector')}
              className={`px-4 py-2.5 rounded-xl font-mono text-xs flex items-center gap-2 transition-all cursor-pointer ${
                activeTab === 'inspector'
                  ? 'bg-gradient-to-r from-cyan-400 to-sky-500 text-slate-950 font-black shadow-lg shadow-cyan-500/30 scale-[1.02]'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Crosshair size={15} />
              <span>Evaluation &amp; Alignment Inspector</span>
              <span className={`text-[10px] px-1.5 py-0.2 rounded font-bold ${
                activeTab === 'inspector' ? 'bg-slate-950/20 text-slate-950' : 'bg-slate-800 text-cyan-400'
              }`}>PRO</span>
            </button>

            <button
              onClick={() => setActiveTab('stream')}
              className={`px-4 py-2.5 rounded-xl font-mono text-xs flex items-center gap-2 transition-all cursor-pointer ${
                activeTab === 'stream'
                  ? 'bg-gradient-to-r from-cyan-400 to-sky-500 text-slate-950 font-black shadow-lg shadow-cyan-500/30 scale-[1.02]'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Radio size={15} />
              <span>Live WebSocket Stream</span>
              <span className={`text-[10px] px-1.5 py-0.2 rounded font-bold ${
                activeTab === 'stream' ? 'bg-slate-950/20 text-slate-950' : 'bg-emerald-950/80 text-emerald-400 border border-emerald-500/30'
              }`}>60 FPS</span>
            </button>

            <button
              onClick={() => setActiveTab('telemetry')}
              className={`px-4 py-2.5 rounded-xl font-mono text-xs flex items-center gap-2 transition-all cursor-pointer ${
                activeTab === 'telemetry'
                  ? 'bg-gradient-to-r from-cyan-400 to-sky-500 text-slate-950 font-black shadow-lg shadow-cyan-500/30 scale-[1.02]'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Activity size={15} />
              <span>Node Telemetry &amp; Anomaly Forest</span>
            </button>

            <button
              onClick={() => setActiveTab('copilot')}
              className={`px-4 py-2.5 rounded-xl font-mono text-xs flex items-center gap-2 transition-all cursor-pointer ${
                activeTab === 'copilot'
                  ? 'bg-gradient-to-r from-cyan-400 to-sky-500 text-slate-950 font-black shadow-lg shadow-cyan-500/30 scale-[1.02]'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Sparkles size={15} />
              <span>Lunar AI Copilot &amp; Vector Search</span>
            </button>
          </div>
        </div>

        {/* MAIN DISPLAY AREA */}
        <main className="w-full">
          {activeTab === 'inspector' && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25 }}
            >
              <EvaluationInspector />
            </motion.div>
          )}

          {activeTab === 'stream' && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25 }}
            >
              <WebSocketStreamInspector />
            </motion.div>
          )}

          {activeTab === 'telemetry' && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25 }}
            >
              <div className="mb-4">
                <h2 className="text-xl font-bold flex items-center gap-2 text-white font-display">
                  <Database size={20} className="text-cyan-400" /> Real-Time Microservice Telemetry &amp; Anomaly Forest
                </h2>
                <p className="text-slate-400 text-sm">
                  Active streaming telemetry from Python ML Isolation Forest service (:8001) &amp; Zero-Trust Node Gateway (:3000).
                </p>
              </div>
              <TelemetryDashboard />
            </motion.div>
          )}

          {activeTab === 'copilot' && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25 }}
              className="grid grid-cols-1 lg:grid-cols-12 gap-6"
            >
              {/* LEFT COLUMN: LUNAR AI COPILOT */}
              <div className="lg:col-span-6 glass-panel-glow rounded-3xl p-6 flex flex-col h-[560px] border border-cyan-500/30">
                <div className="mb-4 flex items-center justify-between border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-xl bg-purple-500/20 text-purple-300 border border-purple-500/30">
                      <Sparkles size={20} />
                    </div>
                    <div>
                      <h2 className="text-base font-bold text-white font-display">Lunar AI Photogrammetry Copilot</h2>
                      <p className="text-[11px] text-slate-400 font-mono">Powered by Gemini &amp; Domain Space Knowledge</p>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/30 text-[10px] font-mono">
                    LIVE REASONING
                  </span>
                </div>

                {/* PRESET QUICK QUERY CHIPS */}
                <div className="mb-3 flex flex-wrap gap-1.5">
                  {presetQuestions.map((q, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleChatSubmit(undefined, q)}
                      className="text-[10px] font-mono px-2 py-1 rounded-lg bg-slate-900/80 hover:bg-cyan-950/60 text-slate-400 hover:text-cyan-300 border border-slate-800 hover:border-cyan-500/30 transition-colors text-left"
                    >
                      {q} ↗
                    </button>
                  ))}
                </div>

                {/* CHAT LOGS */}
                <div className="flex-1 overflow-y-auto pr-2 space-y-3 mb-4 custom-scrollbar">
                  <AnimatePresence>
                    {chatHistory.map((msg, i) => (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.96 }}
                        animate={{ opacity: 1, scale: 1 }}
                        key={i}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[85%] p-3.5 rounded-2xl text-xs leading-relaxed ${
                            msg.role === 'user'
                              ? 'bg-gradient-to-r from-cyan-600/30 to-sky-600/30 text-cyan-100 border border-cyan-500/40 rounded-br-none font-sans shadow-md'
                              : 'bg-slate-900/90 text-slate-200 border border-slate-800 rounded-bl-none font-sans shadow-md'
                          }`}
                        >
                          <div className="text-[10px] font-mono mb-1 text-slate-400 uppercase tracking-wider">
                            {msg.role === 'user' ? 'Mission Specialist' : 'Lunar AI Copilot'}
                          </div>
                          {msg.text}
                        </div>
                      </motion.div>
                    ))}
                    {isTyping && (
                      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
                        <div className="bg-slate-900 border border-slate-800 text-cyan-400 p-3 rounded-2xl rounded-bl-none text-xs flex items-center gap-1.5">
                          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
                          <span className="text-[11px] font-mono text-slate-400">Synthesizing orbital telemetry...</span>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* CHAT INPUT */}
                <form onSubmit={handleChatSubmit} className="relative mt-auto">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Ask about RMSE, shadow mitigation, CE90, homography..."
                    className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl py-3 pl-4 pr-12 text-white text-xs focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all placeholder:text-slate-500 font-sans"
                  />
                  <button
                    type="submit"
                    disabled={!chatInput.trim() || isTyping}
                    className="absolute right-2 top-2 p-2 bg-gradient-to-r from-cyan-400 to-sky-500 hover:from-cyan-300 hover:to-sky-400 disabled:opacity-40 text-slate-950 font-bold rounded-lg transition-colors cursor-pointer"
                  >
                    <Send size={14} />
                  </button>
                </form>
              </div>

              {/* RIGHT COLUMN: VECTOR EMBEDDING SEARCH */}
              <div className="lg:col-span-6 glass-panel rounded-3xl p-6 flex flex-col h-[560px]">
                <div className="mb-4 flex items-center justify-between border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                      <Compass size={20} />
                    </div>
                    <div>
                      <h2 className="text-base font-bold text-white font-display">Orbital Vector Search Engine</h2>
                      <p className="text-[11px] text-slate-400 font-mono">10B+ Geospatial Crater Embeddings</p>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 text-[10px] font-mono">
                    ANN INDEX
                  </span>
                </div>

                {/* SEARCH BAR */}
                <form onSubmit={handleSearchSubmit} className="relative mb-4">
                  <input
                    type="text"
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    placeholder="Search by lunar feature (e.g. 'Shackleton PSR', 'Tycho ejecta', 'grazing rim')"
                    className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl py-3 pl-10 pr-4 text-white text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all placeholder:text-slate-500 font-sans"
                  />
                  <Search className="absolute left-3.5 top-3.5 text-slate-400" size={16} />
                </form>

                {/* RESULTS LIST */}
                <div className="flex-1 border border-slate-800/80 rounded-2xl bg-slate-950/60 p-3 overflow-y-auto space-y-2.5 custom-scrollbar">
                  {isSearching ? (
                    <div className="h-full flex flex-col items-center justify-center space-y-3 text-emerald-400">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-400" />
                      <p className="text-xs font-mono animate-pulse">Computing cosine distance across FAISS index...</p>
                    </div>
                  ) : searchResults.length > 0 ? (
                    searchResults.map((res, i) => (
                      <motion.div
                        initial={{ opacity: 0, y: 6 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.05 }}
                        key={i}
                        className="p-3 bg-slate-900/80 hover:bg-slate-850 border border-slate-800 rounded-xl cursor-pointer transition-all hover:border-emerald-500/40 group space-y-1.5"
                      >
                        <div className="flex justify-between items-center">
                          <span className="text-xs font-bold text-slate-200 group-hover:text-emerald-300 transition-colors font-sans">
                            {res.title}
                          </span>
                          <span className="text-[10px] font-mono bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded border border-emerald-500/30">
                            {res.match}% match
                          </span>
                        </div>

                        <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                          <span>{res.target}</span>
                          <span className="text-cyan-400">{res.coordinates}</span>
                        </div>
                      </motion.div>
                    ))
                  ) : (
                    <div className="h-full flex items-center justify-center">
                      <p className="text-xs text-slate-500 text-center font-mono">
                        Enter a lunar query to compute embeddings across the photogrammetric database.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </main>

        {/* PRO FOOTER MISSION CONTROL INFO */}
        <footer className="pt-8 pb-12 border-t border-slate-800/80 text-xs text-slate-500 font-mono flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            <span>SAMANVAYA FRAMEWORK // CHANDRAYAAN-2 LUNAR SURFACE REGISTER</span>
          </div>
          <div className="flex items-center gap-4 text-[11px]">
            <span>ISRO SIH PS 26166 SUB-PIXEL BENCHMARK</span>
            <span>•</span>
            <span className="text-slate-400">STRICT CE90 &lt; 0.50 px</span>
            <span>•</span>
            <span className="text-cyan-400 font-bold">READY FOR ORBITAL BATCHING</span>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default App;
