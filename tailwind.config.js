// File: tailwind.config.js — Tailwind CSS Configuration
// Description: Configures Tailwind CSS scanning, theming, plugins, and safelist for Reelvo.

module.exports = {
  content: [
    './templates/**/*.html',     // Jinja2/HTML templates
    './**/*.py',                 // Python files (e.g., Flask routes with inline classes)
    './assets/css/**/*.css',     // Custom CSS
    './static/css/safelist.css', // Safelisted styles
    './static/**/*.js',          // JS files with dynamic class names
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
    'dark:border-gray-700',
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
    require('@tailwindcss/forms'),        // Better form element styling
    require('@tailwindcss/typography'),   // Prose styling
    require('@tailwindcss/aspect-ratio'), // Responsive aspect ratios
    require('@tailwindcss/line-clamp'),   // Line clamping for truncation
  ],

  darkMode: 'class', // Supports toggling between dark/light using class
};
