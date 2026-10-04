/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#14181F",
        paper: "#F6F5F1",
        surface: "#FFFFFF",
        line: "#E4E2DA",
        accent: {
          DEFAULT: "#3654FF",
          dark: "#2841D6",
          soft: "#EAEDFF",
        },
        success: { DEFAULT: "#1B8A5A", soft: "#E4F5EC" },
        warning: { DEFAULT: "#B7791F", soft: "#FBF0DD" },
        danger: { DEFAULT: "#C4402B", soft: "#FBEAE7" },
        muted: "#6B7280",
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body: ["'Inter'", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
      borderRadius: {
        sm: "4px",
        DEFAULT: "6px",
        md: "8px",
        lg: "12px",
      },
    },
  },
  plugins: [],
};
