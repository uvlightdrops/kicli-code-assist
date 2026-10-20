import { defineConfig } from 'tailwindcss/defaultConfig'

export default defineConfig({
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        gray: {
          750: '#1f2937',
        },
      },
    },
  },
})
