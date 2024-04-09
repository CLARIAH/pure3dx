/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./**/*.{html,js}"],
  safelist: [
    "order-first",
    "order-last",
    "order-none",
    "order-1",
    "order-2",
    "order-3",
    "order-4",
    "order-5",
    "order-6",
    "order-7",
    "order-8",
    "order-9",
    "order-10",
    "order-11",
    "order-12",
    "h-4",
    "w-4",
    "fill-blue-700",
  ],
  theme: {
    extend: {
      fontFamily: {
        public: ["Public Sans", "sans-serif"],
        poppins: ["Poppins", "sans-serif"],
      },
      colors: {
        p3D: {
          50: '#c6ffe9',
          100: '#99e6c8',
          200: '#83e2bc',
          300: '#9eddd1',
          400: '#2ac0cc',
          500: '#73b9c8',
          600: '#4986c7',
          700: '#2765e6',
          800: 'hsl(220,69%,42%)',
          900: '#293845',
        }
      },
      dropShadow: {
        top: "15px 15px 15px rgba(0, 0, 0, 0.75)",
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
}
