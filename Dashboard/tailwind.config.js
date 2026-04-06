/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: "#0a0a0c",
        teal: {
          neon: "#2dd4bf",
        },
      },
      boxShadow: {
        glass: "0 0 40px rgba(45, 212, 191, 0.08)",
      },
      animation: {
        "pulse-teal": "pulseTeal 1.4s ease-in-out infinite",
        glitch: "glitch 0.35s steps(2) infinite",
        scan: "scanSweep 2.2s ease-in-out forwards",
      },
      keyframes: {
        pulseTeal: {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(45, 212, 191, 0.35)" },
          "50%": { boxShadow: "0 0 24px 4px rgba(45, 212, 191, 0.45)" },
        },
        glitch: {
          "0%": { transform: "translate(0,0)", filter: "hue-rotate(0deg)" },
          "25%": { transform: "translate(-2px,1px)", filter: "hue-rotate(90deg)" },
          "50%": { transform: "translate(2px,-1px)", filter: "hue-rotate(180deg)" },
          "75%": { transform: "translate(-1px,-2px)", filter: "hue-rotate(270deg)" },
          "100%": { transform: "translate(0,0)", filter: "hue-rotate(0deg)" },
        },
        scanSweep: {
          "0%": { transform: "translateY(-120%)" },
          "100%": { transform: "translateY(120%)" },
        },
      },
    },
  },
  plugins: [],
};
