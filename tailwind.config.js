/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./templates/**/*.html', './src/**/*.py'],
  theme: {
    extend: {
      colors: {
        'deep-space': '#0B1120',
        panel: '#1E293B',
        'panel-hover': '#334155',
        border: '#475569',
        'accent-primary': '#F59E0B',
        'accent-primary-hover': '#FBBF24',
        'accent-secondary': '#2DD4BF',
        positive: '#2DD4BF',
        'positive-bg': '#0d2c2e',
        negative: '#F87171',
        'negative-bg': '#450a0a',
      },
      fontFamily: {
        sans: ['Inter', 'Arial', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
