/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        carbon: {
          950: '#0a0c0f',
          900: '#0e1116',
          850: '#12161c',
          800: '#171c24',
          750: '#1d232d',
          700: '#252d3a',
          600: '#343e4f',
          500: '#4d5b70',
          400: '#718096',
          300: '#a0aec0',
          200: '#cbd5e0',
          100: '#edf2f7',
        },
      },
    },
  },
  plugins: [],
};
