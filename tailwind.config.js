module.exports = {
  content: [
    './templates/**/*.html',
    './**/*.py',
    './assets/css/**/*.css',
    './static/css/safelist.css',
    './static/**/*.js'
  ],
  safelist: [
    'bg-white',
    'md:grid-cols-3',
    'text-primary',
    'bg-primary',
    'hover:bg-primary-dark',
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
};
