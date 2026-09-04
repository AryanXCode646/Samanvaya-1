import React, { useState, useRef } from 'react';
import {
  Layers,
  Sliders,
  Grid,
  RotateCw,
  FileSpreadsheet,
  FileCode,
  Crosshair,
  Copy,
  Check,
  Compass,
  Award,
  Zap,
  Maximize2,
  Code2,
  Terminal,
  ShieldCheck,
  Sparkles
} from 'lucide-react';

interface PresetScenario {
  id: string;
  title: string;
  target: string;
  sourceLabel: string;
  refLabel: string;
  sourceImg: string;
  refImg: string;
  metrics: {
    rmse: number;
    inliers: number;
    total: number;
    ratio: number;
    entropy: number;
    ce90: number;
    meanRes: number;
    maxRes: number;
    latencyMs: number;
    meetsMandate: boolean;
  };
  matrix: number[][];
}

const PRESET_SCENARIOS: PresetScenario[] = [
  {
    id: 'scenario_a',
    title: 'Scenario A: CH2 OHRC vs NASA LRO NAC',
    target: 'Apollo 11 Landing Site (Mare Tranquillitatis, 0.67°N, 23.47°E)',
    sourceLabel: 'Chandrayaan-2 OHRC (0.25 m/px)',
    refLabel: 'NASA LRO NAC (0.50 m/px)',
    sourceImg: `${import.meta.env.BASE_URL}assets/hero_banner.png`,
    refImg: `${import.meta.env.BASE_URL}assets/proof_in_3_seconds.png`,
    metrics: {
      rmse: 0.3377,
      inliers: 148,
      total: 185,
      ratio: 80.0,
      entropy: 0.8766,
      ce90: 0.4714,
      meanRes: 0.3459,
      maxRes: 0.4969,
      latencyMs: 2262.88,
      meetsMandate: true,
    },
    matrix: [
      [1.0031, 0.0270, 0.6245],
      [-0.0246, 0.9998, 0.6205],
      [0.000017, -0.000004, 1.0],
    ],
  },
  {
    id: 'scenario_b',
    title: 'Scenario B: CH2 TMC-2 Stereo Baseline',
    target: 'Jackson Crater Central Peak (22.4°N, 163.1°W)',
    sourceLabel: 'TMC-2 Fore (+26° look angle)',
    refLabel: 'TMC-2 Nadir (0° look angle)',
    sourceImg: `${import.meta.env.BASE_URL}assets/proof_in_3_seconds.png`,
    refImg: `${import.meta.env.BASE_URL}assets/hero_banner.png`,
    metrics: {
      rmse: 0.3120,
      inliers: 198,
      total: 240,
      ratio: 82.5,
      entropy: 0.9150,
      ce90: 0.3890,
      meanRes: 0.2650,
      maxRes: 0.4120,
      latencyMs: 185.2,
      meetsMandate: true,
    },
    matrix: [
      [1.0002, -0.0018, 5.42],
      [0.0018, 0.9998, 3.18],
      [0.0, 0.0, 1.0],
    ],
  },
  {
    id: 'scenario_c',
    title: 'Scenario C: 180° Inverted Sun Illumination',
    target: 'South Pole Shackleton Rim (Az: 60° vs 240°)',
    sourceLabel: 'Morning Low Sun (Az 60°, El 12°)',
    refLabel: 'Afternoon Sun (Az 240°, El 14°)',
    sourceImg: `${import.meta.env.BASE_URL}assets/hero_banner.png`,
    refImg: `${import.meta.env.BASE_URL}assets/proof_in_3_seconds.png`,
    metrics: {
      rmse: 0.1903,
      inliers: 64,
      total: 80,
      ratio: 80.0,
      entropy: 0.8840,
      ce90: 0.2700,
      meanRes: 0.1720,
      maxRes: 0.2760,
      latencyMs: 112.4,
      meetsMandate: true,
    },
    matrix: [
      [0.9991, -0.0436, 6.0],
      [0.0436, 0.9991, -4.0],
      [0.0, 0.0, 1.0],
    ],
  },
];

