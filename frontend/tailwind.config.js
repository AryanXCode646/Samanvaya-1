/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        lunar: {
          dark: '#0f172a',
          card: 'rgba(30, 41, 59, 0.7)',
          accent: '#38bdf8'
        }
      }
    },
  },
  plugins: [],
}
