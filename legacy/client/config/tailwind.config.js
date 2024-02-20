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
        diGreen: {
          50: "hsl(174, 40%, 94%)",
          100: "hsl(174, 40%, 90%)",
          200: "hsl(174, 66%, 80%)",
          300: "hsl(174, 66%, 70%)",
          400: "hsl(174, 66%, 57%)",
          500: "hsl(174, 66%, 50%)",
          600: "hsl(174, 66%, 40%)",
          700: "hsl(174, 66%, 30%)",
          800: "hsl(174, 66%, 20%)",
          900: "hsl(174, 66%, 10%)",
        },
        tempCanvas: {
          50: "hsl(37, 25%, 96%)",
          100: "hsl(37, 25%, 90%)",
          200: "hsl(37, 25%, 80%)",
          300: "hsl(37, 25%, 70%)",
          400: "hsl(37, 25%, 60%)",
          500: "hsl(37, 25%, 50%)",
          600: "hsl(37, 25%, 40%)",
          700: "hsl(37, 25%, 30%)",
          800: "hsl(37, 25%, 20%)",
          900: "hsl(37, 25%, 10%)",
        },
        sand: {
          50: "hsl(36, 20%, 97%)",
          100: "hsl(36, 20%, 90%)",
          200: "hsl(36, 20%, 80%)",
          300: "hsl(36, 20%, 70%)",
          400: "hsl(36, 20%, 60%)",
          500: "hsl(36, 20%, 50%)",
          600: "hsl(36, 20%, 40%)",
          700: "hsl(36, 20%, 30%)",
          800: "hsl(36, 20%, 20%)",
          900: "hsl(36, 20%, 10%)",
        },
        pureblue: {
          50: "hsl(220, 79%, 97%)",
          100: "hsl(220, 79%, 90%)",
          200: "hsl(220, 79%, 80%)",
          300: "hsl(220, 79%, 70%)",
          400: "hsl(220, 79%, 60%)",
          500: "hsl(220, 79%, 52%)",
          600: "hsl(220, 79%, 40%)",
          700: "hsl(220, 79%, 30%)",
          800: "hsl(220, 79%, 20%)",
          900: "hsl(220, 79%, 10%)",
        },
        puregreen: {
          50: "hsl(156, 62%, 97%)",
          100: "hsl(156, 62%, 90%)",
          200: "hsl(156, 62%, 80%)",
          300: "hsl(156, 62%, 70%)",
          400: "hsl(156, 62%, 60%)",
          500: "hsl(156, 62%, 52%)",
          600: "hsl(156, 62%, 40%)",
          700: "hsl(156, 62%, 30%)",
          800: "hsl(156, 62%, 20%)",
          900: "hsl(156, 62%, 10%)",
        },
        diploblue: {
          50: "hsl(216, 85%, 97%)",
          100: "hsl(216, 85%, 90%)",
          200: "hsl(216, 85%, 80%)",
          300: "hsl(216, 85%, 70%)",
          400: "hsl(216, 85%, 60%)",
          500: "hsl(216, 85%, 52%)",
          600: "hsl(216, 85%, 40%)",
          700: "hsl(216, 85%, 30%)",
          800: "hsl(216, 85%, 20%)",
          900: "hsl(216, 85%, 10%)",
        },
        blueGrey: {
          50: "hsl(216, 35%, 97%)",
          100: "hsl(216, 35%, 90%)",
          200: "hsl(216, 35%, 80%)",
          300: "hsl(216, 35%, 70%)",
          400: "hsl(216, 35%, 60%)",
          500: "hsl(216, 35%, 52%)",
          600: "hsl(216, 35%, 40%)",
          700: "hsl(216, 35%, 30%)",
          800: "hsl(216, 35%, 20%)",
          900: "hsl(216, 35%, 10%)",
        },
        greenGrey: {
          50: "hsl(170, 35%, 97%)",
          100: "hsl(170, 35%, 90%)",
          200: "hsl(170, 35%, 80%)",
          300: "hsl(170, 35%, 70%)",
          400: "hsl(170, 35%, 60%)",
          500: "hsl(170, 35%, 52%)",
          600: "hsl(170, 35%, 40%)",
          700: "hsl(170, 35%, 30%)",
          800: "hsl(170, 35%, 20%)",
          900: "hsl(170, 35%, 10%)",
        },
        rpBrand1: {
          50: "hsl(48, 45%, 97%)",
          100: "hsl(48, 45%, 90%)",
          200: "hsl(48, 45%, 80%)",
          300: "hsl(48, 45%, 70%)",
          400: "hsl(48, 45%, 60%)",
          500: "hsl(48, 45%, 52%)",
          600: "hsl(48, 45%, 40%)",
          700: "hsl(48, 45%, 30%)",
          800: "hsl(48, 45%, 20%)",
          900: "hsl(48, 45%, 10%)",
        },
        rpBrand1grey: {
          50: "hsl(48, 15%, 97%)",
          100: "hsl(48, 15%, 90%)",
          200: "hsl(48, 15%, 80%)",
          300: "hsl(48, 15%, 70%)",
          400: "hsl(48, 15%, 60%)",
          500: "hsl(48, 15%, 52%)",
          600: "hsl(48, 15%, 40%)",
          700: "hsl(48, 15%, 30%)",
          800: "hsl(48, 15%, 20%)",
          900: "hsl(48, 15%, 10%)",
        },
        rpBrand2: {
          50: "hsl(195, 30%, 97%)",
          100: "hsl(195, 30%, 90%)",
          200: "hsl(195, 30%, 80%)",
          300: "hsl(195, 30%, 70%)",
          400: "hsl(195, 30%, 60%)",
          500: "hsl(195, 30%, 52%)",
          600: "hsl(195, 30%, 40%)",
          700: "hsl(195, 30%, 30%)",
          800: "hsl(195, 30%, 20%)",
          900: "hsl(195, 30%, 10%)",
        },
        entityColor: {
          location: "hsl(20, 67%, 97%)",
          person: "hsl(120, 67%, 90%)",
          institution: "hsl(160, 67%, 80%)",
          300: "hsl(195, 67%, 70%)",
          400: "hsl(195, 67%, 60%)",
          500: "hsl(195, 67%, 52%)",
          600: "hsl(195, 67%, 40%)",
          700: "hsl(195, 67%, 30%)",
          800: "hsl(195, 67%, 20%)",
          900: "hsl(195, 67%, 10%)",
        },
      },
      dropShadow: {
        top: "15px 15px 15px rgba(0, 0, 0, 0.75)",
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
}