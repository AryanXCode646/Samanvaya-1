/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        display: ['Outfit', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        space: {
          void: '#050813',
          base: '#080d1a',
          surface: '#0d1527',
          card: 'rgba(13, 21, 39, 0.72)',
          border: 'rgba(56, 189, 248, 0.15)',
        },
        lunar: {
          dark: '#070b14',
          card: 'rgba(15, 23, 42, 0.75)',
          accent: '#38bdf8',
          cyan: '#00f0ff',
          glow: 'rgba(0, 240, 255, 0.25)',
        },
        isro: {
          orange: '#ff6f00',
          blue: '#0284c7',
        }
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 12s linear infinite',
        'glow-pulse': 'glow 2.5s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 10px rgba(0, 240, 255, 0.2), inset 0 0 10px rgba(0, 240, 255, 0.1)' },
          '100%': { boxShadow: '0 0 25px rgba(0, 240, 255, 0.5), inset 0 0 15px rgba(0, 240, 255, 0.25)' },
        }
      },
      backgroundImage: {
        'space-grid': 'radial-gradient(rgba(56, 189, 248, 0.08) 1px, transparent 1px)',
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      }
    },
  },
  plugins: [],
}
