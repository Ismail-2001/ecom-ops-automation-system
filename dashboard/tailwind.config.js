/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        agent: {
          fraud: "#EF4444",      // Red
          inventory: "#F59E0B",  // Amber
          pricing: "#3B82F6",    // Blue
          reviews: "#8B5CF6",    // Purple
          marketing: "#14B8A6",  // Teal
        },
        risk: {
          critical: "#EF4444",
          high: "#F97316",
          medium: "#F59E0B",
          low: "#22C55E",
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'monospace'],
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
