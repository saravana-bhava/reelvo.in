// File: postcss.config.js — PostCSS config for TailwindCSS & autoprefixer
// Description: Processes Tailwind CSS and adds vendor prefixes for cross-browser support.

module.exports = {
  plugins: {
    tailwindcss: {
      config: './tailwind.config.js', // Ensures consistent config resolution
    },
    autoprefixer: {},
  },
};
