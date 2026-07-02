/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        void: "#0B1120",
        "void-light": "#0F172A",
        surface: {
          DEFAULT: "#111827",
          2: "#1A2035",
          3: "#1E293B",
          4: "#253047",
        },
        border: {
          DEFAULT: "rgba(99, 102, 241, 0.10)",
          bright: "rgba(99, 102, 241, 0.20)",
          solid: "#1E293B",
        },
        primary: {
          DEFAULT: "#6366F1",
          hover: "#818CF8",
          muted: "rgba(99, 102, 241, 0.15)",
        },
        success: "#10B981",
        warning: "#F59E0B",
        danger: "#EF4444",
        info: "#06B6D4",
        text: {
          primary: "#F1F5F9",
          secondary: "#94A3B8",
          muted: "#64748B",
        },
      },
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      fontSize: {
        "display-lg": ["30px", { lineHeight: "36px", fontWeight: "700" }],
        "display-md": ["24px", { lineHeight: "30px", fontWeight: "600" }],
        "display-sm": ["18px", { lineHeight: "24px", fontWeight: "600" }],
        "body-lg": ["16px", { lineHeight: "24px" }],
        "body-md": ["14px", { lineHeight: "20px" }],
        "body-sm": ["12px", { lineHeight: "16px" }],
        "data-lg": ["24px", { lineHeight: "24px", fontWeight: "600" }],
        "data-md": ["16px", { lineHeight: "16px", fontWeight: "500" }],
        "data-sm": ["13px", { lineHeight: "16px", fontWeight: "500" }],
        "label": ["11px", { lineHeight: "16px", letterSpacing: "0.06em", fontWeight: "600" }],
      },
      spacing: {
        sidebar: "240px",
        "sidebar-collapsed": "68px",
        topbar: "64px",
        card: "18px",
        section: "16px",
        inline: "8px",
      },
      borderRadius: {
        card: "12px",
        button: "8px",
        badge: "6px",
        pill: "9999px",
      },
      animation: {
        "pulse-agent": "pulse-agent 2s ease-in-out infinite",
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-up": "slideUp 0.3s ease-out",
        "glow": "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        "pulse-agent": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.4" },
        },
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        glow: {
          "0%": { boxShadow: "0 0 5px rgba(99, 102, 241, 0.1)" },
          "100%": { boxShadow: "0 0 20px rgba(99, 102, 241, 0.15)" },
        },
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
