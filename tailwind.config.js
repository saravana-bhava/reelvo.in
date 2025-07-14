/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './templates/**/*.html.j2',
    './**/*.py',
    './assets/css/**/*.css',
  ],
  safelist: [
    {
      pattern: /grid-cols-\d+/,
      variants: ['md'],
    },
    'grid-cols-1',
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
}
