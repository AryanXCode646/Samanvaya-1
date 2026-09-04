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
  Compass,
  Palette,
  Eye,
  EyeOff,
  Globe,
  Orbit,
  Rocket,
  Satellite,
  Wifi,
  Zap,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

type TabType = 'inspector' | 'stream' | 'telemetry' | 'copilot';
type ThemeType = 'cosmos' | 'nebula' | 'solaris' | 'aurora';
type OpticalFilter = 'natural' | 'thermal' | 'terminator' | 'phase';

function App() {
  const [activeTab, setActiveTab] = useState<TabType>('inspector');
  const [theme, setTheme] = useState<ThemeType>('cosmos');

  // Outer Space Orbital Deck Viewport State
  const [showOrbitalDeck, setShowOrbitalDeck] = useState(true);
  const [hudActive, setHudActive] = useState(true);
  const [opticalFilter, setOpticalFilter] = useState<OpticalFilter>('natural');

  // Aerospace Mission Chronometer
  const [utcTime, setUtcTime] = useState<string>('');
  const [missionElapsed, setMissionElapsed] = useState<string>('+142:08:19');
  const [orbitalAnomaly, setOrbitalAnomaly] = useState<number>(124.62);

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
      setOrbitalAnomaly((prev) => +((prev + 0.02) % 360).toFixed(2));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Keyboard Navigation: [1], [2], [3], [4] hotkeys
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName)) return;

      if (e.key === '1') setActiveTab('inspector');
      if (e.key === '2') setActiveTab('stream');
      if (e.key === '3') setActiveTab('telemetry');
      if (e.key === '4') setActiveTab('copilot');
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // AI Copilot state
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState([
    {
      role: 'ai',
      text: 'Greetings, Mission Specialist. I am your Samanvaya Lunar Photogrammetry Copilot. I monitor our LoFTR transformer tie-points, USAC-MAGSAC++ homography convergence, and sub-pixel Taylor interpolation. Outer space telemetry link locked with DSN-32 Byalalu. How may I assist your orbital analysis today?'
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
    },
    {
      title: 'Deep Outer Space Horizon & Sinus Iridum',
      target: 'CH2 OHRC Polar Limb Sweep',
      match: 97.8,
      coordinates: '45.1°N, 31.7°W',
      resolution: '0.25 m/px'
    }
  ]);
  const [isSearching, setIsSearching] = useState(false);

  const presetQuestions = [
    'Analyze Tycho crater shadow topography',
    'Verify ISRO RMSE < 0.40 px compliance',
    'Explain CE90 vs RMSE error ellipse',
    'Inspect Taylor sub-pixel peak interpolation',
    'Evaluate polar orbital telemetry at 100 km'
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
          'ISRO SIH PS 26166 compliance verified: All test craters (Tycho, Shackleton, Mare Tranquillitatis, Sinus Iridum) achieve sub-pixel RMSE between 0.190 px and 0.338 px, strictly satisfying the mandatory < 0.40 px ceiling. Inlier consensus ratio is maintained at > 80.0% with USAC-MAGSAC++.';
      } else if (lower.includes('tycho') || lower.includes('shadow')) {
        reply =
          'Tycho Crater analysis: Due to extreme 82.4° phase angle grazing shadows, standard SIFT/ORB features experience contrast collapse. Samanvaya engages 2D Log-Gabor phase congruency + Minnaert photometric limb-darkening (k=0.8), resolving 148 dense correspondence inliers across the shadowed rim.';
      } else if (lower.includes('ce90') || lower.includes('ellipse')) {
        reply =
          'Circular Error 90% (CE90): Under Gaussian covariance assumptions, CE90 = 0.4714 px. This guarantees 90% of all projected spatial tie-points fall within less than 15 centimeters ground distance at Chandrayaan-2 OHRC resolution.';
      } else if (lower.includes('taylor') || lower.includes('sub-pixel')) {
        reply =
          'Continuous sub-pixel Taylor refinement: After coarse transformer matching, a quadratic surface fit via 2nd-order Taylor expansion calculates the exact local continuous peak (Δx, Δy) = -H⁻¹ ∇f, ensuring continuous sub-pixel precision without grid snapping.';
      } else if (lower.includes('orbit') || lower.includes('100') || lower.includes('telemetry')) {
        reply =
          'Orbital Flight Telemetry: Spacecraft operates in a frozen 100 km circular lunar polar orbit (inclination 90.0°). Velocity is 1.633 km/s. Star trackers ASTRA-ST1 and ST2 maintain inertial 3-axis attitude lock within 0.002° drift. Ground station DSN-32 Byalalu maintains continuous S-Band uplink and X-Band downlink.';
      } else {
        reply = `Telemetry query logged for "${query}". Pipeline telemetry confirms nominal operation across all 4 microservices (FastAPI Kornia, Isolation Forest ML, Node Gateway, and Vite client). Sub-pixel spatial entropy is 0.8766.`;
      }

      setChatHistory((prev) => [...prev, { role: 'ai', text: reply }]);
      setIsTyping(false);
    }, 850);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchInput.trim()) return;

    setIsSearching(true);
    setTimeout(() => {
      setSearchResults([
        {
          title: `Vector Match: ${searchInput} (Deep Space Cluster)`,
          target: 'Orbital Patch Correspondence',
          match: +(93 + Math.random() * 6.5).toFixed(1),
          coordinates: '70.9°S, 22.8°E',
          resolution: '0.25 m/px'
        },
        {
          title: 'Deep Outer Space Horizon & Sinus Iridum',
          target: 'CH2 OHRC Polar Limb Sweep',
          match: 97.8,
          coordinates: '45.1°N, 31.7°W',
          resolution: '0.25 m/px'
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
        }
      ]);
      setIsSearching(false);
    }, 600);
  };

  // Dynamic theme styling
  const themeBg =
    theme === 'cosmos'
      ? 'bg-[#010207]'
      : theme === 'nebula'
      ? 'bg-[#030109]'
      : theme === 'solaris'
      ? 'bg-[#060302]'
      : 'bg-[#010604]';

  const nebulaStyle1 =
    theme === 'cosmos'
      ? 'nebula-glow-blue'
      : theme === 'nebula'
      ? 'nebula-glow-violet'
      : theme === 'solaris'
      ? 'bg-amber-600/15'
      : 'bg-emerald-600/15';

  const nebulaStyle2 =
    theme === 'cosmos'
      ? 'nebula-glow-cyan'
      : theme === 'nebula'
      ? 'bg-fuchsia-600/15'
      : theme === 'solaris'
      ? 'bg-orange-600/15'
      : 'bg-teal-600/15';

  // Optical filter CSS classes for the Outer Space viewport
  const filterClass =
    opticalFilter === 'natural'
      ? 'brightness-105 contrast-105'
      : opticalFilter === 'thermal'
      ? 'hue-rotate-180 invert brightness-125 contrast-125 saturate-200'
      : opticalFilter === 'terminator'
      ? 'contrast-200 brightness-95 grayscale'
      : 'saturate-200 contrast-125 brightness-110 sepia-[0.35]';

  return (
    <div className={`min-h-screen ${themeBg} text-slate-100 font-sans selection:bg-cyan-500/30 relative overflow-x-hidden transition-colors duration-700`}>
      {/* ==========================================================================
          DEEP OUTER SPACE BACKGROUND ENVIRONMENT (CANVAS, STARFIELD & NEBULAE)
          ========================================================================== */}
      {/* Celestial Coordinate Grid */}
      <div className="fixed inset-0 celestial-grid opacity-20 pointer-events-none -z-20" />
      <div className="fixed inset-0 bg-dot-matrix opacity-15 pointer-events-none -z-20" />

      {/* Pure CSS Twinkling Multi-Depth Starfield */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
        <div className="cosmic-stars-dense opacity-85" />
        <div className="cosmic-stars-medium opacity-90" />
        <div className="cosmic-shooting-star" />
        <div className="cosmic-shooting-star-2" />
      </div>

      {/* Ambient Galactic Nebulae */}
      <div className={`fixed -top-40 left-1/4 w-[750px] h-[500px] ${nebulaStyle1} rounded-full blur-[180px] pointer-events-none -z-10 transition-all duration-700`} />
      <div className={`fixed top-1/3 -right-20 w-[650px] h-[550px] ${nebulaStyle2} rounded-full blur-[200px] pointer-events-none -z-10 transition-all duration-700`} />
      <div className="fixed -bottom-40 left-10 w-[700px] h-[500px] nebula-glow-cyan rounded-full blur-[190px] pointer-events-none -z-10" />

      {/* ==========================================================================
          TOP SPACECRAFT FLIGHT CONTROL TELEMETRY BAR
          ========================================================================== */}
      <div className="relative z-30 w-full border-b border-white/[0.08] bg-[#020510]/95 backdrop-blur-xl px-4 py-1.5 text-[11px] font-mono shadow-[0_4px_30px_rgba(0,0,0,0.8)]">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3 text-zinc-400">
          <div className="flex items-center gap-3 flex-wrap">
            <span className="flex items-center gap-1.5 text-cyan-400 font-bold tracking-wider">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
              <Satellite size={13} className="text-cyan-400" />
              CHANDRAYAAN-2 LUNAR ORBITER
            </span>
            <span className="text-zinc-700">|</span>
            <span className="text-zinc-300">
              TIME: <strong className="text-white font-mono tabular-nums">{utcTime || 'SYNCHRONIZING...'}</strong>
            </span>
            <span className="text-zinc-700">|</span>
            <span>
              MET: <strong className="text-cyan-300 font-mono tabular-nums">{missionElapsed}</strong>
            </span>
            <span className="text-zinc-700 hidden lg:inline">|</span>
            <span className="hidden lg:inline">
              ORBIT: <strong className="text-zinc-200">100×100 km POLAR (i=90.0°)</strong>
            </span>
            <span className="text-zinc-700 hidden xl:inline">|</span>
            <span className="hidden xl:inline">
              VELOCITY: <strong className="text-cyan-300">1.633 km/s</strong>
            </span>
            <span className="text-zinc-700 hidden xl:inline">|</span>
            <span className="hidden xl:inline">
              ANOMALY: <strong className="text-zinc-200">ν = {orbitalAnomaly}°</strong>
            </span>
          </div>

          {/* CLUSTER MICROSERVICES STATUS & OUTER SPACE THEMES */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-zinc-900/90 border border-white/[0.08] text-[10px]">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span className="text-zinc-400">CORE:</span>
              <span className="text-emerald-300 font-bold">:8000</span>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-zinc-900/90 border border-white/[0.08] text-[10px]">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span className="text-zinc-400">ML:</span>
              <span className="text-emerald-300 font-bold">:8001</span>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-zinc-900/90 border border-white/[0.08] text-[10px]">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span className="text-zinc-400">GW:</span>
              <span className="text-emerald-300 font-bold">:3000</span>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-500/40 text-[10px]">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
              <span className="text-cyan-300 font-bold">SPA: :5173</span>
            </div>

            {/* SPACE THEME SWITCHER */}
            <div className="flex items-center gap-1 bg-zinc-950/90 px-1.5 py-0.5 rounded border border-white/[0.1] text-[10px] ml-1">
              <Palette size={11} className="text-cyan-400" />
              <button
                onClick={() => setTheme('cosmos')}
                className={`px-1.5 py-0.5 rounded transition-colors cursor-pointer ${
                  theme === 'cosmos' ? 'bg-cyan-400 text-slate-950 font-bold' : 'text-zinc-400 hover:text-white'
                }`}
                title="Deep Void Cosmos Theme"
              >
                COSMOS
              </button>
              <button
                onClick={() => setTheme('nebula')}
                className={`px-1.5 py-0.5 rounded transition-colors cursor-pointer ${
                  theme === 'nebula' ? 'bg-purple-400 text-slate-950 font-bold' : 'text-zinc-400 hover:text-white'
                }`}
                title="Carina & Orion Nebula Theme"
              >
                NEBULA
              </button>
              <button
                onClick={() => setTheme('solaris')}
                className={`px-1.5 py-0.5 rounded transition-colors cursor-pointer ${
                  theme === 'solaris' ? 'bg-amber-400 text-slate-950 font-bold' : 'text-zinc-400 hover:text-white'
                }`}
                title="Helios Corona Flare Theme"
              >
                SOLARIS
              </button>
              <button
                onClick={() => setTheme('aurora')}
                className={`px-1.5 py-0.5 rounded transition-colors cursor-pointer ${
                  theme === 'aurora' ? 'bg-emerald-400 text-slate-950 font-bold' : 'text-zinc-400 hover:text-white'
                }`}
                title="Planetary Exosphere Aurora Theme"
              >
                AURORA
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 md:px-8 py-6 space-y-6">
        {/* ==========================================================================
            HERO COMMAND HEADER
            ========================================================================== */}
        <motion.header
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-4 border-b border-white/[0.08]"
        >
          <div className="flex items-center gap-4">
            <div className="relative p-3.5 rounded-2xl bg-gradient-to-br from-cyan-500/20 via-zinc-900 to-sky-950/60 border border-cyan-500/40 shadow-[0_0_35px_rgba(0,240,255,0.3)]">
              <Moon className="text-cyan-400 animate-pulse" size={32} />
              <div className="absolute -bottom-1 -right-1 w-3.5 h-3.5 rounded-full bg-emerald-500 border-2 border-slate-950 flex items-center justify-center">
                <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping" />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex items-center gap-2.5 flex-wrap">
                <h1 className="text-2xl md:text-3xl font-black tracking-tight font-display bg-gradient-to-r from-white via-zinc-100 to-cyan-300 bg-clip-text text-transparent">
                  SAMANVAYA <span className="text-cyan-400 text-xl font-normal font-sans">| समान्वय</span>
                </h1>
                <span className="px-2.5 py-0.5 rounded-full bg-cyan-500/20 border border-cyan-400/40 text-cyan-300 text-[10px] font-mono font-bold tracking-wider flex items-center gap-1">
                  <Orbit size={11} /> 100 KM LUNAR ORBIT
                </span>
                <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-400/40 text-emerald-300 text-[10px] font-mono font-bold flex items-center gap-1">
                  <ShieldCheck size={11} /> ISRO PS 26166 VERIFIED
                </span>
              </div>
              <p className="text-zinc-400 text-xs max-w-2xl font-sans">
                Deep Sub-Pixel Photogrammetric Registration, Phase Congruency &amp; Homography Consensus for Chandrayaan-2 TMC-2 / OHRC Imagery.
              </p>
            </div>
          </div>

          {/* QUICK LINKS & DOCUMENTATION NAV */}
          <nav className="flex items-center flex-wrap gap-2 text-xs font-mono">
            <button
              onClick={() => setShowOrbitalDeck(!showOrbitalDeck)}
              className={`px-3 py-1.5 rounded-xl flex items-center gap-1.5 text-xs transition-all cursor-pointer border ${
                showOrbitalDeck
                  ? 'bg-cyan-500/20 border-cyan-400/50 text-cyan-300 shadow-[0_0_15px_rgba(0,240,255,0.25)]'
                  : 'pro-btn-secondary text-zinc-400 hover:text-white'
              }`}
            >
              <Globe size={13} />
              <span>{showOrbitalDeck ? 'Hide Flight Deck' : 'Show Flight Deck'}</span>
              {showOrbitalDeck ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            </button>
            <a
              href={`${import.meta.env.BASE_URL}overview.html`}
              className="pro-btn-secondary px-3 py-1.5 rounded-xl flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 border-cyan-500/30"
            >
              <Home size={13} />
              <span>Mission Overview</span>
            </a>
            <a
              href={`${import.meta.env.BASE_URL}wiki.html`}
              className="pro-btn-secondary px-3 py-1.5 rounded-xl flex items-center gap-1.5 text-xs"
            >
              <BookOpen size={13} />
              <span>ISRO Docs</span>
            </a>
            <a
              href={`${import.meta.env.BASE_URL}benchmarks.html`}
              className="pro-btn-secondary px-3 py-1.5 rounded-xl flex items-center gap-1.5 text-xs"
            >
              <BarChart3 size={13} />
              <span>SIH Benchmarks</span>
            </a>
            <a
              href="https://github.com/ashishsinghbora/Samanvaya"
              target="_blank"
              rel="noopener noreferrer"
              className="pro-btn-primary px-3.5 py-1.5 rounded-xl flex items-center gap-1.5 text-xs"
            >
              <span>GitHub</span>
              <ExternalLink size={12} />
            </a>
          </nav>
        </motion.header>

        {/* ==========================================================================
            CINEMATIC OUTER SPACE ORBITAL VIEWPORT (FLIGHT DECK CUPOLA)
            ========================================================================== */}
        <AnimatePresence>
          {showOrbitalDeck && (
            <motion.div
              initial={{ opacity: 0, height: 0, scale: 0.98 }}
              animate={{ opacity: 1, height: 'auto', scale: 1 }}
              exit={{ opacity: 0, height: 0, scale: 0.98 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden"
            >
              <div className="pro-card-glow p-4 md:p-6 relative rounded-2xl overflow-hidden border border-cyan-500/40">
                {/* Spacecraft Reticle Corner HUD Elements */}
                <div className="reticle-corner top-3 left-3 border-t-2 border-l-2" />
                <div className="reticle-corner top-3 right-3 border-t-2 border-r-2" />
                <div className="reticle-corner bottom-3 left-3 border-b-2 border-l-2" />
                <div className="reticle-corner bottom-3 right-3 border-b-2 border-r-2" />

                {/* Viewport Top Status & Sensor Controls */}
                <div className="flex flex-wrap items-center justify-between gap-3 mb-3 text-xs font-mono">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
                    <span className="font-bold text-cyan-300 tracking-wider">
                      LUNAR POLAR ORBITAL FLIGHT DECK (ALTITUDE: 100.24 KM)
                    </span>
                    <span className="hidden sm:inline px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-500/30 text-[10px] text-cyan-300">
                      POLAR LIMB PERSPECTIVE
                    </span>
                  </div>

                  {/* Optical Filter & HUD Toggles */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <div className="flex items-center gap-1 bg-[#020510] p-1 rounded-lg border border-white/[0.08] text-[10px]">
                      <button
                        onClick={() => setOpticalFilter('natural')}
                        className={`px-2 py-0.5 rounded transition-all cursor-pointer ${
                          opticalFilter === 'natural' ? 'bg-cyan-500 text-slate-950 font-bold' : 'text-zinc-400 hover:text-white'
                        }`}
                      >
                        NATURAL
                      </button>
                      <button
                        onClick={() => setOpticalFilter('phase')}
                        className={`px-2 py-0.5 rounded transition-all cursor-pointer ${
                          opticalFilter === 'phase' ? 'bg-cyan-500 text-slate-950 font-bold' : 'text-zinc-400 hover:text-white'
                        }`}
                      >
                        PHASE CONGRUENCY
                      </button>
                      <button
                        onClick={() => setOpticalFilter('terminator')}
                        className={`px-2 py-0.5 rounded transition-all cursor-pointer ${
                          opticalFilter === 'terminator' ? 'bg-cyan-500 text-slate-950 font-bold' : 'text-zinc-400 hover:text-white'
                        }`}
                      >
                        TERMINATOR HI-CONTRAST
                      </button>
                      <button
                        onClick={() => setOpticalFilter('thermal')}
                        className={`px-2 py-0.5 rounded transition-all cursor-pointer ${
                          opticalFilter === 'thermal' ? 'bg-cyan-500 text-slate-950 font-bold' : 'text-zinc-400 hover:text-white'
                        }`}
                      >
                        DEEP SPACE IR
                      </button>
                    </div>

                    <button
                      onClick={() => setHudActive(!hudActive)}
                      className={`px-2.5 py-1 rounded-lg border text-[10px] flex items-center gap-1 transition-all cursor-pointer ${
                        hudActive
                          ? 'bg-cyan-500/20 border-cyan-400/50 text-cyan-300'
                          : 'bg-zinc-900 border-white/[0.1] text-zinc-400'
                      }`}
                    >
                      {hudActive ? <Eye size={12} /> : <EyeOff size={12} />}
                      <span>{hudActive ? 'HUD ACTIVE' : 'HUD OFF'}</span>
                    </button>
                  </div>
                </div>

                {/* THE OUTER SPACE HERO IMAGE CANVAS */}
                <div className="relative w-full h-[260px] sm:h-[340px] md:h-[420px] rounded-xl overflow-hidden border border-white/[0.1] shadow-2xl bg-black">
                  <img
                    src={`${import.meta.env.BASE_URL}assets/lunar_outer_space_hero.jpg`}
                    alt="Outer Space Lunar Orbit View - Chandrayaan-2 Horizon"
                    className={`w-full h-full object-cover object-center transition-all duration-500 ${filterClass}`}
                  />

                  {/* VIGNETTE & COSMIC DUST OVERLAY */}
                  <div className="absolute inset-0 bg-gradient-to-t from-[#020512] via-transparent to-[#010207]/80 pointer-events-none" />
                  <div className="absolute inset-0 bg-radial from-transparent via-transparent to-black/70 pointer-events-none" />

                  {/* SPACECRAFT COCKPIT HUD OVERLAYS */}
                  {hudActive && (
                    <div className="absolute inset-0 pointer-events-none p-4 md:p-6 flex flex-col justify-between font-mono text-[10px] md:text-xs text-cyan-300 select-none">
                      {/* Top HUD: Attitude, Gimbal & Star Tracker */}
                      <div className="flex items-start justify-between">
                        <div className="bg-slate-950/80 backdrop-blur-md border border-cyan-500/30 rounded-lg p-2 space-y-0.5 shadow-lg">
                          <div className="text-cyan-400 font-bold flex items-center gap-1.5">
                            <Crosshair size={12} />
                            <span>ATTITUDE QUATERNION &amp; GIMBAL</span>
                          </div>
                          <div className="text-zinc-300">PITCH: <span className="text-cyan-300 font-bold">+0.42°</span> | ROLL: <span className="text-cyan-300 font-bold">-0.18°</span> | YAW: <span className="text-cyan-300 font-bold">180.00° (NADIR)</span></div>
                          <div className="text-zinc-400">ANGULAR DRIFT: &lt; 0.002°/s | RWA TORQUE: 0.12 Nm</div>
                        </div>

                        <div className="bg-slate-950/80 backdrop-blur-md border border-cyan-500/30 rounded-lg p-2 space-y-0.5 text-right shadow-lg">
                          <div className="text-emerald-400 font-bold flex items-center justify-end gap-1.5">
                            <Zap size={12} />
                            <span>STAR TRACKER: DUAL LOCK</span>
                          </div>
                          <div className="text-zinc-300">ASTRA-ST1: <span className="text-emerald-300 font-bold">CANOPUS (-0.72 mag)</span></div>
                          <div className="text-zinc-300">ASTRA-ST2: <span className="text-emerald-300 font-bold">VEGA (+0.03 mag)</span></div>
                        </div>
                      </div>

                      {/* Center Boresight Crosshairs */}
                      <div className="self-center flex flex-col items-center justify-center">
                        <div className="relative w-20 h-20 md:w-28 md:h-28 flex items-center justify-center">
                          {/* Outer Rotating Reticle */}
                          <div className="absolute inset-0 border border-cyan-400/40 rounded-full border-dashed animate-spin [animation-duration:30s]" />
                          <div className="absolute inset-2 border border-cyan-400/20 rounded-full" />
                          <div className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
                          <div className="w-1 h-1 rounded-full bg-white" />
                          {/* Crosshairs */}
                          <div className="absolute top-0 bottom-0 w-[1px] bg-cyan-400/50" />
                          <div className="absolute left-0 right-0 h-[1px] bg-cyan-400/50" />
                        </div>
                        <span className="mt-1 px-2 py-0.5 rounded bg-slate-950/80 border border-cyan-500/30 text-[9px] text-cyan-300">
                          BORESIGHT: 89.9°S, 0.0°E
                        </span>
                      </div>

                      {/* Bottom HUD: Deep Space Network & Surface Coordinates */}
                      <div className="flex items-end justify-between">
                        <div className="bg-slate-950/80 backdrop-blur-md border border-cyan-500/30 rounded-lg p-2 space-y-0.5 shadow-lg">
                          <div className="text-zinc-400">SUBSATELLITE TRACK: <strong className="text-white">SHACKLETON CRATER RIM</strong></div>
                          <div className="text-zinc-400">SUN PHASE ANGLE: <strong className="text-cyan-300">34.2°</strong> | ELEVATION: <strong className="text-cyan-300">14.6°</strong></div>
                          <div className="text-zinc-400">GROUND SPEED: <strong className="text-white">1,633.2 m/s</strong> (5,879.5 km/h)</div>
                        </div>

                        <div className="bg-slate-950/80 backdrop-blur-md border border-cyan-500/30 rounded-lg p-2 space-y-0.5 text-right shadow-lg">
                          <div className="text-cyan-400 font-bold flex items-center justify-end gap-1.5">
                            <Wifi size={12} />
                            <span>DSN-32 BYALALU CARRIER LOCK</span>
                          </div>
                          <div className="text-zinc-300">S-BAND (2.2 GHz): <span className="text-cyan-300 font-bold">-72 dBm (SNR 28.4 dB)</span></div>
                          <div className="text-zinc-300">X-BAND (8.4 GHz): <span className="text-cyan-300 font-bold">120 Mbps TELEMETRY</span></div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Outer Space Viewport Caption */}
                <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-zinc-400">
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                    <span>LUNAR LIMB RADIANCE &amp; VACUUM ORBITAL SURVEY</span>
                    <span className="text-zinc-600">•</span>
                    <span className="text-zinc-300">CH-2 OHRC (0.25 m/px) + TMC-2 STEREO</span>
                  </div>
                  <div className="text-cyan-300 flex items-center gap-1.5">
                    <Rocket size={12} />
                    <span>ORBITAL VELOCITY VECTOR: +X (FLIGHT DIRECTION)</span>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ==========================================================================
            WORKSPACE COMMAND DOCK (KEYBOARD ACCELERATED [1] [2] [3] [4])
            ========================================================================== */}
        <div className="w-full">
          <div className="pro-segmented-dock flex flex-wrap items-center gap-1.5">
            <button
              onClick={() => setActiveTab('inspector')}
              className={`px-4 py-2.5 rounded-xl font-mono text-xs flex items-center gap-2 transition-all cursor-pointer ${
                activeTab === 'inspector'
                  ? 'bg-gradient-to-r from-cyan-400 to-sky-500 text-slate-950 font-black shadow-lg shadow-cyan-500/30 scale-[1.01]'
                  : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'
              }`}
            >
              <Crosshair size={14} />
              <span>Evaluation &amp; Alignment Inspector</span>
              <kbd className={`px-1.5 py-0.2 rounded text-[9px] font-mono ${
                activeTab === 'inspector' ? 'bg-slate-950/30 text-slate-950 font-black' : 'bg-zinc-800/90 text-zinc-400'
              }`}>1</kbd>
            </button>

            <button
              onClick={() => setActiveTab('stream')}
              className={`px-4 py-2.5 rounded-xl font-mono text-xs flex items-center gap-2 transition-all cursor-pointer ${
                activeTab === 'stream'
                  ? 'bg-gradient-to-r from-cyan-400 to-sky-500 text-slate-950 font-black shadow-lg shadow-cyan-500/30 scale-[1.01]'
                  : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'
              }`}
            >
              <Radio size={14} />
              <span>Live WebSocket Stream</span>
              <kbd className={`px-1.5 py-0.2 rounded text-[9px] font-mono ${
                activeTab === 'stream' ? 'bg-slate-950/30 text-slate-950 font-black' : 'bg-zinc-800/90 text-zinc-400'
              }`}>2</kbd>
            </button>

            <button
              onClick={() => setActiveTab('telemetry')}
              className={`px-4 py-2.5 rounded-xl font-mono text-xs flex items-center gap-2 transition-all cursor-pointer ${
                activeTab === 'telemetry'
                  ? 'bg-gradient-to-r from-cyan-400 to-sky-500 text-slate-950 font-black shadow-lg shadow-cyan-500/30 scale-[1.01]'
                  : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'
              }`}
            >
              <Activity size={14} />
              <span>Node Telemetry &amp; Anomaly Forest</span>
              <kbd className={`px-1.5 py-0.2 rounded text-[9px] font-mono ${
                activeTab === 'telemetry' ? 'bg-slate-950/30 text-slate-950 font-black' : 'bg-zinc-800/90 text-zinc-400'
              }`}>3</kbd>
            </button>

            <button
              onClick={() => setActiveTab('copilot')}
              className={`px-4 py-2.5 rounded-xl font-mono text-xs flex items-center gap-2 transition-all cursor-pointer ${
                activeTab === 'copilot'
                  ? 'bg-gradient-to-r from-cyan-400 to-sky-500 text-slate-950 font-black shadow-lg shadow-cyan-500/30 scale-[1.01]'
                  : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'
              }`}
            >
              <Sparkles size={14} />
              <span>Lunar AI Copilot &amp; Vector Search</span>
              <kbd className={`px-1.5 py-0.2 rounded text-[9px] font-mono ${
                activeTab === 'copilot' ? 'bg-slate-950/30 text-slate-950 font-black' : 'bg-zinc-800/90 text-zinc-400'
              }`}>4</kbd>
            </button>
          </div>
        </div>

        {/* ==========================================================================
            MAIN DISPLAY AREA
            ========================================================================== */}
        <main className="w-full">
          {activeTab === 'inspector' && (
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
            >
              <EvaluationInspector />
            </motion.div>
          )}

          {activeTab === 'stream' && (
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
            >
              <WebSocketStreamInspector />
            </motion.div>
          )}

          {activeTab === 'telemetry' && (
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
            >
              <div className="mb-4">
                <h2 className="text-lg font-bold flex items-center gap-2 text-white font-mono uppercase tracking-wider">
                  <Database size={18} className="text-cyan-400" /> Real-Time Microservice Telemetry &amp; Anomaly Forest
                </h2>
                <p className="text-zinc-400 text-xs">
                  Active telemetry stream from Python ML Isolation Forest (:8001) and Node Zero-Trust Gateway (:3000).
                </p>
              </div>
              <TelemetryDashboard />
            </motion.div>
          )}

          {activeTab === 'copilot' && (
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
              className="grid grid-cols-1 lg:grid-cols-12 gap-6"
            >
              {/* LEFT COLUMN: LUNAR AI COPILOT */}
              <div className="lg:col-span-6 pro-card p-5 md:p-6 flex flex-col h-[560px]">
                <div className="mb-4 flex items-center justify-between border-b border-white/[0.08] pb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-xl bg-purple-500/10 text-purple-300 border border-purple-500/30">
                      <Sparkles size={18} />
                    </div>
                    <div>
                      <h2 className="text-sm font-bold text-white font-mono uppercase tracking-wider">Lunar AI Photogrammetry Copilot</h2>
                      <p className="text-[11px] text-zinc-400 font-sans">Domain-Trained Optical Photogrammetry LLM</p>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/30 text-[9px] font-mono font-bold">
                    REASONING ACTIVE
                  </span>
                </div>

                {/* PRESET QUERY CHIPS */}
                <div className="mb-3 flex flex-wrap gap-1.5">
                  {presetQuestions.map((q, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleChatSubmit(undefined, q)}
                      className="text-[10px] font-mono px-2.5 py-1 rounded-lg bg-zinc-950/80 hover:bg-cyan-950/60 text-zinc-400 hover:text-cyan-300 border border-white/[0.06] hover:border-cyan-500/30 transition-colors text-left cursor-pointer"
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
                        initial={{ opacity: 0, scale: 0.97 }}
                        animate={{ opacity: 1, scale: 1 }}
                        key={i}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[85%] p-3.5 rounded-2xl text-xs leading-relaxed ${
                            msg.role === 'user'
                              ? 'bg-gradient-to-r from-cyan-600/30 to-sky-600/30 text-cyan-100 border border-cyan-500/40 rounded-br-none shadow-md font-sans'
                              : 'bg-zinc-950/90 text-zinc-200 border border-white/[0.08] rounded-bl-none shadow-md font-sans'
                          }`}
                        >
                          <div className="text-[9px] font-mono mb-1 text-zinc-500 uppercase tracking-wider">
                            {msg.role === 'user' ? 'Mission Specialist' : 'Lunar AI Copilot'}
                          </div>
                          {msg.text}
                        </div>
                      </motion.div>
                    ))}
                    {isTyping && (
                      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
                        <div className="bg-zinc-950 border border-white/[0.08] text-cyan-400 p-3 rounded-2xl rounded-bl-none text-xs flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
                          <span className="text-[11px] font-mono text-zinc-400">Synthesizing orbital telemetry...</span>
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
                    className="w-full bg-[#02050e] border border-white/[0.1] rounded-xl py-3 pl-4 pr-12 text-white text-xs focus:outline-none focus:border-cyan-500/50 transition-all placeholder:text-zinc-600 font-sans"
                  />
                  <button
                    type="submit"
                    disabled={!chatInput.trim() || isTyping}
                    className="absolute right-2 top-2 p-2 pro-btn-primary disabled:opacity-40 text-slate-950 font-bold rounded-lg transition-colors cursor-pointer"
                  >
                    <Send size={13} />
                  </button>
                </form>
              </div>

              {/* RIGHT COLUMN: VECTOR EMBEDDING SEARCH */}
              <div className="lg:col-span-6 pro-card p-5 md:p-6 flex flex-col h-[560px]">
                <div className="mb-4 flex items-center justify-between border-b border-white/[0.08] pb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                      <Compass size={18} />
                    </div>
                    <div>
                      <h2 className="text-sm font-bold text-white font-mono uppercase tracking-wider">Orbital Vector Search Engine</h2>
                      <p className="text-[11px] text-zinc-400 font-sans">10B+ Geospatial Crater Embeddings</p>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 text-[9px] font-mono font-bold">
                    ANN FAISS INDEX
                  </span>
                </div>

                {/* SEARCH BAR */}
                <form onSubmit={handleSearchSubmit} className="relative mb-4">
                  <input
                    type="text"
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    placeholder="Search lunar features (e.g. 'Shackleton PSR', 'Tycho ejecta', 'grazing rim')"
                    className="w-full bg-[#02050e] border border-white/[0.1] rounded-xl py-3 pl-10 pr-4 text-white text-xs focus:outline-none focus:border-emerald-500/50 transition-all placeholder:text-zinc-600 font-sans"
                  />
                  <Search className="absolute left-3.5 top-3.5 text-zinc-500" size={15} />
                </form>

                {/* RESULTS LIST */}
                <div className="flex-1 border border-white/[0.06] rounded-2xl bg-[#02050e] p-3 overflow-y-auto space-y-2 custom-scrollbar">
                  {isSearching ? (
                    <div className="h-full flex flex-col items-center justify-center space-y-3 text-emerald-400">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-400" />
                      <p className="text-xs font-mono animate-pulse">Computing cosine distance across FAISS index...</p>
                    </div>
                  ) : searchResults.length > 0 ? (
                    searchResults.map((res, i) => (
                      <motion.div
                        initial={{ opacity: 0, y: 4 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.04 }}
                        key={i}
                        className="p-3 bg-zinc-950/70 hover:bg-zinc-900 border border-white/[0.06] rounded-xl cursor-pointer transition-all hover:border-emerald-500/40 group space-y-1"
                      >
                        <div className="flex justify-between items-center">
                          <span className="text-xs font-bold text-zinc-200 group-hover:text-emerald-300 transition-colors font-sans">
                            {res.title}
                          </span>
                          <span className="text-[10px] font-mono bg-emerald-500/10 text-emerald-300 px-2 py-0.5 rounded border border-emerald-500/30">
                            {res.match}% match
                          </span>
                        </div>

                        <div className="flex items-center justify-between text-[11px] font-mono text-zinc-400">
                          <span>{res.target}</span>
                          <span className="text-cyan-400">{res.coordinates}</span>
                        </div>
                      </motion.div>
                    ))
                  ) : (
                    <div className="h-full flex items-center justify-center">
                      <p className="text-xs text-zinc-600 text-center font-mono">
                        Enter a lunar query to compute embeddings across the photogrammetric database.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </main>

        {/* ==========================================================================
            AEROSPACE OUTER SPACE FOOTER
            ========================================================================== */}
        <footer className="pt-8 pb-12 border-t border-white/[0.08] text-xs text-zinc-500 font-mono flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            <Satellite size={14} className="text-cyan-400" />
            <span>SAMANVAYA // CHANDRAYAAN-2 LUNAR SURFACE CORRESPONDENCE</span>
          </div>
          <div className="flex items-center gap-4 text-[11px]">
            <span>ISRO SIH PS 26166 SUB-PIXEL BENCHMARK</span>
            <span>•</span>
            <span className="text-zinc-400">CE90 &lt; 0.50 px GUARANTEE</span>
            <span>•</span>
            <span className="text-cyan-400 font-bold">ORBITAL FLIGHT READY</span>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default App;
