/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './routes/**/*.py',
    './assets/css/**/*.css'
  ],
  safelist: [
    'bg-white',
    'text-primary',
    'bg-primary',
    'hover:bg-primary-dark',
    'grid-cols-1',
    'md:grid-cols-3',
    'dark:text-blue-400',
    'dark:bg-gray-800',
    'dark:bg-gray-900',
    'dark:border-gray-700'
  ],
  theme: {
    extend: {
      colors: {
        primary: '#1e88e5',
        'primary-dark': '#1565c0',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/aspect-ratio'),
    require('@tailwindcss/line-clamp'),
  ],
  darkMode: 'class',
}
