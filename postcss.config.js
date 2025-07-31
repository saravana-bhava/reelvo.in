// File: postcss.config.js — PostCSS config for TailwindCSS & autoprefixer
// Description: Processes Tailwind CSS and adds vendor prefixes for cross-browser support.

module.exports = {
  plugins: {
    tailwindcss: {
      config: './tailwind.config.js' // Ensures Tailwind uses the correct config file
    },
    autoprefixer: {} // Adds vendor prefixes for broader browser compatibility
  }
};
