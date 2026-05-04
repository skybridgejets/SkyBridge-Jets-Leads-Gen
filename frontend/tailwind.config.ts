import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          50: '#f0f3f9',
          100: '#d9e0f0',
          200: '#b3c1e0',
          300: '#8da2d1',
          400: '#6783c1',
          500: '#4164b2',
          600: '#34508e',
          700: '#273c6b',
          800: '#1a2847',
          900: '#0d1424',
          950: '#070a12',
        },
        gold: {
          50: '#fdf9ef',
          100: '#faf0d5',
          200: '#f4dea9',
          300: '#edc974',
          400: '#e5af3e',
          500: '#d4982a',
          600: '#b87a20',
          700: '#995c1d',
          800: '#7d4a1f',
          900: '#683d1d',
          950: '#3b1f0d',
        },
      },
    },
  },
  plugins: [],
}
export default config
