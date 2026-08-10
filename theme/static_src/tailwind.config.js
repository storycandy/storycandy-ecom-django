/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    '../templates/**/*.html',
    '../../templates/**/*.html',
    '../../**/templates/**/*.html',
    '../../**/forms.py',
    '../../**/python/*.py',
  ],
  theme: {
    extend: {
      colors: {
        'brand-plum': '#4A1525',
        'brand-coral': '#E84A5F',
        'brand-gold': '#F4A261',
        'brand-teal': '#2A9D8F',
        'brand-cream': '#FFFDF9',
      }
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms'),
    require('@tailwindcss/aspect-ratio'),
    require('daisyui'),
  ],
  daisyui: {
    themes: [
      {
        storycandy: {
          "primary": "#4A1525",          /* Deep Plum / Maroon from Logo Background */
          "primary-content": "#FFFDF9",
          "secondary": "#E84A5F",        /* Coral Pink from Logo Text / Heart */
          "secondary-content": "#FFFDF9",
          "accent": "#F4A261",           /* Warm Mustard Gold from Logo Hoodie & Accents */
          "accent-content": "#4A1525",
          "neutral": "#4A1525",          /* Plum Neutral */
          "neutral-content": "#FFFDF9",
          "base-100": "#FFFDF9",         /* Soft Cream Background */
          "base-200": "#F7EFE5",         /* Soft Warm Beige */
          "base-300": "#EAD3C1",         /* Warm Border Tone */
          "base-content": "#2C121A",      /* Deep Dark Plum Text */
          "info": "#2A9D8F",             /* Teal from Book Cover */
          "success": "#2A9D8F",
          "warning": "#F4A261",
          "error": "#E84A5F",
        },
      },
    ],
    defaultTheme: "storycandy", // Forces DaisyUI to strictly use this color set
  },
}