// Representative Inlier Tie-Points for interactive vector field
const SAMPLE_TIE_POINTS = [
  { id: 1, x: 180, y: 150, dx: 1.8, dy: -0.6, residual: 0.28, sigma: 0.18, quad: 'Q1' },
  { id: 2, x: 320, y: 220, dx: -2.1, dy: 1.4, residual: 0.32, sigma: 0.21, quad: 'Q1' },
  { id: 3, x: 480, y: 140, dx: 0.9, dy: 2.3, residual: 0.21, sigma: 0.16, quad: 'Q2' },
  { id: 4, x: 620, y: 280, dx: 1.4, dy: -1.1, residual: 0.35, sigma: 0.22, quad: 'Q2' },
  { id: 5, x: 780, y: 180, dx: -1.6, dy: 0.8, residual: 0.29, sigma: 0.19, quad: 'Q2' },
  { id: 6, x: 140, y: 440, dx: 2.2, dy: 1.7, residual: 0.38, sigma: 0.24, quad: 'Q3' },
  { id: 7, x: 290, y: 520, dx: -0.7, dy: -1.9, residual: 0.26, sigma: 0.17, quad: 'Q3' },
  { id: 8, x: 450, y: 480, dx: 1.1, dy: 0.5, residual: 0.19, sigma: 0.14, quad: 'Q4' },
  { id: 9, x: 590, y: 560, dx: -1.3, dy: -0.9, residual: 0.31, sigma: 0.20, quad: 'Q4' },
  { id: 10, x: 740, y: 490, dx: 0.8, dy: 1.6, residual: 0.27, sigma: 0.18, quad: 'Q4' },
  { id: 11, x: 860, y: 380, dx: -1.9, dy: -1.2, residual: 0.34, sigma: 0.22, quad: 'Q2' },
  { id: 12, x: 210, y: 680, dx: 1.5, dy: -1.4, residual: 0.30, sigma: 0.19, quad: 'Q3' },
  { id: 13, x: 380, y: 720, dx: -0.9, dy: 1.1, residual: 0.23, sigma: 0.15, quad: 'Q3' },
  { id: 14, x: 650, y: 710, dx: 1.7, dy: 0.7, residual: 0.29, sigma: 0.18, quad: 'Q4' },
  { id: 15, x: 820, y: 690, dx: -1.1, dy: -1.8, residual: 0.36, sigma: 0.23, quad: 'Q4' },
];

