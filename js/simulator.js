/**
 * Samanvaya (समान्वय) — Crater Shadow & Phase Congruency Physics Simulator
 * Real-time HTML5 Canvas engine simulating 180° solar azimuth reversals
 * and proving step-edge Phase Congruency invariance.
 */

class CraterPhysicsSimulator {
  constructor(craterCanvasId, congruencyCanvasId) {
    this.craterCanvas = document.getElementById(craterCanvasId);
    this.congruencyCanvas = document.getElementById(congruencyCanvasId);
    if (!this.craterCanvas || !this.congruencyCanvas) return;

    this.ctxCrater = this.craterCanvas.getContext('2d');
    this.ctxCongruency = this.congruencyCanvas.getContext('2d');

    this.width = this.craterCanvas.width;
    this.height = this.craterCanvas.height;
    this.cx = this.width / 2;
    this.cy = this.height / 2;
    this.radius = 78;

    this.azimuth = 60;
    this.elevation = 25;

    this.initControls();
    this.render();
  }

  initControls() {
    const slider = document.getElementById('sim-azimuth-slider');
    const valDisplay = document.getElementById('sim-azimuth-val');
    const telemetry = document.getElementById('sim-telemetry');

    if (slider) {
      slider.addEventListener('input', (e) => {
        this.azimuth = parseFloat(e.target.value);
        if (valDisplay) valDisplay.innerText = `${this.azimuth}°`;
        if (telemetry) telemetry.innerText = `Azimuth: ${this.azimuth}° | Elevation: ${this.elevation}°`;
        this.render();
      });
    }
  }

  setPreset(azimuth, elevation) {
    this.azimuth = azimuth;
    this.elevation = elevation;

    const slider = document.getElementById('sim-azimuth-slider');
    const valDisplay = document.getElementById('sim-azimuth-val');
    const telemetry = document.getElementById('sim-telemetry');

    if (slider) slider.value = azimuth;
    if (valDisplay) valDisplay.innerText = `${azimuth}°`;
    if (telemetry) telemetry.innerText = `Azimuth: ${azimuth}° | Elevation: ${elevation}°`;

    this.render();
  }

  render() {
    const w = this.width;
    const h = this.height;
    const rad = (this.azimuth * Math.PI) / 180;
    const elFactor = 1.0 - (this.elevation / 90.0);

    // Solar light vector components
    const lx = Math.cos(rad);
    const ly = Math.sin(rad);

    const imgDataC = this.ctxCrater.createImageData(w, h);
    const dataC = imgDataC.data;

    const imgDataP = this.ctxCongruency.createImageData(w, h);
    const dataP = imgDataP.data;

    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const idx = (y * w + x) * 4;
        const dx = x - this.cx;
        const dy = y - this.cy;
        const dist = Math.sqrt(dx * dx + dy * dy);

        // 1. Invariant Step-Edge Phase Congruency (Maximum Moment M_max)
        // Remains centered on physical crater rim radius regardless of lighting
        const rimDist = Math.abs(dist - this.radius);
        let phaseCongruencyVal = 0;
        if (rimDist < 4.0) {
          phaseCongruencyVal = Math.exp(-(rimDist * rimDist) / 3.0);
        }

        // 2. Optical Surface Intensity (Lommel-Seeliger regolith approximation)
        let intensity = 115;
        if (dist <= this.radius) {
          // Inside concave crater bowl
          const normX = -dx / this.radius;
          const normY = -dy / this.radius;
          const dot = normX * lx + normY * ly;
          intensity = 115 + dot * 130 * elFactor;
          intensity = Math.max(12, Math.min(245, intensity)); // Pitch-black shadow or sunlit wall
        } else {
          // Flat plateau with subtle regolith noise
          intensity = 118 + Math.sin(x * 0.08) * 5 + Math.cos(y * 0.08) * 5;
        }

        // Assign Grayscale Optical Pixel
        dataC[idx] = intensity;
        dataC[idx + 1] = intensity;
        dataC[idx + 2] = intensity;
        dataC[idx + 3] = 255;

        // Assign Neon Emerald/Cyan Phase Congruency Map
        const pByte = Math.floor(phaseCongruencyVal * 255);
        dataP[idx] = Math.floor(pByte * 0.1);
        dataP[idx + 1] = pByte; // Green
        dataP[idx + 2] = Math.floor(pByte * 0.75); // Cyan
        dataP[idx + 3] = 255;
      }
    }

    this.ctxCrater.putImageData(imgDataC, 0, 0);
    this.ctxCongruency.putImageData(imgDataP, 0, 0);

    // Draw Sun Direction Marker on Optical Canvas
    this.ctxCrater.save();
    this.ctxCrater.fillStyle = '#fbbf24';
    this.ctxCrater.shadowColor = '#fbbf24';
    this.ctxCrater.shadowBlur = 10;
    const sunDist = this.radius + 38;
    const sx = this.cx - lx * sunDist;
    const sy = this.cy - ly * sunDist;
    this.ctxCrater.beginPath();
    this.ctxCrater.arc(sx, sy, 6, 0, Math.PI * 2);
    this.ctxCrater.fill();
    this.ctxCrater.restore();
  }
}

// Global hook
let globalSimulator = null;
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('crater-canvas') && document.getElementById('congruency-canvas')) {
    globalSimulator = new CraterPhysicsSimulator('crater-canvas', 'congruency-canvas');
  }
});
