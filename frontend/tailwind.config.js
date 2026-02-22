/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#6366f1",
        secondary: "#ec4899",
        accent: "#8b5cf6",
        "bg-dark": "#070912",
        success: "#10b981",
        error: "#f43f5e",
        "glass-bg": "var(--glass-bg)",
        "glass-border": "var(--glass-border)",
        "surface": "var(--surface)",
      },
    },
  },
  plugins: [],
}
