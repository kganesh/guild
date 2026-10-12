/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        serif: ["Instrument Serif", "Georgia", "serif"],
        sans: ["Manrope", "system-ui", "sans-serif"],
      },
      colors: {
        ink: "#12161B",
        paper: "#F5F3EE",
        moss: "#1C6B52",
        clay: "#B44A2E",
      },
    },
  },
  plugins: [],
};