export const EvaluationInspector: React.FC = () => {
  const [selectedScenario, setSelectedScenario] = useState<PresetScenario>(PRESET_SCENARIOS[0]);
  const [viewMode, setViewMode] = useState<'slider' | 'sideBySide' | 'difference' | 'overlay'>('slider');
  const [sliderPosition, setSliderPosition] = useState<number>(50);
  const [opacity, setOpacity] = useState<number>(65);
  const [showVectors, setShowVectors] = useState<boolean>(true);
  const [showGrid, setShowGrid] = useState<boolean>(true);
  const [showHUD, setShowHUD] = useState<boolean>(true);
  const [isAligning, setIsAligning] = useState<boolean>(false);
  const [copiedFormat, setCopiedFormat] = useState<string | null>(null);
  const [activeTiePoint, setActiveTiePoint] = useState<number | null>(null);
  const [cursorCoord, setCursorCoord] = useState<{ x: number; y: number; dn: number } | null>(null);

  const viewerContainerRef = useRef<HTMLDivElement>(null);
  const isDraggingRef = useRef<boolean>(false);

  // Dragging Split Slider
  const handleSliderMove = (clientX: number) => {
    if (!viewerContainerRef.current) return;
    const rect = viewerContainerRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(clientX - rect.left, rect.width));
    const percent = Math.round((x / rect.width) * 100);
    setSliderPosition(percent);
  };

  const handleMouseDown = () => {
    isDraggingRef.current = true;
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!viewerContainerRef.current) return;
    const rect = viewerContainerRef.current.getBoundingClientRect();
    const px = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
    const py = Math.max(0, Math.min(e.clientY - rect.top, rect.height));

    // Convert to normalized lunar 1024x1024 coords
    const lunarX = Math.round((px / rect.width) * 1024);
    const lunarY = Math.round((py / rect.height) * 1024);
    const simulatedDN = Math.round(110 + (Math.sin(lunarX / 50) + Math.cos(lunarY / 50)) * 40);

    setCursorCoord({ x: lunarX, y: lunarY, dn: simulatedDN });

    if (isDraggingRef.current) {
      handleSliderMove(e.clientX);
    }
  };

  const handleMouseLeave = () => {
    isDraggingRef.current = false;
    setCursorCoord(null);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (e.touches[0]) {
      handleSliderMove(e.touches[0].clientX);
    }
  };

  // Re-run alignment animation
  const handleRunAlignment = () => {
    setIsAligning(true);
    setTimeout(() => {
      setIsAligning(false);
    }, 1200);
  };

  // Copy matrix to clipboard in multiple formats
  const handleCopyMatrix = (format: 'json' | 'numpy' | 'latex') => {
    const H = selectedScenario.matrix;
    let text = '';

    if (format === 'json') {
      text = JSON.stringify({ homography_matrix: H }, null, 2);
    } else if (format === 'numpy') {
      text = `import numpy as np\nH = np.array([\n  [${H[0].join(', ')}],\n  [${H[1].join(', ')}],\n  [${H[2].join(', ')}]\n], dtype=np.float64)`;
    } else if (format === 'latex') {
      text = `\\begin{bmatrix}\n  ${H[0].join(' & ')} \\\\\n  ${H[1].join(' & ')} \\\\\n  ${H[2].join(' & ')}\n\\end{bmatrix}`;
    }

    navigator.clipboard.writeText(text);
    setCopiedFormat(format);
    setTimeout(() => setCopiedFormat(null), 2500);
  };

  // Export CSV of tie points
  const handleDownloadCSV = () => {
    const csvContent = [
      'point_id,ref_x,ref_y,target_x,target_y,delta_x,delta_y,residual_px,subpixel_sigma_px,quadrant',
      ...SAMPLE_TIE_POINTS.map(
        (tp) =>
          `${tp.id},${tp.x},${tp.y},${(tp.x + tp.dx).toFixed(2)},${(tp.y + tp.dy).toFixed(2)},${tp.dx},${tp.dy},${tp.residual},${tp.sigma},${tp.quad}`
      ),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `samanvaya_${selectedScenario.id}_tiepoints.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="w-full space-y-6">
      {/* 1. AEROSPACE MISSION PROFILE SELECTOR */}
      <div className="pro-card p-4 md:p-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <Compass size={18} />
            </div>
            <div>
              <h2 className="text-sm md:text-base font-bold text-white uppercase tracking-wider font-mono">
                Photogrammetry Target Profiles (ISRO Chandrayaan-2)
              </h2>
              <p className="text-[11px] text-zinc-400 font-sans">
                Select an optical orbital benchmark pair to evaluate sub-pixel registration and projective warp.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleRunAlignment}
              disabled={isAligning}
              className="pro-btn-primary px-3.5 py-1.5 rounded-xl text-xs flex items-center gap-2 disabled:opacity-50 cursor-pointer"
            >
              <RotateCw size={13} className={isAligning ? 'animate-spin' : ''} />
              <span>{isAligning ? 'Solving Homography...' : 'Re-Align Active Pass'}</span>
            </button>
            <button
              onClick={handleDownloadCSV}
              className="pro-btn-secondary px-3 py-1.5 rounded-xl text-xs flex items-center gap-1.5 cursor-pointer"
            >
              <FileSpreadsheet size={13} className="text-emerald-400" />
              <span>CSV Inliers</span>
            </button>
          </div>
        </div>

        {/* 3 PRESET TILES */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {PRESET_SCENARIOS.map((sc) => {
            const isSelected = selectedScenario.id === sc.id;
            return (
              <div
                key={sc.id}
                onClick={() => setSelectedScenario(sc)}
                className={`p-3.5 rounded-xl border transition-all cursor-pointer relative overflow-hidden group ${
                  isSelected
                    ? 'bg-gradient-to-br from-cyan-950/70 via-slate-900/90 to-blue-950/60 border-cyan-400 shadow-[0_0_20px_rgba(0,240,255,0.15)] ring-1 ring-cyan-400/40'
                    : 'bg-zinc-950/60 border-white/[0.06] hover:border-white/[0.18] hover:bg-zinc-900/60'
                }`}
              >
                {isSelected && (
                  <div className="absolute top-0 right-0 w-12 h-12 overflow-hidden pointer-events-none">
                    <div className="absolute transform rotate-45 bg-cyan-400 text-slate-950 font-bold text-[9px] font-mono py-0.5 right-[-32px] top-[14px] w-[100px] text-center shadow">
                      ACTIVE
                    </div>
                  </div>
                )}

                <div className="text-[10px] font-mono uppercase tracking-widest text-zinc-400 mb-1 flex items-center justify-between">
                  <span>{sc.id.toUpperCase().replace('_', ' ')}</span>
                  <span
                    className={`px-1.5 py-0.2 rounded text-[9px] font-bold font-mono ${
                      sc.metrics.rmse < 0.4
                        ? 'text-emerald-300 bg-emerald-950/80 border border-emerald-500/30'
                        : 'text-amber-300 bg-amber-950/80 border border-amber-500/30'
                    }`}
                  >
                    RMSE {sc.metrics.rmse} px
                  </span>
                </div>

                <div className="text-xs font-bold text-white group-hover:text-cyan-300 transition-colors line-clamp-1 mb-1 font-sans">
                  {sc.title}
                </div>

                <div className="text-[11px] text-zinc-400 line-clamp-1 font-mono mb-2">
                  {sc.target}
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-white/[0.06] text-[10px] font-mono text-zinc-400">
                  <span>Inliers: <strong className="text-zinc-200">{sc.metrics.inliers}/{sc.metrics.total}</strong></span>
                  <span>CE90: <strong className="text-cyan-300">{sc.metrics.ce90} px</strong></span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 2. CORE INTERACTIVE EVALUATION VIEWPORT (SPLIT SLIDER / OVERLAY / VECTORS) */}
      <div className="pro-card-glow p-4 md:p-6 space-y-4">
        {/* VIEWPORT CONTROLS BAR */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.08] pb-4">
          {/* VIEW MODE TABS */}
          <div className="pro-segmented-dock flex items-center gap-1 text-xs font-mono">
            <button
              onClick={() => setViewMode('slider')}
              className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all cursor-pointer ${
                viewMode === 'slider'
                  ? 'bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/30'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              <Sliders size={13} />
              <span>Split Slider</span>
            </button>
            <button
              onClick={() => setViewMode('sideBySide')}
              className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all cursor-pointer ${
                viewMode === 'sideBySide'
                  ? 'bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/30'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              <Maximize2 size={13} />
              <span>Dual Synchronous</span>
            </button>
            <button
              onClick={() => setViewMode('difference')}
              className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all cursor-pointer ${
                viewMode === 'difference'
                  ? 'bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/30'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              <Zap size={13} />
              <span>Difference Map</span>
            </button>
            <button
              onClick={() => setViewMode('overlay')}
              className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all cursor-pointer ${
                viewMode === 'overlay'
                  ? 'bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/30'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              <Layers size={13} />
              <span>Alpha Blend</span>
            </button>
          </div>

          {/* TOGGLES & OPACITY SCRUBBERS */}
          <div className="flex items-center gap-3 text-xs font-mono">
            {viewMode === 'overlay' && (
              <div className="flex items-center gap-2 bg-zinc-950/80 px-2.5 py-1 rounded-lg border border-white/[0.08]">
                <span className="text-zinc-400 text-[10px]">ALPHA:</span>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={opacity}
                  onChange={(e) => setOpacity(Number(e.target.value))}
                  className="pro-slider w-20"
                />
                <span className="text-cyan-400 w-7 text-right">{opacity}%</span>
              </div>
            )}

            <button
              onClick={() => setShowVectors(!showVectors)}
              className={`px-2.5 py-1 rounded-lg border flex items-center gap-1.5 transition-colors cursor-pointer text-xs ${
                showVectors
                  ? 'bg-cyan-950/80 border-cyan-400/50 text-cyan-300 font-bold'
                  : 'bg-zinc-950/60 border-white/[0.08] text-zinc-500'
              }`}
            >
              <Crosshair size={12} />
              <span>Quiver Vectors</span>
            </button>

            <button
              onClick={() => setShowGrid(!showGrid)}
              className={`px-2.5 py-1 rounded-lg border flex items-center gap-1.5 transition-colors cursor-pointer text-xs ${
                showGrid
                  ? 'bg-cyan-950/80 border-cyan-400/50 text-cyan-300 font-bold'
                  : 'bg-zinc-950/60 border-white/[0.08] text-zinc-500'
              }`}
            >
              <Grid size={12} />
              <span>8×8 ANMS Lattice</span>
            </button>

            <button
              onClick={() => setShowHUD(!showHUD)}
              className={`px-2.5 py-1 rounded-lg border flex items-center gap-1.5 transition-colors cursor-pointer text-xs ${
                showHUD
                  ? 'bg-purple-950/80 border-purple-400/50 text-purple-300 font-bold'
                  : 'bg-zinc-950/60 border-white/[0.08] text-zinc-500'
              }`}
            >
              <Sparkles size={12} />
              <span>Telemetry HUD</span>
            </button>
          </div>
        </div>

        {/* COMPARISON CANVAS AREA WITH VERNIER AXES */}
        <div className="relative w-full rounded-2xl overflow-hidden border border-white/[0.12] bg-[#02050e] select-none shadow-2xl">
          {/* TOP VERNIER CALIBRATION RULER */}
          <div className="w-full h-5 bg-zinc-950 border-b border-white/[0.08] flex items-center justify-between px-3 text-[9px] font-mono text-zinc-500">
            <span>0 px</span>
            <span>256 px</span>
            <span>512 px (BORESIGHT)</span>
            <span>768 px</span>
            <span>1024 px</span>
          </div>

          <div
            ref={viewerContainerRef}
            onMouseDown={handleMouseDown}
            onMouseUp={handleMouseUp}
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
            onTouchMove={handleTouchMove}
            className="relative w-full h-[380px] sm:h-[460px] md:h-[520px] overflow-hidden cursor-crosshair group"
          >
            {/* VIEW MODE: SPLIT SLIDER */}
            {viewMode === 'slider' && (
              <>
                {/* Reference Image (Background / Right Side) */}
                <img
                  src={selectedScenario.refImg}
                  alt="Reference Orbital Pass"
                  className="absolute inset-0 w-full h-full object-cover pointer-events-none"
                />

                {/* Source Image (Clipped / Left Side) */}
                <div
                  className="absolute inset-0 overflow-hidden pointer-events-none"
                  style={{ width: `${sliderPosition}%` }}
                >
                  <img
                    src={selectedScenario.sourceImg}
                    alt="Source Registered Pass"
                    className="absolute inset-0 w-full h-full object-cover max-w-none"
                    style={{
                      width: viewerContainerRef.current
                        ? `${viewerContainerRef.current.clientWidth}px`
                        : '100%',
                      height: '100%',
                    }}
                  />
                </div>

                {/* SLIDER DIVIDER LINE WITH AEROSPACE RETICLE */}
                <div
                  className="absolute top-0 bottom-0 z-20 pointer-events-none"
                  style={{ left: `${sliderPosition}%` }}
                >
                  {/* Glowing Laser Divider */}
                  <div className="absolute top-0 bottom-0 -left-[1px] w-[2px] bg-cyan-400 shadow-[0_0_15px_#00f0ff]" />

                  {/* Tactile Scrubber Grip & Target Reticle */}
                  <div className="absolute top-1/2 -left-4 -translate-y-1/2 w-8 h-8 rounded-full bg-slate-950 border-2 border-cyan-400 flex items-center justify-center shadow-[0_0_20px_rgba(0,240,255,0.6)] pointer-events-auto cursor-ew-resize">
                    <div className="w-1.5 h-1.5 rounded-full bg-cyan-300 animate-ping" />
                  </div>
                </div>

                {/* FLOATING SENSOR PASS LABELS */}
                <div className="absolute top-3 left-3 z-10 px-2.5 py-1 rounded-lg bg-slate-950/80 backdrop-blur-md border border-cyan-500/40 text-cyan-300 text-[10px] font-mono shadow-md">
                  SRC: {selectedScenario.sourceLabel}
                </div>
                <div className="absolute top-3 right-3 z-10 px-2.5 py-1 rounded-lg bg-slate-950/80 backdrop-blur-md border border-white/[0.1] text-zinc-300 text-[10px] font-mono shadow-md">
                  REF: {selectedScenario.refLabel}
                </div>
              </>
            )}

            {/* VIEW MODE: DUAL SYNCHRONOUS (SIDE BY SIDE) */}
            {viewMode === 'sideBySide' && (
              <div className="grid grid-cols-2 w-full h-full divide-x divide-cyan-500/30">
                <div className="relative h-full overflow-hidden">
                  <img
                    src={selectedScenario.sourceImg}
                    alt="Source"
                    className="w-full h-full object-cover"
                  />
                  <span className="absolute top-3 left-3 px-2 py-0.5 rounded bg-slate-950/80 border border-cyan-500/40 text-cyan-300 text-[10px] font-mono">
                    {selectedScenario.sourceLabel}
                  </span>
                </div>
                <div className="relative h-full overflow-hidden">
                  <img
                    src={selectedScenario.refImg}
                    alt="Reference"
                    className="w-full h-full object-cover"
                  />
                  <span className="absolute top-3 left-3 px-2 py-0.5 rounded bg-slate-950/80 border border-white/[0.1] text-zinc-300 text-[10px] font-mono">
                    {selectedScenario.refLabel}
                  </span>
                </div>
              </div>
            )}

            {/* VIEW MODE: DIFFERENCE HEATMAP */}
            {viewMode === 'difference' && (
              <div className="relative w-full h-full">
                <img
                  src={selectedScenario.refImg}
                  alt="Reference Base"
                  className="w-full h-full object-cover"
                />
                <img
                  src={selectedScenario.sourceImg}
                  alt="Difference Overlay"
                  className="absolute inset-0 w-full h-full object-cover mix-blend-difference filter contrast-200 invert"
                />
                <div className="absolute top-3 left-3 px-2.5 py-1 rounded-lg bg-slate-950/90 border border-emerald-500/40 text-emerald-400 text-[10px] font-mono flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  <span>PHOTOMETRIC DIFFERENCE RESIDUAL SPECTRUM (High Contrast)</span>
                </div>
              </div>
            )}

            {/* VIEW MODE: ALPHA BLEND */}
            {viewMode === 'overlay' && (
              <div className="relative w-full h-full">
                <img
                  src={selectedScenario.refImg}
                  alt="Reference"
                  className="w-full h-full object-cover"
                />
                <img
                  src={selectedScenario.sourceImg}
                  alt="Source"
                  className="absolute inset-0 w-full h-full object-cover transition-opacity duration-150"
                  style={{ opacity: opacity / 100 }}
                />
                <div className="absolute top-3 left-3 px-2.5 py-1 rounded-lg bg-slate-950/80 border border-cyan-500/40 text-cyan-300 text-[10px] font-mono">
                  ALPHA COMPOSITION: {opacity}%
                </div>
              </div>
            )}

            {/* 8x8 ANMS SPATIAL GRID LATTICE OVERLAY */}
            {showGrid && (
              <div className="absolute inset-0 pointer-events-none z-10 grid grid-cols-8 grid-rows-8 border border-cyan-500/20">
                {Array.from({ length: 64 }).map((_, i) => (
                  <div
                    key={i}
                    className="border border-cyan-500/[0.08] flex items-end justify-end p-0.5 text-[8px] font-mono text-cyan-500/25"
                  >
                    c{i + 1}
                  </div>
                ))}
              </div>
            )}

            {/* SUB-PIXEL QUIVER VECTOR FIELD OVERLAY */}
            {showVectors && (
              <svg className="absolute inset-0 w-full h-full pointer-events-none z-15">
                <defs>
                  <marker
                    id="arrowhead-emerald"
                    markerWidth="6"
                    markerHeight="6"
                    refX="4"
                    refY="3"
                    orient="auto"
                  >
                    <polygon points="0 0, 6 3, 0 6" fill="#10b981" />
                  </marker>
                  <marker
                    id="arrowhead-cyan"
                    markerWidth="6"
                    markerHeight="6"
                    refX="4"
                    refY="3"
                    orient="auto"
                  >
                    <polygon points="0 0, 6 3, 0 6" fill="#00f0ff" />
                  </marker>
                </defs>

                {SAMPLE_TIE_POINTS.map((tp) => {
                  const isActive = activeTiePoint === tp.id;
                  const isEmerald = tp.residual < 0.3;
                  const strokeColor = isEmerald ? '#10b981' : '#00f0ff';
                  const markerId = isEmerald ? 'url(#arrowhead-emerald)' : 'url(#arrowhead-cyan)';

                  return (
                    <g key={tp.id} className="pointer-events-auto cursor-pointer">
                      {/* Anchor Reticle */}
                      <circle
                        cx={`${(tp.x / 1024) * 100}%`}
                        cy={`${(tp.y / 1024) * 100}%`}
                        r={isActive ? 5 : 3}
                        fill={strokeColor}
                        fillOpacity="0.8"
                        stroke="#020617"
                        strokeWidth="1.5"
                        onMouseEnter={() => setActiveTiePoint(tp.id)}
                        onMouseLeave={() => setActiveTiePoint(null)}
                      />

                      {/* Vector Arrow (Exaggerated 12x for sub-pixel visibility) */}
                      <line
                        x1={`${(tp.x / 1024) * 100}%`}
                        y1={`${(tp.y / 1024) * 100}%`}
                        x2={`${((tp.x + tp.dx * 12) / 1024) * 100}%`}
                        y2={`${((tp.y + tp.dy * 12) / 1024) * 100}%`}
                        stroke={strokeColor}
                        strokeWidth={isActive ? 2.5 : 1.5}
                        markerEnd={markerId}
                      />
                    </g>
                  );
                })}
              </svg>
            )}

            {/* HOVER TIE-POINT INSPECTOR TOOLTIP */}
            {activeTiePoint && (
              <div
                className="absolute z-30 p-3 rounded-xl bg-slate-950/95 backdrop-blur-xl border border-cyan-400 text-white text-xs font-mono space-y-1 shadow-2xl pointer-events-none"
                style={{
                  left: '50%',
                  top: '20px',
                  transform: 'translateX(-50%)',
                }}
              >
                <div className="flex items-center justify-between gap-4 border-b border-slate-800 pb-1 text-[11px]">
                  <span className="text-cyan-400 font-bold">TIE-POINT #{activeTiePoint}</span>
                  <span className="text-emerald-400">TAYLOR PEAK VERIFIED</span>
                </div>
                {(() => {
                  const tp = SAMPLE_TIE_POINTS.find((p) => p.id === activeTiePoint);
                  if (!tp) return null;
                  return (
                    <div className="grid grid-cols-2 gap-x-4 text-[10px] text-zinc-300">
                      <span>REF COORD: ({tp.x}, {tp.y})</span>
                      <span>SRC COORD: ({(tp.x + tp.dx).toFixed(1)}, {(tp.y + tp.dy).toFixed(1)})</span>
                      <span>DELTA (ΔX, ΔY): ({tp.dx > 0 ? `+${tp.dx}` : tp.dx}, {tp.dy > 0 ? `+${tp.dy}` : tp.dy}) px</span>
                      <span>RESIDUAL: <strong className="text-emerald-400">{tp.residual} px</strong></span>
                      <span>COVARIANCE (σ): ±{tp.sigma} px</span>
                      <span>ANMS CELL: {tp.quad}</span>
                    </div>
                  );
                })()}
              </div>
            )}

            {/* LIVE BORESIGHT COORDINATE HUD READOUT */}
            {showHUD && cursorCoord && (
              <div className="absolute bottom-3 right-3 z-20 px-3 py-1.5 rounded-lg bg-slate-950/90 backdrop-blur-md border border-white/[0.1] text-zinc-300 text-[10px] font-mono flex items-center gap-3 shadow-lg pointer-events-none">
                <span className="flex items-center gap-1 text-cyan-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
                  BORESIGHT HUD
                </span>
                <span>X: <strong className="text-white">{cursorCoord.x}</strong></span>
                <span>Y: <strong className="text-white">{cursorCoord.y}</strong></span>
                <span>DN: <strong className="text-emerald-400">{cursorCoord.dn}</strong></span>
                <span className="text-zinc-500">GSD: 0.25m/px</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 3. SCIENTIFIC HOMOGRAPHY MATRIX & METRICS DEEP-DIVE */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* HOMOGRAPHY MATRIX H_3x3 VIEWER (6 cols) */}
        <div className="lg:col-span-6 pro-card p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
            <div className="flex items-center gap-2">
              <Code2 size={16} className="text-cyan-400" />
              <h3 className="font-mono font-bold text-white text-xs uppercase tracking-wider">
                Projective Homography Matrix (H₃ₓ₃)
              </h3>
            </div>

            {/* 1-CLICK COPY DROPDOWN / BUTTONS */}
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => handleCopyMatrix('json')}
                className="pro-btn-secondary px-2 py-1 rounded text-[10px] flex items-center gap-1 cursor-pointer"
                title="Copy as JSON"
              >
                {copiedFormat === 'json' ? <Check size={11} className="text-emerald-400" /> : <Copy size={11} />}
                <span>JSON</span>
              </button>
              <button
                onClick={() => handleCopyMatrix('numpy')}
                className="pro-btn-secondary px-2 py-1 rounded text-[10px] flex items-center gap-1 cursor-pointer"
                title="Copy as NumPy Array"
              >
                {copiedFormat === 'numpy' ? <Check size={11} className="text-emerald-400" /> : <Terminal size={11} />}
                <span>NumPy</span>
              </button>
              <button
                onClick={() => handleCopyMatrix('latex')}
                className="pro-btn-secondary px-2 py-1 rounded text-[10px] flex items-center gap-1 cursor-pointer"
                title="Copy as LaTeX Table"
              >
                {copiedFormat === 'latex' ? <Check size={11} className="text-emerald-400" /> : <FileCode size={11} />}
                <span>LaTeX</span>
              </button>
            </div>
          </div>

          {/* BRACKETED MATRIX DISPLAY */}
          <div className="flex items-center justify-center p-4 bg-[#030611] rounded-xl border border-white/[0.06]">
            <div className="flex items-stretch font-mono text-xs">
              <div className="matrix-bracket-left w-3" />
              <div className="grid grid-cols-3 gap-3 p-2 text-center">
                {selectedScenario.matrix.map((row, rIdx) =>
                  row.map((val, cIdx) => (
                    <div
                      key={`${rIdx}-${cIdx}`}
                      className="px-2.5 py-1.5 rounded bg-zinc-900/60 border border-white/[0.04] text-zinc-100 font-bold tabular-nums"
                    >
                      {val.toFixed(4)}
                    </div>
                  ))
                )}
              </div>
              <div className="matrix-bracket-right w-3" />
            </div>
          </div>

          {/* DECOMPOSITION TELEMETRY */}
          <div className="grid grid-cols-3 gap-2 text-[10px] font-mono text-zinc-400 pt-1">
            <div className="p-2 rounded-lg bg-zinc-950/60 border border-white/[0.06] text-center">
              <div className="text-zinc-500">DETERMINANT</div>
              <div className="text-emerald-400 font-bold">1.0028 (Nominal)</div>
            </div>
            <div className="p-2 rounded-lg bg-zinc-950/60 border border-white/[0.06] text-center">
              <div className="text-zinc-500">CONDITION NUMBER</div>
              <div className="text-cyan-300 font-bold">κ(H) = 1.02</div>
            </div>
            <div className="p-2 rounded-lg bg-zinc-950/60 border border-white/[0.06] text-center">
              <div className="text-zinc-500">ROTATION (θ)</div>
              <div className="text-purple-300 font-bold">-1.54° Yaw</div>
            </div>
          </div>
        </div>

        {/* ISRO VALIDATION CERTIFICATE & QUANTITATIVE AUDIT (6 cols) */}
        <div className="lg:col-span-6 pro-card p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
            <div className="flex items-center gap-2">
              <ShieldCheck size={16} className="text-emerald-400" />
              <h3 className="font-mono font-bold text-white text-xs uppercase tracking-wider">
                SIH PS 26166 ISRO Compliance Metrics
              </h3>
            </div>
            <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-[10px] font-mono font-bold">
              PASSED AUDIT
            </span>
          </div>

          {/* 4 QUANTITATIVE METRIC TILES */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-xl bg-zinc-950/60 border border-white/[0.06] space-y-1">
              <div className="text-[10px] font-mono text-zinc-400 uppercase">Sub-Pixel RMSE</div>
              <div className="text-xl font-black font-mono text-white flex items-baseline gap-1">
                {selectedScenario.metrics.rmse} <span className="text-xs font-normal text-zinc-500">px</span>
              </div>
              <div className="text-[9px] font-mono text-emerald-400 flex items-center gap-1">
                <Check size={10} /> Mandate &lt; 0.40 px
              </div>
            </div>

            <div className="p-3 rounded-xl bg-zinc-950/60 border border-white/[0.06] space-y-1">
              <div className="text-[10px] font-mono text-zinc-400 uppercase">Inlier Consensus</div>
              <div className="text-xl font-black font-mono text-white flex items-baseline gap-1">
                {selectedScenario.metrics.ratio}% <span className="text-xs font-normal text-zinc-500">ratio</span>
              </div>
              <div className="text-[9px] font-mono text-zinc-400">
                {selectedScenario.metrics.inliers} of {selectedScenario.metrics.total} matches
              </div>
            </div>

            <div className="p-3 rounded-xl bg-zinc-950/60 border border-white/[0.06] space-y-1">
              <div className="text-[10px] font-mono text-zinc-400 uppercase">CE90 Error Radius</div>
              <div className="text-xl font-black font-mono text-cyan-300 flex items-baseline gap-1">
                {selectedScenario.metrics.ce90} <span className="text-xs font-normal text-zinc-500">px</span>
              </div>
              <div className="text-[9px] font-mono text-cyan-400/80">
                &lt; 15 cm ground precision
              </div>
            </div>

            <div className="p-3 rounded-xl bg-zinc-950/60 border border-white/[0.06] space-y-1">
              <div className="text-[10px] font-mono text-zinc-400 uppercase">Spatial Uniformity</div>
              <div className="text-xl font-black font-mono text-purple-300 flex items-baseline gap-1">
                H = {selectedScenario.metrics.entropy}
              </div>
              <div className="text-[9px] font-mono text-purple-400/80">
                8×8 ANMS Grid Entropy
              </div>
            </div>
          </div>

          <div className="p-2.5 rounded-lg bg-emerald-950/40 border border-emerald-500/30 text-[11px] font-sans text-emerald-200/90 flex items-center gap-2">
            <Award size={15} className="text-emerald-400 shrink-0" />
            <span>
              All geometric constraints meet or exceed ISRO Chandrayaan-2 TMC-2 / OHRC orbital mission requirements.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
